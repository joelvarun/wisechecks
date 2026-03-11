"""Main orchestration script for evaluating an existing RAG extraction pipeline."""

from __future__ import annotations

import importlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from evaluation.deepeval_eval import run_deepeval_extraction_correctness
from evaluation.json_field_eval import evaluate_json_fields
from evaluation.ragas_eval import run_ragas_evaluation
from evaluation.retrieval_eval import evaluate_retrieval
from evaluation.semantic_similarity import evaluate_long_text_semantics
from utils.dataset_loader import DatasetLoader
from utils.ragas_converter import to_ragas_rows

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "data" / "golden_dataset.json"
CONFIG_PATH = BASE_DIR / "configs" / "config.yaml"
OUTPUT_DIR = BASE_DIR / "outputs"


def _resolve_pipeline_function() -> Any:
    """Locate and return `run_rag_pipeline(pdf_text: str) -> dict` from project code.

    Set `RAG_PIPELINE_IMPORT_PATH` to point to your callable module if needed.
    Example: `backend.app.services.pipeline`
    """
    candidate_modules = []
    env_module = __import__("os").environ.get("RAG_PIPELINE_IMPORT_PATH")
    if env_module:
        candidate_modules.append(env_module)

    candidate_modules.extend(
        [
            "backend.app.services.pipeline",
            "app.services.pipeline",
            "pipeline",
        ]
    )

    for module_name in candidate_modules:
        try:
            module = importlib.import_module(module_name)
            fn = getattr(module, "run_rag_pipeline", None)
            if callable(fn):
                logger.info("Using run_rag_pipeline from module: %s", module_name)
                return fn
        except Exception as exc:  # noqa: BLE001 - broad by design for module discovery.
            logger.debug("Skipping module %s due to import error: %s", module_name, exc)

    raise ImportError(
        "Could not locate `run_rag_pipeline(pdf_text: str) -> dict`. "
        "Set RAG_PIPELINE_IMPORT_PATH to the module containing the function."
    )


def run_pipeline_on_dataset(dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run existing RAG pipeline for each dataset record and enrich records with predictions."""
    run_rag_pipeline = _resolve_pipeline_function()
    enriched_records: List[Dict[str, Any]] = []

    for record in dataset:
        prediction = run_rag_pipeline(record["pdf_text"])
        if not isinstance(prediction, dict):
            raise TypeError(
                f"run_rag_pipeline must return dict, got {type(prediction).__name__} for doc_id={record['doc_id']}"
            )

        enriched = {**record, "predicted_output": prediction}

        # Optional convention: pipeline may return retrieved chunks inside prediction payload.
        # If available, extract and keep pure predicted fields separately.
        if "retrieved_chunks" in prediction and isinstance(prediction["retrieved_chunks"], list):
            enriched["retrieved_chunks"] = prediction["retrieved_chunks"]
            enriched["predicted_output"] = {
                k: v for k, v in prediction.items() if k != "retrieved_chunks"
            }

        # Fallback contexts for RAGAS/retrieval eval if pipeline does not expose retrieval.
        enriched.setdefault("retrieved_chunks", record.get("relevant_chunks", []))

        enriched_records.append(enriched)

    return enriched_records


def save_json(path: Path, payload: Dict[str, Any] | List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    config = DatasetLoader.load_yaml_config(CONFIG_PATH)
    dataset = DatasetLoader.load_json_dataset(DATASET_PATH)

    logger.info("Loaded %d records from golden dataset", len(dataset))

    # Step 1: Run pipeline on golden dataset.
    enriched_records = run_pipeline_on_dataset(dataset)

    # Step 2: Convert to RAGAS format.
    ragas_rows = to_ragas_rows(enriched_records)

    # Step 3: RAGAS evaluation.
    ragas_results = run_ragas_evaluation(ragas_rows)

    # Step 4: DeepEval evaluation.
    deepeval_results = run_deepeval_extraction_correctness(enriched_records)

    # Step 5: Field-level JSON evaluation.
    field_df = evaluate_json_fields(enriched_records)

    # Step 6: Long text field semantic similarity.
    semantic_results = evaluate_long_text_semantics(enriched_records)

    # Step 7: Retrieval evaluation.
    retrieval_results = evaluate_retrieval(
        enriched_records,
        top_k=int(config.get("retrieval_top_k", 18)),
    )

    # Step 8: Save outputs.
    save_json(OUTPUT_DIR / "ragas_results.json", ragas_results)
    save_json(OUTPUT_DIR / "deepeval_results.json", deepeval_results)
    field_df.to_csv(OUTPUT_DIR / "field_accuracy.csv", index=False)
    save_json(OUTPUT_DIR / "retrieval_metrics.json", retrieval_results)
    save_json(OUTPUT_DIR / "semantic_similarity.json", semantic_results)

    logger.info("Evaluation completed. Outputs saved under: %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()

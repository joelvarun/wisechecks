"""RAGAS-based evaluation of answer grounding and retrieval context quality."""

from __future__ import annotations

from typing import Any, Dict, List

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness


def run_ragas_evaluation(ragas_rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """Run RAGAS metrics and return aggregate scores."""
    dataset = Dataset.from_list(ragas_rows)
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )
    # Compatible with common RAGAS versions that expose a dict via to_pydict().
    raw = result.to_pydict() if hasattr(result, "to_pydict") else dict(result)
    return {
        "faithfulness": float(raw.get("faithfulness", 0.0)),
        "answer_relevancy": float(raw.get("answer_relevancy", 0.0)),
        "context_precision": float(raw.get("context_precision", 0.0)),
        "context_recall": float(raw.get("context_recall", 0.0)),
    }

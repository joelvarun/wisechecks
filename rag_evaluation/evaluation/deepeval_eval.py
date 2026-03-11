"""DeepEval GEval-based extraction correctness scoring."""

from __future__ import annotations

import json
from statistics import mean
from typing import Any, Dict, List

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase


def run_deepeval_extraction_correctness(prediction_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute extraction correctness score across all records using GEval."""
    metric = GEval(
        name="JSON Extraction Correctness",
        criteria=(
            "Assess whether the extracted JSON output matches expected supplier_name, "
            "supplier_location, and contract_value values accurately and without hallucinations."
        ),
        evaluation_params=["actual_output", "expected_output"],
    )

    per_item_scores: List[Dict[str, Any]] = []
    for record in prediction_records:
        test_case = LLMTestCase(
            input=record["instruction"],
            actual_output=json.dumps(record.get("predicted_output", {}), ensure_ascii=False),
            expected_output=json.dumps(record["expected_output"], ensure_ascii=False),
        )
        metric.measure(test_case)
        per_item_scores.append(
            {
                "doc_id": record["doc_id"],
                "score": float(metric.score),
                "reason": metric.reason,
            }
        )

    return {
        "extraction_correctness_score": mean(item["score"] for item in per_item_scores)
        if per_item_scores
        else 0.0,
        "per_item": per_item_scores,
    }

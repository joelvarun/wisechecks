"""Field-level JSON extraction quality metrics."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

TARGET_FIELDS = ["supplier_name", "supplier_location", "contract_value"]


def evaluate_json_fields(prediction_records: List[Dict[str, Any]]) -> pd.DataFrame:
    """Evaluate each target field and return detailed record-level DataFrame."""
    rows = []

    for record in prediction_records:
        expected = record["expected_output"]
        predicted = record.get("predicted_output", {}) or {}

        correct_fields = 0
        missing_fields = 0

        for field in TARGET_FIELDS:
            pred_value = str(predicted.get(field, "")).strip()
            exp_value = str(expected.get(field, "")).strip()
            is_missing = field not in predicted or not pred_value
            is_correct = pred_value.lower() == exp_value.lower() and not is_missing

            if is_correct:
                correct_fields += 1
            if is_missing:
                missing_fields += 1

        hallucinated_fields = len([key for key in predicted.keys() if key not in TARGET_FIELDS])
        total_fields = len(TARGET_FIELDS)

        rows.append(
            {
                "doc_id": record["doc_id"],
                "field_accuracy": correct_fields / total_fields,
                "missing_field_rate": missing_fields / total_fields,
                "hallucinated_field_rate": hallucinated_fields / max(len(predicted.keys()), 1),
            }
        )

    return pd.DataFrame(rows)

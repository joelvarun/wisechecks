"""Helpers to convert pipeline outputs into RAGAS-compatible rows."""

from __future__ import annotations

import json
from typing import Any, Dict, List


def to_ragas_rows(prediction_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert enriched prediction records into RAGAS evaluation rows."""
    rows: List[Dict[str, Any]] = []
    for record in prediction_records:
        rows.append(
            {
                "question": record["instruction"],
                "contexts": record.get("retrieved_chunks") or record.get("relevant_chunks", []),
                "answer": json.dumps(record.get("predicted_output", {}), ensure_ascii=False),
                "ground_truth": json.dumps(record["expected_output"], ensure_ascii=False),
            }
        )
    return rows

"""Semantic similarity metrics for longer extracted text fields."""

from __future__ import annotations

from typing import Any, Dict, List

from bert_score import score as bert_score
from rouge_score import rouge_scorer


LONG_TEXT_THRESHOLD = 50


def evaluate_long_text_semantics(prediction_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Evaluate long field values (>50 chars) using ROUGE-L and BERTScore."""
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    results: List[Dict[str, Any]] = []

    for record in prediction_records:
        predicted = record.get("predicted_output", {}) or {}
        expected = record["expected_output"]

        for field, expected_value in expected.items():
            predicted_value = str(predicted.get(field, ""))
            expected_value = str(expected_value)

            if len(expected_value) <= LONG_TEXT_THRESHOLD:
                continue

            rouge_l = scorer.score(expected_value, predicted_value)["rougeL"].fmeasure
            _, _, f1 = bert_score([predicted_value], [expected_value], lang="en", verbose=False)

            results.append(
                {
                    "doc_id": record["doc_id"],
                    "field": field,
                    "rouge_l": float(rouge_l),
                    "bert_score_f1": float(f1[0].item()),
                }
            )

    return results

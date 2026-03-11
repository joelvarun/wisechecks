"""Retrieval performance metrics for RAG chunk selection."""

from __future__ import annotations

from statistics import mean
from typing import Any, Dict, List


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def evaluate_retrieval(prediction_records: List[Dict[str, Any]], top_k: int) -> Dict[str, Any]:
    """Compute recall@k, precision@k, and hit rate against annotated relevant chunks."""
    recall_scores: List[float] = []
    precision_scores: List[float] = []
    hits: List[int] = []
    per_item: List[Dict[str, Any]] = []

    for record in prediction_records:
        relevant = {_normalize(chunk) for chunk in record.get("relevant_chunks", [])}
        retrieved_raw = record.get("retrieved_chunks") or []
        retrieved = [_normalize(chunk) for chunk in retrieved_raw[:top_k]]

        matched = len([chunk for chunk in retrieved if chunk in relevant])
        recall = matched / max(len(relevant), 1)
        precision = matched / max(len(retrieved), 1)
        hit = 1 if matched > 0 else 0

        recall_scores.append(recall)
        precision_scores.append(precision)
        hits.append(hit)

        per_item.append(
            {
                "doc_id": record["doc_id"],
                "recall@k": recall,
                "precision@k": precision,
                "hit": hit,
            }
        )

    return {
        "recall@k": mean(recall_scores) if recall_scores else 0.0,
        "precision@k": mean(precision_scores) if precision_scores else 0.0,
        "hit_rate": mean(hits) if hits else 0.0,
        "per_item": per_item,
    }

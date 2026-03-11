"""Dataset and configuration loading utilities for the RAG evaluation framework."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import yaml


class DatasetLoader:
    """Load and validate evaluation datasets and config files."""

    REQUIRED_KEYS = {
        "doc_id",
        "prompt_id",
        "instruction",
        "pdf_text",
        "relevant_chunks",
        "expected_output",
    }

    @staticmethod
    def load_json_dataset(dataset_path: str | Path) -> List[Dict[str, Any]]:
        dataset_path = Path(dataset_path)
        with dataset_path.open("r", encoding="utf-8") as file:
            records = json.load(file)

        if not isinstance(records, list):
            raise ValueError("Dataset file must contain a JSON array of records.")

        for idx, record in enumerate(records):
            missing = DatasetLoader.REQUIRED_KEYS - set(record.keys())
            if missing:
                raise ValueError(f"Record index {idx} is missing required keys: {sorted(missing)}")

        return records

    @staticmethod
    def load_yaml_config(config_path: str | Path) -> Dict[str, Any]:
        config_path = Path(config_path)
        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file) or {}
        if not isinstance(config, dict):
            raise ValueError("Config must deserialize to a dictionary.")
        return config

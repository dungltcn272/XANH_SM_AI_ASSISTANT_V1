# -*- coding: utf-8 -*-
import os
import json
from typing import List, Dict, Any

# Load from official Vietnamese accented Golden Dataset JSON file
JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden_dataset.json")

try:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        GOLDEN_DATASET: List[Dict[str, Any]] = json.load(f)
except Exception as e:
    print(f"[WARN] Failed to load golden_dataset.json: {e}")
    # Fallback
    GOLDEN_DATASET = []

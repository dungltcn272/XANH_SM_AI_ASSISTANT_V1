import json
import os

def load_golden_dataset():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "golden_dataset.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

GOLDEN_DATASET = load_golden_dataset()

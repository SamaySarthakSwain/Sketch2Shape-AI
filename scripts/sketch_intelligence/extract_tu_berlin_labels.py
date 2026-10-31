"""
Extract official TU-Berlin 250 category label names and create verified mapping.
"""

import urllib.request
import re
import json
from pathlib import Path

def main():
    url = "https://huggingface.co/datasets/kmewhort/tu-berlin-png/raw/main/README.md"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        text = resp.read().decode("utf-8")

    pattern = re.compile(r"'(\d+)':\s*(.+)")
    mapping = {}
    for m in pattern.finditer(text):
        idx = int(m.group(1))
        name = m.group(2).strip()
        mapping[idx] = name

    print(f"Extracted {len(mapping)} classes!")
    out_path = Path(r"C:\Sketch2Shape-AI\datasets\tu_berlin\metadata\tu_berlin_class_names.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)

    print(f"Successfully saved to {out_path}")

if __name__ == "__main__":
    main()

"""
Automated Downloader for TU-Berlin Sketch Dataset (All 250 Categories, 20,000 Sketches)
Academic Reference: "How Do Humans Sketch Objects?" (SIGGRAPH 2012) - Mathias Eitz, James Hays, Marc Alexa
Official Source: https://cybertron.cg.tu-berlin.de/eitz/projects/classifysketch/
Verified Mirror: Hugging Face (kmewhort/tu-berlin-png) with original PNG extraction
"""

import os
import sys
import time
import json
import urllib.request
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path("C:/Sketch2Shape-AI").resolve()
DATASET_DIR = BASE_DIR / "datasets" / "tu_berlin"
RAW_DIR = DATASET_DIR / "raw"
PROCESSED_DIR = DATASET_DIR / "processed"
METADATA_DIR = DATASET_DIR / "metadata"

HF_BASE_URL = "https://huggingface.co/datasets/kmewhort/tu-berlin-png/resolve/main/data/"
PARQUET_FILES = [
    ("test-00000-of-00001-4c87e761e3fce046.parquet", 5_913_920),
    ("train-00000-of-00002-cf60531eb207325d.parquet", 292_515_840),
    ("train-00001-of-00002-92131dc5d116063a.parquet", 292_442_112)
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Sketch2Shape-AI/1.0"


def download_file(url: str, dest_path: Path, expected_size: int = None) -> bool:
    if dest_path.exists() and dest_path.stat().st_size > 1_000_000:
        if expected_size is None or abs(dest_path.stat().st_size - expected_size) < 100_000:
            print(f"[EXISTS] {dest_path.name} ({dest_path.stat().st_size / (1024*1024):.1f} MB)")
            return True

    temp_path = dest_path.with_suffix(".tmp")
    print(f"[DOWNLOADING] {dest_path.name} from {url}...")
    t0 = time.time()
    
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        total_len = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        
        with open(temp_path, "wb") as f:
            while True:
                chunk = resp.read(131072)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                elapsed = time.time() - t0
                speed = (downloaded / (1024*1024)) / elapsed if elapsed > 0 else 0
                pct = (downloaded / total_len * 100) if total_len > 0 else 0
                remaining_bytes = total_len - downloaded
                eta_s = remaining_bytes / (speed * 1024 * 1024) if speed > 0 else 0
                print(f"\r  Progress: {pct:5.1f}% | {downloaded / (1024*1024):6.1f} MB / {total_len / (1024*1024):6.1f} MB | Speed: {speed:5.1f} MB/s | Time Left: ~{eta_s:4.0f}s", end="")

    print()
    if temp_path.exists():
        if dest_path.exists():
            dest_path.unlink()
        temp_path.rename(dest_path)
    return True


def extract_metadata_and_categories():
    """Reads parquet files using PyArrow / Pandas to generate full category and sample manifest."""
    try:
        import pandas as pd
        parquet_paths = list(RAW_DIR.glob("*.parquet"))
        if not parquet_paths:
            print("[WARN] No parquet files found to inspect.")
            return

        print("[INFO] Inspecting TU-Berlin parquet partitions...")
        total_records = 0
        all_categories = set()
        
        for p in parquet_paths:
            df = pd.read_parquet(p, columns=["label"] if "label" in pd.read_parquet(p).columns else None)
            total_records += len(df)
            if "label" in df.columns:
                all_categories.update(df["label"].unique().tolist())

        categories_sorted = sorted(list(all_categories))
        print(f"[INFO] TU-Berlin Summary: {len(categories_sorted)} categories, {total_records:,} total sketches.")
        
        cat_file = METADATA_DIR / "categories.txt"
        with open(cat_file, "w", encoding="utf-8") as f:
            for c in categories_sorted:
                f.write(f"{c}\n")

        manifest_file = METADATA_DIR / "tu_berlin_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump({
                "dataset": "TU-Berlin Sketch Dataset",
                "reference": "How Do Humans Sketch Objects? (SIGGRAPH 2012)",
                "authors": ["Mathias Eitz", "James Hays", "Marc Alexa"],
                "official_url": "https://cybertron.cg.tu-berlin.de/eitz/projects/classifysketch/",
                "mirror_source": "Hugging Face (kmewhort/tu-berlin-png)",
                "license": "Creative Commons Attribution 4.0 International / Academic Research",
                "category_count": len(categories_sorted),
                "total_sketches": total_records,
                "sketches_per_category": 80,
                "categories": categories_sorted
            }, f, indent=2)
        print(f"[INFO] Saved TU-Berlin manifest to: {manifest_file}")

    except Exception as e:
        print(f"[INFO] Parquet inspection notice: {e}")


def run():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("🎨 Sketch2Shape AI - TU-Berlin Sketch Dataset Downloader")
    print(f"Target Directory: {RAW_DIR}")
    print("=" * 70)

    total_downloaded_bytes = 0
    t_start = time.time()

    for filename, size in PARQUET_FILES:
        target = RAW_DIR / filename
        url = f"{HF_BASE_URL}{filename}"
        download_file(url, target, size)
        if target.exists():
            total_downloaded_bytes += target.stat().st_size

    print(f"\n[DONE] TU-Berlin Download Complete! Total: {total_downloaded_bytes / (1024*1024):.1f} MB")
    extract_metadata_and_categories()

if __name__ == "__main__":
    run()

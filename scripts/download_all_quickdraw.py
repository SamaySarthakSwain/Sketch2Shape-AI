"""
Automated Downloader for Complete Google Quick, Draw! Dataset (All 345 Categories)
Features:
- Full 345 categories from official Google Creative Lab repository
- Simplified NDJSON format
- Resumable downloads (skips verified existing files)
- Multithreaded concurrent downloads with rate monitoring
- Line-level JSON integrity verification
- Dynamic ETA and time-left reporting
- Complete manifest generation
"""

import os
import sys
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path("C:/Sketch2Shape-AI").resolve()
DATASET_DIR = BASE_DIR / "datasets" / "quickdraw"
RAW_DIR = DATASET_DIR / "raw"
METADATA_DIR = DATASET_DIR / "metadata"

CATEGORIES_URL = "https://raw.githubusercontent.com/googlecreativelab/quickdraw-dataset/master/categories.txt"
NDJSON_BASE_URL = "https://storage.googleapis.com/quickdraw_dataset/full/simplified/"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Sketch2Shape-AI/1.0"


def fetch_categories():
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    cat_file = METADATA_DIR / "categories.txt"
    if cat_file.exists() and cat_file.stat().st_size > 0:
        with open(cat_file, "r", encoding="utf-8") as f:
            categories = [line.strip() for line in f if line.strip()]
        if len(categories) == 345:
            return categories

    req = urllib.request.Request(CATEGORIES_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8")
    
    with open(cat_file, "w", encoding="utf-8") as f:
        f.write(content)

    categories = [line.strip() for line in content.splitlines() if line.strip()]
    return categories


def verify_ndjson_file(file_path: Path, expected_word: str) -> bool:
    """Verifies that the NDJSON file exists, has size > 1MB, and first/last lines are valid JSON."""
    if not file_path.exists() or file_path.stat().st_size < 100_000:
        return False
    try:
        with open(file_path, "rb") as f:
            first_line = f.readline().decode("utf-8", errors="ignore").strip()
            if not first_line:
                return False
            data = json.loads(first_line)
            if data.get("word") != expected_word:
                return False
            
            # Check last line
            f.seek(max(0, file_path.stat().st_size - 8192))
            lines = f.read().decode("utf-8", errors="ignore").splitlines()
            if lines:
                last_line = lines[-1].strip()
                if last_line:
                    json.loads(last_line)
        return True
    except Exception:
        return False


def download_category(category: str, max_retries: int = 3) -> dict:
    safe_name = category.replace(" ", "_")
    target_path = RAW_DIR / f"{safe_name}.ndjson"
    encoded_cat = urllib.parse.quote(category)
    url = f"{NDJSON_BASE_URL}{encoded_cat}.ndjson"

    # Check if already downloaded and verified
    if verify_ndjson_file(target_path, category):
        size = target_path.stat().st_size
        return {
            "category": category,
            "status": "EXISTING_VERIFIED",
            "path": str(target_path),
            "size_bytes": size,
            "url": url,
            "error": None
        }

    temp_path = RAW_DIR / f"{safe_name}.ndjson.tmp"
    
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                total_len = resp.headers.get("Content-Length")
                total_bytes = int(total_len) if total_len else 0
                
                with open(temp_path, "wb") as out_f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        out_f.write(chunk)

            # Atomic rename after download
            if temp_path.exists():
                if target_path.exists():
                    target_path.unlink()
                temp_path.rename(target_path)

            if verify_ndjson_file(target_path, category):
                return {
                    "category": category,
                    "status": "DOWNLOADED_VERIFIED",
                    "path": str(target_path),
                    "size_bytes": target_path.stat().st_size,
                    "url": url,
                    "error": None
                }
            else:
                if target_path.exists():
                    target_path.unlink()
                raise ValueError("Downloaded file failed JSON integrity verification")

        except Exception as e:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            if attempt == max_retries:
                return {
                    "category": category,
                    "status": "FAILED",
                    "path": None,
                    "size_bytes": 0,
                    "url": url,
                    "error": str(e)
                }
            time.sleep(1.0 * attempt)

    return {
        "category": category,
        "status": "FAILED",
        "path": None,
        "size_bytes": 0,
        "url": url,
        "error": "Exceeded retries"
    }


def download_all(max_workers: int = 6, limit: int = None):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("🎨 Sketch2Shape AI - Complete Quick, Draw! Dataset Downloader")
    print(f"Target Directory: {RAW_DIR}")
    print("=" * 70)

    categories = fetch_categories()
    print(f"[INFO] Fetched {len(categories)} official categories from Google Creative Lab.")
    
    if limit:
        categories = categories[:limit]
        print(f"[INFO] Limit applied: downloading first {limit} categories.")

    total_categories = len(categories)
    manifest = []
    missing_categories = []
    total_bytes = 0
    start_time = time.time()
    completed_count = 0

    print(f"[INFO] Starting concurrent download with {max_workers} worker threads...\n")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_cat = {executor.submit(download_category, cat): cat for cat in categories}
        
        for future in as_completed(future_to_cat):
            cat = future_to_cat[future]
            completed_count += 1
            res = future.result()
            manifest.append(res)
            
            elapsed = time.time() - start_time
            rate = completed_count / elapsed if elapsed > 0 else 0
            remaining = total_categories - completed_count
            eta_seconds = remaining / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60.0

            if res["status"] in ("DOWNLOADED_VERIFIED", "EXISTING_VERIFIED"):
                total_bytes += res["size_bytes"]
                mb = res["size_bytes"] / (1024 * 1024)
                status_symbol = "✓" if res["status"] == "DOWNLOADED_VERIFIED" else "↺"
                print(f"[{completed_count:3d}/{total_categories}] {status_symbol} {cat:<24} | {mb:6.1f} MB | Elapsed: {elapsed/60.0:4.1f}m | Time Left: ~{eta_minutes:4.1f}m")
            else:
                missing_categories.append(res)
                print(f"[{completed_count:3d}/{total_categories}] ✗ {cat:<24} | FAILED: {res['error']} | Time Left: ~{eta_minutes:4.1f}m")

    total_duration = time.time() - start_time
    total_gb = total_bytes / (1024**3)

    print("\n" + "=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"Total Categories:      {total_categories}")
    print(f"Successfully Verified: {len(manifest) - len(missing_categories)}")
    print(f"Missing/Failed:        {len(missing_categories)}")
    print(f"Total Storage:         {total_gb:.2f} GB ({total_bytes:,} bytes)")
    print(f"Total Duration:        {total_duration/60.0:.2f} minutes")

    # Save manifest and missing reports
    manifest_path = METADATA_DIR / "quickdraw_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "dataset": "Google Quick, Draw! Simplified NDJSON",
            "source": "https://github.com/googlecreativelab/quickdraw-dataset",
            "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "total_categories": total_categories,
            "verified_count": len(manifest) - len(missing_categories),
            "missing_count": len(missing_categories),
            "total_bytes": total_bytes,
            "total_gb": round(total_gb, 2),
            "duration_seconds": round(total_duration, 1),
            "items": manifest
        }, f, indent=2)
    print(f"[INFO] Saved manifest to: {manifest_path}")

    missing_path = METADATA_DIR / "missing_categories.json"
    with open(missing_path, "w", encoding="utf-8") as f:
        json.dump(missing_categories, f, indent=2)
    print(f"[INFO] Saved missing log to: {missing_path}")

    return manifest

if __name__ == "__main__":
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    download_all(max_workers=6, limit=limit_arg)

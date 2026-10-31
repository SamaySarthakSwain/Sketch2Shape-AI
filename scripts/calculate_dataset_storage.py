"""
Storage Calculation and Disk Space Safety Monitor for Sketch2Shape AI Datasets
Calculates exact bytes per dataset directory and verifies available drive headroom.
"""

import os
import sys
import json
import shutil
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path("C:/Sketch2Shape-AI").resolve()
DATASETS_DIR = BASE_DIR / "datasets"
REPORTS_DIR = DATASETS_DIR / "reports"


def get_dir_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def calculate_storage():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    total_drive, used_drive, free_drive = shutil.disk_usage("C:/")
    
    datasets = {
        "quickdraw_raw": DATASETS_DIR / "quickdraw" / "raw",
        "quickdraw_metadata": DATASETS_DIR / "quickdraw" / "metadata",
        "tu_berlin_raw": DATASETS_DIR / "tu_berlin" / "raw",
        "tu_berlin_metadata": DATASETS_DIR / "tu_berlin" / "metadata",
        "objaverse_metadata": DATASETS_DIR / "objaverse" / "metadata",
        "objaverse_selected_assets": DATASETS_DIR / "objaverse" / "selected_assets",
        "shapenet_metadata": DATASETS_DIR / "shapenet" / "metadata",
        "shapenet_selected_assets": DATASETS_DIR / "shapenet" / "selected_assets",
    }

    storage_breakdown = {}
    total_datasets_bytes = 0

    print("=" * 70)
    print("📊 Sketch2Shape AI - Dataset Storage Footprint Report")
    print("=" * 70)

    for name, path in datasets.items():
        size = get_dir_size(path)
        total_datasets_bytes += size
        mb = size / (1024 * 1024)
        file_count = sum(1 for _ in path.glob("*")) if path.exists() else 0
        storage_breakdown[name] = {
            "path": str(path),
            "size_bytes": size,
            "size_mb": round(mb, 2),
            "file_count": file_count
        }
        print(f"  {name:<28} : {mb:8.2f} MB ({file_count:4d} files)")

    total_datasets_gb = total_datasets_bytes / (1024**3)
    free_drive_gb = free_drive / (1024**3)
    used_drive_gb = used_drive / (1024**3)
    total_drive_gb = total_drive / (1024**3)

    print("-" * 70)
    print(f"Total Datasets Storage:   {total_datasets_gb:.2f} GB ({total_datasets_bytes:,} bytes)")
    print(f"C: Drive Available Free:  {free_drive_gb:.2f} GB ({free_drive:,} bytes)")
    print(f"C: Drive Total Capacity:  {total_drive_gb:.2f} GB")
    print(f"Drive Safety Status:      {'SAFE (>30GB headroom)' if free_drive_gb > 30 else 'WARNING (<30GB free)'}")
    print("=" * 70)

    report_file = REPORTS_DIR / "storage_consumption_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_datasets_bytes": total_datasets_bytes,
            "total_datasets_gb": round(total_datasets_gb, 3),
            "drive_c": {
                "free_gb": round(free_drive_gb, 2),
                "used_gb": round(used_drive_gb, 2),
                "total_gb": round(total_drive_gb, 2),
                "safety_status": "SAFE" if free_drive_gb > 30 else "WARNING"
            },
            "datasets": storage_breakdown
        }, f, indent=2)

    return report_file


if __name__ == "__main__":
    calculate_storage()

"""
Reproducible Downloader for Selected Curated Objaverse 3D Assets (GLB Format)
Prioritizes objects with clear geometry, relevant categories, and valid GLB structures.
Validates each downloaded model with Trimesh.
"""

import os
import sys
import json
import time
import urllib.request
import trimesh
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path("C:/Sketch2Shape-AI").resolve()
METADATA_DIR = BASE_DIR / "datasets" / "objaverse" / "metadata"
ASSETS_DIR = BASE_DIR / "datasets" / "objaverse" / "selected_assets"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Sketch2Shape-AI/1.0"


def download_selected_assets(limit: int = 10):
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    curated_path = METADATA_DIR / "curated_selection.json"
    
    if not curated_path.exists():
        print(f"[ERROR] Curated selection not found at: {curated_path}. Run download_objaverse_metadata.py first.")
        return

    with open(curated_path, "r", encoding="utf-8") as f:
        curated_data = json.load(f)

    models = curated_data.get("models", [])[:limit]
    print("=" * 70)
    print(f"🎨 Sketch2Shape AI - Downloading {len(models)} Curated Objaverse 3D Assets")
    print(f"Destination: {ASSETS_DIR}")
    print("=" * 70)

    downloaded_records = []
    t_start = time.time()

    for idx, item in enumerate(models, 1):
        uid = item["uid"]
        cat = item.get("category", "object")
        url = item["download_url"]
        target_glb = ASSETS_DIR / f"{cat}_{uid[:8]}.glb"

        elapsed = time.time() - t_start
        avg_time = elapsed / (idx - 1) if idx > 1 else 0
        rem_items = len(models) - (idx - 1)
        eta_s = rem_items * avg_time

        print(f"[{idx}/{len(models)}] Fetching {target_glb.name} (Category: {cat})... | Time Left: ~{eta_s:3.0f}s")

        if target_glb.exists() and target_glb.stat().st_size > 50_000:
            print(f"  [EXISTS] Already downloaded ({target_glb.stat().st_size / (1024*1024):.2f} MB)")
            downloaded_records.append({
                "uid": uid,
                "category": cat,
                "path": str(target_glb),
                "size_bytes": target_glb.stat().st_size,
                "status": "EXISTING_VERIFIED"
            })
            continue

        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=45) as resp:
                glb_data = resp.read()

            with open(target_glb, "wb") as f:
                f.write(glb_data)

            # Validate geometry via Trimesh
            mesh = trimesh.load(str(target_glb), process=False)
            if isinstance(mesh, trimesh.Scene):
                mesh = trimesh.util.concatenate([g for g in mesh.geometry.values() if isinstance(g, trimesh.Trimesh)])

            verts = len(mesh.vertices)
            faces = len(mesh.faces)
            size_mb = target_glb.stat().st_size / (1024 * 1024)
            print(f"  ✓ Verified GLB: {verts:,} vertices, {faces:,} faces ({size_mb:.2f} MB)")

            downloaded_records.append({
                "uid": uid,
                "category": cat,
                "path": str(target_glb),
                "size_bytes": target_glb.stat().st_size,
                "vertices": verts,
                "faces": faces,
                "status": "DOWNLOADED_VERIFIED"
            })

        except Exception as e:
            print(f"  ✗ Failed {uid}: {e}")
            if target_glb.exists():
                target_glb.unlink()

    report_path = METADATA_DIR / "selected_assets_manifest.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_downloaded": len(downloaded_records),
            "assets": downloaded_records
        }, f, indent=2)
    print(f"\n[DONE] Finished asset download. Saved record to: {report_path}")

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    download_selected_assets(limit=count)

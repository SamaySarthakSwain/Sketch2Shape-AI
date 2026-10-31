"""
FastAPI Pipeline V1 Endpoint Tests
Tests async and sync reconstruction endpoints, status polling, cancellation, and job queries.
"""

import os
import sys
import time
import base64
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import numpy as np
from PIL import Image

from app.main import app

client = TestClient(app)


@pytest.fixture
def test_image_b64(tmp_path):
    arr = np.ones((128, 128), dtype=np.uint8) * 255
    arr[30:90, 50:70] = 0
    img_path = tmp_path / "api_test_sketch.png"
    Image.fromarray(arr).save(str(img_path))

    with open(img_path, "rb") as f:
        data = f.read()
    return f"data:image/png;base64,{base64.b64encode(data).decode('utf-8')}"


def test_pipeline_jobs_empty_or_list():
    resp = client.get("/api/v1/pipeline/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert "count" in data
    assert "jobs" in data
    assert isinstance(data["jobs"], list)


def test_pipeline_generate_missing_input():
    resp = client.post("/api/v1/pipeline/generate", json={
        "preferred_model": "procedural"
    })
    assert resp.status_code == 400
    assert "Must provide either" in resp.json()["detail"]


def test_pipeline_generate_async_flow(test_image_b64):
    # 1. Submit async job
    resp = client.post("/api/v1/pipeline/generate", json={
        "image_b64": test_image_b64,
        "preferred_model": "procedural",
        "quality_preset": "fast",
        "async_execution": True,
        "category_override": "chair"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["status"] in ["queued", "processing", "completed"]
    job_id = data["job_id"]

    # 2. Poll status
    time.sleep(1.0)
    status_resp = client.get(f"/api/v1/pipeline/status/{job_id}")
    assert status_resp.status_code == 200
    s_data = status_resp.json()
    assert s_data["job_id"] == job_id
    assert "current_stage" in s_data
    assert "stage_history" in s_data

    # 3. Wait for procedural completion (usually 1-2 seconds)
    max_wait = 15
    start = time.time()
    completed = False
    while time.time() - start < max_wait:
        poll = client.get(f"/api/v1/pipeline/status/{job_id}").json()
        if poll["status"] == "completed":
            completed = True
            break
        time.sleep(0.5)

    assert completed is True

    # 4. Query full result
    result_resp = client.get(f"/api/v1/pipeline/result/{job_id}")
    assert result_resp.status_code == 200
    r_data = result_resp.json()
    assert r_data["status"] == "completed"
    assert "artifacts" in r_data
    assert "web_artifacts" in r_data


def test_pipeline_cancel_nonexistent_job():
    resp = client.post("/api/v1/pipeline/cancel/job_nonexistent_123")
    assert resp.status_code == 404

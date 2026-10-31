"""
End-to-End Real Model Inference Test
Tests the full lifecycle from sketch -> OpenCV preprocessing -> Sketch Intelligence -> 3D Reconstruction -> Validation -> Multi-format Export.
"""

import base64
import cv2
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
import trimesh
import io

client = TestClient(app)

def generate_sample_sketch_b64():
    # Draw a 2D vase on a white canvas
    img = np.ones((512, 512), dtype=np.uint8) * 255
    cx, cy = 256, 256
    # Vase outline
    cv2.ellipse(img, (cx, cy + 50), (90, 140), 0, 0, 360, 0, thickness=6)
    cv2.rectangle(img, (cx - 40, cy - 140), (cx + 40, cy - 60), 0, thickness=6)
    cv2.ellipse(img, (cx, cy - 140), (40, 15), 0, 0, 360, 0, thickness=6)
    
    _, buffer = cv2.imencode(".png", img)
    return f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"

def test_e2e_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "gpu" in data
    print("\n[E2E] System Health & Hardware:", data)

def test_e2e_sketch_preprocess_and_intelligence():
    sketch_b64 = generate_sample_sketch_b64()
    response = client.post("/api/sketch/preprocess", json={"image_b64": sketch_b64})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "cleaned_image_b64" in data
    assert "depth_map_b64" in data
    assert "normal_map_b64" in data
    assert "intelligence" in data
    
    intel = data["intelligence"]
    assert "classification" in intel
    assert "symmetry" in intel
    print("\n[E2E] Preprocessing & Intelligence:", intel["classification"])

def test_e2e_real_3d_reconstruction_and_export():
    sketch_b64 = generate_sample_sketch_b64()
    payload = {
        "image_b64": sketch_b64,
        "engine": "hybrid",
        "prompt": "ceramic vase sculpture"
    }
    response = client.post("/api/reconstruct/generate", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    model_id = res["model_id"]
    val = res["validation"]
    
    print(f"\n[E2E] 3D Model Generated in {res['reconstruction_time_ms']}ms!")
    print(f"[E2E] Watertight: {val['is_watertight']}, Faces: {val['face_count']}, Score: {val['health_score']}")
    
    assert val["is_watertight"] is True
    assert val["face_count"] > 100
    assert val["health_score"] >= 80

    # Test downloading GLB
    glb_res = client.get(res["downloads"]["glb"])
    assert glb_res.status_code == 200
    assert glb_res.content[:4] == b"glTF"

    # Test downloading STL
    stl_res = client.get(res["downloads"]["stl"])
    assert stl_res.status_code == 200
    assert len(stl_res.content) > 100

    # Verify loaded mesh from binary stream is watertight
    reloaded = trimesh.load(io.BytesIO(glb_res.content), file_type="glb")
    if isinstance(reloaded, trimesh.Scene):
        reloaded = reloaded.dump(concatenate=True)
    assert reloaded.is_watertight is True

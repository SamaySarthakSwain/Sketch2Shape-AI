# Sketch2Shape AI — Production Deployment & Setup Guide

---

### 1. Local Development Setup

#### Prerequisites
* Windows 11, Ubuntu 22.04 LTS, or macOS (Apple Silicon).
* Python 3.10 or 3.11.
* Node.js v18.0+ & npm v9.0+.
* NVIDIA GPU with CUDA 12.1 (optional for local neural reconstruction; procedural engine runs on CPU).

#### Backend Setup
```bash
# 1. Clone repository
git clone https://github.com/TencentARC/InstantMesh.git C:\Sketch2Shape-AI
cd C:\Sketch2Shape-AI

# 2. Create and activate Python virtual environment
python -m venv .venv_instantmesh
# On Windows PowerShell:
.\.venv_instantmesh\Scripts\Activate.ps1
# On Linux/macOS:
source .venv_instantmesh/bin/activate

# 3. Install core backend dependencies
pip install -r backend/requirements.txt
pip install lxml trimesh

# 4. Configure environment credentials
cp .env.example .env
# Edit .env and supply MESHY_API_KEY, TRIPO_API_KEY if using cloud AI providers

# 5. Launch FastAPI backend server
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Frontend Setup
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev -- --host 0.0.0.0 --port 5173

# 4. Open in browser: http://localhost:5173
```

---

### 2. Production Cloud Deployment Strategies

#### Strategy A: Serverless Frontend on Vercel / Netlify
1. Connect GitHub repository to Vercel or Netlify.
2. Root directory: `frontend`.
3. Build command: `npm run build`.
4. Output directory: `dist`.
5. Environment variable: `VITE_API_BASE_URL=https://api.sketch2shape.ai`.

#### Strategy B: Lightweight API Server (Render / Railway)
* **Architecture:** Deploys the FastAPI backend running the Procedural Engine and routing to Cloud AI Providers (Meshy, Tripo3D, Rodin).
* **Requirements:** 1 vCPU, 1 GB RAM, 0 GB VRAM.
* **Dockerfile:**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend /app
ENV PYTHONPATH=/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Strategy C: Full Neural Workstation / GPU Cloud (RunPod / Lambda Labs)
* **Architecture:** For hosting local InstantMesh Zero123++ diffusion without external API subscriptions.
* **Instance Recommendation:** NVIDIA RTX 4090 ($24\text{ GB}$ VRAM) or NVIDIA A10G ($24\text{ GB}$ VRAM).
* **Throughput:** ~15–25 seconds per full neural triplane reconstruction.

"""
Sketch2Shape AI - Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings, EXPORTS_DIR
from pathlib import Path
from app.routes import (
    health_router,
    sketch_router,
    reconstruct_router,
    intelligence_router,
    reconstruction_v1_router,
    geometry_v1_router,
    pipeline_v1_router,
)

MULTIVIEW_STATIC_DIR = Path(r"C:\Sketch2Shape-AI\outputs\geometry_analysis\multiview")
MULTIVIEW_STATIC_DIR.mkdir(parents=True, exist_ok=True)

JOBS_STATIC_DIR = Path(r"C:\Sketch2Shape-AI\backend\data\jobs")
JOBS_STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Sketch2Shape AI: End-to-end 2D Sketch to Watertight 3D Mesh Reconstruction Engine"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(sketch_router)
app.include_router(reconstruct_router)
app.include_router(intelligence_router)
app.include_router(reconstruction_v1_router)
app.include_router(geometry_v1_router)
app.include_router(pipeline_v1_router)

# Mount static folders
app.mount("/static/exports", StaticFiles(directory=str(EXPORTS_DIR)), name="exports")
app.mount("/static/multiview", StaticFiles(directory=str(MULTIVIEW_STATIC_DIR)), name="multiview")
app.mount("/static/jobs", StaticFiles(directory=str(JOBS_STATIC_DIR)), name="jobs")

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs_url": "/docs",
        "version": settings.VERSION,
        "status": "online"
    }

import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR.parent
STORAGE_DIR = BASE_DIR / "storage"
EXPORTS_DIR = STORAGE_DIR / "exports"
UPLOADS_DIR = STORAGE_DIR / "uploads"
MODELS_DIR = BASE_DIR / "models"

for folder in [STORAGE_DIR, EXPORTS_DIR, UPLOADS_DIR, MODELS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Automatically load environment variables from .env files without requiring python-dotenv
def _load_env_file(filepath: Path):
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and not os.environ.get(key):
                        os.environ[key] = val

_load_env_file(BASE_DIR / ".env")
_load_env_file(WORKSPACE_DIR / ".env")

class Settings(BaseModel):
    APP_NAME: str = "Sketch2Shape AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ]
    DEFAULT_INFERENCE_ENGINE: str = "hybrid" # procedural, shape_e, colab
    COLAB_ENDPOINT_URL: str = os.getenv("SKETCH2SHAPE_COLAB_URL", "")
    COLAB_TIMEOUT_SECONDS: int = 180
    DEVICE: str = os.getenv("DEVICE", "cuda") # will fallback to cpu if cuda unavailable
    MAX_IMAGE_DIM: int = 1024
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()

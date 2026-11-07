"""Backend Configuration and Environment Settings."""

import os
from pathlib import Path
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseModel):
    app_name: str = "Music Genre Classifier API"
    version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1")
    
    # Model configuration
    model_checkpoint_path: str = os.getenv(
        "MODEL_PATH",
        str(ROOT_DIR / "artifacts" / "models" / "genre_cnn_baseline.pt")
    )
    
    # Audio configuration
    sample_rate: int = 22050
    default_duration_seconds: float = 30.0
    live_window_seconds: float = 3.0
    max_upload_size_bytes: int = 30 * 1024 * 1024  # 30 MB
    
    # Cache
    spectrogram_cache_size: int = 100
    
    # Allowed CORS Origins
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]


settings = Settings()

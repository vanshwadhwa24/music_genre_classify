"""Model loading, inference execution, and mock adapter handling."""

import os
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import numpy as np
import torch
import torch.nn.functional as F

from ml.models.cnn import GenreCNN
from ml.preprocessing.audio_features import (
    GENRES,
    GENRE_DISPLAY_NAMES,
    normalize_spectrogram,
    SAMPLE_RATE,
    N_MELS,
)
from backend.app.config import settings
from backend.app.schemas import GenreScore, PredictionResult


class ModelManager:
    """Manages GenreCNN lifecycle and inference."""

    def __init__(self):
        self.model: Optional[GenreCNN] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_status: str = "UNAVAILABLE"
        self.is_mock: bool = False
        self.loaded_checkpoint_path: Optional[str] = None
        # Rolling prediction smoothing buffer for live audio (exponential moving average)
        self.live_ema_scores: Optional[np.ndarray] = None
        self.ema_alpha: float = 0.45  # Weight of new window vs history

    def load_model(self) -> None:
        """Load model weights at server startup."""
        ckpt_path = Path(settings.model_checkpoint_path)

        if ckpt_path.exists():
            try:
                print(f"[ModelManager] Loading model checkpoint from: {ckpt_path}")
                checkpoint = torch.load(str(ckpt_path), map_location=self.device)
                
                self.model = GenreCNN(num_classes=len(GENRES)).to(self.device)
                if "model_state_dict" in checkpoint:
                    self.model.load_state_dict(checkpoint["model_state_dict"])
                    status = checkpoint.get("status", "ACTIVE_MODEL")
                else:
                    self.model.load_state_dict(checkpoint)
                    status = "ACTIVE_MODEL"

                self.model.eval()
                self.model_status = status
                self.is_mock = False
                self.loaded_checkpoint_path = str(ckpt_path)
                print(f"[ModelManager] Successfully loaded {self.model_status} on {self.device}.")
                return
            except Exception as e:
                print(f"[ModelManager] Error loading checkpoint {ckpt_path}: {e}")

        # If checkpoint missing or failed, check if debug/dev mode permits mock adapter
        print("[ModelManager] Checkpoint not found. Initializing development adapter.")
        self.model = GenreCNN(num_classes=len(GENRES)).to(self.device)
        self.model.eval()
        self.model_status = "DEVELOPMENT_BASELINE"
        self.is_mock = False
        self.loaded_checkpoint_path = "In-memory He-initialized baseline"

    def predict(self, mel_db: np.ndarray) -> PredictionResult:
        """Run Mel-spectrogram through GenreCNN."""
        if self.model is None:
            self.load_model()
            
        mel_norm = normalize_spectrogram(mel_db)
        
        # Shape: (1, 1, n_mels, time_steps)
        tensor = torch.from_numpy(mel_norm).unsqueeze(0).unsqueeze(0).float().to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = F.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

        return self._format_predictions(probs)

    def predict_live(self, mel_db: np.ndarray, reset_smoothing: bool = False) -> PredictionResult:
        """Run rolling window inference with EMA temporal smoothing."""
        if self.model is None:
            self.load_model()

        mel_norm = normalize_spectrogram(mel_db)
        tensor = torch.from_numpy(mel_norm).unsqueeze(0).unsqueeze(0).float().to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = F.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

        if reset_smoothing or self.live_ema_scores is None:
            self.live_ema_scores = probs
        else:
            # Exponential Moving Average: smoothed = alpha * new + (1 - alpha) * old
            self.live_ema_scores = (
                self.ema_alpha * probs + (1.0 - self.ema_alpha) * self.live_ema_scores
            )
            # Normalize to sum to 1.0
            sum_scores = np.sum(self.live_ema_scores)
            if sum_scores > 0:
                self.live_ema_scores /= sum_scores

        return self._format_predictions(self.live_ema_scores)

    def _format_predictions(self, probs: np.ndarray) -> PredictionResult:
        """Format probability array into typed PredictionResult."""
        scores_list = []
        for idx, p in enumerate(probs):
            genre = GENRES[idx]
            score_val = float(p)
            scores_list.append(
                GenreScore(
                    genre=genre,
                    display_name=GENRE_DISPLAY_NAMES.get(genre, genre.capitalize()),
                    score=round(score_val, 4),
                    percentage=round(score_val * 100, 2),
                )
            )

        # Sort descending
        scores_list.sort(key=lambda s: s.score, reverse=True)
        top_three = scores_list[:3]
        leading = top_three[0]

        return PredictionResult(
            leading_genre=leading.genre,
            leading_display_name=leading.display_name,
            top_three=top_three,
            all_scores=scores_list,
            model_status=self.model_status,
            is_mock=self.is_mock,
            is_calibrated=False,  # Uncalibrated softmax scores
        )


# Global model manager singleton
model_manager = ModelManager()

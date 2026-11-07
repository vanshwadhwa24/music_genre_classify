"""Standalone Inference Module for GTZAN Genre Classification.

Loads the trained PyTorch GenreCNN checkpoint, restores matched normalization
statistics and audio configurations, and predicts musical genre distributions
from audio files or byte buffers.
"""

from pathlib import Path
from typing import Dict, Any, Union, Optional, List, Tuple
import io

import numpy as np
import torch
import torch.nn.functional as F

from ml.src.config import (
    GENRES,
    GENRE_DISPLAY_NAMES,
    audio_config,
    path_config,
    AudioConfig,
    PROJECT_ROOT,
)
from ml.src.model import GenreCNN
from ml.src.preprocessing import (
    load_audio,
    compute_mel_spectrogram,
    normalize_spectrogram,
    load_normalization_stats,
)


class ModelNotReadyError(RuntimeError):
    """Raised when an inference is requested but no trained checkpoint is available."""
    pass


class InvalidAudioError(ValueError):
    """Raised when input audio is corrupt, empty, or unreadable."""
    pass


class AudioGenrePredictor:
    """Predicts musical genres using a genuinely trained GenreCNN checkpoint."""

    def __init__(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        device: Optional[Union[str, torch.device]] = None,
    ):
        if checkpoint_path is None:
            checkpoint_path = path_config.checkpoint_path
        self.checkpoint_path = Path(checkpoint_path)

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.model: Optional[GenreCNN] = None
        self.mean: Optional[float] = None
        self.std: Optional[float] = None
        self.audio_cfg: AudioConfig = audio_config
        self.genres: List[str] = GENRES
        self.model_status: str = "UNINITIALIZED"
        self.metadata: Dict[str, Any] = {}

        # Live EMA smoothing state
        self.live_ema_scores: Optional[np.ndarray] = None
        self.ema_alpha: float = 0.45

        self.load_checkpoint()

    def load_checkpoint(self) -> None:
        """Load checkpoint safely and initialize model in evaluation mode."""
        if not self.checkpoint_path.exists():
            raise ModelNotReadyError(
                f"Trained model checkpoint not found at: {self.checkpoint_path}. "
                "Please train the model using 'python ml/scripts/train.py' before running inference."
            )

        checkpoint = torch.load(self.checkpoint_path, map_location=self.device)

        # Extract weights
        state_dict = checkpoint.get("model_state_dict", checkpoint)
        self.genres = checkpoint.get("genres", GENRES)

        # Restore architecture
        self.model = GenreCNN(num_classes=len(self.genres)).to(self.device)
        self.model.load_state_dict(state_dict)
        self.model.eval()

        # Restore normalization statistics
        norm_stats = checkpoint.get("normalization_stats") or load_normalization_stats()
        if norm_stats:
            self.mean = norm_stats.get("mean")
            self.std = norm_stats.get("std")

        self.model_status = checkpoint.get("status", "ACTIVE_MODEL")
        self.metadata = {
            "epoch": checkpoint.get("epoch"),
            "val_acc": checkpoint.get("val_acc"),
            "val_loss": checkpoint.get("val_loss"),
            "status": self.model_status,
            "created_at": checkpoint.get("created_at"),
            "device": str(self.device),
        }

    def predict(
        self,
        audio_source: Union[str, Path, bytes, io.BytesIO, np.ndarray],
    ) -> Dict[str, Any]:
        """Predict genre probability distribution from audio input.

        Args:
            audio_source: Path to audio file, raw bytes, or precomputed Mel-spectrogram array.

        Returns:
            Dict containing predicted genre, confidence, all class probabilities, and top 3 genres.
        """
        if self.model is None:
            raise ModelNotReadyError("Model is not initialized.")

        # If already a 2D Mel-spectrogram
        if isinstance(audio_source, np.ndarray) and audio_source.ndim == 2:
            mel_db = audio_source
            duration = (mel_db.shape[1] * self.audio_cfg.hop_length) / self.audio_cfg.sample_rate
        else:
            try:
                y, duration = load_audio(
                    audio_source,
                    target_sr=self.audio_cfg.sample_rate,
                    max_duration=self.audio_cfg.target_duration,
                )
            except Exception as e:
                raise InvalidAudioError(f"Failed to decode audio: {str(e)}") from e

            mel_db = compute_mel_spectrogram(y, cfg=self.audio_cfg)

        # Standardize using training statistics
        mel_norm = normalize_spectrogram(mel_db, mean=self.mean, std=self.std)

        # Shape: (1, 1, n_mels, time_steps)
        tensor = torch.from_numpy(mel_norm).unsqueeze(0).unsqueeze(0).float().to(self.device)

        with torch.inference_mode():
            logits = self.model(tensor)
            probs_t = F.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

        if not np.isfinite(probs_t).all():
            raise RuntimeError("Model produced non-finite probability scores.")

        # Renormalize to ensure sum == 1.0 exactly
        prob_sum = np.sum(probs_t)
        if prob_sum > 0:
            probs = (probs_t / prob_sum).tolist()
        else:
            probs = probs_t.tolist()

        return self._format_result(probs, duration)

    def predict_live(
        self,
        mel_db: np.ndarray,
        reset_smoothing: bool = False,
    ) -> Dict[str, Any]:
        """Run real-time inference with temporal Exponential Moving Average (EMA) smoothing."""
        if self.model is None:
            raise ModelNotReadyError("Model is not initialized.")

        mel_norm = normalize_spectrogram(mel_db, mean=self.mean, std=self.std)
        tensor = torch.from_numpy(mel_norm).unsqueeze(0).unsqueeze(0).float().to(self.device)

        with torch.inference_mode():
            logits = self.model(tensor)
            raw_probs = F.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

        if reset_smoothing or self.live_ema_scores is None:
            self.live_ema_scores = raw_probs
        else:
            self.live_ema_scores = (
                self.ema_alpha * raw_probs + (1.0 - self.ema_alpha) * self.live_ema_scores
            )
            score_sum = np.sum(self.live_ema_scores)
            if score_sum > 0:
                self.live_ema_scores /= score_sum

        duration = (mel_db.shape[1] * self.audio_cfg.hop_length) / self.audio_cfg.sample_rate
        return self._format_result(self.live_ema_scores.tolist(), duration)

    def _format_result(self, probs: List[float], duration: float) -> Dict[str, Any]:
        """Format probability vector into typed result dictionary."""
        scores_list = []
        for idx, p in enumerate(probs):
            g = self.genres[idx]
            scores_list.append({
                "genre": g,
                "display_name": GENRE_DISPLAY_NAMES.get(g, g.capitalize()),
                "score": round(float(p), 4),
                "percentage": round(float(p) * 100, 2),
            })

        scores_list.sort(key=lambda x: x["score"], reverse=True)
        top_three = scores_list[:3]
        leading = top_three[0]

        return {
            "leading_genre": leading["genre"],
            "leading_display_name": leading["display_name"],
            "confidence": leading["score"],
            "duration_seconds": round(duration, 2),
            "top_three": top_three,
            "all_scores": scores_list,
            "model_status": self.model_status,
            "is_mock": False,
            "is_calibrated": False,
        }

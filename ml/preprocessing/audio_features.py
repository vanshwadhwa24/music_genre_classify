"""Audio Preprocessing Pipeline for GTZAN Genre Classification.

Maintains strict consistency between training, batch inference, and live rolling-window inference.
Unified with ml.src.preprocessing.
"""

from typing import Tuple, Optional
import numpy as np

from ml.src.config import (
    GENRES,
    GENRE_DISPLAY_NAMES,
    audio_config,
)
from ml.src.preprocessing import (
    load_audio,
    compute_mel_spectrogram as _compute_mel_spectrogram,
    normalize_spectrogram as _normalize_spectrogram,
    render_spectrogram_png,
)

SAMPLE_RATE: int = audio_config.sample_rate
DEFAULT_DURATION: float = audio_config.target_duration
LIVE_WINDOW_DURATION: float = audio_config.live_window_duration
N_FFT: int = audio_config.n_fft
HOP_LENGTH: int = audio_config.hop_length
N_MELS: int = audio_config.n_mels
F_MIN: float = audio_config.f_min
F_MAX: float = audio_config.f_max


def load_audio_from_bytes(
    audio_bytes: bytes,
    target_sr: int = SAMPLE_RATE,
    max_duration: Optional[float] = DEFAULT_DURATION,
) -> Tuple[np.ndarray, float]:
    """Load audio from in-memory bytes, convert to mono, resample, and return (signal, duration)."""
    return load_audio(audio_bytes, target_sr=target_sr, max_duration=max_duration)


def compute_mel_spectrogram(
    y: np.ndarray,
    sr: int = SAMPLE_RATE,
    n_fft: int = N_FFT,
    hop_length: int = HOP_LENGTH,
    n_mels: int = N_MELS,
    f_min: float = F_MIN,
    f_max: float = F_MAX,
) -> np.ndarray:
    """Compute Log-Mel Spectrogram in dB. Output shape: (n_mels, time_steps)."""
    return _compute_mel_spectrogram(y, cfg=audio_config)


def normalize_spectrogram(
    mel_db: np.ndarray,
    mean: Optional[float] = None,
    std: Optional[float] = None,
) -> np.ndarray:
    """Standardize Mel-spectrogram for CNN input via z-score normalization."""
    return _normalize_spectrogram(mel_db, mean=mean, std=std)

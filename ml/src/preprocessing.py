"""Audio Preprocessing Pipeline for GTZAN Genre Classification.

Provides shared, reproducible audio processing for training, offline evaluation,
and real-time inference. Normalization statistics are strictly fitted to the training
split to prevent data leakage.
"""

import io
import json
from pathlib import Path
from typing import Tuple, Optional, Union, Dict, Any

import numpy as np
import librosa
import soundfile as sf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ml.src.config import audio_config, AudioConfig, path_config


def load_audio(
    source: Union[str, Path, bytes, io.BytesIO],
    target_sr: int = audio_config.sample_rate,
    max_duration: Optional[float] = audio_config.target_duration,
) -> Tuple[np.ndarray, float]:
    """Safely load audio from a file path or in-memory bytes, convert to mono, resample, and clamp/pad length.

    Returns:
        (audio_signal, original_duration_seconds)
    """
    if isinstance(source, (str, Path)):
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"Audio file does not exist: {source_path}")
        try:
            y, sr = sf.read(str(source_path), dtype="float32")
        except Exception:
            y, sr = librosa.load(str(source_path), sr=None, mono=False)
    elif isinstance(source, bytes):
        if len(source) == 0:
            raise ValueError("Empty audio bytes supplied.")
        with io.BytesIO(source) as bio:
            try:
                y, sr = sf.read(bio, dtype="float32")
            except Exception:
                bio.seek(0)
                y, sr = librosa.load(bio, sr=None, mono=False)
    elif isinstance(source, io.BytesIO):
        source.seek(0)
        try:
            y, sr = sf.read(source, dtype="float32")
        except Exception:
            source.seek(0)
            y, sr = librosa.load(source, sr=None, mono=False)
    else:
        raise TypeError(f"Unsupported audio source type: {type(source)}")

    # Ensure 1D mono
    if y.ndim > 1:
        y = np.mean(y, axis=1 if y.shape[1] < y.shape[0] else 0)

    # Ensure float32
    y = y.astype(np.float32)

    # Check for NaN or Inf
    if not np.isfinite(y).all():
        y = np.nan_to_num(y, nan=0.0, posinf=1.0, neginf=-1.0)

    # Resample if sample rate differs
    if sr != target_sr:
        y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)

    original_duration = float(len(y) / target_sr)

    # Deterministic slice or pad to max_duration
    if max_duration is not None and max_duration > 0:
        target_length = int(target_sr * max_duration)
        if len(y) > target_length:
            y = y[:target_length]
        elif len(y) < target_length:
            y = np.pad(y, (0, target_length - len(y)), mode="constant", constant_values=0.0)

    return y, original_duration


def compute_mel_spectrogram(
    y: np.ndarray,
    cfg: AudioConfig = audio_config,
) -> np.ndarray:
    """Compute log-scaled Mel-spectrogram in decibels (dB).

    Shape: (n_mels, time_steps)
    """
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=cfg.sample_rate,
        n_fft=cfg.n_fft,
        hop_length=cfg.hop_length,
        n_mels=cfg.n_mels,
        fmin=cfg.f_min,
        fmax=cfg.f_max,
        power=cfg.power,
    )
    # Log-power dB scaling with numerical safeguard
    mel_db = librosa.power_to_db(mel, ref=np.max, top_db=80.0)
    return mel_db.astype(np.float32)


def normalize_spectrogram(
    mel_db: np.ndarray,
    mean: Optional[float] = None,
    std: Optional[float] = None,
) -> np.ndarray:
    """Standardize Mel-spectrogram using training statistics (or instance z-score fallback)."""
    if mean is not None and std is not None:
        return ((mel_db - mean) / (std + 1e-6)).astype(np.float32)

    # Per-sample fallback
    sample_mean = float(np.mean(mel_db))
    sample_std = float(np.std(mel_db)) + 1e-6
    return ((mel_db - sample_mean) / sample_std).astype(np.float32)


def compute_dataset_stats(spectrograms: list[np.ndarray]) -> Dict[str, float]:
    """Compute global mean and standard deviation across a set of Mel-spectrograms (train split)."""
    all_values = np.concatenate([s.flatten() for s in spectrograms])
    mean_val = float(np.mean(all_values))
    std_val = float(np.std(all_values))
    return {
        "mean": round(mean_val, 6),
        "std": round(std_val, 6),
        "count_spectrograms": len(spectrograms),
    }


def save_normalization_stats(stats: Dict[str, Any], filepath: Path = path_config.norm_stats_path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)


def load_normalization_stats(filepath: Path = path_config.norm_stats_path) -> Optional[Dict[str, float]]:
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def render_spectrogram_png(
    mel_db: np.ndarray,
    sr: int = audio_config.sample_rate,
    hop_length: int = audio_config.hop_length,
    title: str = "Mel-Spectrogram (dB)",
) -> bytes:
    """Render publication-quality, dark-themed scientific Mel-spectrogram PNG with colorbar."""
    fig, ax = plt.subplots(figsize=(10, 4), dpi=140, facecolor="#080B12")
    ax.set_facecolor("#101722")

    img = librosa.display.specshow(
        mel_db,
        sr=sr,
        hop_length=hop_length,
        x_axis="time",
        y_axis="mel",
        fmin=audio_config.f_min,
        fmax=audio_config.f_max,
        cmap="magma",
        ax=ax,
    )

    ax.set_title(title, color="#F3F5FA", fontsize=12, pad=10, fontweight="500")
    ax.set_xlabel("Time (seconds)", color="#A2AEC2", fontsize=10)
    ax.set_ylabel("Frequency (Hz)", color="#A2AEC2", fontsize=10)

    ax.tick_params(colors="#A2AEC2", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#283448")

    cbar = fig.colorbar(img, ax=ax, format="%+2.0f dB", pad=0.02)
    cbar.ax.yaxis.set_tick_params(color="#283448", labelcolor="#A2AEC2", labelsize=8)
    cbar.outline.set_edgecolor("#283448")
    cbar.set_label("Intensity (dB)", color="#A2AEC2", fontsize=9, labelpad=8)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

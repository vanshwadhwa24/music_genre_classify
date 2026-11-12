"""Audio processing, format validation, and in-memory spectrogram caching."""

import base64
import uuid
import collections
from typing import Tuple, Optional, Dict
import numpy as np

from ml.preprocessing.audio_features import (
    load_audio_from_bytes,
    compute_mel_spectrogram,
    normalize_spectrogram,
    render_spectrogram_png,
    SAMPLE_RATE,
    DEFAULT_DURATION,
    LIVE_WINDOW_DURATION,
    N_FFT,
    HOP_LENGTH,
    N_MELS,
)
from backend.app.config import settings

# Bounded in-memory spectrogram cache: analysis_id -> png_bytes
# Prevents storing user files or leaking memory
_SPECTROGRAM_CACHE: collections.OrderedDict[str, bytes] = collections.OrderedDict()


def cache_spectrogram_png(png_bytes: bytes) -> str:
    """Store spectrogram PNG bytes in bounded in-memory cache and return analysis ID."""
    analysis_id = str(uuid.uuid4())
    if len(_SPECTROGRAM_CACHE) >= settings.spectrogram_cache_size:
        _SPECTROGRAM_CACHE.popitem(last=False)  # Evict oldest
    _SPECTROGRAM_CACHE[analysis_id] = png_bytes
    return analysis_id


def get_cached_spectrogram(analysis_id: str) -> Optional[bytes]:
    """Retrieve spectrogram PNG bytes by analysis ID."""
    return _SPECTROGRAM_CACHE.get(analysis_id)


def process_audio_file(
    file_bytes: bytes,
    filename: str,
) -> Tuple[np.ndarray, np.ndarray, float, str, bytes]:
    """Validate, decode, and process uploaded audio file.

    Returns:
        (signal, mel_spectrogram_db, duration_seconds, analysis_id, png_bytes)
    """
    if len(file_bytes) > settings.max_upload_size_bytes:
        raise ValueError(
            f"File exceeds maximum upload size of {settings.max_upload_size_bytes // (1024 * 1024)}MB."
        )

    try:
        y, duration = load_audio_from_bytes(
            file_bytes,
            target_sr=settings.sample_rate,
            max_duration=settings.default_duration_seconds,
        )
    except Exception as e:
        raise ValueError(f"Failed to decode audio: {str(e)}. File may be corrupt or an unsupported codec.")

    if duration < 0.5:
        raise ValueError("Audio duration is too short (< 0.5 seconds). Please upload a longer track.")

    # Compute Mel-spectrogram
    mel_db = compute_mel_spectrogram(y, sr=settings.sample_rate)

    # Render scientific PNG
    png_bytes = render_spectrogram_png(
        mel_db,
        sr=settings.sample_rate,
        title=f"Mel-Spectrogram — {filename[:30]}",
    )
    analysis_id = cache_spectrogram_png(png_bytes)

    return y, mel_db, duration, analysis_id, png_bytes


def _transcode_to_wav(data: bytes) -> bytes:
    """Convert arbitrary browser audio bytes to mono WAV via ffmpeg (stdin to stdout)."""
    import subprocess

    proc = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-ac", "1",
         "-ar", str(settings.sample_rate), "-f", "wav", "pipe:1"],
        input=data, capture_output=True, timeout=20,
    )
    if proc.returncode != 0 or not proc.stdout:
        raise ValueError("ffmpeg could not decode the audio buffer (is ffmpeg installed?)")
    return proc.stdout


def process_live_audio_chunk(
    chunk_bytes: bytes,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """Process rolling-window audio chunk from microphone.

    Returns:
        (signal, mel_spectrogram_db, rms_energy)
    """
    try:
        y, duration = load_audio_from_bytes(
            chunk_bytes,
            target_sr=settings.sample_rate,
            max_duration=settings.live_window_seconds,
        )
    except Exception:
        # Browser MediaRecorder output (webm/opus, ogg, mp4) is not readable by
        # libsndfile; transcode to WAV with ffmpeg and retry.
        y, duration = load_audio_from_bytes(
            _transcode_to_wav(chunk_bytes),
            target_sr=settings.sample_rate,
            max_duration=settings.live_window_seconds,
        )

    # Root Mean Square energy
    rms = float(np.sqrt(np.mean(y ** 2))) if len(y) > 0 else 0.0

    mel_db = compute_mel_spectrogram(y, sr=settings.sample_rate)
    return y, mel_db, rms


def png_to_data_uri(png_bytes: bytes) -> str:
    """Encode PNG bytes to base64 Data URI."""
    encoded = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"

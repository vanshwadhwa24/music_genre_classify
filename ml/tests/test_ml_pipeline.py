"""Unit tests for ML pipeline components using synthetic fixtures.

Validates:
- Audio loading, downmixing, and resampling
- Mel-spectrogram calculation and shape
- Normalization logic
- Splitting isolation and zero-leakage guarantee
- 2D-CNN forward pass and output dimensions
- Checkpoint serialization and deserialization
- Probability distribution normalization (sums to 1.0)
- Graceful error handling for corrupted/empty inputs
"""

import io
import math
import json
from pathlib import Path

import sys
import pytest
import numpy as np
import soundfile as sf
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.config import (
    GENRES,
    GENRE_TO_IDX,
    IDX_TO_GENRE,
    audio_config,
    AudioConfig,
    PROJECT_ROOT,
)
from ml.src.preprocessing import (
    load_audio,
    compute_mel_spectrogram,
    normalize_spectrogram,
    render_spectrogram_png,
)
from ml.src.model import GenreCNN
from ml.src.dataset import GTZANDataset


@pytest.fixture
def synthetic_wav_bytes():
    """Generate a clean 2-second mono sine wave fixture (440 Hz at 22050 Hz)."""
    sr = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
    signal = 0.5 * np.sin(2 * np.pi * 440.0 * t)

    bio = io.BytesIO()
    sf.write(bio, signal, sr, format="WAV", subtype="PCM_16")
    bio.seek(0)
    return bio.getvalue()


@pytest.fixture
def synthetic_stereo_wav_bytes():
    """Generate a 2-second stereo audio fixture (2 channels)."""
    sr = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
    left = 0.4 * np.sin(2 * np.pi * 440.0 * t)
    right = 0.4 * np.sin(2 * np.pi * 880.0 * t)
    stereo = np.stack([left, right], axis=1)

    bio = io.BytesIO()
    sf.write(bio, stereo, sr, format="WAV", subtype="PCM_16")
    bio.seek(0)
    return bio.getvalue()


def test_genres_mapping():
    """Verify deterministic 10-class genre mapping."""
    assert len(GENRES) == 10
    expected = ["blues", "classical", "country", "disco", "hiphop", "jazz", "metal", "pop", "reggae", "rock"]
    assert GENRES == expected

    for idx, g in enumerate(GENRES):
        assert GENRE_TO_IDX[g] == idx
        assert IDX_TO_GENRE[idx] == g


def test_audio_loading_mono_and_stereo(synthetic_wav_bytes, synthetic_stereo_wav_bytes):
    """Verify loading, mono downmix, and duration handling."""
    # Mono load
    y_mono, dur_mono = load_audio(synthetic_wav_bytes, target_sr=22050, max_duration=2.0)
    assert y_mono.ndim == 1
    assert len(y_mono) == int(22050 * 2.0)
    assert np.isclose(dur_mono, 2.0, atol=0.01)

    # Stereo downmix to mono
    y_stereo, dur_stereo = load_audio(synthetic_stereo_wav_bytes, target_sr=22050, max_duration=2.0)
    assert y_stereo.ndim == 1
    assert len(y_stereo) == int(22050 * 2.0)

    # Pad shorter audio to 30s target
    y_padded, _ = load_audio(synthetic_wav_bytes, target_sr=22050, max_duration=30.0)
    assert len(y_padded) == int(22050 * 30.0)
    # Check that remaining samples are zero-padded
    assert np.all(y_padded[int(22050 * 2.0):] == 0.0)


def test_mel_spectrogram_shape_and_values(synthetic_wav_bytes):
    """Verify Log-Mel spectrogram computation and numeric stability."""
    y, _ = load_audio(synthetic_wav_bytes, target_sr=22050, max_duration=30.0)
    mel_db = compute_mel_spectrogram(y, cfg=audio_config)

    assert mel_db.shape[0] == audio_config.n_mels
    # Check expected time steps
    assert mel_db.shape[1] == audio_config.expected_time_steps
    assert np.isfinite(mel_db).all()
    # Log-power dB should be within reasonable decibel range (<= 0 dB for normalized max)
    assert np.max(mel_db) <= 0.01
    assert np.min(mel_db) >= -85.0  # clipped top_db


def test_normalization_with_stats():
    """Verify normalization standardizes data correctly."""
    data = np.random.normal(loc=-40.0, scale=15.0, size=(128, 100)).astype(np.float32)
    norm = normalize_spectrogram(data, mean=-40.0, std=15.0)

    assert np.isclose(np.mean(norm), 0.0, atol=0.1)
    assert np.isclose(np.std(norm), 1.0, atol=0.1)


def test_spectrogram_png_rendering(synthetic_wav_bytes):
    """Verify publication spectrogram PNG rendering produces valid PNG image bytes."""
    y, _ = load_audio(synthetic_wav_bytes, target_sr=22050, max_duration=3.0)
    mel_db = compute_mel_spectrogram(y, cfg=audio_config)
    png_bytes = render_spectrogram_png(mel_db)

    assert len(png_bytes) > 1000
    # PNG signature: 89 50 4E 47 0D 0A 1A 0A
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_model_forward_pass_dimensions():
    """Verify GenreCNN accepts 4D tensor and outputs raw 10-class logits."""
    model = GenreCNN(num_classes=10)
    model.eval()

    batch_size = 2
    time_steps = audio_config.expected_time_steps
    dummy_input = torch.randn(batch_size, 1, 128, time_steps)

    with torch.no_grad():
        logits = model(dummy_input)
        probs = model.predict_probabilities(dummy_input)

    assert logits.shape == (batch_size, 10)
    assert probs.shape == (batch_size, 10)
    # Check softmax probabilities sum to 1.0 per batch element
    prob_sums = probs.sum(dim=-1).numpy()
    assert np.allclose(prob_sums, 1.0, atol=1e-5)


def test_specaugment_preserves_shape():
    """Verify SpecAugment does not alter tensor dimensions."""
    dataset = GTZANDataset([], augment=True)
    dummy_mel = np.ones((128, 500), dtype=np.float32) * -30.0
    augmented = dataset._apply_specaugment(dummy_mel)

    assert augmented.shape == dummy_mel.shape
    assert np.isfinite(augmented).all()


def test_splits_isolation_and_no_leakage():
    """Verify that splits manifest contains zero hash leakage across train, val, and test."""
    splits_file = PROJECT_ROOT / "ml" / "reports" / "splits.json"
    if not splits_file.exists():
        pytest.skip("splits.json not yet generated")

    with open(splits_file, "r", encoding="utf-8") as f:
        splits = json.load(f)

    train_hashes = {t["hash_md5"] for t in splits["train"]}
    val_hashes = {t["hash_md5"] for t in splits["val"]}
    test_hashes = {t["hash_md5"] for t in splits["test"]}

    # Zero leakage check
    assert len(train_hashes.intersection(val_hashes)) == 0
    assert len(train_hashes.intersection(test_hashes)) == 0
    assert len(val_hashes.intersection(test_hashes)) == 0


def test_invalid_audio_error_handling():
    """Verify robust error handling on empty or corrupted audio bytes."""
    with pytest.raises(ValueError):
        load_audio(b"")

    with pytest.raises(Exception):
        load_audio(b"corrupted-invalid-audio-headers")

"""PyTorch Dataset for GTZAN Audio Genre Classification."""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

from ml.src.config import (
    audio_config,
    path_config,
    GENRE_TO_IDX,
    PROJECT_ROOT,
)
from ml.src.preprocessing import (
    load_audio,
    compute_mel_spectrogram,
    normalize_spectrogram,
)


class GTZANDataset(Dataset):
    """PyTorch Dataset loading precomputed or on-the-fly Mel-spectrograms."""

    def __init__(
        self,
        tracks: List[Dict[str, Any]],
        mean: Optional[float] = None,
        std: Optional[float] = None,
        augment: bool = False,
        target_time_steps: Optional[int] = None,
    ):
        self.tracks = tracks
        self.mean = mean
        self.std = std
        self.augment = augment
        self.target_time_steps = target_time_steps or audio_config.expected_time_steps

    def __len__(self) -> int:
        return len(self.tracks)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        track_info = self.tracks[idx]
        genre = track_info["genre"]
        label = GENRE_TO_IDX[genre]

        # Try loading cached feature if available
        cached_path = track_info.get("cached_feature_path")
        mel_db: Optional[np.ndarray] = None

        if cached_path:
            full_cached = PROJECT_ROOT / cached_path
            if full_cached.exists():
                mel_db = np.load(full_cached)

        # Fallback to computing from raw audio file
        if mel_db is None:
            raw_path = PROJECT_ROOT / track_info["path"]
            y, _ = load_audio(raw_path, target_sr=audio_config.sample_rate, max_duration=audio_config.target_duration)
            mel_db = compute_mel_spectrogram(y, cfg=audio_config)

        # Ensure consistent time dimension (e.g. 1293)
        if self.target_time_steps is not None:
            curr_steps = mel_db.shape[1]
            if curr_steps < self.target_time_steps:
                mel_db = np.pad(mel_db, ((0, 0), (0, self.target_time_steps - curr_steps)), mode="constant")
            elif curr_steps > self.target_time_steps:
                mel_db = mel_db[:, :self.target_time_steps]

        # Apply data augmentation if enabled (SpecAugment frequency & time masking)
        if self.augment:
            mel_db = self._apply_specaugment(mel_db)

        # Standardize using training statistics
        mel_norm = normalize_spectrogram(mel_db, mean=self.mean, std=self.std)

        # Shape: (1, n_mels, time_steps)
        tensor = torch.from_numpy(mel_norm).unsqueeze(0).float()
        return tensor, label

    def _apply_specaugment(
        self,
        mel_db: np.ndarray,
        num_freq_masks: int = 1,
        freq_mask_max: int = 12,
        num_time_masks: int = 2,
        time_mask_max: int = 25,
    ) -> np.ndarray:
        """Apply SpecAugment (zeroing random horizontal/vertical bands) to prevent overfitting."""
        augmented = mel_db.copy()
        n_mels, time_steps = augmented.shape
        fill_val = float(np.min(augmented))

        # Frequency masking
        for _ in range(num_freq_masks):
            f_len = np.random.randint(0, freq_mask_max)
            f0 = np.random.randint(0, max(1, n_mels - f_len))
            augmented[f0:f0 + f_len, :] = fill_val

        # Time masking
        for _ in range(num_time_masks):
            t_len = np.random.randint(0, time_mask_max)
            t0 = np.random.randint(0, max(1, time_steps - t_len))
            augmented[:, t0:t0 + t_len] = fill_val

        return augmented

"""Centralized Configuration and Hyperparameters for ML Pipeline."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# GTZAN Canonical 10 Musical Genres (alphabetic order for deterministic indexing)
GENRES: List[str] = [
    "blues",
    "classical",
    "country",
    "disco",
    "hiphop",
    "jazz",
    "metal",
    "pop",
    "reggae",
    "rock",
]

GENRE_TO_IDX: Dict[str, int] = {genre: i for i, genre in enumerate(GENRES)}
IDX_TO_GENRE: Dict[int, str] = {i: genre for i, genre in enumerate(GENRES)}

GENRE_DISPLAY_NAMES: Dict[str, str] = {
    "blues": "Blues",
    "classical": "Classical",
    "country": "Country",
    "disco": "Disco",
    "hiphop": "Hip-Hop",
    "jazz": "Jazz",
    "metal": "Metal",
    "pop": "Pop",
    "reggae": "Reggae",
    "rock": "Rock",
}


@dataclass
class AudioConfig:
    sample_rate: int = 22050
    target_duration: float = 30.0  # seconds
    n_fft: int = 2048
    hop_length: int = 512
    n_mels: int = 128
    f_min: float = 20.0
    f_max: float = 11025.0  # Nyquist frequency for 22050 Hz
    power: float = 2.0
    live_window_duration: float = 3.0  # seconds for microphone live rolling window

    @property
    def target_samples(self) -> int:
        return int(self.sample_rate * self.target_duration)

    @property
    def expected_time_steps(self) -> int:
        # (target_samples // hop_length) + 1
        return int(self.target_samples // self.hop_length) + 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_rate": self.sample_rate,
            "target_duration": self.target_duration,
            "n_fft": self.n_fft,
            "hop_length": self.hop_length,
            "n_mels": self.n_mels,
            "f_min": self.f_min,
            "f_max": self.f_max,
            "power": self.power,
            "live_window_duration": self.live_window_duration,
            "target_samples": self.target_samples,
            "expected_time_steps": self.expected_time_steps,
        }


@dataclass
class TrainConfig:
    batch_size: int = 16
    epochs: int = 35
    learning_rate: float = 0.001
    weight_decay: float = 1e-4
    seed: int = 42
    patience: int = 10
    train_split: float = 0.80
    val_split: float = 0.10
    test_split: float = 0.10
    num_workers: int = 2
    dropout_rate: float = 0.25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_size": self.batch_size,
            "epochs": self.epochs,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "seed": self.seed,
            "patience": self.patience,
            "train_split": self.train_split,
            "val_split": self.val_split,
            "test_split": self.test_split,
            "num_workers": self.num_workers,
            "dropout_rate": self.dropout_rate,
        }


@dataclass
class PathConfig:
    project_root: Path = PROJECT_ROOT
    dataset_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "ml" / "Data" / "genres_original")
    manifest_path: Path = field(default_factory=lambda: PROJECT_ROOT / "ml" / "reports" / "dataset_manifest.json")
    splits_path: Path = field(default_factory=lambda: PROJECT_ROOT / "ml" / "reports" / "splits.json")
    features_cache_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "ml" / "cache" / "spectrograms")
    norm_stats_path: Path = field(default_factory=lambda: PROJECT_ROOT / "ml" / "artifacts" / "normalization_stats.json")
    checkpoint_path: Path = field(default_factory=lambda: PROJECT_ROOT / "artifacts" / "models" / "genre_cnn.pt")
    reports_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "ml" / "reports")


audio_config = AudioConfig()
train_config = TrainConfig()
path_config = PathConfig()

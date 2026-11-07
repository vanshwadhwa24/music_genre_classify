"""Training script for GTZAN Genre Classification using GenreCNN.

Usage:
    python ml/training/train.py --data-dir path/to/gtzan/genres_original --epochs 50 --save-path artifacts/models/genre_cnn.pt
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Ensure workspace root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ml.models.cnn import GenreCNN
from ml.preprocessing.audio_features import (
    compute_mel_spectrogram,
    normalize_spectrogram,
    load_audio_from_bytes,
    GENRES,
    SAMPLE_RATE,
    DEFAULT_DURATION,
)


class GTZANAUDIODataset(Dataset):
    """GTZAN Audio Dataset loading 30s clips and converting to Mel-spectrograms."""

    def __init__(self, file_paths: List[str], labels: List[int]):
        self.file_paths = file_paths
        self.labels = labels

    def __len__(self) -> int:
        return len(self.file_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        file_path = self.file_paths[idx]
        label = self.labels[idx]

        with open(file_path, "rb") as f:
            audio_bytes = f.read()

        y, _ = load_audio_from_bytes(audio_bytes, target_sr=SAMPLE_RATE, max_duration=DEFAULT_DURATION)
        mel_db = compute_mel_spectrogram(y, sr=SAMPLE_RATE)
        mel_norm = normalize_spectrogram(mel_db)

        # Shape: (1, n_mels, time_steps)
        tensor = torch.from_numpy(mel_norm).unsqueeze(0).float()
        return tensor, label


def parse_args():
    parser = argparse.ArgumentParser(description="Train GenreCNN on GTZAN Dataset")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to GTZAN genres_original folder")
    parser.add_argument("--epochs", type=int, default=40, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--save-path", type=str, default="artifacts/models/genre_cnn.pt", help="Path to save weights")
    return parser.parse_args()


def train():
    args = parse_args()
    data_dir = Path(args.data_dir)

    if not data_dir.exists():
        print(f"Error: Dataset directory '{data_dir}' not found.")
        print("Please download GTZAN dataset to data/genres_original/ or specify --data-dir.")
        sys.exit(1)

    print(f"Scanning audio files in {data_dir}...")
    file_paths = []
    labels = []

    for idx, genre in enumerate(GENRES):
        genre_folder = data_dir / genre
        if not genre_folder.exists():
            continue
        for ext in ("*.wav", "*.au"):
            for f in genre_folder.glob(ext):
                file_paths.append(str(f))
                labels.append(idx)

    print(f"Discovered {len(file_paths)} tracks across {len(GENRES)} genres.")
    if len(file_paths) == 0:
        print("No tracks found. Exiting.")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")

    # Random split 80% train, 20% val
    indices = np.random.permutation(len(file_paths))
    split = int(0.8 * len(file_paths))
    train_idx, val_idx = indices[:split], indices[split:]

    train_files = [file_paths[i] for i in train_idx]
    train_labels = [labels[i] for i in train_idx]
    val_files = [file_paths[i] for i in val_idx]
    val_labels = [labels[i] for i in val_idx]

    train_dataset = GTZANAUDIODataset(train_files, train_labels)
    val_dataset = GTZANAUDIODataset(val_files, val_labels)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)

    model = GenreCNN(num_classes=len(GENRES)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val_acc = 0.0
    os.makedirs(Path(args.save_path).parent, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss, correct, total = 0.0, 0, 0

        for inputs, targets in train_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * inputs.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == targets).sum().item()
            total += targets.size(0)

        scheduler.step()
        train_acc = correct / total if total > 0 else 0

        # Validation
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                val_loss += loss.item() * inputs.size(0)
                preds = outputs.argmax(dim=1)
                val_correct += (preds == targets).sum().item()
                val_total += targets.size(0)

        val_acc = val_correct / val_total if val_total > 0 else 0
        print(f"Epoch {epoch:02d}/{args.epochs:02d} | Train Acc: {train_acc*100:.2f}% | Val Acc: {val_acc*100:.2f}%")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                "model_state_dict": model.state_dict(),
                "val_acc": val_acc,
                "epoch": epoch,
                "genres": GENRES,
                "sample_rate": SAMPLE_RATE,
            }, args.save_path)
            print(f"Saved best model checkpoint to {args.save_path} (Val Acc: {val_acc*100:.2f}%)")


if __name__ == "__main__":
    train()

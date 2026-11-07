#!/usr/bin/env python3
"""Training script for GTZAN Genre Classification.

Usage:
    python ml/scripts/train.py [--epochs 30] [--batch-size 16] [--lr 0.001] [--smoke-test]
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any

import torch
from torch.utils.data import DataLoader
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.config import (
    audio_config,
    train_config,
    path_config,
    GENRES,
    TrainConfig,
)
from ml.src.model import GenreCNN
from ml.src.dataset import GTZANDataset
from ml.src.trainer import GenreCNNTrainer, set_seed
from ml.src.preprocessing import load_normalization_stats


def plot_training_history(history: Dict[str, Any], output_path: Path) -> None:
    """Generate loss and accuracy curves across training epochs."""
    epochs = history["epoch"]
    train_loss = history["train_loss"]
    val_loss = history["val_loss"]
    train_acc = [a * 100 for a in history["train_acc"]]
    val_acc = [a * 100 for a in history["val_acc"]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=140, facecolor="#0B0F19")
    for ax in (ax1, ax2):
        ax.set_facecolor("#111827")
        ax.tick_params(colors="#9CA3AF")
        for spine in ax.spines.values():
            spine.set_color("#374151")

    # Loss plot
    ax1.plot(epochs, train_loss, label="Train Loss", color="#38BDF8", linewidth=2.0)
    ax1.plot(epochs, val_loss, label="Val Loss", color="#F43F5E", linewidth=2.0, linestyle="--")
    ax1.set_title("Cross-Entropy Loss", color="#F9FAFB", fontsize=12, pad=10)
    ax1.set_xlabel("Epoch", color="#9CA3AF")
    ax1.set_ylabel("Loss", color="#9CA3AF")
    ax1.legend(facecolor="#1F2937", edgecolor="#374151", labelcolor="#F9FAFB")
    ax1.grid(True, color="#1F2937", linestyle=":")

    # Accuracy plot
    ax2.plot(epochs, train_acc, label="Train Accuracy", color="#10B981", linewidth=2.0)
    ax2.plot(epochs, val_acc, label="Val Accuracy", color="#F59E0B", linewidth=2.0, linestyle="--")
    ax2.set_title("Classification Accuracy (%)", color="#F9FAFB", fontsize=12, pad=10)
    ax2.set_xlabel("Epoch", color="#9CA3AF")
    ax2.set_ylabel("Accuracy (%)", color="#9CA3AF")
    ax2.legend(facecolor="#1F2937", edgecolor="#374151", labelcolor="#F9FAFB")
    ax2.grid(True, color="#1F2937", linestyle=":")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"✅ Saved training curves plot to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Train GenreCNN on GTZAN Dataset")
    parser.add_argument("--epochs", type=int, default=train_config.epochs, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=train_config.batch_size, help="Batch size")
    parser.add_argument("--lr", type=float, default=train_config.learning_rate, help="Learning rate")
    parser.add_argument("--patience", type=int, default=train_config.patience, help="Early stopping patience")
    parser.add_argument("--seed", type=int, default=train_config.seed, help="Random seed")
    parser.add_argument("--splits-path", type=str, default="ml/reports/splits.json", help="Path to splits.json")
    parser.add_argument("--norm-path", type=str, default="ml/artifacts/normalization_stats.json")
    parser.add_argument("--save-path", type=str, default="artifacts/models/genre_cnn.pt")
    parser.add_argument("--smoke-test", action="store_true", help="Run 1 epoch test to verify mechanics")
    args = parser.parse_args()

    set_seed(args.seed)

    splits_file = PROJECT_ROOT / args.splits_path
    norm_file = PROJECT_ROOT / args.norm_path
    save_path = PROJECT_ROOT / args.save_path

    if not splits_file.exists():
        print(f"Error: Splits file {splits_file} not found. Run prepare_features.py first.")
        sys.exit(1)

    with open(splits_file, "r", encoding="utf-8") as f:
        splits_data = json.load(f)

    norm_stats = load_normalization_stats(norm_file)
    mean_val = norm_stats.get("mean") if norm_stats else None
    std_val = norm_stats.get("std") if norm_stats else None

    train_tracks = splits_data["train"]
    val_tracks = splits_data["val"]

    epochs_to_run = 1 if args.smoke_test else args.epochs

    if args.smoke_test:
        print("Running in SMOKE-TEST mode (subset of tracks, 1 epoch)...")
        train_tracks = train_tracks[:32]
        val_tracks = val_tracks[:16]

    train_dataset = GTZANDataset(train_tracks, mean=mean_val, std=std_val, augment=not args.smoke_test)
    val_dataset = GTZANDataset(val_tracks, mean=mean_val, std=std_val, augment=False)

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,  # Stable across environments
        pin_memory=False,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=False,
    )

    cfg = TrainConfig(
        batch_size=args.batch_size,
        epochs=epochs_to_run,
        learning_rate=args.lr,
        patience=args.patience,
        seed=args.seed,
    )

    model = GenreCNN(num_classes=len(GENRES))
    trainer = GenreCNNTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        cfg=cfg,
        audio_cfg=audio_config,
        checkpoint_path=save_path,
        normalization_stats=norm_stats,
    )

    results = trainer.train()

    # Generate curves plot if trained for more than 1 epoch
    if len(results["history"]["epoch"]) > 1:
        plot_training_history(results["history"], PROJECT_ROOT / "ml" / "reports" / "training_curves.png")

    return results


if __name__ == "__main__":
    main()

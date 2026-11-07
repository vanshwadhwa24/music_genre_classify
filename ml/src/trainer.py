"""Model Trainer for GTZAN Genre Classification."""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.src.config import (
    GENRES,
    GENRE_TO_IDX,
    audio_config,
    train_config,
    path_config,
    TrainConfig,
    AudioConfig,
    PROJECT_ROOT,
)
from ml.src.model import GenreCNN
from ml.src.dataset import GTZANDataset


def set_seed(seed: int = 42) -> None:
    """Ensure reproducibility across random, numpy, and torch operations."""
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


class GenreCNNTrainer:
    """Manages training lifecycle, validation, early stopping, and checkpointing."""

    def __init__(
        self,
        model: GenreCNN,
        train_loader: DataLoader,
        val_loader: DataLoader,
        cfg: TrainConfig = train_config,
        audio_cfg: AudioConfig = audio_config,
        device: Optional[torch.device] = None,
        checkpoint_path: Path = path_config.checkpoint_path,
        normalization_stats: Optional[Dict[str, float]] = None,
    ):
        self.cfg = cfg
        self.audio_cfg = audio_cfg
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model.to(self.device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.checkpoint_path = checkpoint_path
        self.normalization_stats = normalization_stats or {}

        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.cfg.learning_rate,
            weight_decay=self.cfg.weight_decay,
        )
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=self.cfg.epochs,
            eta_min=1e-5,
        )

        self.history: Dict[str, List[float]] = {
            "epoch": [],
            "train_loss": [],
            "train_acc": [],
            "val_loss": [],
            "val_acc": [],
            "learning_rate": [],
        }

    def train_epoch(self) -> Tuple[float, float]:
        """Run single training epoch."""
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for inputs, targets in self.train_loader:
            inputs, targets = inputs.to(self.device), targets.to(self.device)
            self.optimizer.zero_grad()
            outputs = self.model(inputs)
            loss = self.criterion(outputs, targets)
            loss.backward()
            nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=5.0)
            self.optimizer.step()

            batch_size = targets.size(0)
            total_loss += loss.item() * batch_size
            preds = outputs.argmax(dim=1)
            correct += (preds == targets).sum().item()
            total += batch_size

        return total_loss / total, correct / total

    def validate(self) -> Tuple[float, float]:
        """Run validation evaluation."""
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for inputs, targets in self.val_loader:
                inputs, targets = inputs.to(self.device), targets.to(self.device)
                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)

                batch_size = targets.size(0)
                total_loss += loss.item() * batch_size
                preds = outputs.argmax(dim=1)
                correct += (preds == targets).sum().item()
                total += batch_size

        return total_loss / total, correct / total

    def train(self) -> Dict[str, Any]:
        """Run complete training loop with validation, early stopping, and best model checkpointing."""
        print(f"\n=======================================================")
        print(f"🚀 Training GenreCNN on {self.device}")
        print(f"   Epochs: {self.cfg.epochs} | Batch Size: {self.cfg.batch_size} | LR: {self.cfg.learning_rate}")
        print(f"   Architecture: 4-stage 2D-CNN with {sum(p.numel() for p in self.model.parameters()):,} parameters")
        print(f"=======================================================\n")

        best_val_acc = 0.0
        best_val_loss = float("inf")
        best_epoch = 0
        patience_counter = 0

        start_time = time.time()

        for epoch in range(1, self.cfg.epochs + 1):
            epoch_start = time.time()
            train_loss, train_acc = self.train_epoch()
            val_loss, val_acc = self.validate()
            curr_lr = self.optimizer.param_groups[0]["lr"]
            self.scheduler.step()

            epoch_time = time.time() - epoch_start

            # Record history
            self.history["epoch"].append(epoch)
            self.history["train_loss"].append(round(train_loss, 4))
            self.history["train_acc"].append(round(train_acc, 4))
            self.history["val_loss"].append(round(val_loss, 4))
            self.history["val_acc"].append(round(val_acc, 4))
            self.history["learning_rate"].append(round(curr_lr, 6))

            improved = False
            if val_acc > best_val_acc or (val_acc == best_val_acc and val_loss < best_val_loss):
                best_val_acc = val_acc
                best_val_loss = val_loss
                best_epoch = epoch
                patience_counter = 0
                improved = True
                self._save_checkpoint(epoch, val_acc, val_loss)
            else:
                patience_counter += 1

            status_flag = "⭐ [BEST CHECKPOINT]" if improved else ""
            print(
                f"Epoch {epoch:02d}/{self.cfg.epochs:02d} [{epoch_time:.1f}s] "
                f"Train Loss: {train_loss:.4f} Acc: {train_acc*100:5.2f}% | "
                f"Val Loss: {val_loss:.4f} Acc: {val_acc*100:5.2f}% {status_flag}"
            )

            if patience_counter >= self.cfg.patience:
                print(f"\n⏹️ Early stopping triggered: No validation improvement for {self.cfg.patience} epochs.")
                break

        total_duration = time.time() - start_time
        print(f"\nTraining completed in {total_duration:.1f}s.")
        print(f"Best Validation Accuracy: {best_val_acc*100:.2f}% (Epoch {best_epoch})")

        # Save training history JSON
        history_path = PROJECT_ROOT / "ml" / "reports" / "training_history.json"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump({
                "best_epoch": best_epoch,
                "best_val_acc": round(best_val_acc, 4),
                "best_val_loss": round(best_val_loss, 4),
                "total_duration_seconds": round(total_duration, 1),
                "device": str(self.device),
                "history": self.history,
            }, f, indent=2)

        return {
            "best_epoch": best_epoch,
            "best_val_acc": best_val_acc,
            "best_val_loss": best_val_loss,
            "total_duration": total_duration,
            "checkpoint_path": str(self.checkpoint_path),
            "history": self.history,
        }

    def _save_checkpoint(self, epoch: int, val_acc: float, val_loss: float) -> None:
        """Save production checkpoint with weights, configs, and normalization stats."""
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_data = {
            "model_state_dict": self.model.state_dict(),
            "architecture_config": self.model.get_architecture_summary(),
            "audio_config": self.audio_cfg.to_dict(),
            "normalization_stats": self.normalization_stats,
            "genres": GENRES,
            "genre_to_idx": GENRE_TO_IDX,
            "val_acc": round(val_acc, 4),
            "val_loss": round(val_loss, 4),
            "epoch": epoch,
            "status": "ACTIVE_MODEL",
            "is_mock": False,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        torch.save(checkpoint_data, self.checkpoint_path)
        print(f"   💾 Saved best model checkpoint to {self.checkpoint_path}")

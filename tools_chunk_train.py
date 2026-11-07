#!/usr/bin/env python3
"""Resume-capable chunked trainer for GTZAN GenreCNN (batch-level checkpointing).

Trains in wall-clock-budgeted chunks, saving full state atomically every N
batches so a hard kill loses little work. On completion writes the same
artifacts as ml/scripts/train.py (checkpoint, training_history.json, curves).
Batch size 8 instead of the default 16: batch 16 OOMs on this 2GB container.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

PROJECT_ROOT = Path("/home/sandbox/music_genre_classify")
sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.config import GENRES, audio_config, TrainConfig
from ml.src.model import GenreCNN
from ml.src.dataset import GTZANDataset
from ml.src.trainer import GenreCNNTrainer, set_seed
from ml.src.preprocessing import load_normalization_stats

STATE_PATH = PROJECT_ROOT / "artifacts" / "models" / "_train_state.pt"
CKPT_PATH = PROJECT_ROOT / "artifacts" / "models" / "genre_cnn.pt"


def atomic_save(obj, path):
    tmp = str(path) + ".tmp"
    torch.save(obj, tmp)
    os.replace(tmp, path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--budget-seconds", type=float, default=95.0)
    p.add_argument("--epochs", type=int, default=35)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--lr", type=float, default=0.001)
    p.add_argument("--patience", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--save-every-batches", type=int, default=20)
    args = p.parse_args()

    torch.set_num_threads(1)
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(PROJECT_ROOT / "ml/reports/splits.json") as f:
        splits = json.load(f)
    norm_stats = load_normalization_stats(PROJECT_ROOT / "ml/artifacts/normalization_stats.json")
    mean_val = norm_stats.get("mean") if norm_stats else None
    std_val = norm_stats.get("std") if norm_stats else None

    train_ds = GTZANDataset(splits["train"], mean=mean_val, std=std_val, augment=True)
    val_ds = GTZANDataset(splits["val"], mean=mean_val, std=std_val, augment=False)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    cfg = TrainConfig(batch_size=args.batch_size, epochs=args.epochs,
                      learning_rate=args.lr, patience=args.patience, seed=args.seed)
    model = GenreCNN(num_classes=len(GENRES))
    trainer = GenreCNNTrainer(model=model, train_loader=None, val_loader=val_loader,
                              cfg=cfg, audio_cfg=audio_config, checkpoint_path=CKPT_PATH,
                              normalization_stats=norm_stats or {})

    start_epoch, start_batch = 1, 0
    best_val_acc, best_val_loss, best_epoch, patience_counter = 0.0, float("inf"), 0, 0
    elapsed = 0.0

    if STATE_PATH.exists():
        st = torch.load(STATE_PATH, map_location="cpu", weights_only=False)
        model.load_state_dict(st["model"])
        trainer.optimizer.load_state_dict(st["optimizer"])
        trainer.scheduler.load_state_dict(st["scheduler"])
        trainer.history = st["history"]
        start_epoch = st["epoch"]
        start_batch = st["batch_idx"]
        best_val_acc = st["best_val_acc"]
        best_val_loss = st["best_val_loss"]
        best_epoch = st["best_epoch"]
        patience_counter = st["patience_counter"]
        elapsed = st.get("elapsed", 0.0)
        print(f"Resumed epoch {start_epoch} batch {start_batch}; best {best_val_acc*100:.2f}% @ {best_epoch}", flush=True)

    if start_epoch > args.epochs or patience_counter >= args.patience:
        print("ALREADY_DONE", flush=True)
        finalize(trainer, best_epoch, best_val_acc, best_val_loss, elapsed)
        return

    budget_end = time.time() + args.budget_seconds
    done = False

    for epoch in range(start_epoch, args.epochs + 1):
        torch.manual_seed(args.seed * 1000 + epoch)
        np.random.seed(args.seed * 1000 + epoch)
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)

        model.train()
        t0 = time.time()
        total_loss, correct, total = 0.0, 0, 0
        b0 = start_batch if epoch == start_epoch else 0

        for bi, (inputs, targets) in enumerate(train_loader):
            if bi < b0:
                continue
            trainer.optimizer.zero_grad()
            outputs = model(inputs)
            loss = trainer.criterion(outputs, targets)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            trainer.optimizer.step()
            bs = targets.size(0)
            total_loss += loss.item() * bs
            correct += (outputs.argmax(1) == targets).sum().item()
            total += bs

            if (bi + 1) % args.save_every_batches == 0:
                over = time.time() > budget_end
                atomic_save(state(model, trainer, epoch, bi + 1, best_val_acc,
                                  best_val_loss, best_epoch, patience_counter,
                                  elapsed + (time.time() - t0)), STATE_PATH)
                print(f"[save] epoch {epoch} batch {bi+1} acc {correct/total*100:.1f}% t={time.time()-t0:.0f}s", flush=True)
                if over:
                    print(f"CHUNK_DONE mid-epoch {epoch} batch {bi+1}", flush=True)
                    return

        train_loss, train_acc = total_loss / total, correct / total
        val_loss, val_acc = trainer.validate()
        curr_lr = trainer.optimizer.param_groups[0]["lr"]
        trainer.scheduler.step()
        epoch_dt = time.time() - t0
        elapsed += epoch_dt

        trainer.history["epoch"].append(epoch)
        trainer.history["train_loss"].append(round(train_loss, 4))
        trainer.history["train_acc"].append(round(train_acc, 4))
        trainer.history["val_loss"].append(round(val_loss, 4))
        trainer.history["val_acc"].append(round(val_acc, 4))
        trainer.history["learning_rate"].append(round(curr_lr, 6))

        improved = False
        if val_acc > best_val_acc or (val_acc == best_val_acc and val_loss < best_val_loss):
            best_val_acc, best_val_loss, best_epoch = val_acc, val_loss, epoch
            patience_counter = 0
            improved = True
            trainer._save_checkpoint(epoch, val_acc, val_loss)
        else:
            patience_counter += 1

        print(f"Epoch {epoch:02d}/{args.epochs} [{epoch_dt:.1f}s] train_loss={train_loss:.4f} "
              f"train_acc={train_acc*100:.2f}% val_loss={val_loss:.4f} val_acc={val_acc*100:.2f}% "
              f"{'BEST' if improved else ''}", flush=True)

        atomic_save(state(model, trainer, epoch + 1, 0, best_val_acc,
                          best_val_loss, best_epoch, patience_counter, elapsed), STATE_PATH)

        if patience_counter >= args.patience:
            print(f"EARLY_STOP at epoch {epoch}", flush=True)
            done = True
            break
        if time.time() > budget_end:
            print("CHUNK_DONE epoch boundary", flush=True)
            return

    done = True
    finalize(trainer, best_epoch, best_val_acc, best_val_loss, elapsed)
    print("TRAINING_COMPLETE", flush=True)


def state(model, trainer, epoch, batch_idx, bva, bvl, be, pc, elapsed):
    return {
        "model": model.state_dict(),
        "optimizer": trainer.optimizer.state_dict(),
        "scheduler": trainer.scheduler.state_dict(),
        "history": trainer.history,
        "epoch": epoch,
        "batch_idx": batch_idx,
        "best_val_acc": bva,
        "best_val_loss": bvl,
        "best_epoch": be,
        "patience_counter": pc,
        "elapsed": elapsed,
    }


def finalize(trainer, best_epoch, best_val_acc, best_val_loss, total_time):
    history_path = PROJECT_ROOT / "ml" / "reports" / "training_history.json"
    with open(history_path, "w") as f:
        json.dump({
            "best_epoch": best_epoch,
            "best_val_acc": round(best_val_acc, 4),
            "best_val_loss": round(best_val_loss, 4),
            "total_duration_seconds": round(total_time, 1),
            "device": str(trainer.device),
            "history": trainer.history,
        }, f, indent=2)
    if len(trainer.history["epoch"]) > 1:
        src = (PROJECT_ROOT / "ml" / "scripts" / "train.py").read_text()
        ns = {}
        exec(compile(src.split("def main()")[0], "train_mod", "exec"), ns)
        ns["plot_training_history"](trainer.history, PROJECT_ROOT / "ml" / "reports" / "training_curves.png")
    print(f"FINAL best_val_acc={best_val_acc*100:.2f}% @ epoch {best_epoch}, time={total_time:.0f}s", flush=True)


if __name__ == "__main__":
    set_seed(42)
    main()

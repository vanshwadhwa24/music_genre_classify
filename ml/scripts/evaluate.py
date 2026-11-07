#!/usr/bin/env python3
"""Standalone Evaluation and Diagnostics Script for GTZAN Genre Classification.

Evaluates the trained checkpoint on the held-out, untouched test set.
Computes:
- Overall Accuracy
- Macro-averaged and per-class Precision, Recall, and F1 scores
- Confusion Matrix (data + publication-quality plot)
- Frequently confused genre pairs analysis
- Full evaluation report export (JSON and Markdown)

Usage:
    python ml/scripts/evaluate.py [--checkpoint artifacts/models/genre_cnn.pt] [--splits ml/reports/splits.json]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.config import (
    GENRES,
    GENRE_TO_IDX,
    GENRE_DISPLAY_NAMES,
    path_config,
    audio_config,
)
from ml.src.model import GenreCNN
from ml.src.dataset import GTZANDataset
from ml.src.preprocessing import load_normalization_stats


def plot_confusion_matrix(
    cm: np.ndarray,
    classes: List[str],
    output_path: Path,
    title: str = "GTZAN Test Set Confusion Matrix",
) -> None:
    """Plot and save confusion matrix with raw counts and normalized percentages."""
    cm_norm = cm.astype("float") / (cm.sum(axis=1)[:, np.newaxis] + 1e-9)

    fig, ax = plt.subplots(figsize=(10, 8), dpi=140, facecolor="#0B0F19")
    ax.set_facecolor("#111827")

    cax = ax.imshow(cm_norm, interpolation="nearest", cmap="magma", vmin=0.0, vmax=1.0)
    cbar = fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.yaxis.set_tick_params(color="#374151", labelcolor="#9CA3AF")
    cbar.outline.set_edgecolor("#374151")
    cbar.set_label("Recall (Normalized)", color="#9CA3AF", fontsize=10, labelpad=10)

    tick_marks = np.arange(len(classes))
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels([GENRE_DISPLAY_NAMES.get(c, c) for c in classes], rotation=45, ha="right", color="#9CA3AF", fontsize=9)
    ax.set_yticklabels([GENRE_DISPLAY_NAMES.get(c, c) for c in classes], color="#9CA3AF", fontsize=9)

    # Label text in cells
    thresh = cm_norm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            count = cm[i, j]
            pct = cm_norm[i, j] * 100
            color = "#0B0F19" if cm_norm[i, j] > thresh else "#F9FAFB"
            text = f"{count}\n({pct:.0f}%)" if count > 0 else "0"
            ax.text(j, i, text, ha="center", va="center", color=color, fontsize=8, fontweight="bold" if i == j else "normal")

    ax.set_title(title, color="#F9FAFB", fontsize=13, pad=15, fontweight="bold")
    ax.set_ylabel("True Genre", color="#9CA3AF", fontsize=11, labelpad=10)
    ax.set_xlabel("Predicted Genre", color="#9CA3AF", fontsize=11, labelpad=10)

    for spine in ax.spines.values():
        spine.set_color("#374151")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"✅ Saved confusion matrix plot to: {output_path}")


def evaluate_checkpoint(
    checkpoint_path: Path,
    splits_path: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    """Load checkpoint and evaluate on held-out test split."""
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found at: {checkpoint_path}")
    if not splits_path.exists():
        raise FileNotFoundError(f"Splits file not found at: {splits_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n=======================================================")
    print(f"🔍 Evaluating GenreCNN on Test Set ({device})")
    print(f"   Checkpoint: {checkpoint_path}")
    print(f"=======================================================\n")

    checkpoint = torch.load(checkpoint_path, map_location=device)
    state_dict = checkpoint["model_state_dict"] if "model_state_dict" in checkpoint else checkpoint

    model = GenreCNN(num_classes=len(GENRES)).to(device)
    model.load_state_dict(state_dict)
    model.eval()

    # Load test split
    with open(splits_path, "r", encoding="utf-8") as f:
        splits_data = json.load(f)
    test_tracks = splits_data["test"]

    # Normalization statistics
    norm_stats = checkpoint.get("normalization_stats") or load_normalization_stats()
    mean_val = norm_stats.get("mean") if norm_stats else None
    std_val = norm_stats.get("std") if norm_stats else None

    print(f"Evaluating {len(test_tracks)} held-out test tracks...")
    test_dataset = GTZANDataset(test_tracks, mean=mean_val, std=std_val, augment=False)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

    y_true: List[int] = []
    y_pred: List[int] = []
    all_probs: List[np.ndarray] = []

    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs = inputs.to(device)
            logits = model(inputs)
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            preds = logits.argmax(dim=1).cpu().numpy()

            y_true.extend(targets.numpy().tolist())
            y_pred.extend(preds.tolist())
            all_probs.extend(probs)

    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)

    # Compute metrics
    acc = float(np.mean(y_true_arr == y_pred_arr))
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true_arr, y_pred_arr, average="macro", zero_division=0
    )
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true_arr, y_pred_arr, average="weighted", zero_division=0
    )

    # Per-class metrics
    p_per, r_per, f_per, s_per = precision_recall_fscore_support(
        y_true_arr, y_pred_arr, labels=list(range(len(GENRES))), zero_division=0
    )
    per_class_metrics = {}
    for idx, genre in enumerate(GENRES):
        per_class_metrics[genre] = {
            "display_name": GENRE_DISPLAY_NAMES[genre],
            "precision": round(float(p_per[idx]), 4),
            "recall": round(float(r_per[idx]), 4),
            "f1_score": round(float(f_per[idx]), 4),
            "support": int(s_per[idx]),
        }

    # Confusion matrix
    cm = confusion_matrix(y_true_arr, y_pred_arr, labels=list(range(len(GENRES))))

    # Frequently confused pairs
    confused_pairs = []
    for i in range(len(GENRES)):
        for j in range(len(GENRES)):
            if i != j and cm[i, j] > 0:
                confused_pairs.append({
                    "true_genre": GENRES[i],
                    "predicted_genre": GENRES[j],
                    "count": int(cm[i, j]),
                    "rate": round(float(cm[i, j] / s_per[i]), 3),
                })
    confused_pairs.sort(key=lambda x: x["count"], reverse=True)

    # Classification report text
    clf_report_str = classification_report(
        y_true_arr,
        y_pred_arr,
        target_names=[GENRE_DISPLAY_NAMES[g] for g in GENRES],
        digits=4,
        zero_division=0,
    )

    evaluation_results = {
        "checkpoint": str(checkpoint_path),
        "test_tracks_count": len(test_tracks),
        "overall_accuracy": round(acc, 4),
        "macro_metrics": {
            "precision": round(float(precision_macro), 4),
            "recall": round(float(recall_macro), 4),
            "f1_score": round(float(f1_macro), 4),
        },
        "weighted_metrics": {
            "precision": round(float(precision_weighted), 4),
            "recall": round(float(recall_weighted), 4),
            "f1_score": round(float(f1_weighted), 4),
        },
        "per_class": per_class_metrics,
        "top_confusions": confused_pairs[:10],
        "confusion_matrix": cm.tolist(),
    }

    # Save outputs
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. JSON report
    with open(output_dir / "evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(evaluation_results, f, indent=2)

    # 2. Text classification report
    with open(output_dir / "classification_report.txt", "w", encoding="utf-8") as f:
        f.write(f"GTZAN Held-Out Test Set Evaluation Report\n")
        f.write(f"Checkpoint: {checkpoint_path}\n")
        f.write(f"Overall Accuracy: {acc * 100:.2f}%\n\n")
        f.write(clf_report_str)

    # 3. Confusion matrix plot
    plot_confusion_matrix(cm, GENRES, output_dir / "confusion_matrix.png")

    # 4. Detailed Markdown Report
    md_report = generate_evaluation_markdown(evaluation_results, clf_report_str)
    with open(output_dir / "evaluation_report.md", "w", encoding="utf-8") as f:
        f.write(md_report)

    # Print summary to console
    print("\n--- TEST EVALUATION SUMMARY ---")
    print(f"Overall Accuracy:  {acc * 100:.2f}%")
    print(f"Macro F1-Score:    {f1_macro * 100:.2f}%")
    print(f"Macro Precision:   {precision_macro * 100:.2f}%")
    print(f"Macro Recall:      {recall_macro * 100:.2f}%")
    print("\n" + clf_report_str)

    if confused_pairs:
        print("Top Frequently Confused Pairs:")
        for cp in confused_pairs[:5]:
            print(f"  {cp['true_genre']} -> misclassified as {cp['predicted_genre']}: {cp['count']} tracks ({cp['rate']*100:.1f}%)")

    return evaluation_results


def generate_evaluation_markdown(res: Dict[str, Any], clf_table: str) -> str:
    lines = [
        "# GTZAN Test Set Model Evaluation Report",
        "",
        "## 1. Summary of Performance",
        "",
        f"- **Checkpoint Evaluated:** `{res['checkpoint']}`",
        f"- **Held-Out Test Samples:** {res['test_tracks_count']}",
        f"- **Overall Test Accuracy:** **{res['overall_accuracy'] * 100:.2f}%**",
        f"- **Macro Precision:** {res['macro_metrics']['precision'] * 100:.2f}%",
        f"- **Macro Recall:** {res['macro_metrics']['recall'] * 100:.2f}%",
        f"- **Macro F1-Score:** **{res['macro_metrics']['f1_score'] * 100:.2f}%**",
        "",
        "## 2. Per-Genre Performance",
        "",
        "| Genre | Precision | Recall | F1-Score | Support |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ]

    for g, data in res["per_class"].items():
        lines.append(
            f"| **{data['display_name']}** | {data['precision']*100:.1f}% | {data['recall']*100:.1f}% | {data['f1_score']*100:.1f}% | {data['support']} |"
        )

    lines.extend([
        "",
        "## 3. Top Confused Genre Pairs",
        "",
        "| True Genre | Misclassified As | Track Count | Misclassification Rate |",
        "| :--- | :--- | :---: | :---: |",
    ])

    for cp in res["top_confusions"]:
        lines.append(
            f"| {cp['true_genre']} | {cp['predicted_genre']} | {cp['count']} | {cp['rate']*100:.1f}% |"
        )

    lines.extend([
        "",
        "## 4. Visual Diagnostics",
        "",
        "- Confusion Matrix: `ml/reports/confusion_matrix.png`",
        "- Training Curves: `ml/reports/training_curves.png`",
        "",
        "```",
        clf_table,
        "```",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evaluate GenreCNN on GTZAN test split")
    parser.add_argument("--checkpoint", type=str, default="artifacts/models/genre_cnn.pt")
    parser.add_argument("--splits", type=str, default="ml/reports/splits.json")
    parser.add_argument("--output-dir", type=str, default="ml/reports")
    args = parser.parse_args()

    checkpoint_path = PROJECT_ROOT / args.checkpoint
    splits_path = PROJECT_ROOT / args.splits
    output_dir = PROJECT_ROOT / args.output_dir

    evaluate_checkpoint(checkpoint_path, splits_path, output_dir)


if __name__ == "__main__":
    main()

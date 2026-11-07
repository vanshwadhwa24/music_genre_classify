#!/usr/bin/env python3
"""Feature Preparation and Stratified Splitting Script for GTZAN Dataset.

Performs:
1. Deduplication-aware, recording-level isolated stratified splitting (80% train, 10% val, 10% test).
2. Verifies zero leakage between train, validation, and test splits.
3. Precomputes Log-Mel spectrograms (22050 Hz, 30s, 128 Mel bands, hop=512, n_fft=2048) and caches them to disk.
4. Computes global dataset mean and std strictly over the train split to prevent data leakage.
5. Saves splits manifest (`ml/reports/splits.json`) and normalization statistics (`ml/artifacts/normalization_stats.json`).

Usage:
    python ml/scripts/prepare_features.py [--seed 42]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Set

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.config import (
    audio_config,
    train_config,
    path_config,
    GENRES,
    GENRE_TO_IDX,
)
from ml.src.preprocessing import (
    load_audio,
    compute_mel_spectrogram,
    compute_dataset_stats,
    save_normalization_stats,
)


def create_reproducible_splits(
    manifest_path: Path,
    seed: int = 42,
    train_ratio: float = 0.80,
    val_ratio: float = 0.10,
    test_ratio: float = 0.10,
) -> Dict[str, Any]:
    """Create reproducible train/val/test splits ensuring recording and duplicate isolation."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    valid_tracks = manifest["valid_tracks"]
    print(f"Loaded {len(valid_tracks)} valid tracks from manifest.")

    # Group tracks by hash to ensure duplicate tracks stay in the same split
    hash_to_tracks: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for track in valid_tracks:
        h = track.get("hash_md5", track["path"])
        hash_to_tracks[h].append(track)

    rng = np.random.RandomState(seed)

    # Cross-genre duplicates: assign all to train split so they never pollute val/test
    cross_genre_hashes = set()
    for h, tracks in hash_to_tracks.items():
        genres = {t["genre"] for t in tracks}
        if len(genres) > 1:
            cross_genre_hashes.add(h)

    train_tracks: List[Dict[str, Any]] = []
    val_tracks: List[Dict[str, Any]] = []
    test_tracks: List[Dict[str, Any]] = []

    # Assign cross-genre duplicates directly to train
    for h in cross_genre_hashes:
        train_tracks.extend(hash_to_tracks[h])

    # Per-genre clustering of remaining hashes
    genre_to_hash_groups: Dict[str, List[List[Dict[str, Any]]]] = defaultdict(list)
    for h, tracks in hash_to_tracks.items():
        if h in cross_genre_hashes:
            continue
        primary_genre = tracks[0]["genre"]
        genre_to_hash_groups[primary_genre].append(tracks)

    # Perform stratified split per genre on hash groups
    for genre in sorted(GENRES):
        groups = genre_to_hash_groups[genre]
        # Shuffle deterministically
        indices = rng.permutation(len(groups))
        n_groups = len(groups)

        n_val = max(1, int(round(n_groups * val_ratio)))
        n_test = max(1, int(round(n_groups * test_ratio)))
        n_train = n_groups - n_val - n_test

        train_indices = indices[:n_train]
        val_indices = indices[n_train:n_train + n_val]
        test_indices = indices[n_train + n_val:]

        for idx in train_indices:
            train_tracks.extend(groups[idx])
        for idx in val_indices:
            val_tracks.extend(groups[idx])
        for idx in test_indices:
            test_tracks.extend(groups[idx])

    # Sort tracks deterministically by path
    train_tracks.sort(key=lambda t: t["path"])
    val_tracks.sort(key=lambda t: t["path"])
    test_tracks.sort(key=lambda t: t["path"])

    # Verify zero recording/hash leakage
    train_hashes = {t["hash_md5"] for t in train_tracks}
    val_hashes = {t["hash_md5"] for t in val_tracks}
    test_hashes = {t["hash_md5"] for t in test_tracks}

    val_leak = train_hashes.intersection(val_hashes)
    test_leak = train_hashes.intersection(test_hashes)
    val_test_leak = val_hashes.intersection(test_hashes)

    assert len(val_leak) == 0, f"Critical error: {len(val_leak)} hashes leaked between train and val!"
    assert len(test_leak) == 0, f"Critical error: {len(test_leak)} hashes leaked between train and test!"
    assert len(val_test_leak) == 0, f"Critical error: {len(val_test_leak)} hashes leaked between val and test!"

    # Verify all valid tracks accounted for
    total_split_tracks = len(train_tracks) + len(val_tracks) + len(test_tracks)
    assert total_split_tracks == len(valid_tracks), (
        f"Mismatch: {total_split_tracks} in splits vs {len(valid_tracks)} valid."
    )

    split_manifest = {
        "metadata": {
            "seed": seed,
            "train_ratio_target": train_ratio,
            "val_ratio_target": val_ratio,
            "test_ratio_target": test_ratio,
            "total_valid_tracks": len(valid_tracks),
            "train_count": len(train_tracks),
            "val_count": len(val_tracks),
            "test_count": len(test_tracks),
            "leakage_check_passed": True,
        },
        "genre_counts": {
            "train": {g: sum(1 for t in train_tracks if t["genre"] == g) for g in GENRES},
            "val": {g: sum(1 for t in val_tracks if t["genre"] == g) for g in GENRES},
            "test": {g: sum(1 for t in test_tracks if t["genre"] == g) for g in GENRES},
        },
        "train": train_tracks,
        "val": val_tracks,
        "test": test_tracks,
    }

    return split_manifest


def prepare_and_cache_features(
    splits_data: Dict[str, Any],
    cache_dir: Path,
) -> Dict[str, Any]:
    """Compute and cache Mel-spectrograms for all tracks and compute train normalization stats."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    for g in GENRES:
        (cache_dir / g).mkdir(parents=True, exist_ok=True)

    all_tracks = splits_data["train"] + splits_data["val"] + splits_data["test"]
    print(f"\nProcessing and caching Mel-spectrograms for {len(all_tracks)} tracks into: {cache_dir}...")

    train_spectrograms = []
    processed_count = 0
    skipped_cache_count = 0

    for idx, track_info in enumerate(all_tracks):
        rel_path = track_info["path"]
        genre = track_info["genre"]
        audio_path = PROJECT_ROOT / rel_path
        filename = Path(rel_path).stem
        cached_npy = cache_dir / genre / f"{filename}.npy"

        if cached_npy.exists():
            mel_db = np.load(cached_npy)
            skipped_cache_count += 1
        else:
            y, _ = load_audio(audio_path, target_sr=audio_config.sample_rate, max_duration=audio_config.target_duration)
            mel_db = compute_mel_spectrogram(y, cfg=audio_config)
            np.save(cached_npy, mel_db)
            processed_count += 1

        # Track relative cache path
        track_info["cached_feature_path"] = cached_npy.relative_to(PROJECT_ROOT).as_posix()
        track_info["spectrogram_shape"] = list(mel_db.shape)

        # Collect train spectrograms for leakage-free normalization statistics
        if any(t["path"] == rel_path for t in splits_data["train"]):
            train_spectrograms.append(mel_db)

        if (idx + 1) % 200 == 0 or (idx + 1) == len(all_tracks):
            print(f"  Processed {idx + 1}/{len(all_tracks)} tracks (Cached: {processed_count}, Reused: {skipped_cache_count})")

    # Compute global mean and std exclusively from training data
    print(f"\nComputing normalization statistics across {len(train_spectrograms)} training spectrograms...")
    norm_stats = compute_dataset_stats(train_spectrograms)
    norm_stats["sample_rate"] = audio_config.sample_rate
    norm_stats["n_mels"] = audio_config.n_mels
    norm_stats["hop_length"] = audio_config.hop_length
    norm_stats["n_fft"] = audio_config.n_fft
    norm_stats["target_duration"] = audio_config.target_duration

    print(f"✅ Training normalization stats: Mean = {norm_stats['mean']}, Std = {norm_stats['std']}")
    return norm_stats


def main():
    parser = argparse.ArgumentParser(description="Prepare features and create isolated splits")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for splitting")
    parser.add_argument("--manifest", type=str, default="ml/reports/dataset_manifest.json")
    parser.add_argument("--splits-output", type=str, default="ml/reports/splits.json")
    parser.add_argument("--cache-dir", type=str, default="ml/cache/spectrograms")
    parser.add_argument("--norm-output", type=str, default="ml/artifacts/normalization_stats.json")
    args = parser.parse_args()

    manifest_path = PROJECT_ROOT / args.manifest
    splits_path = PROJECT_ROOT / args.splits_output
    cache_dir = PROJECT_ROOT / args.cache_dir
    norm_path = PROJECT_ROOT / args.norm_output

    if not manifest_path.exists():
        print(f"Error: Manifest not found at {manifest_path}. Please run audit_dataset.py first.")
        sys.exit(1)

    print("Step 1: Creating isolated stratified splits...")
    splits_data = create_reproducible_splits(manifest_path, seed=args.seed)

    print("Step 2: Precomputing and caching spectrogram features...")
    norm_stats = prepare_and_cache_features(splits_data, cache_dir)

    # Save splits
    splits_path.parent.mkdir(parents=True, exist_ok=True)
    with open(splits_path, "w", encoding="utf-8") as f:
        json.dump(splits_data, f, indent=2)
    print(f"✅ Saved splits manifest to: {splits_path}")

    # Save norm stats
    save_normalization_stats(norm_stats, norm_path)
    print(f"✅ Saved normalization statistics to: {norm_path}")

    print("\n--- SPLIT SUMMARY ---")
    meta = splits_data["metadata"]
    print(f"Train tracks: {meta['train_count']} ({meta['train_count']/meta['total_valid_tracks']*100:.1f}%)")
    print(f"Val tracks:   {meta['val_count']} ({meta['val_count']/meta['total_valid_tracks']*100:.1f}%)")
    print(f"Test tracks:  {meta['test_count']} ({meta['test_count']/meta['total_valid_tracks']*100:.1f}%)")
    print("\nPer-Genre Breakdown:")
    print(f"{'Genre':<12} {'Train':<8} {'Val':<8} {'Test':<8}")
    print("-" * 36)
    for g in GENRES:
        print(f"{g:<12} {splits_data['genre_counts']['train'][g]:<8} {splits_data['genre_counts']['val'][g]:<8} {splits_data['genre_counts']['test'][g]:<8}")


if __name__ == "__main__":
    main()

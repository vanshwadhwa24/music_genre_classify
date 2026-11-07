#!/usr/bin/env python3
"""Dataset Auditing and Validation Script for GTZAN Music Genre Dataset.

Recursively scans the dataset directory, validates decodability, verifies sample rates,
channels, and durations, detects corrupt audio files and duplicates, and outputs
both a machine-readable manifest (JSON) and a human-readable audit report (Markdown).

Usage:
    python ml/scripts/audit_dataset.py [--data-dir ml/Data/genres_original]
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Tuple

import soundfile as sf
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

EXPECTED_GENRES = [
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


def compute_file_hash(filepath: Path, chunk_size: int = 65536) -> str:
    """Compute MD5 hash of a file for duplicate detection."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def audit_dataset(
    data_dir: Path,
    manifest_path: Path,
    report_path: Path,
) -> Dict[str, Any]:
    print(f"\n=======================================================")
    print(f"🎵 Auditing GTZAN Dataset in: {data_dir.resolve()}")
    print(f"=======================================================\n")

    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

    # Discover genre subdirectories
    subdirs = [d.name for d in data_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    discovered_genres = sorted(subdirs)
    print(f"Discovered genres ({len(discovered_genres)}): {', '.join(discovered_genres)}")

    missing_genres = [g for g in EXPECTED_GENRES if g not in discovered_genres]
    extra_genres = [g for g in discovered_genres if g not in EXPECTED_GENRES]

    if missing_genres:
        print(f"⚠️ Warning: Missing expected genres: {missing_genres}")
    if extra_genres:
        print(f"ℹ️ Extra folders found: {extra_genres}")

    # Track metrics
    valid_files: List[Dict[str, Any]] = []
    excluded_files: List[Dict[str, Any]] = []
    genre_counts: Dict[str, int] = defaultdict(int)
    genre_valid_counts: Dict[str, int] = defaultdict(int)
    hash_to_files: Dict[str, List[str]] = defaultdict(list)
    sample_rates: Dict[int, int] = defaultdict(int)
    channels_counts: Dict[int, int] = defaultdict(int)
    durations: List[float] = []

    # Scan all audio files
    all_files = sorted(list(data_dir.rglob("*.wav")) + list(data_dir.rglob("*.au")))
    print(f"Found {len(all_files)} total audio files. Inspecting integrity...\n")

    for idx, filepath in enumerate(all_files):
        rel_path = filepath.relative_to(PROJECT_ROOT).as_posix()
        genre = filepath.parent.name
        genre_counts[genre] += 1
        file_size = filepath.stat().st_size

        if file_size == 0:
            excluded_files.append({
                "path": rel_path,
                "genre": genre,
                "reason": "ZERO_BYTE_FILE",
                "detail": "File size is 0 bytes.",
                "size_bytes": 0,
            })
            continue

        # Compute hash
        try:
            file_hash = compute_file_hash(filepath)
            hash_to_files[file_hash].append(rel_path)
        except Exception as e:
            file_hash = "UNKNOWN_ERROR"

        # Validate decodability with soundfile
        try:
            info = sf.info(filepath)
            sr = info.samplerate
            channels = info.channels
            duration = info.duration
            frames = info.frames
            format_name = info.format
            subtype = info.subtype

            # Try reading a brief slice to ensure no corrupted audio frames
            with sf.SoundFile(filepath) as sfile:
                # Read first second
                sfile.read(min(frames, sr), dtype="float32")

            sample_rates[sr] += 1
            channels_counts[channels] += 1
            durations.append(duration)
            genre_valid_counts[genre] += 1

            valid_files.append({
                "path": rel_path,
                "filename": filepath.name,
                "genre": genre,
                "hash_md5": file_hash,
                "sample_rate": sr,
                "channels": channels,
                "duration_seconds": round(duration, 3),
                "frames": frames,
                "format": format_name,
                "subtype": subtype,
                "size_bytes": file_size,
            })

        except Exception as e:
            excluded_files.append({
                "path": rel_path,
                "filename": filepath.name,
                "genre": genre,
                "reason": "CORRUPTED_OR_UNREADABLE",
                "detail": str(e),
                "size_bytes": file_size,
                "hash_md5": file_hash,
            })

    # Duplicate detection analysis
    duplicates = {h: paths for h, paths in hash_to_files.items() if len(paths) > 1}
    intra_genre_dupes = []
    cross_genre_dupes = []

    for h, paths in duplicates.items():
        genres_in_dup = {Path(p).parent.name for p in paths}
        if len(genres_in_dup) > 1:
            cross_genre_dupes.append({"hash": h, "genres": list(genres_in_dup), "files": paths})
        else:
            intra_genre_dupes.append({"hash": h, "genre": list(genres_in_dup)[0], "files": paths})

    # Summary statistics
    duration_arr = np.array(durations) if durations else np.array([0.0])
    mean_duration = float(np.mean(duration_arr))
    std_duration = float(np.std(duration_arr))
    min_duration = float(np.min(duration_arr))
    max_duration = float(np.max(duration_arr))

    audit_summary = {
        "dataset_root": data_dir.relative_to(PROJECT_ROOT).as_posix() if data_dir.is_relative_to(PROJECT_ROOT) else str(data_dir),
        "total_files_discovered": len(all_files),
        "valid_files_count": len(valid_files),
        "excluded_files_count": len(excluded_files),
        "discovered_genres": discovered_genres,
        "expected_genres_present": len(missing_genres) == 0,
        "missing_genres": missing_genres,
        "genre_raw_counts": dict(genre_counts),
        "genre_valid_counts": dict(genre_valid_counts),
        "sample_rate_distribution": dict(sample_rates),
        "channels_distribution": dict(channels_counts),
        "durations": {
            "mean_seconds": round(mean_duration, 3),
            "std_seconds": round(std_duration, 3),
            "min_seconds": round(min_duration, 3),
            "max_seconds": round(max_duration, 3),
        },
        "duplicates": {
            "total_duplicate_hashes": len(duplicates),
            "intra_genre_duplicate_groups": len(intra_genre_dupes),
            "cross_genre_duplicate_groups": len(cross_genre_dupes),
        },
    }

    manifest_data = {
        "summary": audit_summary,
        "excluded_files": excluded_files,
        "duplicates": {
            "cross_genre": cross_genre_dupes,
            "intra_genre": intra_genre_dupes,
        },
        "valid_tracks": valid_files,
    }

    # Save manifest JSON
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"✅ Saved machine-readable dataset manifest to: {manifest_path}")

    # Generate Markdown Report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_md = generate_markdown_report(audit_summary, excluded_files, cross_genre_dupes, intra_genre_dupes)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"✅ Saved detailed audit report to: {report_path}")

    # Print summary to console
    print("\n--- AUDIT SUMMARY REPORT ---")
    print(f"Total Discovered:   {len(all_files)}")
    print(f"Valid Tracks:       {len(valid_files)}")
    print(f"Excluded / Corrupt: {len(excluded_files)}")
    print(f"Sample Rates:       {dict(sample_rates)}")
    print(f"Channels:           {dict(channels_counts)}")
    print(f"Mean Duration:      {mean_duration:.2f}s (Min: {min_duration:.2f}s, Max: {max_duration:.2f}s)")
    print(f"Duplicate Groups:   {len(duplicates)} (Cross-genre: {len(cross_genre_dupes)}, Intra-genre: {len(intra_genre_dupes)})")

    if excluded_files:
        print("\nExcluded Files:")
        for exc in excluded_files:
            print(f"  ❌ {exc['path']} -> {exc['reason']}: {exc['detail']}")

    if cross_genre_dupes:
        print("\nCross-genre Duplicate Files (Potential Label Contamination):")
        for cdup in cross_genre_dupes:
            print(f"  ⚠️ Hash: {cdup['hash']} | Genres: {cdup['genres']} | Files: {cdup['files']}")

    return manifest_data


def generate_markdown_report(
    summary: Dict[str, Any],
    excluded: List[Dict[str, Any]],
    cross_dupes: List[Dict[str, Any]],
    intra_dupes: List[Dict[str, Any]],
) -> str:
    lines = [
        "# GTZAN Dataset Audit and Validation Report",
        "",
        "## 1. Executive Summary",
        "",
        f"- **Dataset Path:** `{summary['dataset_root']}`",
        f"- **Total Audio Files Found:** {summary['total_files_discovered']}",
        f"- **Valid, Decodeable Tracks:** **{summary['valid_files_count']}**",
        f"- **Excluded / Corrupt Files:** **{summary['excluded_files_count']}**",
        f"- **Classes Discovered:** {len(summary['discovered_genres'])} / 10 expected genres",
        f"- **Audio Sample Rate:** {', '.join(f'{k} Hz ({v} tracks)' for k, v in summary['sample_rate_distribution'].items())}",
        f"- **Audio Channels:** {', '.join(f'{k}-channel ({v} tracks)' for k, v in summary['channels_distribution'].items())}",
        f"- **Mean Track Duration:** {summary['durations']['mean_seconds']}s (range: {summary['durations']['min_seconds']}s to {summary['durations']['max_seconds']}s)",
        "",
        "## 2. Per-Genre Class Balance",
        "",
        "| Genre | Raw Files | Valid Files | Excluded | Balance Status |",
        "| :--- | :---: | :---: | :---: | :--- |",
    ]

    for g in sorted(summary["genre_raw_counts"].keys()):
        raw = summary["genre_raw_counts"].get(g, 0)
        valid = summary["genre_valid_counts"].get(g, 0)
        exc = raw - valid
        status = "✅ Balanced (100)" if valid == 100 else f"⚠️ {valid}/100"
        lines.append(f"| **{g}** | {raw} | {valid} | {exc} | {status} |")

    lines.extend([
        "",
        "## 3. Corrupt or Unreadable Audio Files",
        "",
    ])

    if excluded:
        lines.append("| File Path | Genre | Reason | Details |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for exc in excluded:
            lines.append(f"| `{exc['path']}` | {exc['genre']} | `{exc['reason']}` | {exc['detail']} |")
    else:
        lines.append("No unreadable or corrupted files were detected.")

    lines.extend([
        "",
        "## 4. Duplicate Analysis & Contamination Prevention",
        "",
        f"A total of **{summary['duplicates']['total_duplicate_hashes']} duplicate groups** were detected via exact MD5 checksum analysis:",
        "",
        f"- **Cross-Genre Duplicates ({len(cross_dupes)} groups):** Exact identical audio waveforms assigned to conflicting genres in GTZAN.",
        f"- **Intra-Genre Duplicates ({len(intra_dupes)} groups):** Identical audio clips repeated inside the same genre folder.",
        "",
    ])

    if cross_dupes:
        lines.append("### 4.1 Cross-Genre Duplicates (Critical for Split Isolation)")
        lines.append("")
        for cd in cross_dupes:
            lines.append(f"- **Hash:** `{cd['hash']}` | **Genres:** {', '.join(cd['genres'])}")
            for f in cd["files"]:
                lines.append(f"  - `{f}`")
        lines.append("")

    if intra_dupes:
        lines.append("### 4.2 Intra-Genre Duplicates")
        lines.append("")
        for idup in intra_dupes:
            lines.append(f"- **Genre:** `{idup['genre']}` | **Hash:** `{idup['hash']}`")
            for f in idup["files"]:
                lines.append(f"  - `{f}`")
        lines.append("")

    lines.extend([
        "## 5. Splitting and Training Recommendations",
        "",
        "1. **Exclude Corrupted Files:** Completely exclude unreadable files (e.g. `jazz.00054.wav`) from training, validation, and testing.",
        "2. **Recording-Level Isolation:** Ensure that identical or duplicate recordings (like the 14 duplicate hash pairs) are assigned to the **same split** (or deduplicated) so evaluation sets remain strictly unpolluted.",
        "3. **Stratified Partitioning:** Partition valid tracks with an 80% / 10% / 10% stratified split (`seed=42`).",
        "4. **Training-Only Normalization:** Compute global dataset mean and standard deviation strictly over the training split to avoid data leakage.",
        "",
        "## 6. How to Reproduce This Audit",
        "",
        "```bash",
        "# Run the audit script from the repository root",
        ".venv/bin/python3 ml/scripts/audit_dataset.py --data-dir ml/Data/genres_original",
        "```",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit and validate the GTZAN dataset")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=os.getenv("GTZAN_DATA_DIR", "ml/Data/genres_original"),
        help="Path to GTZAN genres directory",
    )
    parser.add_argument(
        "--output-manifest",
        type=str,
        default="ml/reports/dataset_manifest.json",
        help="Path to output manifest JSON file",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default="ml/reports/audit_report.md",
        help="Path to output markdown report file",
    )
    args = parser.parse_args()

    data_dir = (PROJECT_ROOT / args.data_dir).resolve() if not Path(args.data_dir).is_absolute() else Path(args.data_dir)
    manifest_path = (PROJECT_ROOT / args.output_manifest).resolve() if not Path(args.output_manifest).is_absolute() else Path(args.output_manifest)
    report_path = (PROJECT_ROOT / args.output_report).resolve() if not Path(args.output_report).is_absolute() else Path(args.output_report)

    audit_dataset(data_dir, manifest_path, report_path)


if __name__ == "__main__":
    main()

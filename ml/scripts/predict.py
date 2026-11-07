#!/usr/bin/env python3
"""CLI prediction script for evaluating individual audio tracks.

Usage:
    python ml/scripts/predict.py path/to/song.wav [--json]
"""

import sys
import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.inference import AudioGenrePredictor, ModelNotReadyError, InvalidAudioError
from ml.src.config import path_config


def main():
    parser = argparse.ArgumentParser(description="Predict music genre of an audio file using trained GenreCNN")
    parser.add_argument("audio_path", type=str, help="Path to audio file (WAV, MP3, OGG, FLAC)")
    parser.add_argument("--checkpoint", type=str, default="artifacts/models/genre_cnn.pt", help="Path to model checkpoint")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    audio_file = Path(args.audio_path)
    if not audio_file.exists():
        print(f"Error: Audio file not found at {audio_file}", file=sys.stderr)
        sys.exit(1)

    ckpt_path = PROJECT_ROOT / args.checkpoint

    try:
        predictor = AudioGenrePredictor(checkpoint_path=ckpt_path)
    except ModelNotReadyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        result = predictor.predict(audio_file)
    except InvalidAudioError as e:
        print(f"Error decoding audio: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"Inference error: {e}", file=sys.stderr)
        sys.exit(4)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print("\n" + "=" * 50)
    print(f"🎵 Audio Genre Classification: {audio_file.name}")
    print("=" * 50)
    print(f"Leading Genre:   {result['leading_display_name']} ({result['confidence']*100:.2f}% confidence)")
    print(f"Clip Duration:   {result['duration_seconds']}s")
    print(f"Model Status:    {result['model_status']}")
    print("-" * 50)
    print("Top 3 Genres:")
    for rank, entry in enumerate(result["top_three"], 1):
        bar = "█" * int(entry["score"] * 25)
        print(f"  {rank}. {entry['display_name']:<10} {entry['percentage']:5.1f}%  {bar}")
    print("-" * 50)
    print("Complete Genre Distribution:")
    for entry in result["all_scores"]:
        print(f"  - {entry['display_name']:<10}: {entry['percentage']:5.2f}%")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()

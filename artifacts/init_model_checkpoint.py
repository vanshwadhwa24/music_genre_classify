"""Initialize and verify PyTorch GenreCNN baseline model checkpoint."""

import os
import sys
from pathlib import Path
import torch

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ml.models.cnn import GenreCNN
from ml.preprocessing.audio_features import GENRES, SAMPLE_RATE, N_MELS

def init_baseline():
    model = GenreCNN(num_classes=len(GENRES))
    model.eval()

    # Synthetic test input: batch of 1, 1 channel, 128 mel bands, 1292 time frames (~30s of audio)
    dummy_input = torch.randn(1, 1, N_MELS, 1292)
    with torch.no_grad():
        out = model(dummy_input)
        probs = model.predict_probabilities(dummy_input)

    print("Model initialized successfully.")
    print("Dummy input shape:", dummy_input.shape)
    print("Output logits shape:", out.shape)
    print("Output probabilities sum:", probs.sum().item())
    print("Model summary:", model.get_architecture_summary())

    out_dir = ROOT_DIR / "artifacts" / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    save_path = out_dir / "genre_cnn_baseline.pt"

    torch.save({
        "model_state_dict": model.state_dict(),
        "status": "DEVELOPMENT_BASELINE",
        "description": "Baseline He-initialized PyTorch CNN for GTZAN 10-genre classification",
        "genres": GENRES,
        "sample_rate": SAMPLE_RATE,
        "n_mels": N_MELS,
    }, str(save_path))

    print(f"Saved baseline checkpoint to {save_path}")

if __name__ == "__main__":
    init_baseline()

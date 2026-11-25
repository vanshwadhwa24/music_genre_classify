"""Optional stronger upload classifier: frozen CLAP audio embeddings + logistic regression.

Used only for uploaded tracks (about 30 s). Live microphone windows keep the light CNN.
Loads lazily; if transformers, the CLAP weights or the probe file are unavailable the
caller falls back to the CNN, so the app keeps working without this model.
"""

import os
from pathlib import Path
from typing import Optional
import numpy as np

CLAP_MODEL_ID = "laion/clap-htsat-unfused"
CLAP_REVISION = "79b58ed25fc00386262a2bea4b19fd21dc4310a0"
CLAP_SR = 48000
CLIP_SECONDS = 10
MAX_CLIPS = 3
PROBE_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "artifacts" / "clap_logreg.npz"


def enabled() -> bool:
    return os.getenv("UPLOAD_MODEL", "clap").lower() == "clap"


class ClapUploadClassifier:
    def __init__(self):
        self._model = None
        self._fe = None
        self._probe = None
        self.failed = False

    def available(self) -> bool:
        return enabled() and not self.failed and PROBE_PATH.exists()

    def _load(self) -> None:
        import torch
        from transformers import ClapModel, ClapFeatureExtractor

        self._fe = ClapFeatureExtractor.from_pretrained(CLAP_MODEL_ID, revision=CLAP_REVISION)
        self._model = ClapModel.from_pretrained(CLAP_MODEL_ID, revision=CLAP_REVISION).eval()
        p = np.load(PROBE_PATH, allow_pickle=False)
        self._probe = {k: p[k] for k in ("mean", "scale", "coef", "intercept", "genres")}

    def predict_probs(self, y_22k: np.ndarray, sr: int) -> Optional[np.ndarray]:
        """Return a (10,) probability vector in GENRES order, or None on failure."""
        try:
            import torch
            import librosa

            if self._model is None:
                self._load()
            y = librosa.resample(np.asarray(y_22k, dtype=np.float32), orig_sr=sr, target_sr=CLAP_SR)
            L = CLAP_SR * CLIP_SECONDS
            clips = [y[j:j + L] for j in range(0, max(len(y) - L // 2, 1), L)][:MAX_CLIPS]
            clips = [np.pad(c, (0, L - len(c))) for c in clips]
            inp = self._fe(clips, sampling_rate=CLAP_SR, return_tensors="pt")
            with torch.no_grad():
                e = self._model.get_audio_features(**inp)
            e = (e.pooler_output if hasattr(e, "pooler_output") else e).numpy()
            pr = self._probe
            z = (e - pr["mean"]) / pr["scale"]
            logits = z @ pr["coef"].T + pr["intercept"]
            logits -= logits.max(axis=1, keepdims=True)
            p = np.exp(logits)
            p /= p.sum(axis=1, keepdims=True)
            return p.mean(axis=0)
        except Exception as exc:  # fall back to the CNN
            print(f"[ClapUploadClassifier] disabled after error: {exc}")
            self.failed = True
            return None


clap_classifier = ClapUploadClassifier()

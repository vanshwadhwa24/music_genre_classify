"""Candidate upload classifier: frozen CLAP + frozen AST embeddings -> logistic regression.

Research candidate (held-out 92/101 on one split). Used only for uploaded tracks; live
microphone windows keep the light CNN. AST is BSD-3-Clause (MIT/ast-finetuned-audioset-10-10-0.4593).
Loads lazily and shares the CLAP encoder with clap_inference. Any failure returns None so the
caller falls back to the CLAP probe, then the CNN.
"""

import os
from pathlib import Path
from typing import Optional
import numpy as np

from backend.app.clap_inference import (
    CLAP_SR, CLIP_SECONDS, MAX_CLIPS, clap_classifier,
)

AST_MODEL_ID = "MIT/ast-finetuned-audioset-10-10-0.4593"
AST_SR = 16000
PROBE_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "artifacts" / "clap_ast_logreg.npz"


def enabled() -> bool:
    return os.getenv("UPLOAD_MODEL", "clap").lower() == "clap_ast"


def _clips(y: np.ndarray, sr: int):
    L = sr * CLIP_SECONDS
    cl = [y[j:j + L] for j in range(0, max(len(y) - L // 2, 1), L)][:MAX_CLIPS]
    return [np.pad(c, (0, L - len(c))) for c in cl]


class ClapAstUploadClassifier:
    def __init__(self):
        self._ast = None
        self._ast_fe = None
        self._probe = None
        self.failed = False

    def available(self) -> bool:
        return enabled() and not self.failed and PROBE_PATH.exists()

    def _load(self) -> None:
        from transformers import ASTModel, ASTFeatureExtractor

        if clap_classifier._model is None:
            clap_classifier._load()
        self._ast_fe = ASTFeatureExtractor.from_pretrained(AST_MODEL_ID)
        self._ast = ASTModel.from_pretrained(AST_MODEL_ID).eval()
        p = np.load(PROBE_PATH, allow_pickle=False)
        self._probe = {k: p[k] for k in ("mean", "scale", "coef", "intercept", "genres")}

    def predict_probs(self, y_22k: np.ndarray, sr: int) -> Optional[np.ndarray]:
        """Return a (10,) probability vector in GENRES order, or None on failure."""
        try:
            import torch
            import librosa

            if self._ast is None:
                self._load()
            y22 = np.asarray(y_22k, dtype=np.float32)
            y48 = librosa.resample(y22, orig_sr=sr, target_sr=CLAP_SR)
            y16 = librosa.resample(y22, orig_sr=sr, target_sr=AST_SR)
            c48, c16 = _clips(y48, CLAP_SR), _clips(y16, AST_SR)
            n = min(len(c48), len(c16))
            with torch.no_grad():
                inp = clap_classifier._fe(c48[:n], sampling_rate=CLAP_SR, return_tensors="pt")
                e1 = clap_classifier._model.get_audio_features(**inp)
                e1 = (e1.pooler_output if hasattr(e1, "pooler_output") else e1).numpy()
                inp = self._ast_fe(c16[:n], sampling_rate=AST_SR, return_tensors="pt")
                e2 = self._ast(**inp).pooler_output.numpy()
            e = np.hstack([e1, e2])
            pr = self._probe
            z = (e - pr["mean"]) / pr["scale"]
            logits = z @ pr["coef"].T + pr["intercept"]
            logits -= logits.max(axis=1, keepdims=True)
            p = np.exp(logits)
            p /= p.sum(axis=1, keepdims=True)
            return p.mean(axis=0)
        except Exception as exc:  # fall back to CLAP, then the CNN
            print(f"[ClapAstUploadClassifier] disabled after error: {exc}")
            self.failed = True
            return None


clap_ast_classifier = ClapAstUploadClassifier()

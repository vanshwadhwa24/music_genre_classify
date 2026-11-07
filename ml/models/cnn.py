"""PyTorch Convolutional Neural Network Architecture for GTZAN Genre Classification.

Input: Normalized Mel-spectrogram tensor of shape (Batch, 1, n_mels, time_steps).
Output: Raw logits across the 10 GTZAN musical genre classes.
Unified with ml.src.model.
"""

from ml.src.model import ConvBlock, GenreCNN

__all__ = ["ConvBlock", "GenreCNN"]

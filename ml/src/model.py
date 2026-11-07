"""PyTorch 2D Convolutional Neural Network for Audio Mel-Spectrogram Genre Classification.

Architecture:
- 4 Convolutional stages with 2D convolutions, Batch Normalization, ELU activations, Max Pooling, and Spatial Dropout.
- Global Average Pooling (AdaptiveAvgPool2d((1, 1))).
- 2-layer Dense Classifier head with ReLU, Dropout, and 10 raw output logits.
"""

from typing import Dict, Any, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F

from ml.src.config import GENRES


class ConvBlock(nn.Module):
    """Convolutional Block: Conv2d -> BatchNorm2d -> Activation -> MaxPool2d -> Spatial Dropout."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        padding: int = 1,
        pool_size: int = 2,
        dropout_rate: float = 0.20,
    ):
        super().__init__()
        self.conv = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=kernel_size,
            padding=padding,
            bias=False,
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.act = nn.ELU()
        self.pool = nn.MaxPool2d(kernel_size=pool_size, stride=pool_size)
        self.dropout = nn.Dropout2d(p=dropout_rate)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dropout(self.pool(self.act(self.bn(self.conv(x)))))


class GenreCNN(nn.Module):
    """Deep 4-stage 2D-CNN with Global Average Pooling for Audio Genre Classification."""

    def __init__(
        self,
        num_classes: int = len(GENRES),
        in_channels: int = 1,
        dropout_conv: float = 0.20,
        dropout_dense: float = 0.40,
    ):
        super().__init__()
        self.num_classes = num_classes

        # Feature Extractor Stages: (1, 128, T) -> (256, 1, 1)
        self.block1 = ConvBlock(in_channels, 32, dropout_rate=dropout_conv * 0.75)
        self.block2 = ConvBlock(32, 64, dropout_rate=dropout_conv)
        self.block3 = ConvBlock(64, 128, dropout_rate=dropout_conv * 1.25)
        self.block4 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ELU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        # Classification Head
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(p=dropout_dense),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.
        Args:
            x: Tensor of shape (Batch, 1, n_mels, time_steps)
        Returns:
            Raw logits of shape (Batch, num_classes)
        """
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        logits = self.classifier(x)
        return logits

    def predict_probabilities(self, x: torch.Tensor) -> torch.Tensor:
        """Compute softmax probability distribution across classes."""
        logits = self.forward(x)
        return F.softmax(logits, dim=-1)

    def get_architecture_summary(self) -> Dict[str, Any]:
        """Return structural metadata and parameter counts."""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return {
            "model_type": "2D-CNN Audio Mel-Spectrogram Classifier",
            "input_shape": "(Batch, 1, 128, T)",
            "conv_stages": 4,
            "filters": [32, 64, 128, 256],
            "pooling": "MaxPool2d(2, 2) + AdaptiveAvgPool2d((1, 1))",
            "activations": "ELU (conv) + ReLU (dense)",
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "num_classes": self.num_classes,
        }

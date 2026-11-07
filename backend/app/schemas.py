"""Strict Pydantic schemas for Music Genre Classifier API."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class GenreScore(BaseModel):
    genre: str = Field(..., description="GTZAN genre name")
    display_name: str = Field(..., description="Capitalized readable name")
    score: float = Field(..., ge=0.0, le=1.0, description="Model output score (0.0 to 1.0)")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Score formatted as percentage")


class TrackMetadata(BaseModel):
    filename: str
    duration_seconds: float
    sample_rate: int
    channels: int
    format: str
    file_size_bytes: int


class SpectrogramInfo(BaseModel):
    url: str
    data_uri: Optional[str] = None
    n_mels: int
    hop_length: int
    time_steps: int


class PredictionResult(BaseModel):
    leading_genre: str
    leading_display_name: str
    top_three: List[GenreScore]
    all_scores: List[GenreScore]
    model_status: str = Field(
        ...,
        description="One of: 'ACTIVE_MODEL', 'DEVELOPMENT_BASELINE', 'DEVELOPMENT_MOCK', 'UNAVAILABLE'",
    )
    is_mock: bool = Field(..., description="True if using mock/uncalibrated synthetic adapter")
    is_calibrated: bool = Field(
        default=False,
        description="False: scores are raw softmax outputs, not calibrated probabilities",
    )


class AnalysisResponse(BaseModel):
    id: str
    track: TrackMetadata
    prediction: PredictionResult
    spectrogram: SpectrogramInfo
    processing_time_ms: float


class LivePredictionResponse(BaseModel):
    timestamp_ms: float
    window_duration_seconds: float
    leading_genre: str
    leading_display_name: str
    top_three: List[GenreScore]
    energy_rms: float
    model_status: str
    is_mock: bool
    is_calibrated: bool = False


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_status: str
    model_path: Optional[str] = None
    genres: List[str]
    device: str
    version: str


class ModelArchitectureInfo(BaseModel):
    name: str
    parameters_total: int
    classes: List[str]
    preprocessing: Dict[str, Any]
    limitations: List[str]

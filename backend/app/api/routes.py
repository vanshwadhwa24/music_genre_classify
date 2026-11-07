"""FastAPI route handlers for audio analysis and real-time live prediction."""

import time
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Response
from fastapi.responses import Response

from backend.app.schemas import (
    HealthResponse,
    AnalysisResponse,
    LivePredictionResponse,
    TrackMetadata,
    SpectrogramInfo,
    ModelArchitectureInfo,
)
from backend.app.audio import (
    process_audio_file,
    process_live_audio_chunk,
    get_cached_spectrogram,
    png_to_data_uri,
)
from backend.app.inference import model_manager
from backend.app.config import settings
from ml.preprocessing.audio_features import (
    GENRES,
    GENRE_DISPLAY_NAMES,
    SAMPLE_RATE,
    DEFAULT_DURATION,
    N_FFT,
    HOP_LENGTH,
    N_MELS,
)

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health and model readiness check."""
    if model_manager.model is None:
        model_manager.load_model()
    return HealthResponse(
        status="healthy",
        model_loaded=model_manager.model is not None,
        model_status=model_manager.model_status,
        model_path=model_manager.loaded_checkpoint_path,
        genres=GENRES,
        device=str(model_manager.device),
        version=settings.version,
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_track(
    file: UploadFile = File(..., description="Audio file (WAV, MP3, OGG, M4A, FLAC)"),
):
    """Analyze uploaded audio track and return predicted genre, scores, and Mel-spectrogram."""
    start_time = time.perf_counter()

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file provided.")

    try:
        y, mel_db, duration, analysis_id, png_bytes = process_audio_file(
            file_bytes,
            filename=file.filename,
        )
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failure: {str(e)}")

    # Model inference
    try:
        prediction = model_manager.predict(mel_db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {str(e)}")

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    track_meta = TrackMetadata(
        filename=file.filename,
        duration_seconds=round(duration, 2),
        sample_rate=settings.sample_rate,
        channels=1,  # Downmixed to mono
        format=file.filename.split(".")[-1].lower() if "." in file.filename else "unknown",
        file_size_bytes=len(file_bytes),
    )

    spectrogram_info = SpectrogramInfo(
        url=f"/api/analyses/{analysis_id}/spectrogram",
        data_uri=png_to_data_uri(png_bytes),
        n_mels=N_MELS,
        hop_length=HOP_LENGTH,
        time_steps=mel_db.shape[1],
    )

    return AnalysisResponse(
        id=analysis_id,
        track=track_meta,
        prediction=prediction,
        spectrogram=spectrogram_info,
        processing_time_ms=elapsed_ms,
    )


@router.post("/live/predict", response_model=LivePredictionResponse)
async def live_predict(
    file: UploadFile = File(..., description="Short rolling audio slice (e.g. 2-3 seconds)"),
    reset: bool = Query(False, description="Reset EMA temporal smoothing buffer"),
):
    """Process a rolling audio buffer from the microphone and return smoothed genre scores."""
    chunk_bytes = await file.read()
    if len(chunk_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio buffer received.")

    try:
        y, mel_db, rms = process_live_audio_chunk(chunk_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to decode microphone buffer: {str(e)}")

    prediction = model_manager.predict_live(mel_db, reset_smoothing=reset)

    return LivePredictionResponse(
        timestamp_ms=time.time() * 1000,
        window_duration_seconds=round(len(y) / settings.sample_rate, 2),
        leading_genre=prediction.leading_genre,
        leading_display_name=prediction.leading_display_name,
        top_three=prediction.top_three,
        energy_rms=round(rms, 4),
        model_status=prediction.model_status,
        is_mock=prediction.is_mock,
        is_calibrated=False,
    )


@router.get("/analyses/{analysis_id}/spectrogram")
async def get_spectrogram_image(analysis_id: str):
    """Serve cached high-resolution Mel-spectrogram image as PNG."""
    png_bytes = get_cached_spectrogram(analysis_id)
    if not png_bytes:
        raise HTTPException(status_code=404, detail="Spectrogram not found or expired from cache.")

    return Response(content=png_bytes, media_type="image/png")


@router.get("/model/info", response_model=ModelArchitectureInfo)
async def get_model_info():
    """Return genuine architectural and dataset information."""
    if model_manager.model is None:
        model_manager.load_model()
    arch = model_manager.model.get_architecture_summary() if model_manager.model else {}
    return ModelArchitectureInfo(
        name="GTZAN 2D-CNN Audio Spectrogram Classifier",
        parameters_total=arch.get("total_parameters", 0),
        classes=[GENRE_DISPLAY_NAMES[g] for g in GENRES],
        preprocessing={
            "sample_rate_hz": SAMPLE_RATE,
            "clip_duration_sec": DEFAULT_DURATION,
            "live_window_sec": settings.live_window_seconds,
            "n_fft": N_FFT,
            "hop_length": HOP_LENGTH,
            "n_mels": N_MELS,
            "scaling": "Decibels (dB) via librosa.power_to_db + z-score normalization",
        },
        limitations=[
            "GTZAN dataset contains subtle label noise, occasional repetitions, and distortion artifacts in historical recordings.",
            "Trained predominantly on 30-second studio excerpts; accuracy degrades on very short rolling audio (< 2.0s).",
            "Acoustic noise, microphone frequency response differences, and room reverberation may alter classification scores during live listening.",
            "Raw softmax outputs represent relative model activation scores, not formally calibrated posterior probabilities.",
        ],
    )

"""Unit and integration tests for FastAPI backend and audio inference."""

from pathlib import Path
import pytest
from starlette.testclient import TestClient

from backend.app.main import app

SAMPLE_ROCK_PATH = Path("frontend/public/samples/rock_sample.wav")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert len(data["genres"]) == 10
    assert "rock" in data["genres"]


def test_model_info_endpoint(client):
    response = client.get("/api/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "parameters_total" in data
    assert data["parameters_total"] > 0
    assert len(data["classes"]) == 10
    assert len(data["limitations"]) > 0


def test_analyze_audio_endpoint(client):
    assert SAMPLE_ROCK_PATH.exists(), "Sample test file must exist"

    with open(SAMPLE_ROCK_PATH, "rb") as f:
        response = client.post(
            "/api/analyze",
            files={"file": ("rock_sample.wav", f, "audio/wav")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "track" in data
    assert data["track"]["filename"] == "rock_sample.wav"
    assert data["track"]["duration_seconds"] > 0

    # Prediction verification
    prediction = data["prediction"]
    assert "leading_genre" in prediction
    assert len(prediction["top_three"]) == 3
    assert len(prediction["all_scores"]) == 10
    assert prediction["top_three"][0]["score"] >= prediction["top_three"][1]["score"]

    # Spectrogram verification
    spectrogram = data["spectrogram"]
    assert spectrogram["url"].startswith("/api/analyses/")
    assert spectrogram["data_uri"].startswith("data:image/png;base64,")

    # Check that spectrogram GET endpoint returns the cached PNG
    spec_response = client.get(spectrogram["url"])
    assert spec_response.status_code == 200
    assert spec_response.headers["content-type"] == "image/png"


def test_live_predict_endpoint(client):
    assert SAMPLE_ROCK_PATH.exists()

    with open(SAMPLE_ROCK_PATH, "rb") as f:
        # Take first 44100 bytes (~1-2 seconds)
        chunk = f.read(44100)
        response = client.post(
            "/api/live/predict",
            files={"file": ("slice.wav", chunk, "audio/wav")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "leading_genre" in data
    assert len(data["top_three"]) == 3
    assert "energy_rms" in data
    assert data["window_duration_seconds"] > 0


def test_invalid_file_handling(client):
    # Empty file
    response = client.post(
        "/api/analyze",
        files={"file": ("empty.wav", b"", "audio/wav")},
    )
    assert response.status_code == 400

    # Corrupted audio bytes
    response = client.post(
        "/api/analyze",
        files={"file": ("corrupt.wav", b"not-audio-bytes-at-all", "audio/wav")},
    )
    assert response.status_code == 422

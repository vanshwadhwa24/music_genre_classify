# REST API Contract — Music Genre Classifier

## 1. Base URL
- Development: `http://127.0.0.1:8000` (proxied via Vite frontend at `/api`)
- Configurable via `VITE_API_URL` environment variable.

---

## 2. Endpoints

### GET `/api/health`
Checks server health, model loading status, device, and GTZAN class list.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_status": "ACTIVE_MODEL",
  "model_path": "/path/to/checkpoint.pt",
  "genres": ["blues", "classical", "country", "disco", "hiphop", "jazz", "metal", "pop", "reggae", "rock"],
  "device": "cpu",
  "version": "1.0.0"
}
```

---

### POST `/api/analyze`
Accepts an audio file upload (WAV, MP3, OGG, M4A, FLAC) up to 30MB, validates audio data, computes the Log-Mel spectrogram, and outputs predicted genre distributions.

**Request:** `multipart/form-data`
- `file`: Audio binary payload

**Response (200 OK):**
```json
{
  "id": "c1f7a049-51a1-4ee6-8571-0ce0f6d625d9",
  "track": {
    "filename": "song.wav",
    "duration_seconds": 30.0,
    "sample_rate": 22050,
    "channels": 1,
    "format": "wav",
    "file_size_bytes": 1323044
  },
  "prediction": {
    "leading_genre": "rock",
    "leading_display_name": "Rock",
    "top_three": [
      {"genre": "rock", "display_name": "Rock", "score": 0.7241, "percentage": 72.41},
      {"genre": "metal", "display_name": "Metal", "score": 0.1802, "percentage": 18.02},
      {"genre": "pop", "display_name": "Pop", "score": 0.0512, "percentage": 5.12}
    ],
    "all_scores": [...],
    "model_status": "ACTIVE_MODEL",
    "is_mock": false,
    "is_calibrated": false
  },
  "spectrogram": {
    "url": "/api/analyses/c1f7a049-51a1-4ee6-8571-0ce0f6d625d9/spectrogram",
    "data_uri": "data:image/png;base64,...",
    "n_mels": 128,
    "hop_length": 512,
    "time_steps": 1292
  },
  "processing_time_ms": 142.5
}
```

---

### POST `/api/live/predict`
Accepts a short rolling audio slice (e.g. 2.5s) from browser microphone capture, computes Log-Mel spectrogram, and applies Exponential Moving Average (EMA) temporal smoothing.

**Query Parameters:**
- `reset` (boolean, optional, default: false): Resets temporal smoothing buffer.

**Request:** `multipart/form-data`
- `file`: Audio chunk binary (WAV or WebM)

**Response (200 OK):**
```json
{
  "timestamp_ms": 1728800000000.0,
  "window_duration_seconds": 2.5,
  "leading_genre": "jazz",
  "leading_display_name": "Jazz",
  "top_three": [
    {"genre": "jazz", "display_name": "Jazz", "score": 0.5412, "percentage": 54.12},
    {"genre": "blues", "display_name": "Blues", "score": 0.2810, "percentage": 28.10},
    {"genre": "classical", "display_name": "Classical", "score": 0.0911, "percentage": 9.11}
  ],
  "energy_rms": 0.1245,
  "model_status": "ACTIVE_MODEL",
  "is_mock": false,
  "is_calibrated": false
}
```

---

### GET `/api/analyses/{id}/spectrogram`
Retrieves the rendered publication-quality Mel-spectrogram as an image.

**Response (200 OK):**
- `Content-Type: image/png`

---

### GET `/api/model/info`
Returns architectural metadata, parameter counts, preprocessing constants, and model limitations.

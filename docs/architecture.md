# System Architecture — Music Genre Classifier PWA

## 1. Overview
The Music Genre Classifier is a Progressive Web App (PWA) designed as a sophisticated instrument for exploring sound identity. It bridges modern web audio streaming with a PyTorch 2D Convolutional Neural Network (CNN) trained on the GTZAN Music Genre Dataset.

```
┌────────────────────────────────────────────────────────┐
│               Frontend (React 19 + Vite)               │
│  - Discover (Upload, Player, Spectrogram, Scores)      │
│  - Live Listening (60 FPS Canvas Waveform, Mic Capture)│
│  - About (Scientific Dataset & CNN Methodology)        │
│  - PWA Service Worker (Offline Application Shell)      │
└───────────────────────────┬────────────────────────────┘
                            │ REST API (/api)
┌───────────────────────────▼────────────────────────────┐
│                 Backend (FastAPI + Python)             │
│  - /api/health (Lifespan Model Status)                 │
│  - /api/analyze (Audio Validation, Mel-Spectrogram)    │
│  - /api/live/predict (Rolling Window & EMA Smoothing)  │
│  - /api/analyses/{id}/spectrogram (PNG Caching)        │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│             Machine Learning & Audio Pipeline          │
│  - Preprocessing: 22.05 kHz Mono, 128 Mel Bands, dB    │
│  - Model: 4-Stage 2D-CNN (422k parameters, PyTorch)    │
│  - Evaluation & Checkpoint Lifecycle                   │
└────────────────────────────────────────────────────────┘
```

## 2. Directory Structure
```
music-genre-classifier/
├── frontend/               # React 19 + TypeScript + Vite + Tailwind v4 + PWA
│   ├── public/             # PWA icons, manifest, and synthesized audio samples
│   ├── src/
│   │   ├── components/     # UI design token components, AudioPlayer, LiveCanvas
│   │   ├── pages/          # DiscoverPage, LivePage, AboutPage
│   │   ├── services/       # Typed API communication layer
│   │   ├── types/          # TypeScript contracts matching Pydantic schemas
│   │   └── utils/          # Web Audio API AudioStreamer
│   └── vite.config.ts      # VitePWA, Tailwind plugin, and API proxy
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── api/            # Route endpoints
│   │   ├── audio.py        # Librosa audio loading & spectrogram generation
│   │   ├── config.py       # Environment and CORS settings
│   │   ├── inference.py    # PyTorch ModelManager & EMA smoothing
│   │   ├── main.py         # App lifecycle & middleware
│   │   └── schemas.py      # Pydantic request and response schemas
│   └── tests/              # Pytest test suite
├── ml/                     # Shared Machine Learning Pipeline
│   ├── preprocessing/      # Shared feature extraction (Librosa / SoundFile)
│   ├── models/             # PyTorch GenreCNN architecture
│   ├── training/           # CLI training script for GTZAN
│   └── evaluation/         # Evaluation script & confusion matrix generator
├── artifacts/              # Model checkpoints and test assets
├── docs/                   # Architecture and API documentation
├── requirements.txt        # Pinned Python dependencies
└── README.md
```

## 3. Audio Preprocessing Pipeline
To guarantee exact mathematical parity between training and inference:
- **Sample Rate:** `22,050 Hz` (GTZAN standard).
- **Channels:** Monophonic downmix via channel averaging.
- **Duration:** 30.0s for batch track uploads; 2.5s–3.0s for live microphone slices.
- **STFT Parameters:** FFT size `2048` (~93ms window), Hop length `512` (~23ms hop), 75% frame overlap.
- **Mel Scale:** `128` triangular filterbanks covering 20 Hz to 11,025 Hz (Nyquist limit).
- **Logarithmic Scaling:** `librosa.power_to_db(mel, ref=np.max)`.
- **Normalization:** Standard z-score standardization `(S - μ) / σ`.

## 4. CNN Architecture
The classifier utilizes a 4-stage 2D Convolutional Neural Network:
- **Input:** `(Batch, 1, 128, TimeFrames)`
- **Stage 1:** `Conv2d(1→32, k=3, p=1)` → `BatchNorm2d` → `ELU` → `MaxPool2d(2, 2)` → `Dropout(0.15)`
- **Stage 2:** `Conv2d(32→64, k=3, p=1)` → `BatchNorm2d` → `ELU` → `MaxPool2d(2, 2)` → `Dropout(0.20)`
- **Stage 3:** `Conv2d(64→128, k=3, p=1)` → `BatchNorm2d` → `ELU` → `MaxPool2d(2, 2)` → `Dropout(0.25)`
- **Stage 4:** `Conv2d(128→256, k=3, p=1)` → `BatchNorm2d` → `ELU` → `AdaptiveAvgPool2d((1, 1))`
- **Classifier:** `Flatten()` → `Linear(256→128)` → `ReLU` → `Dropout(0.40)` → `Linear(128→10)` → `Softmax`
- **Total Parameters:** `422,506`

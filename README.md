# JAMBIRD — Playful Editorial Music Genre Classifier PWA

A Progressive Web App (PWA) and deep learning audio system with a **Playful Editorial SaaS Design System** that classifies musical tracks and live microphone audio using a 2D Convolutional Neural Network (CNN) trained on the GTZAN benchmark dataset.

---

## 1. Visual Identity & Design System (Jambird Aesthetic)

- **Design Philosophy:** Expressive, memorable, and youthful editorial branding combined with clean, usable software interfaces (inspired by bold neo-editorial Dribbble design standards).
- **Color Palette:**
  - Butter Yellow: `#FFDF43` (Hero banners, primary highlights, accent pills)
  - Bubblegum Pink: `#F49ACB` (Ticker marquees, primary buttons, secondary emphasis)
  - Chocolate Brown: `#4B2B23` (High-contrast typography, crisp 2px borders, brutalist offset shadows)
  - Periwinkle Blue: `#8CA4E8` (Methodology sections, tertiary cards, audio details)
  - Warm Cream: `#FFF9E9` (Page canvas, comfortable reading surfaces)
  - White: `#FFFFFF` (Interface cards, data containers, input boxes)
- **Typography:**
  - Display Font: **Anton** (tall, condensed, bold uppercase display headings with tight letter spacing)
  - Body Font: **Plus Jakarta Sans** / **Inter** (highly legible sans-serif for forms, metadata, and body copy)
  - Code Font: **Space Mono** (monospaced metrics, sampling parameters, frame counts)
- **Mascot & Illustrated Personality:**
  - "Jambird" — an expressive illustrated bird mascot jamming with a sideways cap, studio headphones, and musical note accents.
- **Destinations:**
  1. **Discover:** Drag-and-drop audio track upload, synthesized demonstration crate, interactive cassette player deck, top-three ranked genre score distributions, and Mel-spectrogram frequency mapping.
  2. **Live Listening:** Dedicated vinyl turntable circular sound visualizer capturing incoming microphone audio in real time, with rolling 2.5s window CNN inference and EMA temporal smoothing.
  3. **About the Model:** Scientific documentation explaining the GTZAN benchmark, 10 supported genres, audio preprocessing pipeline, 4-stage 2D-CNN architecture table, and acoustic limitations.

---

## 2. Monorepo Structure

```
music-genre-classifier/
├── frontend/                  # React 19, TypeScript, Vite, Tailwind v4, PWA
│   ├── public/                # PWA manifest, sound-inspired icons, test samples
│   ├── src/
│   │   ├── components/        # AudioPlayer, LiveVisualizerCanvas, ScoreBar, etc.
│   │   ├── pages/             # DiscoverPage, LivePage, AboutPage
│   │   ├── services/          # Typed API communication client
│   │   ├── types/             # Strict TypeScript API schemas
│   │   └── utils/             # Web Audio API AudioStreamer manager
│   └── vite.config.ts         # VitePWA, Tailwind plugin, API proxy
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── api/routes.py      # /api/health, /api/analyze, /api/live/predict
│   │   ├── audio.py           # Audio decoding, Mel-spectrogram, LRU cache
│   │   ├── config.py          # Environment settings
│   │   ├── inference.py       # PyTorch ModelManager & temporal smoothing
│   │   ├── main.py            # FastAPI entrypoint with lifespan model load
│   │   └── schemas.py         # Strict Pydantic response models
│   └── tests/test_api.py      # Pytest backend test suite
├── ml/                        # Machine Learning Pipeline
│   ├── preprocessing/         # Exact shared audio feature pipeline
│   ├── models/cnn.py          # 4-stage PyTorch GenreCNN (422,506 params)
│   ├── training/train.py      # GTZAN dataset training script
│   └── evaluation/evaluate.py # Evaluation & confusion matrix script
├── artifacts/                 # Model checkpoints, assets, and test files
├── docs/                      # Architecture & API documentation
├── requirements.txt           # Pinned backend & ML dependencies
└── README.md
```

---

## 3. Quickstart & Local Setup

### Prerequisites
- **Node.js:** v18+ (tested on Node v22)
- **Python:** 3.10+ (tested on Python 3.14)

### Step 1: Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API docs will be available at `http://127.0.0.1:8000/docs`.

### Step 2: Frontend Setup
In a new terminal:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
Open `http://localhost:5173` (or the printed port) in your browser.

---

## 4. Running Automated Tests

### Backend Test Suite
```bash
source .venv/bin/activate
pytest backend/tests/test_api.py -v
```
Verifies health checks, file validation, spectrogram rendering, and live audio prediction.

### Frontend Typecheck & PWA Build
```bash
cd frontend
npm run build
```
Validates TypeScript compilation and generates PWA service workers and precache manifests.

---

## 5. Machine Learning & Training Pipeline

### Dataset
The model is designed for the **GTZAN Music Genre Dataset** (1,000 tracks, 100 per genre, 30s clips):
- Genres: Blues, Classical, Country, Disco, Hip-Hop, Jazz, Metal, Pop, Reggae, Rock.

### Preprocessing Specifications
- Sample Rate: `22,050 Hz` (Mono)
- FFT Window: `2,048` samples (~93ms)
- Hop Length: `512` samples (~23ms)
- Mel Filterbanks: `128` bands (20 Hz – 11,025 Hz)
- Scale: Decibels (`librosa.power_to_db`) with z-score normalization

### Training on GTZAN
Whenever your GTZAN dataset is downloaded:
```bash
python ml/training/train.py \
  --data-dir path/to/genres_original \
  --epochs 40 \
  --batch-size 16 \
  --lr 0.001 \
  --save-path artifacts/models/genre_cnn.pt
```

### Model Checkpoint Integration
The backend automatically detects and loads checkpoints:
- **Baseline / Development Checkpoint:** `artifacts/models/genre_cnn_baseline.pt` (loaded by default).
- **Trained Model Checkpoint:** Set `MODEL_PATH=artifacts/models/genre_cnn.pt` or overwrite `artifacts/models/genre_cnn_baseline.pt`.
- The application status badge dynamically updates from `Baseline PyTorch CNN` to `Trained CNN Model`.

---

## 6. Progressive Web App (PWA) Capabilities

- **Manifest:** Standalone display mode, dark theme `#080B12`, 192x192, 512x512, and maskable icons.
- **Service Worker:** Automatic updates with asset precaching via `vite-plugin-pwa` and Workbox.
- **Offline Behavior:** The application shell, interactive UI, and sample previews remain available offline. If the ML backend is unreachable, the UI clearly displays offline badges and reconnect actions rather than fabricating offline predictions.

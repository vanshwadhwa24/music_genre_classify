export interface GenreScore {
  genre: string;
  display_name: string;
  score: number;
  percentage: number;
}

export interface TrackMetadata {
  filename: string;
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  format: string;
  file_size_bytes: number;
}

export interface SpectrogramInfo {
  url: string;
  data_uri?: string;
  n_mels: number;
  hop_length: number;
  time_steps: number;
}

export interface PredictionResult {
  leading_genre: string;
  leading_display_name: string;
  top_three: GenreScore[];
  all_scores: GenreScore[];
  model_status: 'ACTIVE_MODEL' | 'DEVELOPMENT_BASELINE' | 'DEVELOPMENT_MOCK' | 'UNAVAILABLE';
  is_mock: boolean;
  is_calibrated: boolean;
}

export interface AnalysisResponse {
  id: string;
  track: TrackMetadata;
  prediction: PredictionResult;
  spectrogram: SpectrogramInfo;
  processing_time_ms: number;
}

export interface LivePredictionResponse {
  timestamp_ms: number;
  window_duration_seconds: number;
  leading_genre: string;
  leading_display_name: string;
  top_three: GenreScore[];
  energy_rms: number;
  model_status: string;
  is_mock: boolean;
  is_calibrated: boolean;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  model_status: string;
  model_path?: string;
  genres: string[];
  device: string;
  version: string;
}

export interface ModelArchitectureInfo {
  name: string;
  parameters_total: number;
  classes: string[];
  preprocessing: {
    sample_rate_hz: number;
    clip_duration_sec: number;
    live_window_sec: number;
    n_fft: number;
    hop_length: number;
    n_mels: number;
    scaling: string;
  };
  limitations: string[];
}

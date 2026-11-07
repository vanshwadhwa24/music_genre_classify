import type {
  AnalysisResponse,
  HealthResponse,
  LivePredictionResponse,
  ModelArchitectureInfo,
} from '../types/api'

const API_BASE = import.meta.env.VITE_API_URL || ''

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`
    try {
      const errorJson = await res.json()
      if (errorJson && errorJson.detail) {
        detail = errorJson.detail
      }
    } catch {
      // response was not JSON
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export const apiService = {
  async checkHealth(): Promise<HealthResponse> {
    try {
      const res = await fetch(`${API_BASE}/api/health`, {
        cache: 'no-store',
      })
      return await handleResponse<HealthResponse>(res)
    } catch (err: unknown) {
      if (err instanceof ApiError) throw err
      throw new ApiError(0, 'Backend is unreachable. Please check if the FastAPI server is running.')
    }
  },

  async analyzeTrack(file: File): Promise<AnalysisResponse> {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        body: formData,
      })
      return await handleResponse<AnalysisResponse>(res)
    } catch (err: unknown) {
      if (err instanceof ApiError) throw err
      throw new ApiError(0, 'Failed to upload and analyze track. Backend may be offline.')
    }
  },

  async predictLive(audioBlob: Blob, reset: boolean = false): Promise<LivePredictionResponse> {
    const formData = new FormData()
    formData.append('file', audioBlob, 'live_chunk.wav')

    try {
      const res = await fetch(`${API_BASE}/api/live/predict?reset=${reset ? 'true' : 'false'}`, {
        method: 'POST',
        body: formData,
      })
      return await handleResponse<LivePredictionResponse>(res)
    } catch (err: unknown) {
      if (err instanceof ApiError) throw err
      throw new ApiError(0, 'Live prediction request failed.')
    }
  },

  async getModelInfo(): Promise<ModelArchitectureInfo> {
    try {
      const res = await fetch(`${API_BASE}/api/model/info`, {
        cache: 'no-store',
      })
      return await handleResponse<ModelArchitectureInfo>(res)
    } catch (err: unknown) {
      if (err instanceof ApiError) throw err
      throw new ApiError(0, 'Failed to load model architecture documentation.')
    }
  },
}

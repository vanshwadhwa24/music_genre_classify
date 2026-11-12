import React, { useState, useRef } from 'react'
import {
  UploadCloud,
  FileAudio,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ArrowRight,
  RotateCcw,
  Sliders,
  Sparkles,
  Music,
} from 'lucide-react'

import { apiService, ApiError } from '../services/api'
import type { AnalysisResponse } from '../types/api'
import { AudioPlayer } from '../components/AudioPlayer'
import { ScoreBar } from '../components/ScoreBar'
import { SpectrogramView } from '../components/SpectrogramView'
import { StatusBadge } from '../components/StatusBadge'
import { SampleTracks, type SampleTrackItem } from '../components/SampleTracks'
import { NeonLogo } from '../components/NeonLogo'
import { MarqueeBanner } from '../components/MarqueeBanner'

interface DiscoverPageProps {
  isBackendHealthy: boolean | null
}

export const DiscoverPage: React.FC<DiscoverPageProps> = ({ isBackendHealthy }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState<boolean>(false)
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [showAllGenres, setShowAllGenres] = useState<boolean>(false)
  const [analysisStepText, setAnalysisStepText] = useState<string>('Processing audio...')

  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const validateAndSelectFile = (file: File) => {
    setErrorMessage(null)

    // Size limit: 30MB
    if (file.size > 30 * 1024 * 1024) {
      setErrorMessage(
        `File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Maximum supported size is 30 MB.`
      )
      return
    }

    // Supported formats
    const supportedExtensions = ['.wav', '.mp3', '.ogg', '.m4a', '.flac', '.au']
    const hasValidExt = supportedExtensions.some((ext) => file.name.toLowerCase().endsWith(ext))

    if (!hasValidExt && !file.type.startsWith('audio/')) {
      setErrorMessage('Unsupported file format. Please upload a WAV, MP3, OGG, M4A, or FLAC audio file.')
      return
    }

    setSelectedFile(file)
    setAnalysisResult(null)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSelectFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSelectFile(e.target.files[0])
    }
  }

  const handleSampleSelected = async (sample: SampleTrackItem) => {
    setErrorMessage(null)
    setIsAnalyzing(true)
    setAnalysisStepText(`Fetching ${sample.name}...`)

    try {
      const response = await fetch(sample.url)
      if (!response.ok) throw new Error('Failed to load sample audio from server.')
      const blob = await response.blob()
      const sampleFile = new File([blob], sample.filename, { type: 'audio/wav' })

      setSelectedFile(sampleFile)
      setAnalysisStepText('Extracting Mel-Spectrogram & Classifying...')
      const result = await apiService.analyzeTrack(sampleFile)
      setAnalysisResult(result)
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.detail)
      } else {
        setErrorMessage((err as Error).message || 'Analysis failed.')
      }
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleStartAnalysis = async () => {
    if (!selectedFile) return
    setIsAnalyzing(true)
    setErrorMessage(null)
    setAnalysisStepText('Extracting 128 Mel-frequency bands & running CNN...')

    try {
      const result = await apiService.analyzeTrack(selectedFile)
      setAnalysisResult(result)
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.detail)
      } else {
        setErrorMessage('Failed to analyze audio track. Make sure the backend server is reachable.')
      }
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleReset = () => {
    setSelectedFile(null)
    setAnalysisResult(null)
    setErrorMessage(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="w-full">
      {/* 1. Playful Editorial Hero Section (Neon Radio style) */}
      {!analysisResult && (
        <section className="bg-[#FFB347] border-b-2 border-[#FF3CAC] pt-10 pb-8 px-4 sm:px-6 relative overflow-hidden">
          <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-3 text-center md:text-left max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal-sm text-xs font-bold text-[#FFE9FF]">
                <Sparkles className="w-3.5 h-3.5 fill-[#FFB347]" />
                <span>GTZAN CONVOLUTIONAL AUDIO CLASSIFIER</span>
              </div>

              <h1 className="text-6xl sm:text-7xl lg:text-8xl font-display tracking-tight text-[#FFE9FF] leading-none uppercase">
                NEON RADIO
              </h1>

              <p className="text-base sm:text-lg font-bold text-[#FFE9FF] leading-snug">
                Tell your tunes what you&apos;re jamming on. Drop any audio track to unpack its Mel-frequency spectral identity across 10 musical genres.
              </p>
            </div>

            {/* Mascot in Hero */}
            <div className="shrink-0 flex items-center justify-center">
              <div className="relative">
                <NeonLogo size={180} variant="jamming" className="hover:scale-105 transition-transform" />
                <span className="absolute -top-2 -right-4 font-display text-sm bg-[#FF3CAC] text-[#1A0536] px-3 py-1 rounded-full border-2 border-[#FF3CAC] shadow-brutal-sm rotate-6">
                  PLAY IT LOUD!
                </span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* 2. Ticker Marquee Strip */}
      <MarqueeBanner />

      {/* 3. Main Workspace Area */}
      <div className="max-w-5xl mx-auto px-4 py-10 sm:py-14">
        {/* Backend offline warning banner */}
        {isBackendHealthy === false && (
          <div className="mb-8 p-4 rounded-2xl bg-[#1A0536] border-2 border-[#FF6B8A] shadow-brutal flex items-start gap-3.5 text-sm text-[#FFE9FF]">
            <AlertCircle className="w-6 h-6 shrink-0 text-[#FF6B8A] mt-0.5" />
            <div>
              <p className="font-bold text-base text-[#FF6B8A]">FastAPI Backend Unreachable</p>
              <p className="text-xs text-[#C9A8E0] mt-0.5 font-medium leading-relaxed">
                The Python server is offline at <code>/api</code>. File upload analysis and live listening require the FastAPI backend to run.
              </p>
            </div>
          </div>
        )}

        {/* Screen A: Upload Workspace */}
        {!analysisResult ? (
          <div className="space-y-10">
            {/* Upload Box */}
            <div className="bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal-lg rounded-3xl p-6 sm:p-10">
              <div className="text-center max-w-xl mx-auto mb-8 space-y-2">
                <h2 className="text-2xl sm:text-3xl font-display uppercase tracking-tight text-[#FFE9FF]">
                  DROP YOUR TRACK IN THE CRATE
                </h2>
                <p className="text-xs sm:text-sm text-[#C9A8E0] font-medium leading-relaxed">
                  Support for WAV, MP3, OGG, M4A, FLAC up to 30 MB. Evaluates the 30-second GTZAN spectral window.
                </p>
              </div>

              {/* Drag Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !isAnalyzing && fileInputRef.current?.click()}
                className={`relative rounded-2xl border-3 border-dashed p-8 sm:p-12 text-center transition-all cursor-pointer ${
                  isDragging
                    ? 'border-[#FF3CAC] bg-[#FFB347]/40 scale-[1.01]'
                    : selectedFile
                    ? 'border-[#FF3CAC] bg-[#1A0536]'
                    : 'border-[#FF3CAC] bg-[#2A0A4A] hover:bg-[#1A0536]'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*,.wav,.mp3,.ogg,.m4a,.flac"
                  onChange={handleFileChange}
                  className="hidden"
                  aria-label="Upload audio track"
                />

                {isAnalyzing ? (
                  <div className="flex flex-col items-center justify-center py-6 space-y-4">
                    <div className="w-16 h-16 rounded-2xl bg-[#FFB347] border-2 border-[#FF3CAC] shadow-brutal flex items-center justify-center animate-spin">
                      <Loader2 className="w-8 h-8 text-[#FFE9FF]" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-lg font-bold text-[#FFE9FF]">{analysisStepText}</p>
                      <p className="text-xs text-[#C9A8E0] font-mono font-bold">
                        Computing 128 Mel bands · 22,050 Hz resampling
                      </p>
                    </div>
                  </div>
                ) : selectedFile ? (
                  <div className="flex flex-col items-center justify-center space-y-3">
                    <div className="w-14 h-14 rounded-2xl bg-[#FF3CAC] border-2 border-[#FF3CAC] shadow-brutal flex items-center justify-center text-[#1A0536]">
                      <FileAudio className="w-7 h-7" />
                    </div>
                    <div>
                      <p className="text-lg font-bold text-[#FFE9FF] truncate max-w-md">{selectedFile.name}</p>
                      <p className="text-xs font-mono font-bold text-[#C9A8E0] mt-0.5">
                        {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · Click or drag to change
                      </p>
                    </div>
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#FFB347] text-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm">
                      <CheckCircle2 className="w-3.5 h-3.5" /> READY FOR CLASSIFICATION
                    </span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center space-y-4">
                    <div className="w-16 h-16 rounded-2xl bg-[#3DFFD0] border-2 border-[#FF3CAC] shadow-brutal flex items-center justify-center text-[#1A0536]">
                      <UploadCloud className="w-8 h-8" />
                    </div>
                    <div className="space-y-1.5">
                      <p className="text-base sm:text-lg font-bold text-[#FFE9FF]">
                        Drop your audio file here, or{' '}
                        <span className="underline underline-offset-4 text-[#1A0536] bg-[#FFB347] px-2 py-0.5 rounded border border-[#FF3CAC]">
                          browse
                        </span>
                      </p>
                      <p className="text-xs text-[#C9A8E0] font-medium">
                        Standard GTZAN 10-genre audio recognition pipeline
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Error Message */}
              {errorMessage && (
                <div className="mt-6 p-4 rounded-xl bg-[#1A0536] border-2 border-[#FF6B8A] shadow-brutal-sm flex items-center gap-3 text-sm font-bold text-[#FF6B8A]">
                  <AlertCircle className="w-5 h-5 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Action Bar */}
              {selectedFile && !isAnalyzing && (
                <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm">
                  <div className="flex items-center gap-3">
                    <Music className="w-5 h-5 text-[#FFE9FF]" />
                    <span className="text-sm font-bold text-[#FFE9FF] truncate max-w-[240px] sm:max-w-xs">
                      {selectedFile.name}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 w-full sm:w-auto">
                    <button
                      onClick={handleReset}
                      className="px-4 py-2.5 rounded-xl text-xs font-bold text-[#FFE9FF] bg-[#2A0A4A] hover:bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal-sm transition-all active:translate-x-0.5 active:translate-y-0.5"
                    >
                      CLEAR
                    </button>
                    <button
                      onClick={handleStartAnalysis}
                      className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-[#FF3CAC] hover:bg-[#FFB347] text-[#1A0536] text-sm font-display tracking-wide border-2 border-[#FF3CAC] shadow-brutal transition-all brutal-btn"
                    >
                      <span>CLASSIFY GENRE</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Quick Demonstration Crate */}
            <SampleTracks onSelectSample={handleSampleSelected} disabled={isAnalyzing} />
          </div>
        ) : (
          /* Screen B: Results Mode (Playful Editorial celebration) */
          <div className="space-y-10 animate-fadeIn">
            {/* Results Title Banner */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-[#FFB347] border-2 border-[#FF3CAC] shadow-brutal rounded-2xl p-6">
              <div>
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#FFE9FF]">
                  ★ INFERENCE COMPLETE ★
                </span>
                <h2 className="text-3xl sm:text-4xl font-display tracking-tight text-[#FFE9FF] mt-0.5">
                  THEY LOVE IT! MUSICAL IDENTITY REPORT
                </h2>
              </div>
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#2A0A4A] hover:bg-[#FF3CAC] text-xs font-bold text-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm transition-all brutal-btn"
              >
                <RotateCcw className="w-4 h-4" />
                <span>JAM ANOTHER TRACK</span>
              </button>
            </div>

            {/* Audio Tape Player */}
            {selectedFile && (
              <AudioPlayer src={selectedFile} title={analysisResult.track.filename} />
            )}

            {/* Giant Leading Genre Editorial Banner */}
            <div className="p-8 sm:p-12 rounded-3xl bg-[#2A0A4A] border-3 border-[#FF3CAC] shadow-brutal-lg relative overflow-hidden">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 mb-6">
                <div>
                  <span className="text-xs font-mono font-bold uppercase tracking-widest text-[#1A0536] bg-[#FFB347] px-3 py-1 rounded-full border border-[#FF3CAC] shadow-brutal-sm inline-block mb-3">
                    LEADING PREDICTED GENRE
                  </span>
                  <h1 className="text-6xl sm:text-7xl lg:text-8xl font-display text-[#FFE9FF] tracking-tight leading-none uppercase">
                    {analysisResult.prediction.leading_display_name}
                  </h1>
                </div>

                <div className="self-start sm:self-center">
                  <StatusBadge
                    status={analysisResult.prediction.model_status}
                    isMock={analysisResult.prediction.is_mock}
                    isCalibrated={analysisResult.prediction.is_calibrated}
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#1A0536] border-2 border-[#FF3CAC] text-xs text-[#FFE9FF] font-medium leading-relaxed">
                Primary model activation: <strong className="font-mono font-bold text-sm">{analysisResult.prediction.top_three[0].percentage.toFixed(1)}%</strong> ({analysisResult.prediction.top_three[0].score.toFixed(4)} softmax score).
                {!analysisResult.prediction.is_calibrated && (
                  <span className="ml-1 text-[#C9A8E0]">
                    Raw uncalibrated neural activations across the 10 GTZAN categories.
                    The bundled demo clips are short (12s) synthesized snippets outside the model's 30-second GTZAN
                    training distribution - treat their scores as a pipeline demo, not a correctness claim.
                    Measured held-out GTZAN test accuracy: 49.5% (see ml/reports/evaluation_report.md).
                  </span>
                )}
              </div>
            </div>

            {/* Top-3 and Full Genre Distribution */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-display uppercase tracking-tight text-[#FFE9FF]">
                  RANKED GENRE SCORES
                </h3>
                <button
                  onClick={() => setShowAllGenres(!showAllGenres)}
                  className="text-xs font-bold text-[#1A0536] bg-[#2A0A4A] hover:bg-[#FFB347] px-3 py-1.5 rounded-lg border-2 border-[#FF3CAC] shadow-brutal-sm transition-all"
                >
                  {showAllGenres ? 'SHOW TOP 3 ONLY' : 'EXPAND ALL 10 GENRES'}
                </button>
              </div>

              <div className="space-y-3">
                {(showAllGenres
                  ? analysisResult.prediction.all_scores
                  : analysisResult.prediction.top_three
                ).map((scoreItem, idx) => (
                  <ScoreBar
                    key={scoreItem.genre}
                    scoreItem={scoreItem}
                    rank={idx + 1}
                    isLeading={idx === 0}
                  />
                ))}
              </div>
            </div>

            {/* Mel-Spectrogram Visualizer */}
            <div className="space-y-3">
              <h3 className="text-xl font-display uppercase tracking-tight text-[#FFE9FF]">
                TIME-FREQUENCY SOUNDPRINT
              </h3>
              <SpectrogramView
                spectrogram={analysisResult.spectrogram}
                title={analysisResult.track.filename}
              />
            </div>

            {/* Technical Metadata Panel */}
            <div className="p-6 rounded-2xl bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal space-y-4">
              <div className="flex items-center gap-2 pb-2 border-b-2 border-[#FF3CAC]/20">
                <Sliders className="w-4 h-4 text-[#FFE9FF]" />
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[#FFE9FF]">
                  TECHNICAL AUDIO & INFERENCE METADATA
                </h4>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
                <div className="p-3.5 rounded-xl bg-[#FFB347] border-2 border-[#FF3CAC]">
                  <span className="text-[#FFE9FF]/70 font-bold block mb-1">Target Sampling</span>
                  <span className="text-sm font-bold text-[#FFE9FF]">
                    {analysisResult.track.sample_rate.toLocaleString()} Hz
                  </span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#FF3CAC] border-2 border-[#FF3CAC]">
                  <span className="text-[#FFE9FF]/70 font-bold block mb-1">Analyzed Duration</span>
                  <span className="text-sm font-bold text-[#FFE9FF]">
                    {analysisResult.track.duration_seconds.toFixed(1)}s
                  </span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#3DFFD0] border-2 border-[#FF3CAC]">
                  <span className="text-[#FFE9FF]/70 font-bold block mb-1">Inference Latency</span>
                  <span className="text-sm font-bold text-[#FFE9FF]">
                    {analysisResult.processing_time_ms} ms
                  </span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#1A0536] border-2 border-[#FF3CAC]">
                  <span className="text-[#FFE9FF]/70 font-bold block mb-1">Payload Size</span>
                  <span className="text-sm font-bold text-[#FFE9FF]">
                    {(analysisResult.track.file_size_bytes / 1024).toFixed(1)} KB
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

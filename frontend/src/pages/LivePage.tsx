import React, { useState, useEffect, useRef } from 'react'
import { Mic, Square, AlertCircle, ShieldAlert } from 'lucide-react'

import { AudioStreamer } from '../utils/audioStreamer'
import { apiService, ApiError } from '../services/api'
import type { LivePredictionResponse } from '../types/api'
import { LiveVisualizerCanvas } from '../components/LiveVisualizerCanvas'
import { ScoreBar } from '../components/ScoreBar'
import { StatusBadge } from '../components/StatusBadge'
import { MarqueeBanner } from '../components/MarqueeBanner'

interface LivePageProps {
  isBackendHealthy: boolean | null
}

export const LivePage: React.FC<LivePageProps> = ({ isBackendHealthy }) => {
  const [isListening, setIsListening] = useState<boolean>(false)
  const [statusMessage, setStatusMessage] = useState<string>('Ready to listen')
  const [permissionError, setPermissionError] = useState<string | null>(null)
  const [livePrediction, setLivePrediction] = useState<LivePredictionResponse | null>(null)
  const [sliceCount, setSliceCount] = useState<number>(0)
  const [isInferring, setIsInferring] = useState<boolean>(false)

  const streamerRef = useRef<AudioStreamer | null>(null)
  const firstSliceSent = useRef<boolean>(false)

  // Cleanup on unmount: always release microphone and AudioContext
  useEffect(() => {
    return () => {
      if (streamerRef.current) {
        streamerRef.current.stop()
        streamerRef.current = null
      }
    }
  }, [])

  const handleStartListening = async () => {
    setPermissionError(null)
    setStatusMessage('Requesting microphone access...')

    firstSliceSent.current = false
    const streamer = new AudioStreamer({
      onAudioChunk: async (blob: Blob) => {
        setSliceCount((prev) => prev + 1)
        setIsInferring(true)
        setStatusMessage('Evaluating audio window...')

        try {
          const isFirst = !firstSliceSent.current
          firstSliceSent.current = true
          const res = await apiService.predictLive(blob, isFirst)
          setLivePrediction(res)
          setStatusMessage(`Live stream active · Slice #${sliceCount + 1}`)
        } catch (err: unknown) {
          if (err instanceof ApiError) {
            setStatusMessage(`Inference failed: ${err.detail}`)
          } else {
            setStatusMessage('Backend offline — waiting for reconnection...')
          }
        } finally {
          setIsInferring(false)
        }
      },
      onError: (errMsg: string) => {
        setPermissionError(errMsg)
        setIsListening(false)
        setStatusMessage('Error encountered')
      },
      onPermissionDenied: () => {
        setPermissionError(
          'Microphone permission was denied. Please allow microphone access in your browser address bar and try again.'
        )
        setIsListening(false)
        setStatusMessage('Permission denied')
      },
    })

    streamerRef.current = streamer
    const started = await streamer.start()

    if (started) {
      setIsListening(true)
      setStatusMessage('Listening to acoustic environment · Buffering 2.5s slice...')
      setSliceCount(0)
    } else {
      setIsListening(false)
    }
  }

  const handleStopListening = () => {
    if (streamerRef.current) {
      streamerRef.current.stop()
      streamerRef.current = null
    }
    setIsListening(false)
    setStatusMessage('Listening stopped')
  }

  return (
    <div className="w-full">
      {/* Playful Ticker Banner */}
      <MarqueeBanner
        text="★ LIVE ACOUSTIC RADAR ★ REAL-TIME MICROPHONE LISTENING ★ ROLLING 2.5S AUDIO WINDOWS ★"
        bg="bg-[#14032A]"
      />

      <div className="max-w-4xl mx-auto px-4 py-8 sm:py-12 flex flex-col justify-between min-h-[calc(100vh-12rem)] space-y-8">
        {/* Top Status & Disclaimers */}
        <div className="flex flex-col items-center gap-3.5 text-center">
          <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal-sm text-xs font-mono font-bold">
            <span
              className={`w-3 h-3 rounded-full border border-[#FF3CAC] ${
                isListening
                  ? 'bg-[#3DFFD0] shadow-[0_0_10px_#3DFFD0] animate-pulse'
                  : 'bg-[#FFB347]'
              }`}
            />
            <span className="text-[#FFE9FF]">{statusMessage.toUpperCase()}</span>
            {isInferring && (
              <span className="text-[#1A0536] bg-[#FF3CAC] px-2 py-0.5 rounded border border-[#FF3CAC] animate-pulse">
                INFERRING...
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 text-xs font-bold text-[#C9A8E0]">
            <StatusBadge
              status={livePrediction?.model_status || 'DEVELOPMENT_BASELINE'}
              isMock={livePrediction?.is_mock || false}
              compact
            />
            <span>· Rolling 2.5s window temporal smoothing</span>
          </div>

          {/* Backend Warning */}
          {isBackendHealthy === false && (
            <div className="p-3.5 rounded-xl bg-[#1A0536] border-2 border-[#FF6B8A] shadow-brutal-sm text-xs font-bold text-[#FF6B8A] flex items-center gap-2 max-w-lg">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>
                FastAPI backend unreachable. The vinyl visualizer responds to mic locally, but predictions require the server.
              </span>
            </div>
          )}

          {/* Permission Denied Error */}
          {permissionError && (
            <div className="p-4 rounded-xl bg-[#1A0536] border-2 border-[#FF6B8A] shadow-brutal text-xs text-[#FFE9FF] flex items-start gap-3 max-w-md text-left">
              <ShieldAlert className="w-5 h-5 shrink-0 text-[#FF6B8A] mt-0.5" />
              <div>
                <p className="font-bold text-sm text-[#FF6B8A] mb-0.5">Microphone Permission Required</p>
                <p className="text-[#C9A8E0] leading-relaxed font-medium">{permissionError}</p>
              </div>
            </div>
          )}
        </div>

        {/* Center: The Turntable Circular Sound Visualizer */}
        <div className="my-auto py-2 flex flex-col items-center justify-center">
          <LiveVisualizerCanvas
            streamer={streamerRef.current}
            isActive={isListening}
          />

          {/* Leading Genre Display */}
          <div className="mt-6 text-center">
            <span className="text-xs font-mono font-bold uppercase tracking-widest text-[#1A0536] bg-[#FFB347] px-3 py-1 rounded-full border border-[#FF3CAC] shadow-brutal-sm inline-block mb-2">
              {isListening
                ? livePrediction
                  ? 'DETECTED ACOUSTIC GENRE'
                  : 'BUFFERING AUDIO SLICE...'
                : 'TURNTABLE STANDBY'}
            </span>
            <h2 className="text-5xl sm:text-7xl font-display tracking-tight text-[#FFE9FF] uppercase leading-none">
              {livePrediction
                ? livePrediction.leading_display_name
                : isListening
                ? 'LISTENING...'
                : 'IDLE'}
            </h2>
          </div>
        </div>

        {/* Bottom Ranked Scores & Big Tactile Controls */}
        <div className="space-y-6 max-w-lg mx-auto w-full">
          {livePrediction ? (
            <div className="space-y-2.5">
              {livePrediction.top_three.map((item, idx) => (
                <ScoreBar
                  key={item.genre}
                  scoreItem={item}
                  rank={idx + 1}
                  isLeading={idx === 0}
                />
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-2xl bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal-sm text-center text-xs font-mono font-bold text-[#C9A8E0]">
              {isListening
                ? 'Analyzing ambient harmonics... genre activations will appear after the first 2.5s slice.'
                : 'Click START LISTENING to engage the microphone stream and real-time CNN inference.'}
            </div>
          )}

          {/* Tactile Start / Stop Button */}
          <div className="flex justify-center pb-2">
            {!isListening ? (
              <button
                onClick={handleStartListening}
                className="flex items-center gap-3 px-9 py-4 rounded-2xl bg-[#FF3CAC] hover:bg-[#FFB347] text-[#1A0536] text-base font-display tracking-wide border-2 border-[#FF3CAC] shadow-brutal transition-all brutal-btn"
              >
                <Mic className="w-5 h-5 fill-current" />
                <span>START LISTENING</span>
              </button>
            ) : (
              <button
                onClick={handleStopListening}
                className="flex items-center gap-3 px-9 py-4 rounded-2xl bg-[#1A0536] hover:bg-[#FF6B8A] hover:text-white text-[#FFE9FF] text-base font-display tracking-wide border-2 border-[#FF3CAC] shadow-brutal transition-all brutal-btn"
              >
                <Square className="w-5 h-5 fill-current" />
                <span>STOP LISTENING</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

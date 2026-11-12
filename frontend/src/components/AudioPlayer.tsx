import React, { useState, useRef, useEffect } from 'react'
import { Play, Pause, Volume2, VolumeX, RotateCcw, Disc3 } from 'lucide-react'

interface AudioPlayerProps {
  src: string | File
  title?: string
  autoPlay?: boolean
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ src, title, autoPlay = false }) => {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const [currentTime, setCurrentTime] = useState<number>(0)
  const [duration, setDuration] = useState<number>(0)
  const [volume, setVolume] = useState<number>(0.85)
  const [isMuted, setIsMuted] = useState<boolean>(false)
  const [audioUrl, setAudioUrl] = useState<string>('')

  useEffect(() => {
    let url = ''
    if (typeof src === 'string') {
      url = src
    } else if (src instanceof File) {
      url = URL.createObjectURL(src)
    }
    setAudioUrl(url)

    return () => {
      if (src instanceof File && url) {
        URL.revokeObjectURL(url)
      }
    }
  }, [src])

  const togglePlay = () => {
    if (!audioRef.current) return
    if (isPlaying) {
      audioRef.current.pause()
    } else {
      audioRef.current.play().catch((err) => console.warn('Playback error:', err))
    }
  }

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime)
    }
  }

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration || 0)
      if (autoPlay) {
        audioRef.current.play().catch(() => {})
      }
    }
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value)
    setCurrentTime(time)
    if (audioRef.current) {
      audioRef.current.currentTime = time
    }
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const vol = parseFloat(e.target.value)
    setVolume(vol)
    if (audioRef.current) {
      audioRef.current.volume = vol
      setIsMuted(vol === 0)
    }
  }

  const toggleMute = () => {
    if (!audioRef.current) return
    if (isMuted) {
      audioRef.current.volume = volume || 0.8
      setIsMuted(false)
    } else {
      audioRef.current.volume = 0
      setIsMuted(true)
    }
  }

  const handleRestart = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0
      audioRef.current.play().catch(() => {})
    }
  }

  const formatTime = (secs: number) => {
    if (isNaN(secs) || secs < 0) return '0:00'
    const minutes = Math.floor(secs / 60)
    const seconds = Math.floor(secs % 60)
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`
  }

  return (
    <div className="bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal rounded-2xl p-5">
      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => setIsPlaying(false)}
      />

      {/* Player Header */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-[#FF3CAC]/20">
        <div className="flex items-center gap-2">
          <Disc3 className={`w-4 h-4 text-[#FFE9FF] ${isPlaying ? 'animate-spin' : ''}`} />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#FFE9FF]">
            TAPE PLAYBACK DECK
          </span>
        </div>
        {title && (
          <span className="text-xs font-bold text-[#1A0536] bg-[#FFB347] px-2.5 py-0.5 rounded-full border border-[#FF3CAC] truncate max-w-[240px]">
            {title}
          </span>
        )}
      </div>

      <div className="flex flex-col gap-3.5">
        {/* Scrubber slider */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono font-bold text-[#FFE9FF] w-10 text-right">
            {formatTime(currentTime)}
          </span>
          <div className="flex-1 relative flex items-center">
            <input
              type="range"
              min={0}
              max={duration || 100}
              step={0.1}
              value={currentTime}
              onChange={handleSeek}
              aria-label="Audio playback seeker"
              className="w-full h-2.5 bg-[#1A0536] border-2 border-[#FF3CAC] rounded-lg appearance-none cursor-pointer accent-[#FF3CAC] focus:outline-none"
            />
          </div>
          <span className="text-xs font-mono font-bold text-[#FFE9FF] w-10">
            {formatTime(duration)}
          </span>
        </div>

        {/* Controls row */}
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="w-11 h-11 rounded-xl bg-[#FF3CAC] hover:bg-[#FFB347] text-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm flex items-center justify-center transition-all active:translate-x-0.5 active:translate-y-0.5"
              aria-label={isPlaying ? 'Pause track' : 'Play track'}
            >
              {isPlaying ? (
                <Pause className="w-5 h-5 fill-current" />
              ) : (
                <Play className="w-5 h-5 fill-current ml-0.5" />
              )}
            </button>

            <button
              onClick={handleRestart}
              className="w-9 h-9 rounded-xl bg-[#1A0536] hover:bg-[#3DFFD0] text-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm flex items-center justify-center transition-all active:translate-x-0.5 active:translate-y-0.5"
              title="Restart from beginning"
              aria-label="Restart audio track"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-2 bg-[#1A0536] border-2 border-[#FF3CAC] px-3 py-1.5 rounded-xl">
            <button
              onClick={toggleMute}
              className="text-[#FFE9FF] hover:text-[#FF6B8A] transition-colors"
              aria-label={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? <VolumeX className="w-4 h-4 text-[#FF6B8A]" /> : <Volume2 className="w-4 h-4" />}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              aria-label="Volume level"
              className="w-16 h-1.5 bg-[#2A0A4A] border border-[#FF3CAC] rounded appearance-none cursor-pointer accent-[#FF3CAC]"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

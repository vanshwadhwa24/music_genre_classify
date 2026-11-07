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
    <div className="bg-[#FFFDF7] border-2 border-[#4B2B23] shadow-brutal rounded-2xl p-5">
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
      <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-[#4B2B23]/20">
        <div className="flex items-center gap-2">
          <Disc3 className={`w-4 h-4 text-[#4B2B23] ${isPlaying ? 'animate-spin' : ''}`} />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#4B2B23]">
            TAPE PLAYBACK DECK
          </span>
        </div>
        {title && (
          <span className="text-xs font-bold text-[#4B2B23] bg-[#FFDF43] px-2.5 py-0.5 rounded-full border border-[#4B2B23] truncate max-w-[240px]">
            {title}
          </span>
        )}
      </div>

      <div className="flex flex-col gap-3.5">
        {/* Scrubber slider */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono font-bold text-[#4B2B23] w-10 text-right">
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
              className="w-full h-2.5 bg-[#FFF9E9] border-2 border-[#4B2B23] rounded-lg appearance-none cursor-pointer accent-[#4B2B23] focus:outline-none"
            />
          </div>
          <span className="text-xs font-mono font-bold text-[#4B2B23] w-10">
            {formatTime(duration)}
          </span>
        </div>

        {/* Controls row */}
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="w-11 h-11 rounded-xl bg-[#F49ACB] hover:bg-[#FFDF43] text-[#4B2B23] border-2 border-[#4B2B23] shadow-brutal-sm flex items-center justify-center transition-all active:translate-x-0.5 active:translate-y-0.5"
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
              className="w-9 h-9 rounded-xl bg-[#FFF9E9] hover:bg-[#8CA4E8] text-[#4B2B23] border-2 border-[#4B2B23] shadow-brutal-sm flex items-center justify-center transition-all active:translate-x-0.5 active:translate-y-0.5"
              title="Restart from beginning"
              aria-label="Restart audio track"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-2 bg-[#FFF9E9] border-2 border-[#4B2B23] px-3 py-1.5 rounded-xl">
            <button
              onClick={toggleMute}
              className="text-[#4B2B23] hover:text-[#E5484D] transition-colors"
              aria-label={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? <VolumeX className="w-4 h-4 text-[#E5484D]" /> : <Volume2 className="w-4 h-4" />}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              aria-label="Volume level"
              className="w-16 h-1.5 bg-[#FFFDF7] border border-[#4B2B23] rounded appearance-none cursor-pointer accent-[#4B2B23]"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

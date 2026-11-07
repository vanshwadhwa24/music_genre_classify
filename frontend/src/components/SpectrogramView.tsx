import React, { useState } from 'react'
import { Download, Maximize2, Minimize2, Info, Activity } from 'lucide-react'
import type { SpectrogramInfo } from '../types/api'

interface SpectrogramViewProps {
  spectrogram: SpectrogramInfo
  title?: string
}

export const SpectrogramView: React.FC<SpectrogramViewProps> = ({ spectrogram, title = 'Mel-Spectrogram' }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false)

  const imageSrc = spectrogram.data_uri || spectrogram.url

  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = imageSrc
    link.download = `spectrogram_${Date.now()}.png`
    link.click()
  }

  return (
    <div className="bg-white border-2 border-[#4B2B23] shadow-brutal rounded-2xl overflow-hidden">
      {/* Editorial Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b-2 border-[#4B2B23] bg-[#FFDF43]">
        <div className="flex items-center gap-2.5">
          <Activity className="w-4 h-4 text-[#4B2B23]" />
          <span className="text-sm font-display uppercase tracking-wide text-[#4B2B23]">
            MEL-SPECTROGRAM FREQUENCY MAP
          </span>
          <span className="hidden sm:inline-block text-xs font-bold text-[#4B2B23]/70">
            — {title}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-lg bg-white hover:bg-[#F49ACB] text-[#4B2B23] border-2 border-[#4B2B23] shadow-brutal-sm transition-all active:translate-x-0.5 active:translate-y-0.5"
            title={isExpanded ? 'Minimize view' : 'Expand full view'}
            aria-label={isExpanded ? 'Minimize view' : 'Expand full view'}
          >
            {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={handleDownload}
            className="p-1.5 rounded-lg bg-white hover:bg-[#8CA4E8] text-[#4B2B23] border-2 border-[#4B2B23] shadow-brutal-sm transition-all active:translate-x-0.5 active:translate-y-0.5"
            title="Download spectrogram image"
            aria-label="Download spectrogram image"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Image container */}
      <div
        className={`relative bg-[#4B2B23] p-3 flex items-center justify-center transition-all ${
          isExpanded ? 'min-h-[480px]' : 'min-h-[260px]'
        }`}
      >
        <img
          src={imageSrc}
          alt="Mel-spectrogram visualizing time vs frequency intensity in decibels"
          className="w-full h-auto rounded-xl object-contain max-h-[550px] border-2 border-[#4B2B23]"
          loading="lazy"
        />
      </div>

      {/* Axis metadata footer */}
      <div className="px-5 py-3 bg-[#FFFDF7] border-t-2 border-[#4B2B23] flex flex-wrap items-center justify-between gap-3 text-xs text-[#4B2B23] font-mono">
        <div className="flex items-center gap-4">
          <span className="bg-[#FFF9E9] px-2.5 py-1 rounded-md border border-[#4B2B23]">
            Mel Bands: <strong>{spectrogram.n_mels}</strong>
          </span>
          <span className="bg-[#FFF9E9] px-2.5 py-1 rounded-md border border-[#4B2B23]">
            Hop Length: <strong>{spectrogram.hop_length}</strong>
          </span>
          <span className="bg-[#FFF9E9] px-2.5 py-1 rounded-md border border-[#4B2B23]">
            Frames: <strong>{spectrogram.time_steps}</strong>
          </span>
        </div>
        <div className="flex items-center gap-1.5 font-bold text-[#7A5247]">
          <Info className="w-3.5 h-3.5" />
          <span>X: Time (s) · Y: Frequency (Hz) · Color: Power (dB)</span>
        </div>
      </div>
    </div>
  )
}

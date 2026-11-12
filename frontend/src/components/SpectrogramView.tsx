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
    <div className="bg-[#2A0A4A] border-2 border-[#FF3CAC] shadow-brutal rounded-2xl overflow-hidden">
      {/* Editorial Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b-2 border-[#FF3CAC] bg-[#FFB347]">
        <div className="flex items-center gap-2.5">
          <Activity className="w-4 h-4 text-[#FFE9FF]" />
          <span className="text-sm font-display uppercase tracking-wide text-[#FFE9FF]">
            MEL-SPECTROGRAM FREQUENCY MAP
          </span>
          <span className="hidden sm:inline-block text-xs font-bold text-[#FFE9FF]/70">
            — {title}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-lg bg-[#2A0A4A] hover:bg-[#FF3CAC] text-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm transition-all active:translate-x-0.5 active:translate-y-0.5"
            title={isExpanded ? 'Minimize view' : 'Expand full view'}
            aria-label={isExpanded ? 'Minimize view' : 'Expand full view'}
          >
            {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={handleDownload}
            className="p-1.5 rounded-lg bg-[#2A0A4A] hover:bg-[#3DFFD0] text-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm transition-all active:translate-x-0.5 active:translate-y-0.5"
            title="Download spectrogram image"
            aria-label="Download spectrogram image"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Image container */}
      <div
        className={`relative bg-[#FF3CAC] p-3 flex items-center justify-center transition-all ${
          isExpanded ? 'min-h-[480px]' : 'min-h-[260px]'
        }`}
      >
        <img
          src={imageSrc}
          alt="Mel-spectrogram visualizing time vs frequency intensity in decibels"
          className="w-full h-auto rounded-xl object-contain max-h-[550px] border-2 border-[#FF3CAC]"
          loading="lazy"
        />
      </div>

      {/* Axis metadata footer */}
      <div className="px-5 py-3 bg-[#2A0A4A] border-t-2 border-[#FF3CAC] flex flex-wrap items-center justify-between gap-3 text-xs text-[#FFE9FF] font-mono">
        <div className="flex items-center gap-4">
          <span className="bg-[#1A0536] px-2.5 py-1 rounded-md border border-[#FF3CAC]">
            Mel Bands: <strong>{spectrogram.n_mels}</strong>
          </span>
          <span className="bg-[#1A0536] px-2.5 py-1 rounded-md border border-[#FF3CAC]">
            Hop Length: <strong>{spectrogram.hop_length}</strong>
          </span>
          <span className="bg-[#1A0536] px-2.5 py-1 rounded-md border border-[#FF3CAC]">
            Frames: <strong>{spectrogram.time_steps}</strong>
          </span>
        </div>
        <div className="flex items-center gap-1.5 font-bold text-[#C9A8E0]">
          <Info className="w-3.5 h-3.5" />
          <span>X: Time (s) · Y: Frequency (Hz) · Color: Power (dB)</span>
        </div>
      </div>
    </div>
  )
}

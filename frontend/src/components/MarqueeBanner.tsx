import React from 'react'

interface MarqueeBannerProps {
  text?: string
  bg?: string
}

export const MarqueeBanner: React.FC<MarqueeBannerProps> = ({
  text = 'WHAT ARE YOU JAMMING ON? ★ SOUND, MADE VISIBLE ★ 10 GTZAN GENRES ★ REAL-TIME CNN LISTENING ★ MEL-SPECTROGRAM ANALYSIS ★',
  bg = 'bg-[#FF3CAC]',
}) => {
  return (
    <div className={`w-full overflow-hidden border-y-2 border-[#FF3CAC] ${bg} py-2.5 select-none`}>
      <div className="animate-marquee whitespace-nowrap flex items-center font-display text-lg sm:text-xl text-[#FFE9FF] tracking-wider uppercase">
        <span className="mx-4">{text}</span>
        <span className="mx-4">{text}</span>
        <span className="mx-4">{text}</span>
        <span className="mx-4">{text}</span>
      </div>
    </div>
  )
}

import React from 'react'

interface MarqueeBannerProps {
  text?: string
  bg?: string
}

export const MarqueeBanner: React.FC<MarqueeBannerProps> = ({
  text = 'NEON RADIO ★ 10 GTZAN GENRES ★ MEL-SPECTROGRAM CNN ★ UPLOAD OR LISTEN ★',
  bg = 'bg-[#14032A]',
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

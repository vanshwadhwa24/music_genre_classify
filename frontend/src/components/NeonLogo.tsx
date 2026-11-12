import React, { useId } from 'react'

interface NeonLogoProps {
  size?: number
  variant?: string
  className?: string
}

/** Striped sunset disc. Neutral brand mark; a character mascot can replace it later. */
export const NeonLogo: React.FC<NeonLogoProps> = ({ size = 48, className = '' }) => {
  const id = useId().replace(/:/g, '')
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" className={className} role="img" aria-label="Neon Radio logo">
      <defs>
        <linearGradient id={`${id}-g`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#FFB347" />
          <stop offset="1" stopColor="#FF3CAC" />
        </linearGradient>
        <clipPath id={`${id}-c`}>
          <circle cx="50" cy="50" r="44" />
        </clipPath>
      </defs>
      <circle cx="50" cy="50" r="44" fill={`url(#${id}-g)`} />
      <g clipPath={`url(#${id}-c)`} fill="#1A0536">
        <rect x="0" y="56" width="100" height="3" />
        <rect x="0" y="66" width="100" height="5" />
        <rect x="0" y="77" width="100" height="7" />
        <rect x="0" y="89" width="100" height="9" />
      </g>
    </svg>
  )
}

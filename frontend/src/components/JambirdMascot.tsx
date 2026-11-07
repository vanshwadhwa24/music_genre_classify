import React from 'react'

interface JambirdMascotProps {
  className?: string
  size?: number
  variant?: 'jamming' | 'headphones' | 'dancing' | 'icon'
}

export const JambirdMascot: React.FC<JambirdMascotProps> = ({
  className = '',
  size = 120,
  variant = 'jamming',
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 160 160"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`select-none ${className}`}
      aria-label="Jambird musical mascot"
    >
      {/* Ground shadow */}
      <ellipse cx="80" cy="144" rx="42" ry="7" fill="#4B2B23" fillOpacity="0.25" />

      {/* Feet */}
      <path
        d="M66 128 L60 142 M66 128 L66 143 M66 128 L72 142"
        stroke="#4B2B23"
        strokeWidth="3.5"
        strokeLinecap="round"
      />
      <path
        d="M94 128 L88 142 M94 128 L94 143 M94 128 L100 142"
        stroke="#4B2B23"
        strokeWidth="3.5"
        strokeLinecap="round"
      />

      {/* Body / Head: Plump, charming round bird */}
      <circle
        cx="80"
        cy="88"
        r="44"
        fill="#FFFDF7"
        stroke="#4B2B23"
        strokeWidth="4"
      />

      {/* Tummy highlight (Warm Butter Cream) */}
      <path
        d="M52 92 C54 116 106 116 108 92 C108 122 52 122 52 92 Z"
        fill="#FFDF43"
        fillOpacity="0.4"
      />

      {/* Pink Rosy Cheeks */}
      <ellipse cx="58" cy="94" rx="7" ry="4.5" fill="#F49ACB" />
      <ellipse cx="102" cy="94" rx="7" ry="4.5" fill="#F49ACB" />

      {/* Expressive Eyes */}
      <circle cx="68" cy="80" r="5" fill="#4B2B23" />
      <circle cx="92" cy="80" r="5" fill="#4B2B23" />
      <circle cx="69.5" cy="78.5" r="1.8" fill="#FFFFFF" />
      <circle cx="93.5" cy="78.5" r="1.8" fill="#FFFFFF" />

      {/* Joyful Beak */}
      <path
        d="M74 85 Q80 82 86 85 Q80 96 74 85 Z"
        fill="#FFDF43"
        stroke="#4B2B23"
        strokeWidth="3.5"
        strokeLinejoin="round"
      />

      {/* Left Wing (Waving / Jamming) */}
      {variant === 'jamming' || variant === 'icon' ? (
        <path
          d="M40 88 C32 82 24 74 20 62 C32 64 38 74 44 80"
          fill="#F49ACB"
          stroke="#4B2B23"
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ) : (
        <path
          d="M40 88 C30 94 28 106 34 114 C40 110 42 98 44 88"
          fill="#F49ACB"
          stroke="#4B2B23"
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}

      {/* Right Wing (Conducting / Dancing to the beat) */}
      <path
        d="M120 86 C132 80 142 74 148 62 C136 64 128 72 118 78"
        fill="#F49ACB"
        stroke="#4B2B23"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Headwear: Backwards / Sideways Cap OR Studio Headphones */}
      {variant === 'headphones' ? (
        <g id="headphones">
          {/* Headband arch */}
          <path
            d="M44 80 C44 48 116 48 116 80"
            stroke="#4B2B23"
            strokeWidth="6"
            strokeLinecap="round"
          />
          {/* Earcups in Periwinkle */}
          <rect
            x="36"
            y="72"
            width="12"
            height="22"
            rx="6"
            fill="#8CA4E8"
            stroke="#4B2B23"
            strokeWidth="3.5"
          />
          <rect
            x="112"
            y="72"
            width="12"
            height="22"
            rx="6"
            fill="#8CA4E8"
            stroke="#4B2B23"
            strokeWidth="3.5"
          />
        </g>
      ) : (
        <g id="sideways-cap">
          {/* Cap Dome */}
          <path
            d="M58 56 C62 40 98 40 102 56 Z"
            fill="#8CA4E8"
            stroke="#4B2B23"
            strokeWidth="3.5"
          />
          {/* Cap Visor / Brim turned sideways */}
          <path
            d="M54 55 Q72 50 114 54 Q124 51 128 47 Q116 43 100 48"
            fill="#4B2B23"
            stroke="#4B2B23"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          {/* Cap button */}
          <circle cx="80" cy="44" r="3.5" fill="#FFDF43" stroke="#4B2B23" strokeWidth="2" />
        </g>
      )}

      {/* Floating Musical Notes */}
      <g opacity="0.85">
        <path
          d="M130 38 L138 34 L138 48 M130 42 L130 52"
          stroke="#4B2B23"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <circle cx="127" cy="52" r="3.5" fill="#4B2B23" />
        <circle cx="135" cy="48" r="3.5" fill="#4B2B23" />
        
        {/* Star Sparkle */}
        <path
          d="M32 36 L34 40 L38 42 L34 44 L32 48 L30 44 L26 42 L30 40 Z"
          fill="#FFDF43"
          stroke="#4B2B23"
          strokeWidth="1.5"
        />
      </g>
    </svg>
  )
}

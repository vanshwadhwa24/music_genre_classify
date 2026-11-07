import React from 'react'
import type { GenreScore } from '../types/api'

interface ScoreBarProps {
  scoreItem: GenreScore
  rank: number
  isLeading?: boolean
}

export const ScoreBar: React.FC<ScoreBarProps> = ({ scoreItem, rank, isLeading = false }) => {
  // Color palette per rank inspired by Jambird
  let barColor = 'bg-[#FFF9E9]'
  let rankBadgeColor = 'bg-[#FFF9E9] text-[#4B2B23]'

  if (rank === 1) {
    barColor = 'bg-[#FFDF43]'
    rankBadgeColor = 'bg-[#FFDF43] text-[#4B2B23]'
  } else if (rank === 2) {
    barColor = 'bg-[#F49ACB]'
    rankBadgeColor = 'bg-[#F49ACB] text-[#4B2B23]'
  } else if (rank === 3) {
    barColor = 'bg-[#8CA4E8]'
    rankBadgeColor = 'bg-[#8CA4E8] text-[#4B2B23]'
  }

  return (
    <div
      className={`p-3.5 rounded-xl transition-all duration-200 border-2 border-[#4B2B23] ${
        isLeading
          ? 'bg-[#FFFDF7] shadow-brutal'
          : 'bg-white shadow-brutal-sm hover:translate-x-0.5'
      }`}
    >
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-2.5">
          <span
            className={`text-xs font-mono font-bold px-2 py-0.5 rounded-md border-2 border-[#4B2B23] ${rankBadgeColor}`}
          >
            #{rank}
          </span>
          <span className="text-base font-bold text-[#4B2B23] tracking-tight">
            {scoreItem.display_name}
          </span>
          {isLeading && (
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-[#FFDF43] text-[#4B2B23] border border-[#4B2B23] shadow-brutal-sm">
              ★ TOP GENRE
            </span>
          )}
        </div>

        <div className="flex items-baseline gap-2 font-mono">
          <span className="text-base font-bold text-[#4B2B23]">
            {scoreItem.percentage.toFixed(1)}%
          </span>
          <span className="text-xs text-[#7A5247] font-semibold">
            ({scoreItem.score.toFixed(3)})
          </span>
        </div>
      </div>

      {/* Progress track */}
      <div className="w-full bg-[#FFF9E9] rounded-full h-3 overflow-hidden p-0.5 border-2 border-[#4B2B23]">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out border-r-2 border-[#4B2B23] ${barColor}`}
          style={{ width: `${Math.max(3, Math.min(100, scoreItem.percentage))}%` }}
          role="progressbar"
          aria-valuenow={scoreItem.score}
          aria-valuemin={0}
          aria-valuemax={1}
          aria-label={`${scoreItem.display_name} score: ${scoreItem.percentage.toFixed(1)}%`}
        />
      </div>
    </div>
  )
}

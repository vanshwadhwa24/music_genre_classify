import React from 'react'
import type { GenreScore } from '../types/api'

interface ScoreBarProps {
  scoreItem: GenreScore
  rank: number
  isLeading?: boolean
}

export const ScoreBar: React.FC<ScoreBarProps> = ({ scoreItem, rank, isLeading = false }) => {
  // Color palette per rank inspired by Neon Radio
  let barColor = 'bg-[#1A0536]'
  let rankBadgeColor = 'bg-[#1A0536] text-[#FFE9FF]'

  if (rank === 1) {
    barColor = 'bg-[#FFB347]'
    rankBadgeColor = 'bg-[#FFB347] text-[#1A0536]'
  } else if (rank === 2) {
    barColor = 'bg-[#FF3CAC]'
    rankBadgeColor = 'bg-[#FF3CAC] text-[#1A0536]'
  } else if (rank === 3) {
    barColor = 'bg-[#3DFFD0]'
    rankBadgeColor = 'bg-[#3DFFD0] text-[#1A0536]'
  }

  return (
    <div
      className={`p-3.5 rounded-xl transition-all duration-200 border-2 border-[#FF3CAC] ${
        isLeading
          ? 'bg-[#2A0A4A] shadow-brutal'
          : 'bg-[#2A0A4A] shadow-brutal-sm hover:translate-x-0.5'
      }`}
    >
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-2.5">
          <span
            className={`text-xs font-mono font-bold px-2 py-0.5 rounded-md border-2 border-[#FF3CAC] ${rankBadgeColor}`}
          >
            #{rank}
          </span>
          <span className="text-base font-bold text-[#FFE9FF] tracking-tight">
            {scoreItem.display_name}
          </span>
          {isLeading && (
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-[#FFB347] text-[#1A0536] border border-[#FF3CAC] shadow-brutal-sm">
              ★ TOP GENRE
            </span>
          )}
        </div>

        <div className="flex items-baseline gap-2 font-mono">
          <span className="text-base font-bold text-[#FFE9FF]">
            {scoreItem.percentage.toFixed(1)}%
          </span>
          <span className="text-xs text-[#C9A8E0] font-semibold">
            ({scoreItem.score.toFixed(3)})
          </span>
        </div>
      </div>

      {/* Progress track */}
      <div className="w-full bg-[#1A0536] rounded-full h-3 overflow-hidden p-0.5 border-2 border-[#FF3CAC]">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out border-r-2 border-[#FF3CAC] ${barColor}`}
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

import React from 'react'
import { Sparkles, Cpu, AlertTriangle, AlertCircle } from 'lucide-react'

interface StatusBadgeProps {
  status: string
  isMock?: boolean
  isCalibrated?: boolean
  compact?: boolean
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  isMock = false,
  isCalibrated = false,
  compact = false,
}) => {
  if (status === 'ACTIVE_MODEL' && !isMock) {
    return (
      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#FFB347] text-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm">
        <Sparkles className="w-3.5 h-3.5 text-[#FFE9FF]" />
        <span>TRAINED CNN MODEL</span>
        {!isCalibrated && !compact && (
          <span className="text-[#FFE9FF]/70 font-mono text-[10px] ml-1">(Raw Softmax)</span>
        )}
      </div>
    )
  }

  if (status === 'DEVELOPMENT_BASELINE') {
    return (
      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#3DFFD0] text-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm">
        <Cpu className="w-3.5 h-3.5 text-[#FFE9FF]" />
        <span>BASELINE PYTORCH CNN</span>
        {!compact && (
          <span className="text-[#FFE9FF]/70 font-mono text-[10px] ml-1">· Dev Checkpoint</span>
        )}
      </div>
    )
  }

  if (isMock || status === 'DEVELOPMENT_MOCK') {
    return (
      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#FF3CAC] text-[#1A0536] border-2 border-[#FF3CAC] shadow-brutal-sm">
        <AlertTriangle className="w-3.5 h-3.5 text-[#FFE9FF]" />
        <span>MOCK INFERENCE ADAPTER</span>
      </div>
    )
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#1A0536] text-[#FF6B8A] border-2 border-[#FF6B8A] shadow-brutal-sm">
      <AlertCircle className="w-3.5 h-3.5 text-[#FF6B8A]" />
      <span>MODEL OFFLINE</span>
    </div>
  )
}

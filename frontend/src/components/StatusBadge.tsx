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
      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#FFDF43] text-[#4B2B23] border-2 border-[#4B2B23] shadow-brutal-sm">
        <Sparkles className="w-3.5 h-3.5 text-[#4B2B23]" />
        <span>TRAINED CNN MODEL</span>
        {!isCalibrated && !compact && (
          <span className="text-[#4B2B23]/70 font-mono text-[10px] ml-1">(Raw Softmax)</span>
        )}
      </div>
    )
  }

  if (status === 'DEVELOPMENT_BASELINE') {
    return (
      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#8CA4E8] text-[#4B2B23] border-2 border-[#4B2B23] shadow-brutal-sm">
        <Cpu className="w-3.5 h-3.5 text-[#4B2B23]" />
        <span>BASELINE PYTORCH CNN</span>
        {!compact && (
          <span className="text-[#4B2B23]/70 font-mono text-[10px] ml-1">· Dev Checkpoint</span>
        )}
      </div>
    )
  }

  if (isMock || status === 'DEVELOPMENT_MOCK') {
    return (
      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#F49ACB] text-[#4B2B23] border-2 border-[#4B2B23] shadow-brutal-sm">
        <AlertTriangle className="w-3.5 h-3.5 text-[#4B2B23]" />
        <span>MOCK INFERENCE ADAPTER</span>
      </div>
    )
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#FFF9E9] text-[#E5484D] border-2 border-[#E5484D] shadow-brutal-sm">
      <AlertCircle className="w-3.5 h-3.5 text-[#E5484D]" />
      <span>MODEL OFFLINE</span>
    </div>
  )
}

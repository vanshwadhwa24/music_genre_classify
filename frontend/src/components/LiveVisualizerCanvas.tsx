import React, { useRef, useEffect } from 'react'
import type { AudioStreamer } from '../utils/audioStreamer'

interface LiveVisualizerCanvasProps {
  streamer: AudioStreamer | null
  isActive: boolean
}

export const LiveVisualizerCanvas: React.FC<LiveVisualizerCanvasProps> = ({
  streamer,
  isActive,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const animFrameRef = useRef<number | null>(null)
  const smoothedAmpRef = useRef<number>(0)
  const rotationAngleRef = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const freqData = new Uint8Array(256)
    const timeData = new Uint8Array(256)

    let isRunning = true

    const render = () => {
      if (!isRunning) return

      const dpr = window.devicePixelRatio || 1
      const rect = canvas.getBoundingClientRect()
      const width = rect.width
      const height = rect.height

      if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
        canvas.width = width * dpr
        canvas.height = height * dpr
      }

      ctx.save()
      ctx.scale(dpr, dpr)

      // Background: Warm Cream / Butter Yellow
      ctx.fillStyle = '#FFFDF7'
      ctx.fillRect(0, 0, width, height)

      const centerX = width / 2
      const centerY = height / 2
      const baseRadius = Math.min(width, height) * 0.32

      let currentAmp = 0

      if (isActive && streamer && streamer.isActive()) {
        streamer.getFrequencyData(freqData)
        streamer.getTimeDomainData(timeData)

        let sum = 0
        for (let i = 0; i < freqData.length; i++) {
          sum += freqData[i]
        }
        currentAmp = (sum / freqData.length) / 255.0
      }

      // Smooth amplitude dampening
      smoothedAmpRef.current = smoothedAmpRef.current * 0.85 + currentAmp * 0.15
      const energy = smoothedAmpRef.current

      // Continuous vinyl rotational drift
      rotationAngleRef.current += (0.008 + energy * 0.025)
      const rot = rotationAngleRef.current

      // 1. Outer Turntable Ring / Vinyl Border
      ctx.beginPath()
      ctx.arc(centerX, centerY, baseRadius * 1.38, 0, Math.PI * 2)
      ctx.fillStyle = '#FFDF43'
      ctx.fill()
      ctx.strokeStyle = '#4B2B23'
      ctx.lineWidth = 4
      ctx.stroke()

      // Vinyl Record Body (Warm Cream inner groove)
      ctx.beginPath()
      ctx.arc(centerX, centerY, baseRadius * 1.34, 0, Math.PI * 2)
      ctx.fillStyle = '#FFF9E9'
      ctx.fill()
      ctx.strokeStyle = '#4B2B23'
      ctx.lineWidth = 2
      ctx.stroke()

      // 2. Vinyl Grooves / Frequency Radial Ticks
      const numTicks = 48
      for (let i = 0; i < numTicks; i++) {
        const tickAngle = (Math.PI * 2 / numTicks) * i + rot
        const r1 = baseRadius * 1.22
        const r2 = (i % 4 === 0) ? baseRadius * 1.32 : baseRadius * 1.26
        const x1 = centerX + Math.cos(tickAngle) * r1
        const y1 = centerY + Math.sin(tickAngle) * r1
        const x2 = centerX + Math.cos(tickAngle) * r2
        const y2 = centerY + Math.sin(tickAngle) * r2

        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.lineTo(x2, y2)
        ctx.strokeStyle = (i % 4 === 0) ? '#4B2B23' : '#4B2B23'
        ctx.lineWidth = (i % 4 === 0) ? 2.5 : 1.2
        ctx.stroke()
      }

      // Concentric groove tracks
      const grooveRadii = [baseRadius * 1.15, baseRadius * 0.95, baseRadius * 0.75]
      grooveRadii.forEach((r, idx) => {
        ctx.beginPath()
        ctx.arc(centerX, centerY, r, 0, Math.PI * 2)
        ctx.strokeStyle = '#4B2B23'
        ctx.lineWidth = 1.5
        if (idx % 2 === 1) {
          ctx.setLineDash([4, 6])
        } else {
          ctx.setLineDash([])
        }
        ctx.stroke()
      })
      ctx.setLineDash([])

      // 3. Audio-Reactive Harmonic Waveform Ring (Vibrant Bubblegum Pink)
      const numPoints = 120
      const angleStep = (Math.PI * 2) / numPoints

      ctx.beginPath()
      for (let i = 0; i <= numPoints; i++) {
        const idx = i % numPoints
        const angle = idx * angleStep + rot
        
        let freqVal = 0
        if (isActive && freqData.length > 0) {
          const bin = Math.floor((idx / numPoints) * 64)
          freqVal = (freqData[bin] / 255.0)
        } else {
          freqVal = 0.08 * (Math.sin(rot * 3 + idx * 0.12) * 0.5 + 0.5)
        }

        const radialOffset = freqVal * (baseRadius * 0.40)
        const r = baseRadius + radialOffset
        const x = centerX + Math.cos(angle) * r
        const y = centerY + Math.sin(angle) * r

        if (i === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      }
      ctx.closePath()

      // Fill and outline harmonic wave
      ctx.fillStyle = isActive ? 'rgba(244, 154, 203, 0.55)' : 'rgba(244, 154, 203, 0.35)'
      ctx.fill()
      ctx.strokeStyle = '#4B2B23'
      ctx.lineWidth = 3
      ctx.stroke()

      // 4. Inner Time-Domain Waveform Ring (Periwinkle Blue)
      ctx.beginPath()
      for (let i = 0; i <= numPoints; i++) {
        const idx = i % numPoints
        const angle = idx * angleStep - rot * 0.8
        
        let waveVal = 0
        if (isActive && timeData.length > 0) {
          const sample = timeData[idx % timeData.length]
          waveVal = (sample - 128) / 128.0
        } else {
          waveVal = 0.06 * Math.sin(rot * 4 + idx * 0.15)
        }

        const r = (baseRadius * 0.72) + waveVal * (baseRadius * 0.24)
        const x = centerX + Math.cos(angle) * r
        const y = centerY + Math.sin(angle) * r

        if (i === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      }
      ctx.closePath()
      ctx.fillStyle = isActive ? 'rgba(140, 164, 232, 0.4)' : 'rgba(140, 164, 232, 0.25)'
      ctx.fill()
      ctx.strokeStyle = '#4B2B23'
      ctx.lineWidth = 2.5
      ctx.stroke()

      // 5. Center Vinyl Center Label
      const coreRadius = (baseRadius * 0.38) * (1.0 + energy * 0.15)
      ctx.beginPath()
      ctx.arc(centerX, centerY, coreRadius, 0, Math.PI * 2)
      ctx.fillStyle = '#FFDF43'
      ctx.fill()
      ctx.strokeStyle = '#4B2B23'
      ctx.lineWidth = 3
      ctx.stroke()

      // Spindle hole
      const spindleRadius = coreRadius * 0.22
      ctx.beginPath()
      ctx.arc(centerX, centerY, spindleRadius, 0, Math.PI * 2)
      ctx.fillStyle = '#4B2B23'
      ctx.fill()

      // Center record label text / decorative stars
      ctx.save()
      ctx.translate(centerX, centerY)
      ctx.rotate(rot * 1.5)
      ctx.fillStyle = '#4B2B23'
      ctx.font = 'bold 9px "Space Mono", monospace'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      if (coreRadius > 25) {
        ctx.fillText('★ JAMBIRD ★', 0, -coreRadius * 0.55)
        ctx.fillText('45 RPM', 0, coreRadius * 0.55)
      }
      ctx.restore()

      ctx.restore()
      animFrameRef.current = requestAnimationFrame(render)
    }

    animFrameRef.current = requestAnimationFrame(render)

    return () => {
      isRunning = false
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current)
      }
    }
  }, [isActive, streamer])

  return (
    <div className="relative w-full max-w-[500px] aspect-square mx-auto flex items-center justify-center p-2">
      <div className="w-full h-full rounded-full border-4 border-[#4B2B23] shadow-brutal-lg overflow-hidden bg-[#FFFDF7]">
        <canvas
          ref={canvasRef}
          className="w-full h-full rounded-full cursor-default select-none pointer-events-none"
          aria-label="Sound visualization vinyl waveform displaying real-time microphone audio amplitude"
        />
      </div>
    </div>
  )
}

import { useState } from 'react'
import type { BrainVisualizationPayload } from '../types'

interface BrainViewerProps {
  visualization: BrainVisualizationPayload
  currentTime: number
}

export function BrainViewer({ visualization, currentTime }: BrainViewerProps) {
  const frames = visualization.frames.filter(f => f.image_b64)

  if (frames.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500 text-sm">
        No brain renders available.
      </div>
    )
  }

  // Find closest frame to currentTime
  let closestFrame = frames[0]
  let minDiff = Infinity
  for (const f of frames) {
    const diff = Math.abs(f.timestamp - currentTime)
    if (diff < minDiff) {
      minDiff = diff
      closestFrame = f
    }
  }

  const frame = closestFrame

  function fmt(s: number) {
    const m = Math.floor(s / 60)
    const sec = (s % 60).toFixed(1).padStart(4, '0')
    return `${m}:${sec}`
  }

  return (
    <div className="space-y-3">
      <div className="relative rounded-xl overflow-hidden bg-[#080818]">
        <img
          src={`data:image/png;base64,${frame.image_b64}`}
          alt={`Brain at ${fmt(frame.timestamp)}`}
          className="w-full object-contain max-h-64"
        />
        <div className="absolute top-2 right-2 text-xs font-mono bg-black/60 text-slate-300 px-2 py-0.5 rounded">
          t = {fmt(frame.timestamp)}s
        </div>
      </div>

      <div className="flex justify-between text-xs text-slate-500 font-mono">
        <span>{fmt(frames[0].timestamp)}s</span>
        <span>{frames.length} frames</span>
        <span>{fmt(frames[frames.length - 1].timestamp)}s</span>
      </div>
    </div>
  )
}

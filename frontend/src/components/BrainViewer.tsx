import { useState } from 'react'
import type { BrainVisualizationPayload } from '../types'
import { Brain3D } from './Brain3D'

interface BrainViewerProps {
  visualization: BrainVisualizationPayload
  currentTime: number
}

type ViewMode = 'true' | 'predicted'
type SurfaceMode = 'normal' | 'inflated'
type HemiMode = 'open' | 'close'

/** Small pill-shaped toggle button matching TRIBE v2 demo aesthetic */
function ToggleButton({
  label,
  active,
  onClick,
}: {
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '5px 14px',
        fontSize: '11px',
        fontWeight: 600,
        fontFamily: 'monospace',
        borderRadius: '4px',
        border: active ? '1px solid rgba(255,255,255,0.5)' : '1px solid rgba(255,255,255,0.12)',
        background: active ? 'rgba(255,255,255,0.1)' : 'transparent',
        color: active ? '#fff' : 'rgba(255,255,255,0.4)',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        letterSpacing: '0.02em',
      }}
    >
      {label}
    </button>
  )
}

export function BrainViewer({ visualization, currentTime }: BrainViewerProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('predicted')
  const [surfaceMode, setSurfaceMode] = useState<SurfaceMode>('normal')
  const [hemiMode, setHemiMode] = useState<HemiMode>('close')

  const frames = visualization.frames

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

  // For "True" mode, show a baseline frame (low activation)
  const displayFrame = viewMode === 'true'
    ? { ...frame, max_activation: 0.05, roi_activations: {} }
    : frame

  return (
    <div className="space-y-0">
      {/* 3D Brain Canvas */}
      <Brain3D
        frame={displayFrame}
        surfaceMode={surfaceMode}
        hemiMode={hemiMode}
      />

      {/* TRIBE v2-style control bar */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          padding: '16px 20px',
          background: 'rgba(0,0,0,0.6)',
          borderBottomLeftRadius: '12px',
          borderBottomRightRadius: '12px',
          borderTop: '1px solid rgba(255,255,255,0.04)',
        }}
      >
        {/* Row 1: View mode + Hemi + Surface */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* View Mode: True / Compare / Predicted */}
          <ToggleButton label="True" active={viewMode === 'true'} onClick={() => setViewMode('true')} />
          <ToggleButton label="Predicted" active={viewMode === 'predicted'} onClick={() => setViewMode('predicted')} />

          {/* Spacer */}
          <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.08)', margin: '0 4px' }} />

          {/* Hemisphere: Open / Close */}
          <ToggleButton label="Open" active={hemiMode === 'open'} onClick={() => setHemiMode('open')} />
          <ToggleButton label="Close" active={hemiMode === 'close'} onClick={() => setHemiMode('close')} />

          {/* Spacer */}
          <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.08)', margin: '0 4px' }} />

          {/* Surface: Normal / Inflated */}
          <ToggleButton label="Normal" active={surfaceMode === 'normal'} onClick={() => setSurfaceMode('normal')} />
          <ToggleButton label="Inflated" active={surfaceMode === 'inflated'} onClick={() => setSurfaceMode('inflated')} />
        </div>

        {/* Row 2: Frame info */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '10px',
          fontFamily: 'monospace',
          color: 'rgba(255,255,255,0.25)',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
        }}>
          <span>t = {frame.timestamp.toFixed(1)}s</span>
          <span>{frames.length} frames · fsaverage5</span>
          <span>
            Peak: {(frame.max_activation * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  )
}

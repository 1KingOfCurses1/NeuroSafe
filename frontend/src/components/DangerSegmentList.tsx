import type { DangerSegment, Severity } from '../types'

interface DangerSegmentListProps {
  segments: DangerSegment[]
}

const SEV_COLORS: Record<Severity, string> = {
  low:      'bg-emerald-900/50 text-emerald-300 border-emerald-700',
  medium:   'bg-yellow-900/50 text-yellow-300 border-yellow-700',
  high:     'bg-orange-900/50 text-orange-300 border-orange-700',
  critical: 'bg-red-900/50 text-red-300 border-red-700',
}

function fmt(s: number) {
  const m = Math.floor(s / 60)
  const sec = (s % 60).toFixed(1).padStart(4, '0')
  return `${m}:${sec}`
}

export function DangerSegmentList({ segments }: DangerSegmentListProps) {
  if (segments.length === 0) {
    return (
      <p className="text-center py-8 text-slate-500 text-sm">
        No danger segments detected.
      </p>
    )
  }

  return (
    <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
      {segments.map((seg, i) => (
        <div
          key={i}
          className="flex items-center gap-3 bg-slate-800/60 rounded-lg px-4 py-3 border border-slate-700/40"
        >
          <span className="text-slate-400 text-xs font-mono w-24 shrink-0">
            {fmt(seg.start_time)} → {fmt(seg.end_time)}
          </span>
          <span className="text-slate-300 text-xs font-mono bg-slate-700 rounded px-2 py-0.5 shrink-0">
            {seg.roi}
          </span>
          <span className="text-slate-400 text-xs grow truncate">
            Peak {seg.activation_level.toFixed(2)} at {fmt(seg.peak_time)}
          </span>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded border shrink-0 ${SEV_COLORS[seg.severity]}`}>
            {seg.severity.toUpperCase()}
          </span>
        </div>
      ))}
    </div>
  )
}

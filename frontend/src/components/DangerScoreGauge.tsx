import type { Severity } from '../types'

interface DangerScoreGaugeProps {
  score: number
  severity: Severity
}

const SEVERITY_COLOR: Record<Severity, string> = {
  low:      '#10b981',
  medium:   '#f59e0b',
  high:     '#f97316',
  critical: '#ef4444',
}

const SEVERITY_LABEL: Record<Severity, string> = {
  low:      'LOW RISK',
  medium:   'MODERATE RISK',
  high:     'HIGH RISK',
  critical: 'CRITICAL RISK',
}

export function DangerScoreGauge({ score, severity }: DangerScoreGaugeProps) {
  const color = SEVERITY_COLOR[severity]
  const label = SEVERITY_LABEL[severity]

  const r = 54
  const cx = 64
  const cy = 64
  const circumference = Math.PI * r
  const filled = (score / 100) * circumference
  const trackD = `M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`

  return (
    <div className="flex flex-col items-center gap-3">
      <svg width="128" height="80" viewBox="0 0 128 80">
        <path d={trackD} fill="none" stroke="#1e293b" strokeWidth="10" strokeLinecap="round" />
        <path
          d={trackD}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
          style={{ transition: 'stroke-dasharray 0.8s ease' }}
        />
        <text x={cx} y={cy - 4} textAnchor="middle" fill="white" fontSize="26" fontWeight="700" fontFamily="Inter, sans-serif">
          {score}
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle" fill="#94a3b8" fontSize="10" fontFamily="Inter, sans-serif">
          / 100
        </text>
      </svg>
      <span
        className="text-xs font-bold tracking-widest px-3 py-1 rounded-full"
        style={{ color, backgroundColor: `${color}22` }}
      >
        {label}
      </span>
    </div>
  )
}

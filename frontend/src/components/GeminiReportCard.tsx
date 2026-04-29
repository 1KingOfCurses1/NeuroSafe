import type { GeminiReport } from '../types'

interface GeminiReportCardProps {
  report: GeminiReport
}

export function GeminiReportCard({ report }: GeminiReportCardProps) {
  return (
    <div className="space-y-4">
      <p className="text-slate-200 font-semibold text-base leading-snug">
        {report.headline}
      </p>

      <div>
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
          Findings
        </h4>
        <ul className="space-y-1.5">
          {report.findings.map((f, i) => (
            <li key={i} className="flex gap-2 text-sm text-slate-300">
              <span className="text-blue-400 shrink-0 mt-0.5">›</span>
              <span>{f}</span>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
          Recommended Actions
        </h4>
        <ul className="space-y-1.5">
          {report.recommended_actions.map((a, i) => (
            <li key={i} className="flex gap-2 text-sm text-slate-300">
              <span className="text-emerald-400 shrink-0 mt-0.5">✓</span>
              <span>{a}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

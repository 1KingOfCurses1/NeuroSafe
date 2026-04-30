import type { JobStatus } from '../types'

interface ProgressBarProps {
  progress: number
  status: JobStatus
  message: string
}

const STAGE_LABELS: Partial<Record<JobStatus, string>> = {
  queued: 'Queued',
  processing: 'Processing',
  extracting_metadata: 'Reading video metadata',
  running_model: 'Running TRIBE v2 cortical model',
  scoring_danger: 'Scoring danger segments',
  generating_visualization: 'Rendering 3D brain',
  generating_report: 'Generating clinical report',
  completed: 'Complete',
  failed: 'Failed',
}

export function ProgressBar({ progress, status, message }: ProgressBarProps) {
  const barColor =
    status === 'completed' ? 'bg-clinical-teal shadow-[0_0_10px_rgba(0,169,157,0.5)]' :
    status === 'failed'    ? 'bg-danger-red shadow-[0_0_10px_rgba(255,76,76,0.5)]' :
                             'bg-clinical-teal shadow-[0_0_10px_rgba(0,169,157,0.5)]'

  return (
    <div className="w-full space-y-3">
      <div className="flex justify-between items-center text-sm font-medium">
        <span className={`tracking-wide ${status === 'failed' ? 'text-danger-red' : 'text-soft-white/90'}`}>
          {STAGE_LABELS[status] ?? status}
        </span>
        <span className="text-soft-white/60 font-mono text-xs">{progress}%</span>
      </div>
      
      <div className="h-1.5 w-full bg-deep-navy/30 rounded-full overflow-hidden border border-white/5">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out relative ${barColor}`}
          style={{ width: `${progress}%` }}
        >
          {status !== 'completed' && status !== 'failed' && (
             <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
          )}
        </div>
      </div>

      <div className="h-4">
        {message && (
          <p className="text-xs text-soft-white/40 truncate font-mono tracking-tight animate-pulse-fast">
            {'>'} {message}
          </p>
        )}
      </div>
    </div>
  )
}

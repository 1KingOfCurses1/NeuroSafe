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
    status === 'completed' ? 'bg-emerald-500' :
    status === 'failed'    ? 'bg-red-500' :
                             'bg-blue-500'

  return (
    <div className="w-full space-y-2">
      <div className="flex justify-between items-center text-sm">
        <span className="text-slate-300 font-medium">
          {STAGE_LABELS[status] ?? status}
        </span>
        <span className="text-slate-400">{progress}%</span>
      </div>
      <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${progress}%` }}
        />
      </div>
      {message && (
        <p className="text-xs text-slate-500 truncate">{message}</p>
      )}
    </div>
  )
}

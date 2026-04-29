export type JobStatus =
  | 'queued'
  | 'processing'
  | 'extracting_metadata'
  | 'running_model'
  | 'scoring_danger'
  | 'generating_visualization'
  | 'generating_report'
  | 'completed'
  | 'failed'

export type Severity = 'low' | 'medium' | 'high' | 'critical'

export interface VideoMetadata {
  filename: string
  duration_seconds: number
  fps: number
  resolution: string
}

export interface DangerSegment {
  start_time: number
  end_time: number
  peak_time: number
  roi: string
  activation_level: number
  threshold: number
  severity: Severity
  reason: string
}

export interface AnalysisSummary {
  severity: Severity
  segments_detected: number
  total_danger_duration_seconds: number
}

export interface RoiTimeSeries {
  timestamps: number[]
  V1: number[]
  V2: number[]
  V3: number[]
  V4: number[]
  'MT+': number[]
}

export interface GeminiReport {
  headline: string
  findings: string[]
  recommended_actions: string[]
}

export interface BrainFrame {
  timestamp: number
  roi_activations: Record<string, number>
  max_activation: number
  danger_level: Severity
  image_b64: string | null
}

export interface BrainVisualizationPayload {
  job_id: string
  frames: BrainFrame[]
  color_map: string
  timestamp_unit: string
}

export interface AnalysisResult {
  job_id: string
  status: JobStatus
  video: VideoMetadata
  danger_score: number
  summary: AnalysisSummary
  danger_segments: DangerSegment[]
  roi_timeseries: RoiTimeSeries
  gemini_report: GeminiReport
  brain_visualization: BrainVisualizationPayload | null
}

export interface ProgressEvent {
  job_id: string
  status: JobStatus
  progress: number
  message: string
  timestamp: string
}

export interface JobCreateResponse {
  job_id: string
  status: JobStatus
  message: string
}

export interface JobStatusResponse {
  job_id: string
  status: JobStatus
  progress: number
  message: string
  result: AnalysisResult | null
  error: string | null
}

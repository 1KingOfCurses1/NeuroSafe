import { useState } from 'react'
import type { AnalysisResult } from '../types'
import { DangerScoreGauge } from '../components/DangerScoreGauge'
import { DangerSegmentList } from '../components/DangerSegmentList'
import { GeminiReportCard } from '../components/GeminiReportCard'
import { RoiTimeline } from '../components/RoiTimeline'
import { BrainViewer } from '../components/BrainViewer'
import { VideoPlayer } from '../components/VideoPlayer'

interface ResultsPageProps {
  result: AnalysisResult
  onReset: () => void
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
      <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">{title}</h3>
      {children}
    </div>
  )
}

function fmtDuration(s: number) {
  return `${Math.floor(s / 60)}m ${(s % 60).toFixed(0)}s`
}

export function ResultsPage({ result, onReset }: ResultsPageProps) {
  const { video, danger_score, summary, danger_segments, roi_timeseries, gemini_report, brain_visualization } = result
  const [currentTime, setCurrentTime] = useState(0)

  const backendHost = window.location.hostname === 'localhost' ? 'http://localhost:8000' : ''
  const videoUrl = `${backendHost}/video/${video.filename}`

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Analysis Complete</h1>
            <p className="text-slate-400 text-sm mt-1 truncate max-w-xs">{video.filename}</p>
          </div>
          <button
            onClick={onReset}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm text-slate-300 transition-colors"
          >
            Analyze Another
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card title="Danger Score">
            <DangerScoreGauge score={danger_score} severity={summary.severity} />
          </Card>

          <Card title="Video Info">
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Duration</dt>
                <dd className="text-slate-200 font-mono">{fmtDuration(video.duration_seconds)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Frame rate</dt>
                <dd className="text-slate-200 font-mono">{video.fps} fps</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Resolution</dt>
                <dd className="text-slate-200 font-mono">{video.resolution}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Segments flagged</dt>
                <dd className="text-slate-200 font-mono">{summary.segments_detected}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Total danger time</dt>
                <dd className="text-slate-200 font-mono">{fmtDuration(summary.total_danger_duration_seconds)}</dd>
              </div>
            </dl>
          </Card>

          <Card title="Clinical Report">
            <GeminiReportCard report={gemini_report} />
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-4">
            <VideoPlayer 
              videoUrl={videoUrl}
              metadata={video}
              dangerSegments={danger_segments}
              currentTime={currentTime}
              onTimeUpdate={setCurrentTime}
            />
            <Card title="Flagged Segments">
              <DangerSegmentList segments={danger_segments} />
            </Card>
          </div>
          
          <div className="space-y-4">
            {brain_visualization && brain_visualization.frames.some(f => f.image_b64) ? (
              <Card title="3D Cortical Activation — TRIBE v2">
                <BrainViewer visualization={brain_visualization} currentTime={currentTime} />
              </Card>
            ) : (
              <Card title="3D Cortical Activation">
                <div className="h-48 flex items-center justify-center text-slate-500">Visualization not available</div>
              </Card>
            )}
            <Card title="Cortical ROI Activation Over Time">
              <RoiTimeline timeseries={roi_timeseries} dangerSegments={danger_segments} />
            </Card>
          </div>
        </div>

      </div>
    </div>
  )
}

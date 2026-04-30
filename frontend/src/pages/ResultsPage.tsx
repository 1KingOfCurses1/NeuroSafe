import { useState } from 'react'
import type { AnalysisResult } from '../types'
import { DangerScoreGauge } from '../components/DangerScoreGauge'
import { DangerSegmentList } from '../components/DangerSegmentList'
import { GeminiReportCard } from '../components/GeminiReportCard'
import { RoiTimeline } from '../components/RoiTimeline'
import { BrainViewer } from '../components/BrainViewer'
import { VideoPlayer } from '../components/VideoPlayer'
import { Footer } from '../components/Footer'

interface ResultsPageProps {
  result: AnalysisResult
  onReset: () => void
}

function Card({ title, children, className = '' }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-[#0A0A0B]/80 backdrop-blur-md border border-white/5 rounded-2xl p-6 shadow-xl relative overflow-hidden group ${className}`}>
      {/* Subtle hover gradient */}
      <div className="absolute -inset-px bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl pointer-events-none"></div>
      
      <h3 className="text-[10px] font-bold text-soft-white/40 uppercase tracking-[0.2em] mb-5">{title}</h3>
      <div className="relative z-10">
        {children}
      </div>
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
    <div className="min-h-screen bg-[#000000] text-soft-white relative overflow-hidden selection:bg-clinical-teal/30 flex flex-col">
      
      {/* Vercel-style Background Ambient Glows */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[400px] bg-clinical-teal/10 blur-[150px] rounded-full pointer-events-none"></div>
      <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-deep-navy/20 blur-[150px] rounded-full pointer-events-none"></div>

      <div className="relative z-10 max-w-[1200px] mx-auto px-6 py-12 space-y-8 flex-1 w-full">

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-white/5 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-white/5 border border-white/5 text-[10px] font-mono text-soft-white/60 uppercase tracking-widest mb-3">
              <span className="w-1.5 h-1.5 rounded-full bg-clinical-teal"></span>
              Analysis Complete
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white to-white/70">
              Cortical Report
            </h1>
            <p className="text-soft-white/50 text-sm mt-2 font-mono truncate max-w-md">
              {video.filename}
            </p>
          </div>
          <button
            onClick={onReset}
            className="px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-sm font-medium text-soft-white transition-all shadow-lg backdrop-blur-sm focus:ring-2 focus:ring-white/20 whitespace-nowrap"
          >
            Analyze Another Video
          </button>
        </div>

        {/* Top KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card title="Danger Severity">
            <div className="flex items-center justify-center pt-2">
              <DangerScoreGauge score={danger_score} severity={summary.severity} />
            </div>
          </Card>

          <Card title="Video Telemetry">
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <dt className="text-soft-white/40">Duration</dt>
                <dd className="text-soft-white/90 font-mono">{fmtDuration(video.duration_seconds)}</dd>
              </div>
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <dt className="text-soft-white/40">Frame rate</dt>
                <dd className="text-soft-white/90 font-mono">{video.fps} fps</dd>
              </div>
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <dt className="text-soft-white/40">Resolution</dt>
                <dd className="text-soft-white/90 font-mono">{video.resolution}</dd>
              </div>
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <dt className="text-soft-white/40">Segments flagged</dt>
                <dd className={`font-mono font-bold ${summary.segments_detected > 0 ? 'text-danger-red' : 'text-clinical-teal'}`}>
                  {summary.segments_detected}
                </dd>
              </div>
              <div className="flex justify-between items-center">
                <dt className="text-soft-white/40">Danger time</dt>
                <dd className="text-soft-white/90 font-mono">{fmtDuration(summary.total_danger_duration_seconds)}</dd>
              </div>
            </dl>
          </Card>

          <Card title="AI Clinical Summary" className="md:col-span-1">
            <GeminiReportCard report={gemini_report} />
          </Card>
        </div>

        {/* Main Visualization Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Video & Segments */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-[#0A0A0B]/80 rounded-2xl border border-white/5 overflow-hidden shadow-2xl relative group">
              <VideoPlayer 
                videoUrl={videoUrl}
                metadata={video}
                dangerSegments={danger_segments}
                currentTime={currentTime}
                onTimeUpdate={setCurrentTime}
              />
            </div>
            <Card title="Flagged Anomalies">
              <DangerSegmentList segments={danger_segments} />
            </Card>
          </div>
          
          {/* Right Column: Brain & Timeline */}
          <div className="lg:col-span-7 space-y-6">
            {brain_visualization && brain_visualization.frames.some(f => f.image_b64) ? (
              <Card title="3D Cortical Activation Map — TRIBE v2">
                <BrainViewer visualization={brain_visualization} currentTime={currentTime} />
              </Card>
            ) : (
              <Card title="3D Cortical Activation Map">
                <div className="h-[250px] flex flex-col items-center justify-center text-soft-white/30 space-y-3">
                  <svg className="w-8 h-8 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-xs tracking-widest uppercase font-mono">Visualization Offline</span>
                </div>
              </Card>
            )}
            <Card title="Cortical ROI Time Series">
              <RoiTimeline timeseries={roi_timeseries} dangerSegments={danger_segments} />
            </Card>
          </div>
        </div>

      </div>

      <div className="relative z-10 w-full mt-auto">
        <Footer />
      </div>
    </div>
  )
}

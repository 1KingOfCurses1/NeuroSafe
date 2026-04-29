import { useState } from 'react'
import { useAnalysisJob } from './hooks/useAnalysisJob'
import { UploadPage } from './pages/UploadPage'
import { ResultsPage } from './pages/ResultsPage'
import { ProgressBar } from './components/ProgressBar'

type View = 'upload' | 'analyzing' | 'results'

export default function App() {
  const [view, setView] = useState<View>('upload')
  const [jobId, setJobId] = useState<string | null>(null)
  const { status, progress, message, result, error, reset } = useAnalysisJob(jobId)

  function handleJobCreated(id: string) {
    setJobId(id)
    setView('analyzing')
  }

  function handleReset() {
    reset()
    setJobId(null)
    setView('upload')
  }

  if (view === 'upload') {
    return <UploadPage onJobCreated={handleJobCreated} />
  }

  if ((view === 'results' || status === 'completed') && result) {
    return <ResultsPage result={result} onReset={handleReset} />
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold tracking-tight">
            Neuro<span className="text-blue-400">Safe</span>
          </h1>
          <p className="text-slate-400 text-sm">Running cortical safety analysis…</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <ProgressBar progress={progress} status={status} message={message} />
        </div>

        {error && (
          <div className="bg-red-950/40 border border-red-800 rounded-xl px-4 py-3 text-sm text-red-300 text-center">
            {error}
          </div>
        )}

        {(status === 'failed' || error) && (
          <button
            onClick={handleReset}
            className="w-full py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm text-slate-300 transition-colors"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  )
}

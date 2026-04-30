import { useState } from 'react'
import { useAnalysisJob } from './hooks/useAnalysisJob'
import { UploadPage } from './pages/UploadPage'
import { ResultsPage } from './pages/ResultsPage'
import { ProgressBar } from './components/ProgressBar'
import { Footer } from './components/Footer'

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
    <div className="relative min-h-screen bg-[#000000] text-soft-white flex flex-col overflow-hidden selection:bg-clinical-teal/30">
      
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-clinical-teal/10 blur-[100px] rounded-full opacity-60 pointer-events-none"></div>

      <div className="relative z-10 w-full max-w-md space-y-10 flex-1 flex flex-col justify-center mx-auto px-4 py-20">
        <div className="text-center space-y-4">
          <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60">
            Analyzing Content
          </h1>
          <p className="text-clinical-teal/80 text-xs font-mono tracking-widest uppercase">
            In-Silico Neural Simulation Active
          </p>
        </div>

        <div className="bg-[#0A0A0B]/90 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
          {/* Subtle moving light effect on top of card */}
          <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-clinical-teal to-transparent opacity-50"></div>
          
          <ProgressBar progress={progress} status={status} message={message} />
        </div>

        {error && (
          <div className="bg-danger-red/10 border border-danger-red/20 rounded-xl px-5 py-4 text-sm text-danger-red font-medium text-center shadow-[0_0_20px_rgba(255,76,76,0.1)]">
            {error}
          </div>
        )}

        {(status === 'failed' || error) && (
          <button
            onClick={handleReset}
            className="w-full py-3.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-sm font-medium text-soft-white transition-all focus:outline-none focus:ring-2 focus:ring-white/20 backdrop-blur-sm"
          >
            Reset Analysis
          </button>
        )}
      </div>

      <div className="relative z-10 w-full mt-auto">
        <Footer />
      </div>
    </div>
  )
}

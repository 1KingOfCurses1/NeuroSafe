import { useState, useRef, useCallback } from 'react'
import { submitUpload, submitYouTube } from '../api/neurosafe'

interface UploadZoneProps {
  onJobCreated: (jobId: string) => void
}

type Tab = 'file' | 'youtube'

export function UploadZone({ onJobCreated }: UploadZoneProps) {
  const [tab, setTab] = useState<Tab>('file')
  const [dragging, setDragging] = useState(false)
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback(async (file: File) => {
    if (!file.type.startsWith('video/')) {
      setError('Please upload a video file.')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      const { job_id } = await submitUpload(file)
      onJobCreated(job_id)
    } catch {
      setError('Upload failed. Is the server running?')
    } finally {
      setSubmitting(false)
    }
  }, [onJobCreated])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const handleYouTube = async () => {
    if (!youtubeUrl.trim()) { setError('Please enter a YouTube URL.'); return }
    setError(null)
    setSubmitting(true)
    try {
      const { job_id } = await submitYouTube(youtubeUrl.trim())
      onJobCreated(job_id)
    } catch {
      setError('Failed to submit YouTube URL.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="w-full max-w-xl mx-auto flex flex-col gap-5">
      <div className="flex rounded-xl bg-deep-navy/40 p-1.5 gap-1.5 border border-deep-navy">
        {(['file', 'youtube'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => { setTab(t); setError(null) }}
            className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all ${tab === t ? 'bg-clinical-teal text-near-black shadow-md' : 'text-soft-white/60 hover:text-soft-white hover:bg-deep-navy/60'}`}
          >
            {t === 'file' ? 'Upload File' : 'YouTube URL'}
          </button>
        ))}
      </div>

      <div className="flex flex-col relative w-full">
        <div className={`grid transition-all duration-300 ease-in-out ${tab === 'file' ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}>
          <div className="overflow-hidden">
            <div
              onDrop={onDrop}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onClick={() => !submitting && fileInputRef.current?.click()}
              className={`flex flex-col items-center justify-center gap-4 border-2 border-dashed rounded-2xl px-8 py-16 cursor-pointer transition-colors ${dragging ? 'border-clinical-teal bg-clinical-teal/10' : 'border-deep-navy hover:border-clinical-teal/50 bg-deep-navy/20'} ${submitting ? 'opacity-80 pointer-events-none' : ''}`}
            >
              {submitting ? (
                <div className="flex items-end justify-center h-10 gap-1.5">
                  <div className="eeg-bar"></div>
                  <div className="eeg-bar"></div>
                  <div className="eeg-bar"></div>
                  <div className="eeg-bar"></div>
                  <div className="eeg-bar"></div>
                </div>
              ) : (
                <svg className="w-12 h-12 text-clinical-teal/80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              )}
              
              <div className="text-center space-y-1">
                <p className="text-soft-white text-base font-medium">
                  {submitting ? 'Running cortical safety analysis...' : 'Drop a video file here'}
                </p>
                {!submitting && (
                  <p className="text-soft-white/50 text-sm">or click to browse · MP4, WebM, MOV</p>
                )}
              </div>
              <input ref={fileInputRef} type="file" accept="video/*" className="hidden" onChange={onInputChange} />
            </div>
          </div>
        </div>

        <div className={`grid transition-all duration-300 ease-in-out ${tab === 'youtube' ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}>
          <div className="overflow-hidden">
            <div className="space-y-4 pt-1">
              <input
                type="url"
                value={youtubeUrl}
                onChange={e => setYoutubeUrl(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleYouTube()}
                placeholder="https://youtube.com/watch?v=..."
                className="w-full bg-deep-navy/30 border border-deep-navy rounded-xl px-5 py-4 text-base text-soft-white placeholder-soft-white/30 focus:outline-none focus:border-clinical-teal focus:ring-1 focus:ring-clinical-teal transition-all"
              />
              <button
                onClick={handleYouTube}
                disabled={submitting}
                className="w-full py-4 rounded-xl bg-clinical-teal hover:bg-clinical-teal/90 disabled:opacity-50 disabled:hover:bg-clinical-teal text-near-black text-base font-bold shadow-lg shadow-clinical-teal/20 transition-all flex justify-center items-center gap-3"
              >
                {submitting ? (
                  <>
                    <div className="flex items-end justify-center h-3 gap-1">
                      <div className="eeg-bar !bg-near-black" style={{ height: '60%' }}></div>
                      <div className="eeg-bar !bg-near-black" style={{ animationDelay: '0.1s', height: '100%' }}></div>
                      <div className="eeg-bar !bg-near-black" style={{ animationDelay: '0.2s', height: '80%' }}></div>
                    </div>
                    Analyzing...
                  </>
                ) : 'Analyze YouTube Video'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-danger-red/10 border border-danger-red/30 rounded-lg p-3 text-center">
          <p className="text-sm text-danger-red font-medium">{error}</p>
        </div>
      )}
    </div>
  )
}

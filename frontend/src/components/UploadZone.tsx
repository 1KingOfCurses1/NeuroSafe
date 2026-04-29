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
    <div className="w-full max-w-xl mx-auto space-y-4">
      <div className="flex rounded-lg bg-slate-800 p-1 gap-1">
        {(['file', 'youtube'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => { setTab(t); setError(null) }}
            className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${tab === t ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            {t === 'file' ? 'Upload File' : 'YouTube URL'}
          </button>
        ))}
      </div>

      {tab === 'file' ? (
        <div
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`flex flex-col items-center justify-center gap-3 border-2 border-dashed rounded-xl px-8 py-14 cursor-pointer transition-colors ${dragging ? 'border-blue-500 bg-blue-950/20' : 'border-slate-700 hover:border-slate-500 bg-slate-800/40'}`}
        >
          <svg className="w-10 h-10 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <div className="text-center">
            <p className="text-slate-300 text-sm font-medium">Drop a video file here</p>
            <p className="text-slate-500 text-xs mt-1">or click to browse · MP4, WebM, MOV</p>
          </div>
          <input ref={fileInputRef} type="file" accept="video/*" className="hidden" onChange={onInputChange} />
        </div>
      ) : (
        <div className="space-y-3">
          <input
            type="url"
            value={youtubeUrl}
            onChange={e => setYoutubeUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleYouTube()}
            placeholder="https://youtube.com/watch?v=..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
          <button
            onClick={handleYouTube}
            disabled={submitting}
            className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-semibold transition-colors"
          >
            {submitting ? 'Submitting…' : 'Analyze YouTube Video'}
          </button>
        </div>
      )}

      {error && (
        <p className="text-center text-sm text-red-400">{error}</p>
      )}

      {submitting && tab === 'file' && (
        <p className="text-center text-sm text-slate-400 animate-pulse">Uploading…</p>
      )}
    </div>
  )
}

import { useState, useEffect, useRef, useCallback } from 'react'
import type { AnalysisResult, JobStatus, ProgressEvent } from '../types'
import { fetchJob } from '../api/neurosafe'

export interface JobState {
  status: JobStatus
  progress: number
  message: string
  result: AnalysisResult | null
  error: string | null
}

const INITIAL_STATE: JobState = {
  status: 'queued',
  progress: 0,
  message: '',
  result: null,
  error: null,
}

function wsBase(): string {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}`
}

export function useAnalysisJob(jobId: string | null) {
  const [state, setState] = useState<JobState>(INITIAL_STATE)
  const wsRef = useRef<WebSocket | null>(null)

  const reset = useCallback(() => setState(INITIAL_STATE), [])

  useEffect(() => {
    if (!jobId) return

    const ws = new WebSocket(`${wsBase()}/ws/analyze/${jobId}`)
    wsRef.current = ws

    ws.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data as string) as ProgressEvent

      setState(prev => ({
        ...prev,
        status: data.status,
        progress: data.progress,
        message: data.message,
      }))

      if (data.status === 'completed') {
        fetchJob(jobId)
          .then(job => setState(prev => ({ ...prev, result: job.result })))
          .catch(err =>
            setState(prev => ({
              ...prev,
              status: 'failed',
              error: err instanceof Error ? err.message : 'Failed to load results.',
            }))
          )
      }

      if (data.status === 'failed') {
        setState(prev => ({ ...prev, error: 'Analysis failed on the server.' }))
      }
    }

    ws.onerror = () => {
      setState(prev => ({
        ...prev,
        status: 'failed',
        error: 'Lost connection to the server.',
      }))
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [jobId])

  return { ...state, reset }
}

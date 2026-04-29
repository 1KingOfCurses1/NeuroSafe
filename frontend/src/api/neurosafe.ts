import axios from 'axios'
import type { JobCreateResponse, JobStatusResponse } from '../types'

const api = axios.create({ baseURL: '/api' })

export async function submitUpload(file: File): Promise<JobCreateResponse> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<JobCreateResponse>('/analyze/upload', form)
  return data
}

export async function submitYouTube(url: string): Promise<JobCreateResponse> {
  const { data } = await api.post<JobCreateResponse>('/analyze/youtube', { url })
  return data
}

export async function fetchJob(jobId: string): Promise<JobStatusResponse> {
  const { data } = await api.get<JobStatusResponse>(`/analyze/${jobId}`)
  return data
}

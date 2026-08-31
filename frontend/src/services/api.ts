import axios from 'axios'
import type { VerificationRequest, VerificationResult, InputType } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function verifyClaim(
  inputType: InputType,
  inputText: string,
  inputUrl?: string
): Promise<VerificationResult> {
  const response = await api.post<VerificationResult>('/verify', {
    input_type: inputType,
    input_text: inputText,
    input_url: inputUrl,
  })
  return response.data
}

export async function getVerificationResult(id: string): Promise<VerificationResult> {
  const response = await api.get<VerificationResult>(`/verification/${id}`)
  return response.data
}

export async function getHistory(
  skip: number = 0,
  limit: number = 20
): Promise<VerificationRequest[]> {
  const response = await api.get<VerificationRequest[]>('/history', {
    params: { skip, limit },
  })
  return response.data
}

export async function deleteHistoryItem(id: string): Promise<void> {
  await api.delete(`/history/${id}`)
}

export async function checkHealth(): Promise<{ status: string; version: string }> {
  const response = await api.get('/health')
  return response.data
}

export async function getTrendingNews(limit: number = 20): Promise<any> {
  const response = await api.get('/auto-scan/trending', {
    params: { limit }
  })
  return response.data
}

export async function getDailyUpdates(limit: number = 20): Promise<any> {
  const response = await api.get('/auto-scan/daily-updates', {
    params: { limit }
  })
  return response.data
}

export async function getScanSources(): Promise<any> {
  const response = await api.get('/auto-scan/sources')
  return response.data
}

export async function scanUrls(urls: string[]): Promise<any> {
  const response = await api.post('/auto-scan/scan-urls', urls)
  return response.data
}

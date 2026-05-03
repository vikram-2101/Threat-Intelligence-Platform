/**
 * Axios instance with Bearer token interceptor.
 * DEMO MODE: 401 interceptor disabled — no forced logout during presentation.
 */

import axios, { type InternalAxiosRequestConfig } from 'axios'
import { getToken } from './token'

const api = axios.create({
  baseURL: (import.meta as any).env?.VITE_API_BASE_URL || '/api/v1/',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15_000,
})

// Attach Bearer token on every request
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// DEMO MODE: response interceptor with 401 redirect removed.
// Errors will surface as TanStack Query isError states in the UI instead.

export default api

/**
 * Auth API functions
 * Agent.md §12: "All API types are in /src/types/"
 */

import api from '@/lib/axios'
import { setToken } from '@/lib/token'
import type { TokenResponse } from '@/types'

export interface LoginCredentials {
  username: string
  password: string
}

/**
 * POST /api/v1/auth/login
 * OAuth2 password flow — stores the returned JWT in memory.
 */
export const login = async (credentials: LoginCredentials): Promise<void> => {
  // FastAPI OAuth2PasswordRequestForm requires multipart/form-data
  const formData = new URLSearchParams()
  formData.append('username', credentials.username)
  formData.append('password', credentials.password)

  const { data } = await api.post<TokenResponse>('auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })

  setToken(data.access_token)
}

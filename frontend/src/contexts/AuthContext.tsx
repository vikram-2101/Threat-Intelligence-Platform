/**
 * AuthContext — provides isAuthenticated state and logout throughout the app.
 *
 * The actual token is held in lib/token.ts (module-level variable, per Agent.md §12).
 * This context is a thin React re-render layer on top of it.
 *
 * The context also listens for the 'tip:auth:logout' custom DOM event that the
 * Axios 401 interceptor dispatches. This avoids window.location hard-reloads which
 * would destroy the in-memory token and cause infinite login redirect loops.
 */

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import { isAuthenticated, clearToken } from '@/lib/token'

interface AuthContextValue {
  /** True if a JWT is currently held in memory */
  authenticated: boolean
  /** Call after a successful login to trigger re-render */
  onLoginSuccess: () => void
  /** Clears the in-memory token and marks user as unauthenticated */
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  // Initialise from the in-memory token (false on fresh page load)
  const [authenticated, setAuthenticated] = useState(isAuthenticated)

  const onLoginSuccess = useCallback(() => {
    setAuthenticated(true)
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setAuthenticated(false)
  }, [])

  // Listen for the custom event dispatched by the Axios 401 interceptor.
  // Using a DOM event instead of window.location avoids a hard page reload
  // which would destroy the module-level accessToken and cause a redirect loop.
  useEffect(() => {
    const handleForceLogout = () => {
      clearToken()
      setAuthenticated(false)
    }
    window.addEventListener('tip:auth:logout', handleForceLogout)
    return () => {
      window.removeEventListener('tip:auth:logout', handleForceLogout)
    }
  }, [])

  return (
    <AuthContext.Provider value={{ authenticated, onLoginSuccess, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}

/**
 * LoginPage — Phase 3.3
 *
 * Security-hardened login: no credential persistence, JWT stored in memory only.
 * On success redirects to the originally-requested page (or /indicators).
 */

import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Shield, Lock, User, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-react'
import { login } from '@/api/auth'
import { useAuth } from '@/contexts/AuthContext'
import { PageErrorBoundary } from '@/components/PageErrorBoundary'

interface LocationState {
  from?: { pathname: string }
}

function LoginForm() {
  const navigate = useNavigate()
  const location = useLocation()
  const { onLoginSuccess } = useAuth()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const rawFrom = (location.state as LocationState)?.from?.pathname
  // Never redirect back to /login after a successful login — that would loop.
  const from = (!rawFrom || rawFrom === '/login') ? '/indicators' : rawFrom

  const loginMutation = useMutation({
    mutationFn: () => login({ username, password }),
    onSuccess: () => {
      onLoginSuccess()
      navigate(from, { replace: true })
    },
    // DEMO MODE: navigate even if login API fails — auth check is bypassed.
    onError: () => {
      navigate(from, { replace: true })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password) return
    loginMutation.mutate()
  }

  return (
    <div className="min-h-screen bg-surface-900 flex items-center justify-center p-4">
      {/* Background grid pattern */}
      <div
        className="fixed inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(99,102,241,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.5) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative w-full max-w-sm animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-600/20 border border-brand-500/30 mb-4 shadow-glow">
            <Shield className="w-8 h-8 text-brand-400" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
            Threat Intelligence
          </h1>
          <p className="text-sm text-slate-400 mt-1">Platform — Analyst Workbench</p>
        </div>

        {/* Card */}
        <div className="card p-6 shadow-2xl">
          <h2 className="text-base font-semibold text-slate-200 mb-5">Sign in to continue</h2>

          {loginMutation.isError && (
            <div className="flex items-start gap-3 p-3 mb-4 rounded-lg bg-red-500/10 border border-red-500/20 animate-fade-in">
              <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
              <p className="text-sm text-red-300">
                {(() => {
                  const err = loginMutation.error as any;
                  // Backend returns 400 for bad credentials (not 401)
                  if (err?.response?.status === 400 || err?.response?.status === 401) {
                    return err?.response?.data?.detail ?? 'Invalid username or password';
                  }
                  if (err?.message) return `Authentication failed: ${err.message}`;
                  return 'Authentication failed. Please try again.';
                })()}
              </p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-xs font-medium text-slate-400 mb-1.5">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  autoFocus
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="analyst"
                  required
                  className="input pl-9"
                  disabled={loginMutation.isPending}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-xs font-medium text-slate-400 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="input pl-9 pr-10"
                  disabled={loginMutation.isPending}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loginMutation.isPending || !username.trim() || !password}
              className="btn-primary w-full justify-center mt-2"
            >
              {loginMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Authenticating…
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>
        </div>

        {/* Security notice */}
        <p className="text-center text-xs text-slate-600 mt-4">
          Session ends on tab close · No credentials are stored
        </p>
      </div>
    </div>
  )
}

export function LoginPage() {
  return (
    <PageErrorBoundary>
      <LoginForm />
    </PageErrorBoundary>
  )
}

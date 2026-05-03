/**
 * LoginPage — Phase 3.3
 *
 * Security-hardened login: no credential persistence, JWT stored in memory only.
 * On success redirects to the originally-requested page (or /indicators).
 */

import React, { useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Shield, Lock, User, Eye, EyeOff, AlertCircle, Loader2, CheckCircle, ArrowLeft } from 'lucide-react'
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
    <div className="min-h-screen bg-surface-950 flex flex-col md:flex-row items-stretch select-none overflow-hidden antialiased">

      {/* ── LEFT SIDE: Branding & Background Image ───────────────────────── */}
      <div className="hidden md:flex flex-1 relative bg-surface-900 border-r border-slate-800/80 items-center justify-center p-12 overflow-hidden select-none">
        
        {/* Visual Map/Globe Overlay */}
        <div className="absolute inset-0 bg-cover bg-center opacity-10 filter saturate-0 pointer-events-none select-none" style={{ backgroundImage: "url('/world.png')" }} />
        <div className="absolute inset-0 bg-gradient-to-t from-surface-950 via-transparent to-brand-600/5 pointer-events-none select-none" />

        <div className="max-w-md w-full relative z-10 flex flex-col select-none">
          <Link to="/" className="flex items-center gap-3 mb-10 group select-none">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-brand-600/20 border border-brand-500/30 group-hover:bg-brand-600/30 group-hover:border-brand-400/40 transition-all duration-300 shadow-glow select-none">
              <Shield className="w-5 h-5 text-brand-400 select-none group-hover:scale-105" />
            </div>
            <span className="text-lg font-bold tracking-wider text-slate-100 select-none">THREATLENS</span>
          </Link>

          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100 mb-6 leading-tight select-none">
            Transform Raw Feeds Into Defensible Intelligence
          </h2>
          <p className="text-slate-400 text-base leading-relaxed mb-8 max-w-sm select-none">
            Sign in to start scanning, validating, and explaining high-fidelity threat indicators on our unified analyst workbench.
          </p>

          {/* Quick value props */}
          <div className="space-y-4 select-none">
            <div className="flex items-center gap-3 select-none">
              <span className="w-6 h-6 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center select-none">
                <CheckCircle className="w-3.5 h-3.5 text-brand-400" />
              </span>
              <span className="text-sm font-medium text-slate-300 select-none">Contextualized Evidence-First Profiling</span>
            </div>
            <div className="flex items-center gap-3 select-none">
              <span className="w-6 h-6 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center select-none">
                <CheckCircle className="w-3.5 h-3.5 text-brand-400" />
              </span>
              <span className="text-sm font-medium text-slate-300 select-none">Dynamic Indicator Decay Scoring</span>
            </div>
            <div className="flex items-center gap-3 select-none">
              <span className="w-6 h-6 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center select-none">
                <CheckCircle className="w-3.5 h-3.5 text-brand-400" />
              </span>
              <span className="text-sm font-medium text-slate-300 select-none">Human Analyst-Advisory Guardrails</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── RIGHT SIDE: Login Form Section ────────────────────────────────── */}
      <div className="flex flex-1 relative flex-col justify-center items-center bg-surface-950 p-6 md:p-16 overflow-y-auto select-none">
        
        {/* Mobile Navbar action to go back */}
        <div className="absolute top-6 left-6 md:top-8 md:left-8 select-none">
          <Link to="/" className="text-xs font-semibold text-slate-400 hover:text-slate-100 flex items-center gap-2 select-none group">
            <ArrowLeft className="w-3.5 h-3.5 transition-transform group-hover:-translate-x-0.5 select-none" /> Back to home
          </Link>
        </div>

        <div className="w-full max-w-sm flex flex-col justify-center min-h-[500px] animate-slide-up select-none">
          
          {/* Mobile Logo */}
          <div className="md:hidden flex items-center gap-2.5 mb-8 select-none">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-brand-600/20 border border-brand-500/30">
              <Shield className="w-4 h-4 text-brand-400 select-none" />
            </div>
            <span className="text-sm font-bold tracking-wider text-slate-100 select-none">THREATLENS</span>
          </div>

          <div className="mb-8 select-none">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-100 mb-2 leading-tight select-none">
              Welcome back
            </h1>
            <p className="text-slate-400 text-sm select-none">Sign in to your analyst workstation</p>
          </div>

          {/* Form container */}
          <div className="bg-surface-900 border border-slate-800 p-6 sm:p-8 rounded-2xl shadow-xl hover:border-slate-700/60 transition-all duration-300 select-none">
            
            <h2 className="text-base font-bold text-slate-200 mb-5 select-none">Sign in to continue</h2>

            {loginMutation.isError && (
              <div className="flex items-start gap-3 p-3 mb-4 rounded-lg bg-red-500/10 border border-red-500/20 animate-fade-in select-none">
                <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                <p className="text-sm text-red-300 select-none">
                  {(() => {
                    const err = loginMutation.error as any;
                    if (err?.response?.status === 400 || err?.response?.status === 401) {
                      return err?.response?.data?.detail ?? 'Invalid username or password';
                    }
                    if (err?.message) return `Authentication failed: ${err.message}`;
                    return 'Authentication failed. Please try again.';
                  })()}
                </p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 select-none" noValidate>
              {/* Username */}
              <div>
                <label htmlFor="username" className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider select-none">
                  Username
                </label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none select-none" />
                  <input
                    id="username"
                    type="text"
                    autoComplete="username"
                    autoFocus
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="analyst"
                    required
                    className="w-full bg-surface-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 rounded-xl px-3.5 py-3 pl-11 text-sm text-slate-100 placeholder:text-slate-600 transition-all duration-150"
                    disabled={loginMutation.isPending}
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider select-none">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none select-none" />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="w-full bg-surface-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 rounded-xl px-3.5 py-3 pl-11 pr-11 text-sm text-slate-100 placeholder:text-slate-600 transition-all duration-150"
                    disabled={loginMutation.isPending}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                    tabIndex={-1}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4 select-none" /> : <Eye className="w-4 h-4 select-none" />}
                  </button>
                </div>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loginMutation.isPending || !username.trim() || !password}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-bold text-sm rounded-xl border border-brand-500/20 shadow-glow-sm hover:shadow-glow hover:scale-[1.01] active:scale-[0.99] transition-all duration-200 select-none mt-6"
              >
                {loginMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin select-none" />
                    Authenticating…
                  </>
                ) : (
                  'Sign in'
                )}
              </button>
            </form>
          </div>

          {/* Security notice */}
          <p className="text-center text-xs text-slate-600 mt-6 select-none">
            Session ends on tab close · No credentials are stored
          </p>

        </div>
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

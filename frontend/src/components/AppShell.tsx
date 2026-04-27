/**
 * AppShell — persistent layout for authenticated pages.
 * Contains the left sidebar navigation and top header.
 */

import { NavLink, Outlet } from 'react-router-dom'
import { Shield, List, Database, LogOut, Activity, Bell, UploadCloud, FileText } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { clsx } from 'clsx'

const navItems = [
  { to: '/indicators', icon: List, label: 'Indicators' },
  { to: '/ingest', icon: UploadCloud, label: 'Ingest' },
  { to: '/sources', icon: Database, label: 'Sources' },
  { to: '/audit-logs', icon: FileText, label: 'Audit Logs' },
]

export function AppShell() {
  const { logout } = useAuth()

  return (
    <div className="flex h-screen overflow-hidden bg-surface-900">
      {/* ── Sidebar ───────────────────────────────────────────────────────── */}
      <aside className="flex flex-col w-56 shrink-0 bg-surface-950 border-r border-slate-700/50">
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-4 py-5 border-b border-slate-700/50">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-brand-600/30 border border-brand-500/30">
            <Shield className="w-4 h-4 text-brand-400" />
          </div>
          <div>
            <div className="text-sm font-bold text-slate-100 leading-none">TIP</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Threat Intelligence</div>
          </div>
        </div>

        {/* Nav links */}
        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-brand-600/20 text-brand-300 border border-brand-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800',
                )
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Bottom actions */}
        <div className="p-2 border-t border-slate-700/50">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium
                       text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all duration-150"
          >
            <LogOut className="w-4 h-4 shrink-0" />
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main content ──────────────────────────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Top header */}
        <header className="flex items-center justify-between px-6 h-14 shrink-0 bg-surface-900 border-b border-slate-700/50">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Activity className="w-3.5 h-3.5 text-green-400" />
            <span className="text-green-400 font-medium">System operational</span>
          </div>
          <div className="flex items-center gap-3">
            <button className="p-1.5 rounded-lg hover:bg-surface-800 text-slate-500 hover:text-slate-300 transition-colors">
              <Bell className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Page area */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

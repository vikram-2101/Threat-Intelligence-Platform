/**
 * RequireAuth — DEMO MODE: auth check bypassed for presentation.
 * Restore by uncommenting the auth check block below.
 */

import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
}

export function RequireAuth({ children }: Props) {
  // ── DEMO MODE ── auth wall removed for presentation ──────────────────────
  // To restore: uncomment the block below and remove the direct return.
  //
  // const { authenticated } = useAuth()
  // const location = useLocation()
  // if (!authenticated) {
  //   return <Navigate to="/login" state={{ from: location }} replace />
  // }
  // ─────────────────────────────────────────────────────────────────────────

  return <>{children}</>
}

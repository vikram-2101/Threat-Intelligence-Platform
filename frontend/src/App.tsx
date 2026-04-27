import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from '@/contexts/AuthContext'
import { RequireAuth } from '@/components/RequireAuth'
import { AppShell } from '@/components/AppShell'
import { LoginPage } from '@/pages/LoginPage'
import { IndicatorsPage } from '@/pages/IndicatorsPage'
import { IndicatorDetailPage } from '@/pages/IndicatorDetailPage'
import { SourcesPage } from '@/pages/SourcesPage'
import { IngestPage } from '@/pages/IngestPage'
import { AuditLogsPage } from '@/pages/AuditLogsPage'

// Configure TanStack Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      // Default cache time
      staleTime: 5 * 60 * 1000,
    },
  },
})

// Configure React Router
const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/indicators" replace />,
      },
      {
        path: 'indicators',
        element: <IndicatorsPage />,
      },
      {
        path: 'indicators/:id',
        element: <IndicatorDetailPage />,
      },
      {
        path: 'ingest',
        element: <IngestPage />,
      },
      {
        path: 'sources',
        element: <SourcesPage />,
      },
      {
        path: 'audit-logs',
        element: <AuditLogsPage />,
      },
      {
        path: '*',
        element: <Navigate to="/indicators" replace />,
      },
    ],
  },
])

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
        <Toaster 
          position="bottom-right" 
          toastOptions={{
            className: '!bg-surface-800 !text-slate-200 !border !border-slate-700',
            duration: 4000,
          }}
        />
      </AuthProvider>
    </QueryClientProvider>
  )
}

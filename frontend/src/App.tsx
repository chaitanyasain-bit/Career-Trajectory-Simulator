import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import { AppLayout } from '@/components/AppLayout'
import {
  CareerDetailPage,
  ComparisonPage,
  DashboardPage,
  HistoryDetailPage,
  HistoryPage,
  LoginPage,
  ProfilePage,
  RegisterPage,
  RoadmapPage,
  SimulationPage,
  WhatIfPage,
} from '@/pages'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (count, error) =>
        count < 2 && (error as { code?: string }).code !== 'UNAUTHORIZED',
      refetchOnWindowFocus: false,
    },
  },
})

function RequireAuth() {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="flex items-center gap-3 text-sm font-medium text-slate-600">
          <span className="spinner" /> Securing your workspace…
        </div>
      </div>
    )
  }
  return user ? <Outlet /> : <Navigate to="/login" replace />
}

function GuestOnly() {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen bg-slate-50" />
  return user ? <Navigate to="/" replace /> : <Outlet />
}

function AppRoutes() {
  return (
    <Routes>
      <Route element={<GuestOnly />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>
      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/simulation" element={<SimulationPage />} />
          <Route path="/careers/:roleId" element={<CareerDetailPage />} />
          <Route path="/comparison" element={<ComparisonPage />} />
          <Route path="/what-if" element={<WhatIfPage />} />
          <Route path="/roadmap/:pathId" element={<RoadmapPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/history/:simulationId" element={<HistoryDetailPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

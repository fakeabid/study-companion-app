import { useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AnimatedBackground } from './components/AnimatedBackground'
import { AuthPage } from './pages/AuthPage'
import { DashboardPage } from './pages/DashboardPage'
import { WorkspaceDetailPage } from './pages/WorkspaceDetailPage'
import { useAuthStore } from './stores/authStore'

function ProtectedRoute({ children }) {
  const { accessToken } = useAuthStore()

  if (!accessToken) {
    return <Navigate to="/auth" replace />
  }

  return children
}

function App() {
  const { accessToken, user, fetchMe } = useAuthStore()

  useEffect(() => {
    if (accessToken && !user) {
      fetchMe()
    }
  }, [accessToken, user, fetchMe])

  return (
    <main className="relative min-h-screen">
      <AnimatedBackground />
      <Routes>
        <Route
          path="/"
          element={
            accessToken ? <Navigate to="/dashboard" replace /> : <Navigate to="/auth" replace />
          }
        />
        <Route
          path="/auth"
          element={accessToken ? <Navigate to="/dashboard" replace /> : <AuthPage />}
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/workspaces/:workspaceId"
          element={
            <ProtectedRoute>
              <WorkspaceDetailPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  )
}

export default App

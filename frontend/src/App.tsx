import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import { DashboardLayout } from '@/components/DashboardLayout';
import { EmailVerificationBanner } from '@/components/EmailVerificationBanner';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { VerifyEmailPage } from '@/pages/VerifyEmailPage';
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { AdminDashboardPage } from '@/pages/AdminDashboardPage';
import { SpeechToTextPage } from '@/pages/SpeechToTextPage';

// Layout wrapper for authenticated routes
function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  return (
    <>
      {user && !user.verified && <EmailVerificationBanner />}
      <DashboardLayout>{children}</DashboardLayout>
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />

        {/* Protected routes with DashboardLayout */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <DashboardPage />
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/speech-to-text"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <SpeechToTextPage />
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/recordings"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <div>Recordings Page (Coming Soon)</div>
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <div>Search & RAG Page (Coming Soon)</div>
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <div>Settings Page (Coming Soon)</div>
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin"
          element={
            <ProtectedRoute requireAdmin={true}>
              <AuthenticatedLayout>
                <AdminDashboardPage />
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

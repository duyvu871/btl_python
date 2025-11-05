import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mantine/core';
import { useAuth } from '@/providers/AuthProvider';
import { EmailVerificationBanner } from '@/components/EmailVerificationBanner';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { VerifyEmailPage } from '@/pages/VerifyEmailPage';
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { AdminDashboardPage } from '@/pages/AdminDashboardPage';


function App() {
  const { isAuthenticated, user } = useAuth();

  return (
    <BrowserRouter>
      <Box style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        {isAuthenticated && user && !user.verified && <EmailVerificationBanner />}

        <Box style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />

            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/admin"
              element={
                <ProtectedRoute requireAdmin={true}>
                  <AdminDashboardPage />
                </ProtectedRoute>
              }
            />

            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Box>
      </Box>
    </BrowserRouter>
  );
}

export default App;

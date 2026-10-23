import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AppShell } from './components/AppShell';
import { LandingPage, AuthAndOnboardingPage } from './pages/LandingAndAuth';
import { StudentDashboard } from './pages/student/StudentDashboard';
import { StudentMentor } from './pages/student/StudentMentor';
import { StudentPyqAndNcert } from './pages/student/StudentPyqAndNcert';
import { StudentTestsAndCbt } from './pages/student/StudentTestsAndCbt';
import { StudentRevisionAndTools } from './pages/student/StudentRevisionAndTools';
import { ParentPortal } from './pages/ParentPortal';
import { SuperAdminPortal } from './pages/SuperAdminPortal';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Landing & Auth Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<AuthAndOnboardingPage initialTab="login" />} />
          <Route path="/register" element={<AuthAndOnboardingPage initialTab="register" />} />
          <Route path="/onboarding" element={<AuthAndOnboardingPage initialTab="onboarding" />} />

          {/* Student Portal Routes */}
          <Route
            path="/student/dashboard"
            element={
              <AppShell>
                <StudentDashboard />
              </AppShell>
            }
          />
          <Route
            path="/student/mentor"
            element={
              <AppShell>
                <StudentMentor />
              </AppShell>
            }
          />
          <Route
            path="/student/pyq"
            element={
              <AppShell>
                <StudentPyqAndNcert />
              </AppShell>
            }
          />
          <Route
            path="/student/tests"
            element={
              <AppShell>
                <StudentTestsAndCbt />
              </AppShell>
            }
          />
          <Route
            path="/student/exam/:testId"
            element={
              <AppShell>
                <StudentTestsAndCbt />
              </AppShell>
            }
          />
          <Route
            path="/student/revision"
            element={
              <AppShell>
                <StudentRevisionAndTools />
              </AppShell>
            }
          />
          <Route
            path="/student/tools"
            element={
              <AppShell>
                <StudentRevisionAndTools />
              </AppShell>
            }
          />

          {/* Parent & Teacher Portal Routes */}
          <Route
            path="/parent/dashboard"
            element={
              <AppShell>
                <ParentPortal />
              </AppShell>
            }
          />
          <Route
            path="/parent/reports"
            element={
              <AppShell>
                <ParentPortal />
              </AppShell>
            }
          />
          <Route
            path="/parent/assignments"
            element={
              <AppShell>
                <ParentPortal />
              </AppShell>
            }
          />
          <Route
            path="/parent/billing"
            element={
              <AppShell>
                <ParentPortal />
              </AppShell>
            }
          />

          {/* SuperAdmin Portal Routes */}
          <Route
            path="/superadmin/dashboard"
            element={
              <AppShell>
                <SuperAdminPortal />
              </AppShell>
            }
          />
          <Route
            path="/superadmin/users"
            element={
              <AppShell>
                <SuperAdminPortal />
              </AppShell>
            }
          />
          <Route
            path="/superadmin/questions"
            element={
              <AppShell>
                <SuperAdminPortal />
              </AppShell>
            }
          />
          <Route
            path="/superadmin/content"
            element={
              <AppShell>
                <SuperAdminPortal />
              </AppShell>
            }
          />
          <Route
            path="/superadmin/ai-settings"
            element={
              <AppShell>
                <SuperAdminPortal />
              </AppShell>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;

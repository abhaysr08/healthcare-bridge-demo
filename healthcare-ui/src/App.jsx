import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import ProfilePage from './pages/ProfilePage';
import ChangePasswordPage from './pages/ChangePasswordPage';
import AdminPage from './pages/admin/AdminPage';
import NurseDashboardPage from './pages/NurseDashboardPage';
import DoctorDashboardPage from './pages/DoctorDashboardPage';
import PatientDetailPage from './pages/PatientDetailPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import RoleRoute from './components/auth/RoleRoute';
import { useAuth } from './contexts/AuthContext';
import { getHomeRouteForRole } from './utils/roleRoutes';

function RoleHome() {
  const { user } = useAuth();
  return <Navigate to={getHomeRouteForRole(user?.role)} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/change-password"
        element={
          <ProtectedRoute>
            <ChangePasswordPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <RoleRoute allow={['admin']}>
            <AdminPage />
          </RoleRoute>
        }
      />
      <Route
        path="/nurse"
        element={
          <RoleRoute allow={['nurse', 'admin']}>
            <NurseDashboardPage />
          </RoleRoute>
        }
      />
      <Route
        path="/doctor"
        element={
          <RoleRoute allow={['doctor', 'admin']}>
            <DoctorDashboardPage />
          </RoleRoute>
        }
      />
      <Route
        path="/patient/:patientId"
        element={
          <RoleRoute allow={['nurse', 'doctor', 'admin']}>
            <PatientDetailPage />
          </RoleRoute>
        }
      />
      <Route
        path="*"
        element={
          <ProtectedRoute>
            <RoleHome />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

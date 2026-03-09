import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading, mustChangePassword } = useAuth();
  const { pathname } = useLocation();

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-navy">
        <span className="text-white text-lg">Caricamento...</span>
      </div>
    );
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (mustChangePassword && pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />;
  }

  return children;
}

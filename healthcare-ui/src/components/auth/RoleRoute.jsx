import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getHomeRouteForRole } from '../../utils/roleRoutes';

export default function RoleRoute({ allow, children }) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!allow.includes(user?.role)) {
    return <Navigate to={getHomeRouteForRole(user?.role)} replace />;
  }

  return children;
}

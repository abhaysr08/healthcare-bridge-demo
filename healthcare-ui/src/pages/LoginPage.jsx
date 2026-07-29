import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import PasswordInput from '../components/ui/PasswordInput';
import { getHomeRouteForRole } from '../utils/roleRoutes';
import { APP_NAME } from '../constants/branding';

export default function LoginPage() {
  const { login, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) return <Navigate to={getHomeRouteForRole(user?.role)} replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await login(username, password);
      if (result.mustChangePassword) {
        navigate('/change-password', { replace: true });
      } else {
        navigate(getHomeRouteForRole(result.role), { replace: true });
      }
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 423) {
        setError('Account bloccato dopo troppi tentativi. Contattare l\'amministratore.');
      } else if (status === 403) {
        setError('Account disabilitato. Contattare l\'amministratore.');
      } else {
        setError(detail || 'Credenziali non valide.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy to-navy-dark flex flex-col">
      <header className="text-white px-6 py-5 shrink-0 animate-fade-in">
        <h1 className="text-lg font-bold tracking-wider uppercase">
          {APP_NAME}
        </h1>
      </header>

      <div className="flex-1 flex items-center justify-center px-6 pb-10">
        <div className="w-full max-w-sm bg-white rounded-[2rem] shadow-card-hover px-6 pt-8 pb-8 animate-slide-up">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Accedi</h2>

          {error && (
            <p className="text-red-500 text-sm mb-4 animate-pop-in">{error}</p>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1.5">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Inserisci username"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal text-sm transition-shadow"
                required
                autoComplete="username"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1.5">
                Password
              </label>
              <PasswordInput
                value={password}
                onChange={setPassword}
                placeholder="Inserisci password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal text-white py-3 rounded-lg font-semibold hover:bg-teal-dark hover:shadow-lg transition-all cursor-pointer disabled:opacity-50 active:scale-[0.99]"
            >
              {loading ? 'Accesso in corso...' : 'Accedi'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

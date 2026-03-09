import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import PasswordInput from '../components/ui/PasswordInput';

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) return <Navigate to="/chat" replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await login(username, password);
      if (result.mustChangePassword) {
        navigate('/change-password', { replace: true });
      } else {
        navigate('/chat', { replace: true });
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
    <div className="min-h-screen bg-navy flex flex-col">
      <header className="text-white px-6 py-5 shrink-0">
        <h1 className="text-lg font-bold tracking-wider uppercase">
          Healthbridge Care
        </h1>
      </header>

      <div className="flex-1 bg-white rounded-t-[2rem] mt-1 px-6 pt-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Accedi</h2>

        {error && (
          <p className="text-red-500 text-sm mb-4">{error}</p>
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
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal text-sm"
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
            className="w-full bg-teal text-white py-3 rounded-lg font-semibold hover:bg-teal-dark transition-colors cursor-pointer disabled:opacity-50"
          >
            {loading ? 'Accesso in corso...' : 'Accedi'}
          </button>
        </form>
      </div>
    </div>
  );
}

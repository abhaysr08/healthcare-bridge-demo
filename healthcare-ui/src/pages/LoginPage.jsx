import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import PasswordInput from '../components/ui/PasswordInput';

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  if (isAuthenticated) return <Navigate to="/chat" replace />;

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    const result = login(email, password);
    if (result.success) {
      navigate('/chat');
    } else {
      setError(result.error);
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
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Login!</h2>

        {error && (
          <p className="text-red-500 text-sm mb-4">{error}</p>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1.5">
              Email ID
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter Email ID"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1.5">
              Password
            </label>
            <PasswordInput
              value={password}
              onChange={setPassword}
              placeholder="Enter Password"
            />
          </div>

          <button
            type="submit"
            className="w-full bg-teal text-white py-3 rounded-lg font-semibold hover:bg-teal-dark transition-colors cursor-pointer"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
}

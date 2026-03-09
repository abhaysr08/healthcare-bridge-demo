import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import PasswordInput from '../components/ui/PasswordInput';

export default function ChangePasswordPage() {
  const { changePassword, user } = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    if (newPassword.length < 12) {
      setError('La nuova password deve essere di almeno 12 caratteri.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Le password non coincidono.');
      return;
    }

    setLoading(true);
    try {
      await changePassword(currentPassword, newPassword);
      navigate('/chat', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore durante il cambio password.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-lg p-8">
        <h1 className="text-2xl font-bold text-navy mb-2">Cambio Password Obbligatorio</h1>
        <p className="text-sm text-gray-500 mb-6">
          Benvenuto, <strong>{user?.fullName}</strong>. Prima di continuare devi impostare una nuova password.
        </p>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password attuale</label>
            <PasswordInput
              value={currentPassword}
              onChange={setCurrentPassword}
              placeholder="Password attuale"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nuova password</label>
            <PasswordInput
              value={newPassword}
              onChange={setNewPassword}
              placeholder="Minimo 12 caratteri"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Conferma nuova password</label>
            <PasswordInput
              value={confirmPassword}
              onChange={setConfirmPassword}
              placeholder="Ripeti la nuova password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-teal text-white rounded-lg font-medium hover:bg-teal-dark disabled:opacity-50 transition-colors"
          >
            {loading ? 'Salvataggio...' : 'Imposta nuova password'}
          </button>
        </form>
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { listUsersApi, createUserApi, disableUserApi, enableUserApi, unlockUserApi } from '../../services/authApi';

const ROLE_LABELS = { admin: 'Amministratore', nurse: 'Infermiere', doctor: 'Medico' };
const ROLE_BADGE_CLASSES = {
  admin: 'bg-navy/10 text-navy',
  nurse: 'bg-teal/10 text-teal',
  doctor: 'bg-warning/10 text-warning',
};

export default function UsersTab() {
  const { accessToken } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ username: '', password: '', full_name: '', designation: '', role: 'nurse' });
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  async function loadUsers() {
    try {
      const data = await listUsersApi(accessToken);
      setUsers(data);
    } catch {
      setError('Errore nel caricamento utenti.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadUsers(); }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setFormError('');
    if (form.password.length < 12) {
      setFormError('La password deve essere di almeno 12 caratteri.');
      return;
    }
    setFormLoading(true);
    try {
      await createUserApi(form, accessToken);
      setShowForm(false);
      setForm({ username: '', password: '', full_name: '', designation: '', role: 'nurse' });
      await loadUsers();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Errore nella creazione utente.');
    } finally {
      setFormLoading(false);
    }
  }

  async function handleAction(id, action) {
    try {
      if (action === 'disable') await disableUserApi(id, accessToken);
      else if (action === 'enable') await enableUserApi(id, accessToken);
      else if (action === 'unlock') await unlockUserApi(id, accessToken);
      await loadUsers();
    } catch (err) {
      alert(err.response?.data?.detail || 'Operazione fallita.');
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center py-16 text-gray-400 text-sm">
      Caricamento utenti...
    </div>
  );
  if (error) return (
    <div className="flex items-center justify-center py-16 text-red-500 text-sm">{error}</div>
  );

  const activeCount = users.filter(u => u.is_active && !u.is_locked).length;
  const lockedCount = users.filter(u => u.is_locked).length;
  const adminCount = users.filter(u => u.role === 'admin').length;

  return (
    <div>
      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="bg-navy/5 rounded-xl p-4">
          <p className="text-2xl font-bold text-navy">{users.length}</p>
          <p className="text-xs text-gray-500 mt-0.5">Utenti totali</p>
        </div>
        <div className="bg-teal/5 rounded-xl p-4">
          <p className="text-2xl font-bold text-teal">{activeCount}</p>
          <p className="text-xs text-gray-500 mt-0.5">Attivi</p>
        </div>
        <div className="bg-red-50 rounded-xl p-4">
          <p className="text-2xl font-bold text-red-500">{lockedCount}</p>
          <p className="text-xs text-gray-500 mt-0.5">Bloccati</p>
        </div>
      </div>

      {/* Header row */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-base font-semibold text-gray-800">
          Gestione Utenti
          <span className="ml-2 text-xs font-normal text-gray-400">{adminCount} admin · {users.length - adminCount} clinici</span>
        </h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            showForm
              ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              : 'bg-teal text-white hover:bg-teal-dark'
          }`}
        >
          {showForm ? '✕ Annulla' : '+ Nuovo utente'}
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <form onSubmit={handleCreate} className="mb-6 p-5 border border-gray-200 rounded-2xl bg-gray-50 space-y-4">
          <h3 className="font-semibold text-gray-700 text-sm">Nuovo utente</h3>
          {formError && (
            <p className="text-red-600 text-sm bg-red-50 border border-red-100 rounded-lg px-3 py-2">{formError}</p>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Username *</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal"
                value={form.username}
                onChange={e => setForm({ ...form, username: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Nome completo *</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal"
                value={form.full_name}
                onChange={e => setForm({ ...form, full_name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Password (min. 12 car.) *</label>
              <input
                type="password"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal"
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Qualifica</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal"
                value={form.designation}
                onChange={e => setForm({ ...form, designation: e.target.value })}
                placeholder="es. Infermiere, Medico..."
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Ruolo *</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal bg-white"
                value={form.role}
                onChange={e => setForm({ ...form, role: e.target.value })}
              >
                <option value="nurse">Infermiere</option>
                <option value="doctor">Medico</option>
                <option value="admin">Amministratore</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={formLoading}
              className="px-5 py-2 bg-teal text-white rounded-lg text-sm font-medium hover:bg-teal-dark disabled:opacity-50 transition-colors"
            >
              {formLoading ? 'Creazione...' : 'Crea utente'}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-5 py-2 bg-white border border-gray-200 text-gray-600 rounded-lg text-sm hover:bg-gray-50 transition-colors"
            >
              Annulla
            </button>
          </div>
        </form>
      )}

      {/* Users table */}
      <div className="overflow-x-auto rounded-xl border border-gray-100">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-left text-gray-500 text-xs uppercase tracking-wide">
              <th className="px-4 py-3 font-medium">Username</th>
              <th className="px-4 py-3 font-medium">Nome</th>
              <th className="px-4 py-3 font-medium">Qualifica</th>
              <th className="px-4 py-3 font-medium">Ruolo</th>
              <th className="px-4 py-3 font-medium">Stato</th>
              <th className="px-4 py-3 font-medium">Azioni</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {users.map(u => (
              <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 font-medium text-navy">{u.username}</td>
                <td className="px-4 py-3 text-gray-700">{u.full_name}</td>
                <td className="px-4 py-3 text-gray-500">{u.designation || '—'}</td>
                <td className="px-4 py-3">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                    ROLE_BADGE_CLASSES[u.role] || 'bg-gray-100 text-gray-600'
                  }`}>
                    {ROLE_LABELS[u.role] || u.role}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {u.is_locked ? (
                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-600">Bloccato</span>
                  ) : u.is_active ? (
                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">Attivo</span>
                  ) : (
                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500">Disabilitato</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    {u.is_locked && (
                      <button
                        onClick={() => handleAction(u.id, 'unlock')}
                        className="text-xs font-medium text-orange-600 hover:text-orange-700"
                      >
                        Sblocca
                      </button>
                    )}
                    {u.is_active ? (
                      <button
                        onClick={() => handleAction(u.id, 'disable')}
                        className="text-xs font-medium text-red-500 hover:text-red-700"
                      >
                        Disabilita
                      </button>
                    ) : (
                      <button
                        onClick={() => handleAction(u.id, 'enable')}
                        className="text-xs font-medium text-teal hover:text-teal-dark"
                      >
                        Abilita
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {users.length === 0 && (
          <p className="text-center text-gray-400 text-sm py-10">Nessun utente trovato.</p>
        )}
      </div>
    </div>
  );
}

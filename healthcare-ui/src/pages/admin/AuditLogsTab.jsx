import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { getAuditLogsApi } from '../../services/authApi';

const ACTION_STYLES = {
  chat_query:       'bg-blue-100 text-blue-700',
  login:            'bg-green-100 text-green-700',
  logout:           'bg-gray-100 text-gray-600',
  account_locked:   'bg-red-100 text-red-600',
  user_created:     'bg-teal/10 text-teal',
  user_disabled:    'bg-orange-100 text-orange-700',
  user_enabled:     'bg-green-100 text-green-700',
  user_unlocked:    'bg-yellow-100 text-yellow-700',
  password_changed: 'bg-purple-100 text-purple-700',
};

export default function AuditLogsTab() {
  const { accessToken } = useAuth();
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ username: '', action: '', fiscal_code: '' });
  const [loading, setLoading] = useState(true);

  async function loadLogs() {
    setLoading(true);
    try {
      const params = { page, page_size: 50 };
      if (filters.username) params.username = filters.username;
      if (filters.action) params.action = filters.action;
      if (filters.fiscal_code) params.fiscal_code = filters.fiscal_code;
      const data = await getAuditLogsApi(params, accessToken);
      setLogs(data.items);
      setTotal(data.total);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadLogs(); }, [page, filters]);

  function formatDate(ts) {
    return new Date(ts).toLocaleString('it-IT', { dateStyle: 'short', timeStyle: 'short' });
  }

  const totalPages = Math.ceil(total / 50);

  return (
    <div>
      {/* Stats */}
      <div className="flex items-center gap-2 mb-5">
        <div className="bg-navy/5 rounded-xl px-5 py-3">
          <span className="text-xl font-bold text-navy">{total}</span>
          <span className="text-xs text-gray-500 ml-2">eventi totali</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-5">
        <input
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-44 focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal"
          placeholder="Filtra per utente..."
          value={filters.username}
          onChange={e => { setFilters({ ...filters, username: e.target.value }); setPage(1); }}
        />
        <input
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-44 focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal"
          placeholder="Codice fiscale..."
          value={filters.fiscal_code}
          onChange={e => { setFilters({ ...filters, fiscal_code: e.target.value }); setPage(1); }}
        />
        <select
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal bg-white"
          value={filters.action}
          onChange={e => { setFilters({ ...filters, action: e.target.value }); setPage(1); }}
        >
          <option value="">Tutte le azioni</option>
          <option value="login">login</option>
          <option value="logout">logout</option>
          <option value="chat_query">chat_query</option>
          <option value="user_created">user_created</option>
          <option value="user_disabled">user_disabled</option>
          <option value="user_enabled">user_enabled</option>
          <option value="user_unlocked">user_unlocked</option>
          <option value="account_locked">account_locked</option>
          <option value="password_changed">password_changed</option>
        </select>
        {(filters.username || filters.action || filters.fiscal_code) && (
          <button
            onClick={() => { setFilters({ username: '', action: '', fiscal_code: '' }); setPage(1); }}
            className="text-xs text-gray-500 hover:text-gray-700 border border-gray-200 px-3 py-2 rounded-lg"
          >
            ✕ Reset
          </button>
        )}
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-16 text-gray-400 text-sm">
          Caricamento log...
        </div>
      ) : (
        <div className="rounded-xl border border-gray-100 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-gray-500 text-xs uppercase tracking-wide">
                <th className="px-4 py-3 font-medium">Data / Ora</th>
                <th className="px-4 py-3 font-medium">Utente</th>
                <th className="px-4 py-3 font-medium">Azione</th>
                <th className="px-4 py-3 font-medium">Cod. Fiscale</th>
                <th className="px-4 py-3 font-medium">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.map(log => (
                <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap text-xs">{formatDate(log.created_at)}</td>
                  <td className="px-4 py-3 font-medium text-navy">{log.username}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${ACTION_STYLES[log.action] || 'bg-gray-100 text-gray-600'}`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{log.fiscal_code || '—'}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{log.ip_address || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {logs.length === 0 && (
            <p className="text-center text-gray-400 text-sm py-10">Nessun evento trovato.</p>
          )}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center gap-2 mt-4 justify-center">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
          >
            ← Prec.
          </button>
          <span className="text-sm text-gray-500 px-2">
            Pagina {page} di {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
          >
            Succ. →
          </button>
        </div>
      )}
    </div>
  );
}

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import UsersTab from './UsersTab';
import AuditLogsTab from './AuditLogsTab';
import { APP_NAME } from '../../constants/branding';

const TABS = [
  { id: 'users', label: 'Utenti' },
  { id: 'audit', label: 'Log Accessi' },
];

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('users');
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-navy to-navy-dark">
      {/* Header — matches AppHeader style */}
      <header className="shrink-0 flex items-center justify-between px-5 py-4 shadow-md animate-fade-in">
        <div>
          <p className="text-xs text-white/50 uppercase tracking-widest font-medium">
            {APP_NAME}
          </p>
          <h1 className="text-white font-bold text-base leading-tight">
            Pannello Amministratore
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-white/60">{user?.fullName}</span>
          <button
            onClick={() => navigate('/chat')}
            className="flex items-center gap-1.5 text-xs text-white/80 hover:text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-full transition-colors active:scale-95"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 12H5M12 5l-7 7 7 7" />
            </svg>
            Chat
          </button>
          <button
            onClick={handleLogout}
            className="w-8 h-8 rounded-full border border-white/40 flex items-center justify-center transition-colors hover:bg-white/10 active:scale-95"
            aria-label="Logout"
            title="Logout"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        </div>
      </header>

      {/* Main card */}
      <div className="flex-1 mt-1 mb-3 mx-3 bg-white rounded-[2rem] overflow-hidden flex flex-col min-h-0 shadow-card-hover animate-slide-up">
        {/* Tab bar */}
        <div className="flex border-b border-gray-100 px-2 shrink-0">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-5 py-4 text-sm font-medium transition-all border-b-2 ${
                activeTab === tab.id
                  ? 'text-teal border-teal'
                  : 'text-gray-400 border-transparent hover:text-gray-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'users' && <UsersTab />}
          {activeTab === 'audit' && <AuditLogsTab />}
        </div>
      </div>
    </div>
  );
}

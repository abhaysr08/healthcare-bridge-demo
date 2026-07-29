import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import HeaderMenu from './HeaderMenu';
import { useAuth } from '../../contexts/AuthContext';
import { APP_NAME } from '../../constants/branding';

export default function AppHeader({ showInfoIcon = false, showBackButton = false }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();
  const { logout } = useAuth();

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <header className="bg-gradient-to-br from-navy to-navy-dark text-white px-4 py-4 flex items-center justify-between relative shrink-0 shadow-md">
      <div className="flex items-center gap-3">
        {showBackButton && (
          <button
            onClick={() => navigate(-1)}
            className="w-8 h-8 rounded-full border border-white/40 flex items-center justify-center transition-colors hover:bg-white/10 active:scale-95"
            aria-label="Back"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 12H5M12 5l-7 7 7 7" />
            </svg>
          </button>
        )}
        <h1 className="text-lg font-bold tracking-wider uppercase">
          {APP_NAME}
        </h1>
      </div>
      <div className="flex items-center gap-3">
        {showInfoIcon && (
          <button className="w-8 h-8 rounded-full border border-white/40 flex items-center justify-center text-sm font-serif italic transition-colors hover:bg-white/10">
            i
          </button>
        )}
        <button
          onClick={handleLogout}
          className="w-8 h-8 rounded-full border border-white/40 flex items-center justify-center transition-colors hover:bg-white/10 active:scale-95"
          aria-label="Logout"
          title="Logout"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
        </button>
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="w-8 h-8 rounded-full border border-white/40 flex items-center justify-center text-xl leading-none transition-colors hover:bg-white/10 active:scale-95"
        >
          &#8942;
        </button>
      </div>
      {menuOpen && <HeaderMenu onClose={() => setMenuOpen(false)} />}
    </header>
  );
}

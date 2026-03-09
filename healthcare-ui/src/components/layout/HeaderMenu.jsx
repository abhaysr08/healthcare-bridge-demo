import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export default function HeaderMenu({ onClose }) {
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const ref = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        onClose();
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  async function handleLogout() {
    onClose();
    await logout();
    navigate('/login');
  }

  return (
    <div
      ref={ref}
      className="absolute right-4 top-14 bg-white rounded-lg shadow-lg py-2 w-44 z-50"
    >
      <button
        onClick={() => { onClose(); navigate('/profile'); }}
        className="w-full px-4 py-3 flex items-center gap-3 text-gray-700 hover:bg-gray-50 text-sm"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
        <span>Profilo</span>
      </button>

      {user?.role === 'admin' && (
        <button
          onClick={() => { onClose(); navigate('/admin'); }}
          className="w-full px-4 py-3 flex items-center gap-3 text-gray-700 hover:bg-gray-50 text-sm"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
          </svg>
          <span>Pannello Admin</span>
        </button>
      )}

      <button
        onClick={handleLogout}
        className="w-full px-4 py-3 flex items-center gap-3 text-red-500 hover:bg-gray-50 text-sm"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
        <span>Esci</span>
      </button>
    </div>
  );
}

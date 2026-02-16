import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

export default function HeaderMenu({ onClose }) {
  const navigate = useNavigate();
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

  return (
    <div
      ref={ref}
      className="absolute right-4 top-14 bg-white rounded-lg shadow-lg py-2 w-44 z-50"
    >
      <button
        onClick={() => {
          onClose();
          navigate('/profile');
        }}
        className="w-full px-4 py-3 flex items-center gap-3 text-gray-700 hover:bg-gray-50 text-sm"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
        <span>Profile</span>
      </button>
    </div>
  );
}

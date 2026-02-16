import { useState } from 'react';
import HeaderMenu from './HeaderMenu';

export default function AppHeader({ showInfoIcon = false }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="bg-navy text-white px-4 py-4 flex items-center justify-between relative shrink-0">
      <h1 className="text-lg font-bold tracking-wider uppercase">
        Healthbridge Care
      </h1>
      <div className="flex items-center gap-3">
        {showInfoIcon && (
          <button className="w-8 h-8 rounded-full border border-white/40 flex items-center justify-center text-sm font-serif italic">
            i
          </button>
        )}
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="w-8 h-8 rounded-full border border-white/40 flex items-center justify-center text-xl leading-none"
        >
          &#8942;
        </button>
      </div>
      {menuOpen && <HeaderMenu onClose={() => setMenuOpen(false)} />}
    </header>
  );
}

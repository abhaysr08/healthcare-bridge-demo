import { useState, useRef } from 'react';
import AppHeader from '../components/layout/AppHeader';
import { useAuth } from '../contexts/AuthContext';
import avatarImg from '../assets/avatar-nurse.svg';

export default function ProfilePage() {
  const { user } = useAuth();
  const [profilePic, setProfilePic] = useState(null);
  const fileInputRef = useRef(null);

  const roleLabel = user?.role === 'admin' ? 'Amministratore' : 'Operatore';
  const roleBadgeClass = user?.role === 'admin'
    ? 'bg-teal/10 text-teal border border-teal/20'
    : 'bg-navy/10 text-navy border border-navy/20';

  const infoRows = [
    { label: 'Nome Completo', value: user?.fullName },
    { label: 'Qualifica', value: user?.designation },
    { label: 'Username', value: user?.username },
  ];

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setProfilePic(ev.target.result);
    reader.readAsDataURL(file);
  };

  return (
    <div className="h-screen flex flex-col bg-navy">
      <AppHeader />

      <div className="flex-1 mt-1 mb-3 mx-3 bg-white rounded-[2rem] overflow-hidden relative">
        {/* Avatar + name */}
        <div className="flex flex-col items-center pt-6 pb-4">
          <img
            src={profilePic || avatarImg}
            alt="Profile"
            className="w-24 h-24 rounded-full mb-3 object-cover border-4 border-white shadow-lg"
          />
          <h2 className="text-xl font-semibold text-navy mb-1">
            {user?.fullName}
          </h2>
          <p className="text-sm text-gray-500 mb-2">{user?.designation}</p>
          <span className={`text-xs font-medium px-3 py-1 rounded-full ${roleBadgeClass}`}>
            {roleLabel}
          </span>
        </div>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleFileChange}
        />

        {/* Change Profile button */}
        <div className="flex justify-center mb-6">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-2 border border-navy/20 rounded-full px-6 py-2 text-sm text-navy hover:bg-gray-50 transition-colors"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            <span>Change Profile</span>
          </button>
        </div>

        {/* Personal Information */}
        <div className="max-w-md mx-auto px-6 pb-6">
          <h3 className="text-base font-semibold text-text-primary mb-4">
            Personal Information
          </h3>
          <div className="space-y-4">
            {infoRows.map(({ label, value }) => (
              <div key={label} className="grid grid-cols-[120px_1fr] gap-4">
                <span className="text-sm font-medium text-navy">{label}</span>
                <span className="text-sm text-text-primary">{value || '---'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

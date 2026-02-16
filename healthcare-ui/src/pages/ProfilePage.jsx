import AppHeader from '../components/layout/AppHeader';
import avatarImg from '../assets/avatar-nurse.svg';

export default function ProfilePage() {
  // Hardcoded user data
  const user = {
    fullName: 'Elisa Rossi',
    designation: 'Home Care Nurse',
    email: 'elisa@healthbridge.it',
    contact: '+39 02 7654321',
  };

  const infoRows = [
    { label: 'Full Name', value: user.fullName },
    { label: 'Designation', value: user.designation },
    { label: 'Email', value: user.email },
    { label: 'Contact', value: user.contact },
  ];

  return (
    <div className="h-screen flex flex-col bg-navy">
      <AppHeader />

      {/* White rounded card with avatar overlapping */}
      <div className="flex-1 mt-1 mb-3 mx-3 bg-white rounded-[2rem] overflow-hidden relative">
        {/* Avatar positioned at top, overlapping the navy */}
        <div className="flex flex-col items-center pt-6 pb-4">
          <img
            src={avatarImg}
            alt="Profile"
            className="w-24 h-24 rounded-full mb-3 object-cover border-4 border-white shadow-lg"
          />
          <h2 className="text-xl font-semibold text-navy mb-1">
            {user.fullName}
          </h2>
          <p className="text-sm text-gray-500">{user.designation}</p>
        </div>

        {/* Change Profile button */}
        <div className="flex justify-center mb-6">
          <button className="flex items-center gap-2 border border-navy/20 rounded-full px-6 py-2 text-sm text-navy hover:bg-gray-50 transition-colors">
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
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            <span>Change Profile</span>
          </button>
        </div>

        {/* Personal Information */}
        <div className="px-6 pb-6">
          <h3 className="text-base font-semibold text-text-primary mb-4">
            Personal Information
          </h3>
          <div className="space-y-4">
            {infoRows.map(({ label, value }) => (
              <div key={label} className="grid grid-cols-[120px_1fr] gap-4">
                <span className="text-sm font-medium text-navy">
                  {label}
                </span>
                <span className="text-sm text-text-primary">{value || '---'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AppHeader from '../components/layout/AppHeader';
import Sparkline from '../components/ui/Sparkline';
import { useAuth } from '../contexts/AuthContext';
import { getDoctorDashboardApi } from '../services/authApi';

function StatTile({ label, value, tone = 'navy' }) {
  const toneClasses = {
    navy: 'bg-navy/5 text-navy',
    error: 'bg-error/10 text-error',
    teal: 'bg-teal/10 text-teal',
  };
  return (
    <div className={`rounded-2xl p-4 ${toneClasses[tone]} animate-slide-up`}>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs opacity-70 mt-0.5">{label}</p>
    </div>
  );
}

export default function DoctorDashboardPage() {
  const { user, accessToken } = useAuth();
  const navigate = useNavigate();
  const [patients, setPatients] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    getDoctorDashboardApi(accessToken)
      .then((data) => { if (!cancelled) setPatients(data.patients); })
      .catch(() => { if (!cancelled) setError('Impossibile caricare i pazienti.'); });
    return () => { cancelled = true; };
  }, [accessToken]);

  const withEscalations = patients?.filter((p) => p.escalations.length > 0).length ?? 0;
  const totalEscalations = patients?.reduce((sum, p) => sum + p.escalations.length, 0) ?? 0;

  return (
    <div className="h-screen flex flex-col bg-chat-bg">
      <AppHeader />

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-5">
          <div className="animate-fade-in mb-5">
            <h2 className="text-xl font-semibold text-navy">
              Welcome, {user?.fullName}
            </h2>
            <p className="text-sm text-gray-500">Clinical picture of your patients</p>
          </div>

          {patients && (
            <div className="grid grid-cols-3 gap-3 mb-6">
              <StatTile label="Total patients" value={patients.length} tone="navy" />
              <StatTile label="With escalations" value={withEscalations} tone="error" />
              <StatTile label="Open escalations" value={totalEscalations} tone="teal" />
            </div>
          )}

          <div className="space-y-3">
            {error && <p className="text-error text-sm">{error}</p>}

            {!patients && !error && (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-24 rounded-2xl bg-white/60 animate-pulse" />
                ))}
              </div>
            )}

            {patients?.length === 0 && (
              <p className="text-sm text-gray-500">No patients assigned.</p>
            )}

            {patients?.map((p, i) => (
              <button
                key={p.patient_id}
                onClick={() => navigate(`/patient/${p.patient_id}`)}
                style={{ animationDelay: `${i * 40}ms` }}
                className="w-full text-left bg-white border border-gray-100 rounded-2xl p-4 shadow-card hover:shadow-card-hover hover:-translate-y-0.5 active:scale-[0.99] transition-all animate-slide-up"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-navy">{p.full_name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{p.conditions.join(', ')}</p>
                    <p className="text-xs text-gray-400 mt-1">Nurse: {p.assigned_nurse}</p>
                  </div>
                  {p.escalations.length > 0 && (
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-error/10 text-error border border-error/20 shrink-0">
                      {p.escalations.length} escalation{p.escalations.length > 1 ? 's' : ''}
                    </span>
                  )}
                </div>

                {p.escalations.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {p.escalations.map((e, idx) => (
                      <p key={idx} className="text-xs text-error">
                        {e.date}: {e.message}
                      </p>
                    ))}
                  </div>
                )}

                <div className="flex items-center justify-between mt-3">
                  {p.latest_vitals_summary && (
                    <p className="text-xs text-gray-500">
                      Latest ({p.latest_vitals_summary.date}): BP {p.latest_vitals_summary.blood_pressure},
                      {' '}glucose {p.latest_vitals_summary.glucose ?? 'n/a'}, weight {p.latest_vitals_summary.weight_kg}kg
                    </p>
                  )}
                  {p.vitals_history?.length > 1 && (
                    <Sparkline
                      values={p.vitals_history.map((v) => v.weight_kg)}
                      color="#225884"
                    />
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

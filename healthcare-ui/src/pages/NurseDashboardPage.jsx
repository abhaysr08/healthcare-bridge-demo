import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AppHeader from '../components/layout/AppHeader';
import Sparkline from '../components/ui/Sparkline';
import { useAuth } from '../contexts/AuthContext';
import { getNurseDashboardApi } from '../services/authApi';

function StatTile({ label, value, tone = 'navy' }) {
  const toneClasses = {
    navy: 'bg-navy/5 text-navy',
    error: 'bg-error/10 text-error',
    warning: 'bg-warning/10 text-warning',
    teal: 'bg-teal/10 text-teal',
  };
  return (
    <div className={`rounded-2xl p-4 ${toneClasses[tone]} animate-slide-up`}>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs opacity-70 mt-0.5">{label}</p>
    </div>
  );
}

export default function NurseDashboardPage() {
  const { user, accessToken } = useAuth();
  const navigate = useNavigate();
  const [roster, setRoster] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    getNurseDashboardApi(accessToken)
      .then((data) => { if (!cancelled) setRoster(data.roster); })
      .catch(() => { if (!cancelled) setError('Impossibile caricare i pazienti.'); });
    return () => { cancelled = true; };
  }, [accessToken]);

  const needAttention = roster?.filter((p) => p.unresolved_alert_count > 0).length ?? 0;
  const adherenceIssues = roster?.filter((p) => p.adherence_flag).length ?? 0;

  return (
    <div className="h-screen flex flex-col bg-chat-bg">
      <AppHeader />

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-5">
          <div className="animate-fade-in mb-5">
            <h2 className="text-xl font-semibold text-navy">
              Welcome, {user?.fullName}
            </h2>
            <p className="text-sm text-gray-500">Your patients in home care</p>
          </div>

          {roster && (
            <div className="grid grid-cols-3 gap-3 mb-6">
              <StatTile label="Total patients" value={roster.length} tone="navy" />
              <StatTile label="Need attention" value={needAttention} tone="error" />
              <StatTile label="Adherence flags" value={adherenceIssues} tone="warning" />
            </div>
          )}

          <div className="space-y-3">
            {error && <p className="text-error text-sm">{error}</p>}

            {!roster && !error && (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-24 rounded-2xl bg-white/60 animate-pulse" />
                ))}
              </div>
            )}

            {roster?.length === 0 && (
              <p className="text-sm text-gray-500">No patients assigned.</p>
            )}

            {roster?.map((p, i) => (
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
                    <p className="text-xs text-gray-400 mt-1">Doctor: {p.assigned_doctor}</p>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    {p.unresolved_alert_count > 0 && (
                      <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-error/10 text-error border border-error/20">
                        {p.unresolved_alert_count} alert{p.unresolved_alert_count > 1 ? 's' : ''}
                      </span>
                    )}
                    {p.adherence_flag && (
                      <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-warning/10 text-warning border border-warning/20">
                        Adherence review
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center justify-between mt-3">
                  {p.latest_vitals_summary && (
                    <p className="text-xs text-gray-500">
                      Latest ({p.latest_vitals_summary.date}): BP {p.latest_vitals_summary.blood_pressure},
                      {' '}HR {p.latest_vitals_summary.heart_rate}, SpO2 {p.latest_vitals_summary.spo2}%
                    </p>
                  )}
                  {p.vitals_history?.length > 1 && (
                    <Sparkline
                      values={p.vitals_history.map((v) => v.heart_rate)}
                      color="#0d9488"
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

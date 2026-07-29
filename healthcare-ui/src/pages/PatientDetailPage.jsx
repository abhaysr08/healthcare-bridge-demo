import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import AppHeader from '../components/layout/AppHeader';
import { useAuth } from '../contexts/AuthContext';
import { getPatientApi } from '../services/authApi';

const SEVERITY_STYLES = {
  high: 'bg-error/10 text-error border-error/20',
  medium: 'bg-warning/10 text-warning border-warning/20',
  low: 'bg-navy/10 text-navy border-navy/20',
};

function StatTile({ label, value, unit, trend }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-4 animate-slide-up">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-xl font-semibold text-navy mt-1">
        {value ?? '—'}{unit && value != null ? <span className="text-sm font-normal text-gray-400 ml-1">{unit}</span> : null}
      </p>
      {trend && (
        <p className={`text-xs mt-1 ${trend.direction === 'up' ? 'text-error' : trend.direction === 'down' ? 'text-teal' : 'text-gray-400'}`}>
          {trend.direction === 'up' ? '↑' : trend.direction === 'down' ? '↓' : '→'} {trend.label}
        </p>
      )}
    </div>
  );
}

function TrendCard({ title, dataKey, data, unit, color = '#225884' }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-4 animate-slide-up">
      <h3 className="text-sm font-semibold text-navy mb-2">{title}</h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eef1f5" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(d) => d?.slice(5)} />
            <YAxis tick={{ fontSize: 11 }} unit={unit} />
            <Tooltip
              contentStyle={{ borderRadius: 12, border: '1px solid #e5e7eb', fontSize: 12 }}
              labelFormatter={(d) => `Date: ${d}`}
            />
            <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={{ r: 3 }} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function numericTrend(history, key) {
  const values = history.map((v) => v[key]).filter((v) => v != null);
  if (values.length < 2) return null;
  const [first, last] = [values[0], values[values.length - 1]];
  if (last === first) return { direction: 'flat', label: 'stable' };
  return {
    direction: last > first ? 'up' : 'down',
    label: `${last > first ? '+' : ''}${(last - first).toFixed(1)} since first reading`,
  };
}

export default function PatientDetailPage() {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const { accessToken } = useAuth();
  const [patient, setPatient] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    getPatientApi(patientId, accessToken)
      .then((data) => { if (!cancelled) setPatient(data); })
      .catch(() => { if (!cancelled) setError('Unable to load patient details.'); });
    return () => { cancelled = true; };
  }, [patientId, accessToken]);

  const vitals = patient?.vitals_history || [];
  const latest = vitals[vitals.length - 1];
  const bpData = vitals.map((v) => {
    const [systolic, diastolic] = (v.blood_pressure || '').split('/').map(Number);
    return { date: v.date, systolic, diastolic };
  });

  return (
    <div className="h-screen flex flex-col bg-chat-bg">
      <AppHeader />

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-5">
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-navy/70 hover:text-navy mb-4 flex items-center gap-1 transition-colors"
          >
            ← Back
          </button>

          {error && <p className="text-error text-sm">{error}</p>}

          {!patient && !error && (
            <div className="space-y-3">
              <div className="h-24 rounded-2xl bg-white/60 animate-pulse" />
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[1, 2, 3, 4].map((i) => <div key={i} className="h-20 rounded-2xl bg-white/60 animate-pulse" />)}
              </div>
            </div>
          )}

          {patient && (
            <div className="space-y-6">
              {/* Header strip */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5 animate-fade-in">
                <div className="flex items-start justify-between gap-3">
                  <h1 className="text-2xl font-semibold text-navy">{patient.full_name}</h1>
                  <button
                    onClick={() => navigate('/chat', { state: { prefill: `Tell me about ${patient.full_name}` } })}
                    className="shrink-0 flex items-center gap-2 bg-teal text-white text-sm font-medium px-4 py-2 rounded-full hover:bg-teal-dark hover:shadow-lg active:scale-95 transition-all"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
                    </svg>
                    Ask about this patient
                  </button>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {(patient.conditions || []).map((c) => (
                    <span key={c} className="text-xs font-medium px-2.5 py-1 rounded-full bg-teal/10 text-teal border border-teal/20">
                      {c}
                    </span>
                  ))}
                </div>
                <div className="flex flex-wrap gap-x-6 gap-y-1 mt-3 text-sm text-gray-500">
                  <span>Nurse: <span className="text-gray-700 font-medium">{patient.assigned_nurse}</span></span>
                  <span>Doctor: <span className="text-gray-700 font-medium">{patient.assigned_doctor}</span></span>
                  {patient.date_of_birth && <span>DOB: <span className="text-gray-700 font-medium">{patient.date_of_birth}</span></span>}
                </div>
                {(patient.care_program || patient.enrollment_date) && (
                  <div className="flex flex-wrap gap-x-6 gap-y-1 mt-1 text-sm text-gray-500">
                    {patient.care_program && <span>Program: <span className="text-gray-700 font-medium">{patient.care_program}</span></span>}
                    {patient.enrollment_date && <span>Enrolled: <span className="text-gray-700 font-medium">{patient.enrollment_date}</span></span>}
                  </div>
                )}
                {patient.allergies?.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {patient.allergies.map((a) => (
                      <span key={a} className="text-xs font-medium px-2.5 py-1 rounded-full bg-error/10 text-error border border-error/20">
                        ⚠ Allergy: {a}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Stat tiles */}
              {latest && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <StatTile label="Blood Pressure" value={latest.blood_pressure} trend={null} />
                  <StatTile label="Heart Rate" value={latest.heart_rate} unit="bpm" trend={numericTrend(vitals, 'heart_rate')} />
                  <StatTile label="Glucose" value={latest.glucose} unit="mg/dL" trend={numericTrend(vitals, 'glucose')} />
                  <StatTile label="SpO2" value={latest.spo2} unit="%" trend={numericTrend(vitals, 'spo2')} />
                </div>
              )}

              {/* Trend charts */}
              {vitals.length > 1 && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <TrendCard title="Blood Pressure (systolic)" dataKey="systolic" data={bpData} color="#225884" />
                  <TrendCard title="Glucose (mg/dL)" dataKey="glucose" data={vitals} color="#0d9488" />
                  <TrendCard title="Weight (kg)" dataKey="weight_kg" data={vitals} color="#f59e0b" />
                </div>
              )}

              {/* Contact / emergency contact / insurance */}
              {(patient.contact || patient.emergency_contact || patient.insurance) && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {patient.contact && (
                    <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-4 animate-slide-up">
                      <h3 className="text-sm font-semibold text-navy mb-2">Contact</h3>
                      <p className="text-xs text-gray-600">{patient.contact.phone}</p>
                      <p className="text-xs text-gray-600 mt-0.5">{patient.contact.email}</p>
                      <p className="text-xs text-gray-600 mt-0.5">{patient.contact.address}</p>
                    </div>
                  )}
                  {patient.emergency_contact && (
                    <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-4 animate-slide-up">
                      <h3 className="text-sm font-semibold text-navy mb-2">Emergency Contact</h3>
                      <p className="text-xs text-gray-600">{patient.emergency_contact.name} ({patient.emergency_contact.relationship})</p>
                      <p className="text-xs text-gray-600 mt-0.5">{patient.emergency_contact.phone}</p>
                    </div>
                  )}
                  {patient.insurance && (
                    <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-4 animate-slide-up">
                      <h3 className="text-sm font-semibold text-navy mb-2">Insurance</h3>
                      <p className="text-xs text-gray-600">{patient.insurance.provider}</p>
                      <p className="text-xs text-gray-600 mt-0.5">Policy: {patient.insurance.policy_number}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Lab results */}
              {patient.labs?.length > 0 && (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5 animate-slide-up">
                  <h3 className="text-sm font-semibold text-navy mb-3">Lab Results</h3>
                  <div className="space-y-2">
                    {[...patient.labs].reverse().map((lab, i) => (
                      <div key={i} className="flex items-center justify-between text-sm border-b border-gray-50 last:border-0 pb-2 last:pb-0">
                        <span className="text-gray-700">{lab.test}</span>
                        <span className="text-gray-500 text-xs">{lab.date}</span>
                        <span className="font-medium text-navy">{lab.value} {lab.unit}</span>
                        <span className="text-xs text-gray-400">ref: {lab.reference_range}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Care plan */}
              {patient.care_plan && (patient.care_plan.goals?.length > 0 || patient.care_plan.next_appointment) && (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5 animate-slide-up">
                  <h3 className="text-sm font-semibold text-navy mb-3">Care Plan</h3>
                  {patient.care_plan.goals?.length > 0 && (
                    <ul className="space-y-1.5 mb-3">
                      {patient.care_plan.goals.map((goal, i) => (
                        <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                          <span className="text-teal mt-0.5">●</span>
                          <span>{goal}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {patient.care_plan.next_appointment && (
                    <p className="text-xs text-gray-500">
                      Next appointment: <span className="text-gray-700 font-medium">{patient.care_plan.next_appointment}</span>
                    </p>
                  )}
                </div>
              )}

              {/* Medications */}
              {patient.medications?.length > 0 && (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5 animate-slide-up">
                  <h3 className="text-sm font-semibold text-navy mb-3">Medications</h3>
                  <div className="space-y-3">
                    {patient.medications.map((med, i) => (
                      <div key={i} className="border-b border-gray-50 last:border-0 pb-3 last:pb-0">
                        <p className="text-sm font-medium text-gray-800">{med.name} — {med.dose} ({med.frequency})</p>
                        <p className="text-xs text-gray-500 mt-0.5">{med.adherence_notes}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Alerts timeline */}
              {patient.alerts?.length > 0 && (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5 animate-slide-up">
                  <h3 className="text-sm font-semibold text-navy mb-3">Alerts</h3>
                  <div className="space-y-2">
                    {[...patient.alerts].reverse().map((a, i) => (
                      <div
                        key={i}
                        className={`flex items-start gap-3 rounded-xl border px-3 py-2 text-sm ${SEVERITY_STYLES[a.severity] || SEVERITY_STYLES.low}`}
                      >
                        <span className="font-medium shrink-0">{a.date}</span>
                        <span className="flex-1">{a.message}</span>
                        <span className="text-xs font-semibold shrink-0">{a.resolved ? 'RESOLVED' : 'OPEN'}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Visit history */}
              {patient.visit_history?.length > 0 && (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5 animate-slide-up mb-6">
                  <h3 className="text-sm font-semibold text-navy mb-3">Visit History</h3>
                  <div className="space-y-3">
                    {[...patient.visit_history].reverse().map((v, i) => (
                      <div key={i} className="border-b border-gray-50 last:border-0 pb-3 last:pb-0">
                        <p className="text-sm font-medium text-gray-800">{v.date} — {v.type}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{v.summary}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

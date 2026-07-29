import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // needed for httpOnly refresh cookie
});

// Called once from AuthProvider to wire up session-expiry redirect.
// On any 401 (expired/invalid token): clear local state + go to /login.
let _interceptorId = null;
export function setupInterceptors(onUnauthorized) {
  if (_interceptorId !== null) api.interceptors.response.eject(_interceptorId);
  _interceptorId = api.interceptors.response.use(
    (res) => res,
    (err) => {
      if (err.response?.status === 401) {
        // Skip interceptor for auth endpoints themselves (login/refresh)
        const url = err.config?.url || '';
        if (!url.includes('/auth/login') && !url.includes('/auth/refresh')) {
          onUnauthorized();
        }
      }
      return Promise.reject(err);
    }
  );
}

export async function loginApi(username, password) {
  const res = await api.post('/auth/login', { username, password });
  return res.data;
}

export async function refreshTokenApi() {
  const res = await api.post('/auth/refresh');
  return res.data;
}

export async function logoutApi(token) {
  await api.post('/auth/logout', {}, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getMeApi(token) {
  const res = await api.get('/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

export async function changePasswordApi(currentPassword, newPassword, token) {
  await api.post(
    '/auth/change-password',
    { current_password: currentPassword, new_password: newPassword },
    { headers: { Authorization: `Bearer ${token}` } }
  );
}

// Admin APIs
export async function listUsersApi(token) {
  const res = await api.get('/admin/users', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

export async function createUserApi(data, token) {
  const res = await api.post('/admin/users', data, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

export async function disableUserApi(id, token) {
  await api.patch(`/admin/users/${id}/disable`, {}, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function enableUserApi(id, token) {
  await api.patch(`/admin/users/${id}/enable`, {}, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function unlockUserApi(id, token) {
  await api.patch(`/admin/users/${id}/unlock`, {}, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getAuditLogsApi(params, token) {
  const res = await api.get('/admin/audit-logs', {
    params,
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

// Dashboard APIs
export async function getNurseDashboardApi(token) {
  const res = await api.get('/dashboard/nurse', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

export async function getDoctorDashboardApi(token) {
  const res = await api.get('/dashboard/doctor', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

export async function getPatientApi(patientId, token) {
  const res = await api.get(`/patients/${patientId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

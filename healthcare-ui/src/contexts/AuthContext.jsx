import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { loginApi, logoutApi, refreshTokenApi, changePasswordApi, setupInterceptors } from '../services/authApi';

const AuthContext = createContext(null);

// Normalize snake_case API user to camelCase for consistent frontend use
function normalizeUser(apiUser) {
  if (!apiUser) return null;
  return {
    id: apiUser.id,
    username: apiUser.username,
    fullName: apiUser.full_name,
    designation: apiUser.designation,
    role: apiUser.role,
  };
}

const INACTIVITY_TIMEOUT = (import.meta.env.VITE_INACTIVITY_TIMEOUT_MINUTES
  ? parseInt(import.meta.env.VITE_INACTIVITY_TIMEOUT_MINUTES)
  : 15) * 60 * 1000;

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const [mustChangePassword, setMustChangePassword] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const inactivityTimer = useRef(null);

  const doLogout = useCallback(async (token) => {
    try { await logoutApi(token); } catch { /* ignore */ }
    setUser(null);
    setAccessToken(null);
    setMustChangePassword(false);
    localStorage.removeItem('hb_user');
  }, []);

  // Intercept 401 responses globally — redirect to login on expired token
  useEffect(() => {
    setupInterceptors(() => {
      setUser(null);
      setAccessToken(null);
      setMustChangePassword(false);
      localStorage.removeItem('hb_user');
    });
  }, []);

  // Reset inactivity timer on user activity
  const resetTimer = useCallback((token) => {
    if (inactivityTimer.current) clearTimeout(inactivityTimer.current);
    inactivityTimer.current = setTimeout(() => doLogout(token), INACTIVITY_TIMEOUT);
  }, [doLogout]);

  // Attach activity listeners when logged in
  useEffect(() => {
    if (!user) return;
    const events = ['mousedown', 'keydown', 'touchstart', 'scroll'];
    const handler = () => resetTimer(accessToken);
    events.forEach(e => window.addEventListener(e, handler));
    resetTimer(accessToken); // start timer on login
    return () => {
      events.forEach(e => window.removeEventListener(e, handler));
      if (inactivityTimer.current) clearTimeout(inactivityTimer.current);
    };
  }, [user, accessToken, resetTimer]);

  // On mount: try to restore session via refresh token cookie
  useEffect(() => {
    async function restoreSession() {
      try {
        const data = await refreshTokenApi();
        const normalizedUser = normalizeUser(data.user);
        setAccessToken(data.access_token);
        setUser(normalizedUser);
        setMustChangePassword(data.must_change_password);
        localStorage.setItem('hb_user', JSON.stringify(normalizedUser));
      } catch {
        localStorage.removeItem('hb_user');
        setUser(null);
        setAccessToken(null);
      } finally {
        setIsLoading(false);
      }
    }
    restoreSession();
  }, []);

  const login = useCallback(async (username, password) => {
    const data = await loginApi(username, password);
    const normalizedUser = normalizeUser(data.user);
    setAccessToken(data.access_token);
    setUser(normalizedUser);
    setMustChangePassword(data.must_change_password);
    localStorage.setItem('hb_user', JSON.stringify(normalizedUser));
    return { success: true, mustChangePassword: data.must_change_password, role: normalizedUser.role };
  }, []);

  const logout = useCallback(async () => {
    if (inactivityTimer.current) clearTimeout(inactivityTimer.current);
    await doLogout(accessToken);
  }, [accessToken, doLogout]);

  const changePassword = useCallback(async (currentPassword, newPassword) => {
    await changePasswordApi(currentPassword, newPassword, accessToken);
    setMustChangePassword(false);
  }, [accessToken]);

  return (
    <AuthContext.Provider value={{
      user,
      accessToken,
      isAuthenticated: !!user,
      isLoading,
      mustChangePassword,
      login,
      logout,
      changePassword,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

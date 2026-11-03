import { createContext, useContext, useEffect, useState } from 'react';
import { loginUser, getMe } from './api';

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('access'));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!localStorage.getItem('access'));

  useEffect(() => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    if (user) return;
    getMe(token)
      .then(setUser)
      .catch(logout)
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function login(email, password) {
    const data = await loginUser({ email, password });
    const me = await getMe(data.access);
    localStorage.setItem('access', data.access);
    setUser(me);
    setToken(data.access);
  }

  function logout() {
    localStorage.removeItem('access');
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ token, user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
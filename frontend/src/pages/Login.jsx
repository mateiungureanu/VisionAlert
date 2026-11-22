import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import AuthLayout from '../components/AuthLayout';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (!identifier.trim()) {
      setError('Introdu username-ul sau adresa de email.');
      return;
    }
    if (!password) {
      setError('Introdu parola.');
      return;
    }
    try {
      await login(identifier, password);
      const destination = location.state?.from;
      navigate(destination
        ? `${destination.pathname}${destination.search}${destination.hash}`
        : '/');
    } catch {
      setError('Username/email sau parolă greșită.');
    }
  }

  return (
    <AuthLayout title="Autentificare">
      <form className="auth-form" onSubmit={handleSubmit}>
        <input placeholder="Nume de utilizator sau e-mail" aria-label="Nume de utilizator sau e-mail"
               autoComplete="username" value={identifier}
               onChange={(e) => setIdentifier(e.target.value)} required />
        <input type="password" placeholder="Parolă" aria-label="Parolă"
               autoComplete="current-password" value={password}
               onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="auth-error" role="alert">{error}</p>}
        <button type="submit">Intră în cont</button>
      </form>
      <p className="auth-switch">Nu ai cont? <Link to="/register">Creează unul</Link></p>
    </AuthLayout>
  );
}
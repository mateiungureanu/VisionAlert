import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

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
    <div className="card">
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <input placeholder="Nume de utilizator sau e-mail" value={identifier}
               onChange={(e) => setIdentifier(e.target.value)} required />
        <input type="password" placeholder="Parolă" value={password}
               onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="error">{error}</p>}
        <button type="submit">Intră în cont</button>
      </form>
      <p>Nu ai cont? <Link to="/register">Creează unul</Link></p>
    </div>
  );
}
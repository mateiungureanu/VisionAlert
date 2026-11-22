import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { registerUser, formatErrors } from '../api';
import AuthLayout from '../components/AuthLayout';

const PASSWORD_RE = /^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,64}$/;

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    first_name: '', last_name: '', username: '', email: '', phone: '', password: '', confirm: '',
  });
  const [error, setError] = useState('');

  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (!PASSWORD_RE.test(form.password)) {
      return setError('Parola: 8-64 caractere, o literă mare, o cifră și un caracter special.');
    }
    if (form.password !== form.confirm) return setError('Parolele nu coincid.');

    const { confirm, ...payload } = form;
    if (!payload.phone) delete payload.phone;
    try {
      await registerUser(payload);
      navigate('/login');
    } catch (err) {
      setError(formatErrors(err));
    }
  }

  return (
    <AuthLayout title="Creează cont" wide>
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="auth-row">
          <input name="first_name" placeholder="Prenume" aria-label="Prenume" autoComplete="given-name" onChange={change} required />
          <input name="last_name" placeholder="Nume" aria-label="Nume" autoComplete="family-name" onChange={change} required />
        </div>
        <input name="username" placeholder="Nume de utilizator" aria-label="Nume de utilizator" autoComplete="username" onChange={change} required />
        <input name="email" type="email" placeholder="Adresă de e-mail" aria-label="Adresă de e-mail" autoComplete="email" onChange={change} required />
        <input name="phone" placeholder="Număr de telefon (opțional)" aria-label="Număr de telefon (opțional)" autoComplete="tel" onChange={change} />
        <input name="password" type="password" placeholder="Parolă" aria-label="Parolă" autoComplete="new-password" onChange={change} required />
        <input name="confirm" type="password" placeholder="Confirmă parola" aria-label="Confirmă parola" autoComplete="new-password" onChange={change} required />
        {error && <p className="auth-error" role="alert">{error}</p>}
        <button type="submit">Înregistrează-mă</button>
      </form>
      <p className="auth-switch">Ai deja cont? <Link to="/login">Autentifică-te</Link></p>
    </AuthLayout>
  );
}
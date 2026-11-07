import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { registerUser, formatErrors } from '../api';

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
    <div className="card">
      <h2>Creează cont</h2>
      <form onSubmit={handleSubmit}>
        <input name="first_name" placeholder="Prenume" onChange={change} required />
        <input name="last_name" placeholder="Nume" onChange={change} required />
        <input name="username" placeholder="Nume de utilizator" onChange={change} required />
        <input name="email" type="email" placeholder="Adresă de e-mail" onChange={change} required />
        <input name="phone" placeholder="Număr de telefon (opțional)" onChange={change} />
        <input name="password" type="password" placeholder="Parolă" onChange={change} required />
        <input name="confirm" type="password" placeholder="Confirmă parola" onChange={change} required />
        {error && <p className="error" style={{ whiteSpace: 'pre-line' }}>{error}</p>}
        <button type="submit">Înregistrează-mă</button>
      </form>
      <p>Ai deja cont? <Link to="/login">Login</Link></p>
    </div>
  );
}
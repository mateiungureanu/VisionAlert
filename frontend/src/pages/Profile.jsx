import Navbar from '../components/Navbar';
import { useAuth } from '../AuthContext';
import { Link } from 'react-router-dom';

export default function Profile() {
  const { user } = useAuth();
  if (!user) return null;

  const rows = [
    ['Prenume', user.first_name],
    ['Nume', user.last_name],
    ['Username', user.username],
    ['Email', user.email],
    ['Telefon', user.phone || '-'],
    ['Cont creat la', new Date(user.date_joined).toLocaleDateString('ro-RO')],
  ];

  return (
    <>
      <Navbar />
      <div className="card">
        <Link to="/" className="back-link">← Înapoi la Home</Link>
        <h2>Profilul meu</h2>
        <table>
          <tbody>
            {rows.map(([label, value]) => (
              <tr key={label}><th>{label}</th><td>{value}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
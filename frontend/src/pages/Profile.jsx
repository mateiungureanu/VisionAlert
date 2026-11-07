import Navbar from '../components/Navbar';
import { useAuth } from '../AuthContext';
import { Link } from 'react-router-dom';
import { useState } from 'react';

export default function Profile() {
  const { user, deleteAccount } = useAuth();
  const [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [showDeleteControls, setShowDeleteControls] = useState(false);
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
        <section className="danger-zone">
          {showDeleteControls && (
            <>
              <p>Această acțiune șterge datele personale și nu poate fi anulată.</p>
              <p>Scrie <strong>STERGE CONTUL</strong> pentru confirmare:</p>
              <input
                value={confirmation}
                onChange={(e) => setConfirmation(e.target.value)}
                placeholder="STERGE CONTUL"
                aria-label="Confirmare ștergere cont"
              />
              {error && <p className="error">{error}</p>}
            </>
          )}
          <button
            type="button"
            className={`delete-button${
              showDeleteControls && confirmation !== 'STERGE CONTUL'
                ? ' delete-button-confirm'
                : ''
            }`}
            disabled={deleting || (showDeleteControls && confirmation !== 'STERGE CONTUL')}
            onClick={async () => {
              if (!showDeleteControls) {
                setShowDeleteControls(true);
                return;
              }
              setError('');
              setDeleting(true);
              try {
                await deleteAccount();
              } catch {
                setError('Contul nu a putut fi șters. Încearcă din nou.');
                setDeleting(false);
              }
            }}
          >
            {deleting ? 'Se șterge...' : 'Șterge contul'}
          </button>
        </section>
      </div>
    </>
  );
}
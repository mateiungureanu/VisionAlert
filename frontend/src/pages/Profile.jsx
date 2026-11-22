import { useState } from 'react';
import { useAuth } from '../AuthContext';

const DELETE_PHRASE = 'STERGE CONTUL';

export default function Profile() {
  const { user, deleteAccount } = useAuth();
  const [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [showDeleteControls, setShowDeleteControls] = useState(false);
  if (!user) return null;

  const fullName = `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim() || user.username;
  const initials = `${user.first_name?.[0] ?? ''}${user.last_name?.[0] ?? ''}`.toUpperCase()
    || user.username?.[0]?.toUpperCase()
    || '?';
  const memberSince = new Date(user.date_joined).toLocaleDateString('ro-RO', { dateStyle: 'long' });
  const fields = [
    ['Prenume', user.first_name],
    ['Nume', user.last_name],
    ['Nume de utilizator', user.username],
    ['Email', user.email],
    ['Telefon', user.phone || '—'],
  ];
  const confirmed = confirmation === DELETE_PHRASE;

  function cancelDelete() {
    setShowDeleteControls(false);
    setConfirmation('');
    setError('');
  }

  async function handleDelete() {
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
  }

  return (
    <main className="profile-page">
      <header className="profile-hero">
        <span className="profile-avatar" aria-hidden="true">{initials}</span>
        <div>
          <p className="offers-eyebrow">PROFILUL MEU</p>
          <h1>{fullName}</h1>
          <p className="profile-since">Membru din {memberSince}</p>
        </div>
      </header>

      <section className="profile-section" aria-labelledby="profile-info-title">
        <h2 id="profile-info-title">Informații personale</h2>
        <dl className="profile-fields">
          {fields.map(([label, value]) => (
            <div className="profile-field" key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="profile-section profile-danger" aria-labelledby="profile-danger-title">
        <h2 id="profile-danger-title">Ștergerea contului</h2>
        <p className="profile-danger-text">
          Această acțiune șterge datele personale și nu poate fi anulată.
        </p>
        {showDeleteControls && (
          <div className="profile-confirm">
            <label htmlFor="delete-confirmation">
              Scrie <strong>{DELETE_PHRASE}</strong> pentru confirmare:
            </label>
            <input
              id="delete-confirmation"
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
              placeholder={DELETE_PHRASE}
              autoComplete="off"
            />
            {error && <p className="error" role="alert">{error}</p>}
          </div>
        )}
        <div className="profile-actions">
          <button
            type="button"
            className={`profile-delete${showDeleteControls && confirmed ? ' ready' : ''}`}
            disabled={deleting || (showDeleteControls && !confirmed)}
            onClick={handleDelete}
          >
            {deleting ? 'Se șterge...' : 'Șterge contul'}
          </button>
          {showDeleteControls && !deleting && (
            <button type="button" className="profile-cancel" onClick={cancelDelete}>
              Anulează
            </button>
          )}
        </div>
      </section>
    </main>
  );
}

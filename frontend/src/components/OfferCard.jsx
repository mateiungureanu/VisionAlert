import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../AuthContext';
import { addFavoriteOffer, removeFavoriteOffer } from '../api';

function formatDate(value) {
  return new Intl.DateTimeFormat('ro-RO', { dateStyle: 'medium' }).format(new Date(value));
}

function formatPrice(value) {
  return new Intl.NumberFormat('ro-RO', {
    style: 'currency',
    currency: 'RON',
  }).format(Number(value));
}

function formatPercentage(value) {
  return `${new Intl.NumberFormat('ro-RO', {
    maximumFractionDigits: 2,
  }).format(Number(value))}%`;
}

function formatValidity(offer) {
  return `${offer.valid_from ? formatDate(offer.valid_from) : 'început nespecificat'} – ${
    offer.valid_until ? formatDate(offer.valid_until) : 'fără dată de încheiere'
  }`;
}

function ShareOffer({ offer }) {
  const [status, setStatus] = useState('');
  const sourceUrl = offer.source_urls[0];
  const canNativeShare = typeof navigator !== 'undefined' && typeof navigator.share === 'function';

  if (!sourceUrl) return null;

  async function copyLink(event) {
    event.stopPropagation();
    try {
      await navigator.clipboard.writeText(sourceUrl);
    } catch {
      const textarea = document.createElement('textarea');
      textarea.value = sourceUrl;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
    setStatus('Link copiat');
  }

  async function nativeShare(event) {
    event.stopPropagation();
    try {
      await navigator.share({
        title: offer.title,
        text: `${offer.brand} - ${offer.title}`,
        url: sourceUrl,
      });
    } catch (error) {
      if (error?.name !== 'AbortError') setStatus('Distribuirea nu a putut fi finalizată');
    }
  }

  return (
    <span className="offer-share-actions">
      {canNativeShare && (
        <button
          type="button"
          className="offer-share-button"
          onClick={nativeShare}
          aria-label={`Distribuie oferta ${offer.title}`}
        >
          Distribuie
        </button>
      )}
      <button
        type="button"
        className="offer-share-button"
        onClick={copyLink}
        aria-label={`Copiază linkul pentru oferta ${offer.title}`}
      >
        Copiază link
      </button>
      <span className="offer-share-status" role="status" aria-live="polite">{status}</span>
    </span>
  );
}

function isExpired(offer) {
  return Boolean(offer.valid_until) && new Date(offer.valid_until) < new Date();
}

function FavoriteButton({ offer, isFavorite, busy, onToggle }) {
  const label = isFavorite
    ? `Elimină oferta ${offer.title} din favorite`
    : `Salvează oferta ${offer.title} la favorite`;
  return (
    <button
      type="button"
      className={`favorite-heart${isFavorite ? ' active' : ''}`}
      aria-pressed={isFavorite}
      aria-label={label}
      title={isFavorite ? 'Elimină din favorite' : 'Salvează la favorite'}
      disabled={busy}
      onClick={onToggle}
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill={isFavorite ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21.2l7.8-7.7 1-1.1a5.5 5.5 0 0 0 0-7.8z" />
      </svg>
    </button>
  );
}

function OfferPricing({ offer }) {
  const hasPricing =
    offer.price != null ||
    offer.previous_price != null ||
    offer.discount_percentage != null;
  if (!hasPricing) return null;

  return (
    <div className="offer-pricing" aria-label="Preț și reducere">
      {offer.previous_price != null && (
        <span className="offer-price-item">
          <span className="offer-price-label">Preț anterior</span>
          <span className="offer-previous-price">{formatPrice(offer.previous_price)}</span>
        </span>
      )}
      {offer.price != null && (
        <span className="offer-price-item">
          <span className="offer-price-label">Preț nou</span>
          <strong className="offer-current-price">{formatPrice(offer.price)}</strong>
        </span>
      )}
      {offer.discount_percentage != null && (
        <span className="offer-discount">
          Reducere {formatPercentage(offer.discount_percentage)}
        </span>
      )}
    </div>
  );
}

function OfferDetails({ offer, headingId, actions }) {
  return (
    <>
      <div className="offer-card-top">
        <span className="offer-brand">{offer.brand}</span>
        {isExpired(offer) && <span className="offer-expired">Expirată</span>}
        {offer.categories.map((category) => (
          <span className="offer-category-tag" key={category.id}>{category.name}</span>
        ))}
        {actions}
      </div>
      <h2 id={headingId}>{offer.title}</h2>
      <OfferPricing offer={offer} />
      {offer.description && <p className="offer-description">{offer.description}</p>}
      {offer.products.length > 0 && (
        <div className="offer-detail">
          <strong>Produse</strong>
          <ul className="offer-products">
            {offer.products.map((product) => (
              <li key={product}>{product}</li>
            ))}
          </ul>
        </div>
      )}
      {offer.terms && (
        <div className="offer-detail">
          <strong>Condiții</strong>
          <p>{offer.terms}</p>
        </div>
      )}
      {(offer.valid_from || offer.valid_until) && (
        <p className="offer-validity">Valabilitate: {formatValidity(offer)}</p>
      )}
    </>
  );
}

function OfferDialog({ offer, onClose, actions }) {
  const dialogRef = useRef(null);
  const headingId = `offer-dialog-title-${offer.id}`;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) dialog.showModal();
  }, []);

  return createPortal(
    <dialog
      className="offer-dialog"
      ref={dialogRef}
      aria-labelledby={headingId}
      onClose={onClose}
      onClick={(event) => {
        // A click on the backdrop targets the dialog element itself.
        if (event.target === dialogRef.current) dialogRef.current.close();
      }}
    >
      <div className="offer-dialog-content">
        <button
          className="offer-dialog-close"
          type="button"
          aria-label="Închide"
          onClick={() => dialogRef.current?.close()}
        >
          ×
        </button>
        <OfferDetails offer={offer} headingId={headingId} actions={actions} />
        <div className="offer-card-footer">
          <span>Adăugată {formatDate(offer.created_at)}</span>
          <span className="offer-footer-actions">
            {offer.source_urls.map((url) => (
              <a href={url} key={url} target="_blank" rel="noreferrer">
                Vezi oferta <span aria-hidden="true">↗</span>
              </a>
            ))}
            <ShareOffer offer={offer} />
          </span>
        </div>
      </div>
    </dialog>,
    document.body,
  );
}

export default function OfferCard({ offer, onFavoriteChange }) {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [favoriteOverride, setFavoriteOverride] = useState(null);
  const [favoriteBusy, setFavoriteBusy] = useState(false);
  const [favoriteError, setFavoriteError] = useState('');
  const isFavorite = favoriteOverride ?? offer.is_favorite ?? false;

  async function toggleFavorite(event) {
    event.stopPropagation();
    if (favoriteBusy) return;
    const next = !isFavorite;
    setFavoriteError('');
    setFavoriteOverride(next);
    setFavoriteBusy(true);
    try {
      await (next ? addFavoriteOffer : removeFavoriteOffer)(offer.id, token);
      onFavoriteChange?.(offer, next);
    } catch {
      setFavoriteOverride(!next);
      setFavoriteError('Nu am putut actualiza favoritele. Încearcă din nou.');
    } finally {
      setFavoriteBusy(false);
    }
  }

  const favoriteControls = (
    <>
      <FavoriteButton
        offer={offer}
        isFavorite={isFavorite}
        busy={favoriteBusy}
        onToggle={toggleFavorite}
      />
      {favoriteError && <span className="offer-favorite-error" role="alert">{favoriteError}</span>}
    </>
  );

  function handleKeyDown(event) {
    if (event.target !== event.currentTarget) return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      setOpen(true);
    }
  }

  return (
    <>
      <article
        className="offer-card"
        tabIndex={0}
        aria-label={`${offer.title}. Apasă pentru detalii`}
        onClick={() => setOpen(true)}
        onKeyDown={handleKeyDown}
      >
        <div className="offer-card-top">
          <span className="offer-brand">{offer.brand}</span>
          {isExpired(offer) && <span className="offer-expired">Expirată</span>}
          {favoriteControls}
        </div>
        <h2>{offer.title}</h2>
        <OfferPricing offer={offer} />
        <div className="offer-card-body">
          {offer.description && <p className="offer-description">{offer.description}</p>}
          {offer.products.length > 0 && (
            <div className="offer-detail">
              <strong>Produse</strong>
              <p>{offer.products.join(', ')}</p>
            </div>
          )}
          {offer.terms && (
            <div className="offer-detail">
              <strong>Condiții</strong>
              <p>{offer.terms}</p>
            </div>
          )}
          {(offer.valid_from || offer.valid_until) && (
            <p className="offer-validity">Valabilitate: {formatValidity(offer)}</p>
          )}
        </div>
        <div className="offer-card-footer">
          <span>Adăugată {formatDate(offer.created_at)}</span>
          <span className="offer-footer-actions">
            {offer.source_urls.map((url) => (
              <a
                href={url}
                key={url}
                target="_blank"
                rel="noreferrer"
                onClick={(event) => event.stopPropagation()}
              >
                Vezi oferta <span aria-hidden="true">↗</span>
              </a>
            ))}
            <ShareOffer offer={offer} />
          </span>
        </div>
      </article>
      {open && <OfferDialog offer={offer} onClose={() => setOpen(false)} actions={favoriteControls} />}
    </>
  );
}

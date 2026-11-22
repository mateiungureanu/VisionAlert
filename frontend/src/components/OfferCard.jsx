import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

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

function OfferDetails({ offer, headingId }) {
  return (
    <>
      <div className="offer-card-top">
        <span className="offer-brand">{offer.brand}</span>
        {offer.categories.map((category) => (
          <span className="offer-category-tag" key={category.id}>{category.name}</span>
        ))}
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

function OfferDialog({ offer, onClose }) {
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
        <OfferDetails offer={offer} headingId={headingId} />
        <div className="offer-card-footer">
          <span>Adăugată {formatDate(offer.created_at)}</span>
          {offer.source_urls.map((url) => (
            <a href={url} key={url} target="_blank" rel="noreferrer">
              Vezi oferta <span aria-hidden="true">↗</span>
            </a>
          ))}
        </div>
      </div>
    </dialog>,
    document.body,
  );
}

export default function OfferCard({ offer }) {
  const [open, setOpen] = useState(false);

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
        </div>
      </article>
      {open && <OfferDialog offer={offer} onClose={() => setOpen(false)} />}
    </>
  );
}

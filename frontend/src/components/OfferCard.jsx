function formatDate(value) {
  return new Intl.DateTimeFormat('ro-RO', { dateStyle: 'medium' }).format(new Date(value));
}

export default function OfferCard({ offer }) {
  const hasPricing =
    offer.price != null ||
    offer.previous_price != null ||
    offer.discount_percentage != null;

  return (
    <article className="offer-card">
      <div className="offer-card-top">
        <span className="offer-brand">{offer.brand}</span>
      </div>
      <h2>{offer.title}</h2>
      {hasPricing && (
        <div className="offer-pricing" aria-label="Preț și reducere">
          {offer.previous_price != null && (
            <span className="offer-price-item">
              <span className="offer-price-label">Preț anterior</span>
              <span className="offer-previous-price">
                {formatPrice(offer.previous_price)}
              </span>
            </span>
          )}
          {offer.price != null && (
            <span className="offer-price-item">
              <span className="offer-price-label">Preț nou</span>
              <strong className="offer-current-price">
                {formatPrice(offer.price)}
              </strong>
            </span>
          )}
          {offer.discount_percentage != null && (
            <span className="offer-discount">
              Reducere {formatPercentage(offer.discount_percentage)}
            </span>
          )}
        </div>
      )}
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
        <p className="offer-validity">
          Valabilitate:{' '}
          {offer.valid_from ? formatDate(offer.valid_from) : 'început nespecificat'}
          {' – '}
          {offer.valid_until ? formatDate(offer.valid_until) : 'fără dată de încheiere'}
        </p>
      )}
      <div className="offer-card-footer">
        <span>Adăugată {formatDate(offer.created_at)}</span>
        {offer.source_urls.map((url) => (
          <a href={url} key={url} target="_blank" rel="noreferrer">
            Vezi oferta <span aria-hidden="true">↗</span>
          </a>
        ))}
      </div>
    </article>
  );
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

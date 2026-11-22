import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import FilterDropdown from '../components/FilterDropdown';
import { useAuth } from '../AuthContext';
import { formatErrors, getBrandSubscriptions, getMyOffers, setBrandFavorite } from '../api';

const MAX_SHOWN_CATEGORIES = 3;

function categorySummary(categories) {
  if (categories.length === 0) return 'Toate categoriile';
  const names = categories.slice(0, MAX_SHOWN_CATEGORIES).map((category) => category.name);
  const extra = categories.length - names.length;
  return extra > 0 ? `${names.join(', ')} +${extra}` : names.join(', ');
}

export default function FollowedBrands() {
  const { token } = useAuth();
  const [favoriteError, setFavoriteError] = useState('');
  const [pendingFavoriteIds, setPendingFavoriteIds] = useState([]);
  const [offers, setOffers] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedBrandIds, setSelectedBrandIds] = useState([]);

  const offerCounts = offers.reduce((counts, offer) => {
    counts[offer.brand_id] = (counts[offer.brand_id] || 0) + 1;
    return counts;
  }, {});
  const subscribedBrands = subscriptions.map((subscription) => ({
    id: subscription.brand.id,
    name: subscription.brand.name,
    isFavorite: subscription.is_favorite,
    categories: subscription.categories,
    hasCategories: subscription.brand.categories.length > 0,
    offerCount: offerCounts[subscription.brand.id] || 0,
  }));
  const filterOptions = subscribedBrands.map((brand) => ({
    id: brand.id,
    name: brand.name,
    count: brand.offerCount,
  }));
  const visibleBrands = selectedBrandIds.length
    ? subscribedBrands.filter((brand) => selectedBrandIds.includes(brand.id))
    : subscribedBrands;
  const visibleOfferCount = visibleBrands.reduce((sum, brand) => sum + brand.offerCount, 0);
  const favoriteCount = subscribedBrands.filter((brand) => brand.isFavorite).length;

  useEffect(() => {
    let active = true;
    Promise.all([getMyOffers(token), getBrandSubscriptions(token)])
      .then(([offerList, subscriptionList]) => {
        if (!active) return;
        setOffers(offerList);
        setSubscriptions(subscriptionList);
      })
      .catch((requestError) => {
        if (active) setError(formatErrors(requestError));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [token]);

  async function toggleFavorite(brand) {
    if (pendingFavoriteIds.includes(brand.id)) return;
    setFavoriteError('');
    setPendingFavoriteIds((current) => [...current, brand.id]);
    try {
      const updated = await setBrandFavorite(brand.id, !brand.isFavorite, token);
      setSubscriptions((current) =>
        current.map((subscription) =>
          subscription.brand.id === brand.id
            ? { ...subscription, is_favorite: updated.is_favorite }
            : subscription,
        ),
      );
    } catch (requestError) {
      setFavoriteError(formatErrors(requestError));
    } finally {
      setPendingFavoriteIds((current) => current.filter((id) => id !== brand.id));
    }
  }

  return (
    <main className="offers-page">
      <header className="offers-heading">
        <div>
          <p className="offers-eyebrow">BRANDURILE MELE</p>
          <h1>Brandurile urmărite</h1>
          <p>Marchează cu stea brandurile favorite ca să le vezi ofertele pe pagina principală.</p>
        </div>
      </header>

      {error && <p className="error offers-error" role="alert">{error}</p>}
      {favoriteError && <p className="error offers-error" role="alert">{favoriteError}</p>}
      {loading ? (
        <div className="brand-grid" role="status" aria-label="Se încarcă brandurile">
          {Array.from({ length: 6 }, (_, index) => (
            <div className="brand-card-skeleton" key={index} aria-hidden="true" />
          ))}
        </div>
      ) : error ? (
        <section className="offers-empty">
          <h2>Ofertele nu au putut fi încărcate</h2>
          <p>Verifică dacă serverul este disponibil și încearcă din nou.</p>
        </section>
      ) : subscriptions.length === 0 ? (
        <section className="offers-empty">
          <h2>Începe să urmărești un brand</h2>
          <p>Abonează-te la branduri și categorii ca să vezi aici promoțiile potrivite pentru tine.</p>
          <Link className="subscription-link" to="/subscriptions">Alege abonamente</Link>
        </section>
      ) : (
        <section aria-label="Brandurile urmărite">
          <div className="feed-toolbar feed-toolbar-row">
            <FilterDropdown
              label="Branduri"
              allLabel="Toate brandurile"
              options={filterOptions}
              selectedIds={selectedBrandIds}
              onChange={setSelectedBrandIds}
              searchable
              searchPlaceholder="Caută un brand..."
              emptyText="Niciun brand găsit."
            />
            <span className="feed-count brands-summary">
              {visibleBrands.length} {visibleBrands.length === 1 ? 'brand' : 'branduri'}
              {' · '}
              {visibleOfferCount} {visibleOfferCount === 1 ? 'ofertă activă' : 'oferte active'}
              {' · '}
              {favoriteCount} {favoriteCount === 1 ? 'favorit' : 'favorite'}
            </span>
          </div>
          <div className="brand-grid">
            {visibleBrands.map((brand) => (
              <article className="brand-card" key={brand.id}>
                <Link className="brand-card-link" to={`/offers/${brand.id}`}>
                  <span className="brand-card-head">
                    <span className="brand-avatar" aria-hidden="true">
                      {brand.name[0]?.toUpperCase()}
                    </span>
                    <span className="brand-card-name">{brand.name}</span>
                  </span>
                  <span className="brand-card-count">
                    <strong>{brand.offerCount}</strong>
                    {brand.offerCount === 1 ? 'ofertă activă' : 'oferte active'}
                  </span>
                  {brand.hasCategories && (
                    <span className="brand-card-categories">
                      {categorySummary(brand.categories)}
                    </span>
                  )}
                  <span className="brand-card-action">
                    Vezi ofertele <span aria-hidden="true">→</span>
                  </span>
                </Link>
                <button
                  className={`favorite-star${brand.isFavorite ? ' active' : ''}`}
                  type="button"
                  aria-pressed={brand.isFavorite}
                  aria-label={brand.isFavorite ? `Elimină ${brand.name} din favorite` : `Marchează ${brand.name} ca favorit`}
                  title={brand.isFavorite ? 'Elimină din favorite' : 'Marchează ca favorit'}
                  disabled={pendingFavoriteIds.includes(brand.id)}
                  onClick={() => toggleFavorite(brand)}
                >
                  {brand.isFavorite ? '★' : '☆'}
                </button>
              </article>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

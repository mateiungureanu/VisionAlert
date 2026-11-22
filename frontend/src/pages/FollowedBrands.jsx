import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import FilterDropdown from '../components/FilterDropdown';
import { useAuth } from '../AuthContext';
import { formatErrors, getBrandSubscriptions, getMyOffers, setBrandFavorite } from '../api';

export default function FollowedBrands() {
  const { token } = useAuth();
  const [favoriteError, setFavoriteError] = useState('');
  const [pendingFavoriteIds, setPendingFavoriteIds] = useState([]);
  const [offers, setOffers] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const offersByBrand = offers.reduce((groups, offer) => {
    groups[offer.brand_id] = groups[offer.brand_id] || {
      id: offer.brand_id,
      name: offer.brand,
      offers: [],
    };
    groups[offer.brand_id].offers.push(offer);
    return groups;
  }, {});
  const subscribedBrands = subscriptions.map((subscription) => ({
    id: subscription.brand.id,
    name: subscription.brand.name,
    isFavorite: subscription.is_favorite,
    offers: offersByBrand[subscription.brand.id]?.offers || [],
  }));
  const totalOffers = offers.length;
  const [selectedBrandIds, setSelectedBrandIds] = useState([]);
  const filterOptions = subscribedBrands.map((brand) => ({
    id: brand.id,
    name: brand.name,
    count: brand.offers.length,
  }));
  const visibleBrands = selectedBrandIds.length
    ? subscribedBrands.filter((brand) => selectedBrandIds.includes(brand.id))
    : subscribedBrands;

  useEffect(() => {
    let active = true;
    Promise.all([getMyOffers(token), getBrandSubscriptions(token)])
      .then(([offerList, subscriptions]) => {
        if (!active) return;
        setOffers(offerList);
        setSubscriptions(subscriptions);
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
    <>
      <Navbar />
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
          <p className="offers-status" role="status">Se încarcă ofertele...</p>
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
          <section aria-label="Oferte grupate pe brand">
            <div className="offers-total">
              <span>Total oferte active</span>
              <strong>{totalOffers}</strong>
            </div>
            {offers.length === 0 && (
              <p className="offers-status">Nu există oferte active momentan.</p>
            )}
            <div className="feed-toolbar">
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
            </div>
            <div className="brand-offers-grid">
              {visibleBrands.map((brand) => (
                <div className="brand-offers-item" key={brand.id}>
                  <Link className="brand-offers-card" to={`/offers/${brand.id}`}>
                    <span className="brand-offers-count">{brand.offers.length}</span>
                    <span className="brand-offers-name">{brand.name}</span>
                    <span className="brand-offers-label">
                      {brand.offers.length === 1 ? 'ofertă' : 'oferte'}
                    </span>
                    <span className="brand-offers-action">Vezi ofertele <span aria-hidden="true">→</span></span>
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
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </>
  );
}
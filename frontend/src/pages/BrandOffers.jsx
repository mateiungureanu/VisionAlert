import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import OfferCard from '../components/OfferCard';
import { useAuth } from '../AuthContext';
import { formatErrors, getBrandSubscriptions, getMyOffers } from '../api';

export default function BrandOffers() {
  const { brandId } = useParams();
  const { token } = useAuth();
  const [offers, setOffers] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [selectedCategoryIds, setSelectedCategoryIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    Promise.all([getMyOffers(token), getBrandSubscriptions(token)])
      .then(([offerList, subscriptionList]) => {
        if (!active) return;
        setOffers(offerList.filter((offer) => String(offer.brand_id) === brandId));
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
  }, [brandId, token]);

  const subscription = subscriptions.find(
    (item) => String(item.brand.id) === brandId,
  );
  const brandName = subscription?.brand.name || offers[0]?.brand;
  const groupedOffers = useMemo(() => {
    const groups = new Map();
    const uncategorized = [];

    offers.forEach((offer) => {
      if (offer.categories.length === 0) {
        uncategorized.push(offer);
        return;
      }

      offer.categories.forEach((category) => {
        const group = groups.get(category.id) || {
          id: category.id,
          name: category.name,
          offers: [],
        };
        group.offers.push(offer);
        groups.set(category.id, group);
      });
    });

    const categories = [...groups.values()].sort((first, second) =>
      first.name.localeCompare(second.name, 'ro'),
    );
    if (uncategorized.length > 0) {
      categories.push({
        id: 'uncategorized',
        name: 'Fără categorie',
        offers: uncategorized,
      });
    }
    return categories;
  }, [offers]);
  const availableCategoryIds = groupedOffers.map((group) => group.id);
  const activeCategoryIds = selectedCategoryIds.filter((id) =>
    availableCategoryIds.includes(id),
  );
  const visibleGroups = activeCategoryIds.length
    ? groupedOffers.filter((group) => activeCategoryIds.includes(group.id))
    : groupedOffers;

  function toggleCategory(categoryId) {
    setSelectedCategoryIds((current) => {
      const activeIds = current.filter((id) => availableCategoryIds.includes(id));
      return activeIds.includes(categoryId)
        ? activeIds.filter((id) => id !== categoryId)
        : [...activeIds, categoryId];
    });
  }

  return (
    <>
      <Navbar />
      <main className="offers-page">
        <Link className="back-link" to="/offers">← Toate brandurile</Link>
        {error && <p className="error offers-error" role="alert">{error}</p>}
        {loading ? (
          <p className="offers-status" role="status">Se încarcă ofertele...</p>
        ) : error ? (
          <section className="offers-empty">
            <h1>Ofertele nu au putut fi încărcate</h1>
            <p>Verifică dacă serverul este disponibil și încearcă din nou.</p>
          </section>
        ) : !subscription ? (
          <section className="offers-empty">
            <h1>Brandul nu este în abonamentele tale</h1>
            <p>Abonează-te la acest brand pentru a vedea ofertele.</p>
            <Link className="subscription-link" to="/subscriptions">Gestionează abonamentele</Link>
          </section>
        ) : (
          <>
            <header className="offers-heading">
              <div>
                <p className="offers-eyebrow">OFERTE DE LA BRAND</p>
                <h1>{brandName}</h1>
                <p>{offers.length} {offers.length === 1 ? 'ofertă activă' : 'oferte active'}</p>
              </div>
              <Link className="subscription-link" to="/subscriptions">
                Gestionează abonamentele
              </Link>
            </header>
            {offers.length === 0 ? (
              <section className="offers-empty">
                <h2>Nicio ofertă momentan</h2>
                <p>Nu am găsit oferte active pentru acest brand. Revino mai târziu.</p>
              </section>
            ) : (
              <>
                <p className="category-count-note">
                  Selectează una sau mai multe categorii pentru a filtra ofertele. O ofertă asociată mai multor categorii apare în fiecare categorie relevantă.
                </p>
                <div className="category-pills" role="group" aria-label="Filtrează după categorie">
                  <button
                    className={`category-pill${activeCategoryIds.length === 0 ? ' selected' : ''}`}
                    type="button"
                    aria-pressed={activeCategoryIds.length === 0}
                    onClick={() => setSelectedCategoryIds([])}
                  >
                    Toate <span>{offers.length}</span>
                  </button>
                  {groupedOffers.map((group) => (
                    <button
                      className={`category-pill${activeCategoryIds.includes(group.id) ? ' selected' : ''}`}
                      key={group.id}
                      type="button"
                      aria-pressed={activeCategoryIds.includes(group.id)}
                      onClick={() => toggleCategory(group.id)}
                    >
                      {group.name} <span>{group.offers.length}</span>
                    </button>
                  ))}
                </div>
                <section className="offer-category-groups" aria-label={`Oferte ${brandName} pe categorii`}>
                  {visibleGroups.map((group) => (
                    <section className="offer-category-group" key={group.id}>
                      <header className="offer-category-heading">
                        <h2>{group.name}</h2>
                        <span>
                          {group.offers.length} {group.offers.length === 1 ? 'ofertă' : 'oferte'}
                        </span>
                      </header>
                      <div className="offers-grid">
                        {group.offers.map((offer) => (
                          <OfferCard offer={offer} key={`${group.id}-${offer.id}`} />
                        ))}
                      </div>
                    </section>
                  ))}
                </section>
              </>
            )}
          </>
        )}
      </main>
    </>
  );
}

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import OfferCard from '../components/OfferCard';
import FilterDropdown from '../components/FilterDropdown';
import { useAuth } from '../AuthContext';
import { discountLabel, discountOrder } from '../discounts';
import {
  formatErrors,
  getBrandSubscriptions,
  getFavoriteOfferDiscounts,
  getFavoriteOffers,
  getMyOffers,
} from '../api';

const PAGE_SIZE = 12;

export default function Home() {
  const { token, user } = useAuth();
  const [offers, setOffers] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [selectedBrandIds, setSelectedBrandIds] = useState([]);
  const [selectedDiscounts, setSelectedDiscounts] = useState([]);
  const [discountBands, setDiscountBands] = useState([]);
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [feed, setFeed] = useState({ count: 0, results: [] });
  const [feedLoading, setFeedLoading] = useState(true);
  const [feedError, setFeedError] = useState('');

  const favoriteSubscriptions = subscriptions.filter((subscription) => subscription.is_favorite);
  const hasFavorites = favoriteSubscriptions.length > 0;
  const filterOptions = favoriteSubscriptions
    .map((subscription) => ({
      id: subscription.brand.id,
      name: subscription.brand.name,
      count: offers.filter((offer) => offer.brand_id === subscription.brand.id).length,
    }))
    .sort((first, second) => first.name.localeCompare(second.name, 'ro'));
  const selectedKey = selectedBrandIds.join(',');
  const discountKey = selectedDiscounts.join(',');
  const discountOptions = [
    ...discountBands,
    ...selectedDiscounts
      .filter((key) => !discountBands.some((band) => band.key === key))
      .map((key) => ({ key, count: 0 })),
  ]
    .sort((first, second) => discountOrder(first.key) - discountOrder(second.key))
    .map((band) => ({ id: band.key, name: discountLabel(band.key), count: band.count }));
  const pageCount = Math.max(1, Math.ceil(feed.count / PAGE_SIZE));

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

  useEffect(() => {
    if (!hasFavorites) return undefined;
    let active = true;
    const brandIds = selectedKey ? selectedKey.split(',').map(Number) : [];
    const discounts = discountKey ? discountKey.split(',') : [];
    getFavoriteOffers(token, { page, brandIds, search, discounts })
      .then((data) => {
        if (!active) return;
        setFeed(data);
        setFeedError('');
      })
      .catch((requestError) => {
        if (active) setFeedError(formatErrors(requestError));
      })
      .finally(() => {
        if (active) setFeedLoading(false);
      });

    return () => {
      active = false;
    };
  }, [token, hasFavorites, page, selectedKey, search, discountKey]);

  useEffect(() => {
    if (!hasFavorites) return undefined;
    let active = true;
    const brandIds = selectedKey ? selectedKey.split(',').map(Number) : [];
    getFavoriteOfferDiscounts(token, { brandIds, search })
      .then((bands) => {
        if (active) setDiscountBands(bands);
      })
      .catch(() => {
        if (active) setDiscountBands([]);
      });

    return () => {
      active = false;
    };
  }, [token, hasFavorites, selectedKey, search]);

  useEffect(() => {
    const trimmed = searchInput.trim();
    if (trimmed === search) return undefined;
    const timer = setTimeout(() => {
      setFeedLoading(true);
      setSearch(trimmed);
      setPage(1);
    }, 350);
    return () => clearTimeout(timer);
  }, [searchInput, search]);

  function changeBrands(brandIds) {
    setFeedLoading(true);
    setSelectedBrandIds(brandIds);
    setPage(1);
  }

  function changeDiscounts(discounts) {
    setFeedLoading(true);
    setSelectedDiscounts(discounts);
    setPage(1);
  }

  function changePage(nextPage) {
    setFeedLoading(true);
    setPage(nextPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <>
      <Navbar />
      <main className="offers-page">
        <header className="offers-heading">
          <div>
            <p className="offers-eyebrow">PERSONALIZAT PENTRU TINE</p>
            <h1>Salut{user?.first_name ? `, ${user.first_name}` : ''}!</h1>
            {!loading && !error && subscriptions.length > 0 && (
              <p>
                Din brandurile urmărite ai <strong>{offers.length}</strong>{' '}
                {offers.length === 1 ? 'ofertă activă' : 'oferte active'}.
              </p>
            )}
          </div>
          <Link className="subscription-link" to="/brands">
            Brandurile urmărite
          </Link>
        </header>

        {error && <p className="error offers-error" role="alert">{error}</p>}
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
        ) : !hasFavorites ? (
          <section className="offers-empty">
            <h2>Încă nu ai marcat niciun brand ca favorit</h2>
            <p>
              Dacă vrei să fii mai atent la ofertele brandurilor preferate, marchează-le cu stea
              în pagina brandurilor urmărite și ele vor apărea aici.
            </p>
            <Link className="subscription-link" to="/brands">Marchează-ți favoritele</Link>
          </section>
        ) : (
          <section aria-label="Oferte de la brandurile favorite">
            <h2 className="feed-title">Oferte de la brandurile mele favorite</h2>
            <div className="feed-toolbar">
              <FilterDropdown
                label="Branduri"
                allLabel="Toate brandurile"
                options={filterOptions}
                selectedIds={selectedBrandIds}
                onChange={changeBrands}
                searchable
                searchPlaceholder="Caută un brand..."
                emptyText="Niciun brand găsit."
              />
              <FilterDropdown
                label="Reducere"
                allLabel="Toate reducerile"
                options={discountOptions}
                selectedIds={selectedDiscounts}
                onChange={changeDiscounts}
                emptyText="Nicio reducere disponibilă."
              />
              <input
                className="feed-search"
                type="search"
                placeholder="Caută în titlul ofertelor..."
                aria-label="Caută în titlul ofertelor"
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
              />
              {!feedLoading && !feedError && (
                <span className="feed-count">
                  {feed.count} {feed.count === 1 ? 'ofertă' : 'oferte'}
                </span>
              )}
            </div>

            {feedError && <p className="error offers-error" role="alert">{feedError}</p>}
            {feedLoading ? (
              <p className="offers-status" role="status">Se încarcă ofertele...</p>
            ) : feed.results.length === 0 && !feedError ? (
              <section className="offers-empty">
                <h2>Nicio ofertă găsită</h2>
                <p>
                  {search
                    ? `Nicio ofertă nu are „${search}” în titlu. Încearcă alt cuvânt sau schimbă filtrele.`
                    : selectedDiscounts.length
                      ? 'Nicio ofertă nu se potrivește filtrelor alese. Încearcă alte reduceri sau branduri.'
                      : 'Brandurile favorite selectate nu au oferte active momentan. Revino mai târziu.'}
                </p>
              </section>
            ) : (
              <>
                <div className="offers-grid">
                  {feed.results.map((offer) => (
                    <OfferCard offer={offer} key={offer.id} />
                  ))}
                </div>
                {pageCount > 1 && (
                  <nav className="pagination" aria-label="Paginare oferte">
                    <button
                      type="button"
                      disabled={page <= 1}
                      onClick={() => changePage(page - 1)}
                    >
                      ← Anterioară
                    </button>
                    <span>Pagina {page} din {pageCount}</span>
                    <button
                      type="button"
                      disabled={page >= pageCount}
                      onClick={() => changePage(page + 1)}
                    >
                      Următoarea →
                    </button>
                  </nav>
                )}
              </>
            )}
          </section>
        )}
      </main>
    </>
  );
}

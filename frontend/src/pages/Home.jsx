import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
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

const ICON = {
  width: 28,
  height: 28,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
};
const StoreIcon = () => (
  <svg {...ICON}>
    <path d="M4 9l1.5-5h13L20 9" />
    <path d="M4 9a2.67 2.67 0 0 0 5.33 0 2.67 2.67 0 0 0 5.34 0A2.67 2.67 0 0 0 20 9" />
    <path d="M5 12v8h14v-8" />
    <path d="M10 20v-4h4v4" />
  </svg>
);
const StarIcon = () => (
  <svg {...ICON}><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg>
);

function EmptyState({ icon, title, children, action }) {
  return (
    <section className="offers-empty">
      <span className="empty-icon">{icon}</span>
      <h2>{title}</h2>
      <p>{children}</p>
      {action}
    </section>
  );
}

function StatTile({ label, value, hint, to, tone }) {
  const content = (
    <>
      <span className="stat-label">{label}</span>
      <strong className={`stat-value${tone ? ` ${tone}` : ''}`}>{value}</strong>
      <span className="stat-hint">{hint}</span>
    </>
  );
  return to ? (
    <Link className="stat-tile stat-link" to={to}>{content}</Link>
  ) : (
    <div className="stat-tile">{content}</div>
  );
}

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

  const bestDiscountOffer = offers.reduce(
    (best, offer) =>
      offer.discount_percentage != null &&
      (!best || Number(offer.discount_percentage) > Number(best.discount_percentage))
        ? offer
        : best,
    null,
  );
  const bestDiscount = bestDiscountOffer
    ? `${new Intl.NumberFormat('ro-RO', { maximumFractionDigits: 0 }).format(Number(bestDiscountOffer.discount_percentage))}%`
    : null;

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
    <main className="offers-page">
      <header className="offers-heading">
        <div>
          <p className="offers-eyebrow">PERSONALIZAT PENTRU TINE</p>
          <h1>Salut{user?.first_name ? `, ${user.first_name}` : ''}!</h1>
          <p>Ofertele active de la brandurile pe care le urmărești, într-un singur loc.</p>
        </div>
      </header>

      {error && <p className="error offers-error" role="alert">{error}</p>}
      {loading ? (
        <p className="offers-status" role="status">Se încarcă ofertele...</p>
      ) : error ? (
        <EmptyState icon={<StoreIcon />} title="Ofertele nu au putut fi încărcate">
          Verifică dacă serverul este disponibil și încearcă din nou.
        </EmptyState>
      ) : subscriptions.length === 0 ? (
        <EmptyState
          icon={<StoreIcon />}
          title="Începe să urmărești un brand"
          action={<Link className="subscription-link" to="/subscriptions">Alege abonamente</Link>}
        >
          Abonează-te la branduri și categorii ca să vezi aici promoțiile potrivite pentru tine.
        </EmptyState>
      ) : (
        <>
          <section className="stat-grid" aria-label="Rezumat">
            <StatTile
              label="Oferte active"
              value={offers.length}
              hint="din brandurile urmărite"
            />
            <StatTile
              label="Branduri urmărite"
              value={subscriptions.length}
              hint="vezi toate brandurile"
              to="/brands"
            />
            <StatTile
              label="Branduri favorite"
              value={favoriteSubscriptions.length}
              hint={hasFavorites ? 'afișate mai jos' : 'marchează-le cu stea'}
              to="/brands"
            />
            {bestDiscount && (
              <StatTile
                label="Cea mai mare reducere"
                value={bestDiscount}
                hint={bestDiscountOffer.brand}
                tone="success"
              />
            )}
          </section>

          {!hasFavorites ? (
            <EmptyState
              icon={<StarIcon />}
              title="Încă nu ai marcat niciun brand ca favorit"
              action={<Link className="subscription-link" to="/brands">Marchează-ți favoritele</Link>}
            >
              Dacă vrei să fii mai atent la ofertele brandurilor preferate, marchează-le cu stea
              în pagina brandurilor urmărite și ele vor apărea aici.
            </EmptyState>
          ) : (
            <section className="feed-section" aria-label="Oferte de la brandurile favorite">
              <h2 className="feed-title">Oferte de la brandurile tale favorite</h2>
              <div className="feed-toolbar feed-toolbar-row">
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
                <div className="offers-grid" role="status" aria-label="Se încarcă ofertele">
                  {Array.from({ length: 6 }, (_, index) => (
                    <div className="offer-skeleton" key={index} aria-hidden="true" />
                  ))}
                </div>
              ) : feed.results.length === 0 && !feedError ? (
                <EmptyState icon={<StoreIcon />} title="Nicio ofertă găsită">
                  {search
                    ? `Nicio ofertă nu are „${search}” în titlu. Încearcă alt cuvânt sau schimbă filtrele.`
                    : selectedDiscounts.length
                      ? 'Nicio ofertă nu se potrivește filtrelor alese. Încearcă alte reduceri sau branduri.'
                      : 'Brandurile favorite selectate nu au oferte active momentan. Revino mai târziu.'}
                </EmptyState>
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
        </>
      )}
    </main>
  );
}

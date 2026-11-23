import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import OfferCard from '../components/OfferCard';
import FilterDropdown from '../components/FilterDropdown';
import { useAuth } from '../AuthContext';
import { discountLabel, discountOrder } from '../discounts';
import {
  formatErrors,
  getFavoriteOfferBrands,
  getFavoriteOfferDiscountBands,
  getFavoriteOfferList,
} from '../api';

const PAGE_SIZE = 12;

const HeartIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21.2l7.8-7.7 1-1.1a5.5 5.5 0 0 0 0-7.8z" />
  </svg>
);

export default function FavoriteOffers() {
  const { token } = useAuth();
  const [selectedBrandIds, setSelectedBrandIds] = useState([]);
  const [selectedDiscounts, setSelectedDiscounts] = useState([]);
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [reloadKey, setReloadKey] = useState(0);
  const [list, setList] = useState({ count: 0, results: [] });
  const [brandFacets, setBrandFacets] = useState([]);
  const [discountBands, setDiscountBands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const brandKey = selectedBrandIds.join(',');
  const discountKey = selectedDiscounts.join(',');
  const hasFilters = brandKey !== '' || discountKey !== '' || search !== '';
  const pageCount = Math.max(1, Math.ceil(list.count / PAGE_SIZE));

  // Selected options that dropped out of the facets stay listed (count 0) so they can be cleared.
  const brandOptions = [
    ...brandFacets,
    ...selectedBrandIds
      .filter((id) => !brandFacets.some((brand) => brand.id === id))
      .map((id) => ({ id, name: `Brand #${id}`, count: 0 })),
  ];
  const discountOptions = [
    ...discountBands,
    ...selectedDiscounts
      .filter((key) => !discountBands.some((band) => band.key === key))
      .map((key) => ({ key, count: 0 })),
  ]
    .sort((first, second) => discountOrder(first.key) - discountOrder(second.key))
    .map((band) => ({ id: band.key, name: discountLabel(band.key), count: band.count }));

  useEffect(() => {
    let active = true;
    const brandIds = brandKey ? brandKey.split(',').map(Number) : [];
    const discounts = discountKey ? discountKey.split(',') : [];
    getFavoriteOfferList(token, { page, brandIds, search, discounts })
      .then((data) => {
        if (!active) return;
        if (data.results.length === 0 && page > 1) {
          setPage(page - 1);
          return;
        }
        setList(data);
        setError('');
        setLoading(false);
      })
      .catch((requestError) => {
        if (!active) return;
        setError(formatErrors(requestError));
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [token, page, brandKey, discountKey, search, reloadKey]);

  useEffect(() => {
    let active = true;
    const brandIds = brandKey ? brandKey.split(',').map(Number) : [];
    const discounts = discountKey ? discountKey.split(',') : [];
    Promise.all([
      getFavoriteOfferBrands(token, { search, discounts }),
      getFavoriteOfferDiscountBands(token, { brandIds, search }),
    ])
      .then(([brands, bands]) => {
        if (!active) return;
        setBrandFacets(brands);
        setDiscountBands(bands);
      })
      .catch(() => {
        if (!active) return;
        setBrandFacets([]);
        setDiscountBands([]);
      });
    return () => {
      active = false;
    };
  }, [token, brandKey, discountKey, search, reloadKey]);

  useEffect(() => {
    const trimmed = searchInput.trim();
    if (trimmed === search) return undefined;
    const timer = setTimeout(() => {
      setLoading(true);
      setSearch(trimmed);
      setPage(1);
    }, 350);
    return () => clearTimeout(timer);
  }, [searchInput, search]);

  function changeBrands(brandIds) {
    setLoading(true);
    setSelectedBrandIds(brandIds);
    setPage(1);
  }

  function changeDiscounts(discounts) {
    setLoading(true);
    setSelectedDiscounts(discounts);
    setPage(1);
  }

  function changePage(nextPage) {
    setLoading(true);
    setPage(nextPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function clearFilters() {
    setLoading(true);
    setSelectedBrandIds([]);
    setSelectedDiscounts([]);
    setSearchInput('');
    setSearch('');
    setPage(1);
  }

  // Removing a favorite here drops the card right away, then the list and filters are refreshed.
  function handleFavoriteChange(offer, isFavorite) {
    if (isFavorite) return;
    setList((current) => ({
      ...current,
      count: Math.max(0, current.count - 1),
      results: current.results.filter((item) => item.id !== offer.id),
    }));
    setReloadKey((key) => key + 1);
  }

  return (
    <main className="offers-page">
      <header className="offers-heading">
        <div>
          <p className="offers-eyebrow">SALVATE DE TINE</p>
          <h1>Oferte favorite</h1>
          <p>Ofertele pe care le-ai salvat, ca să le găsești ușor când ești gata să cumperi.</p>
        </div>
      </header>

      {error && <p className="error offers-error" role="alert">{error}</p>}
      {loading && !error ? (
        <div className="offers-grid" role="status" aria-label="Se încarcă ofertele">
          {Array.from({ length: 6 }, (_, index) => (
            <div className="offer-skeleton" key={index} aria-hidden="true" />
          ))}
        </div>
      ) : error ? (
        <section className="offers-empty">
          <span className="empty-icon"><HeartIcon /></span>
          <h2>Ofertele favorite nu au putut fi încărcate</h2>
          <p>Verifică dacă serverul este disponibil și încearcă din nou.</p>
        </section>
      ) : list.count === 0 && !hasFilters ? (
        <section className="offers-empty">
          <span className="empty-icon"><HeartIcon /></span>
          <h2>Încă nu ai salvat nicio ofertă</h2>
          <p>
            Apasă pe inimă pe orice ofertă interesantă și o vei găsi aici, ca s-o poți
            consulta mai târziu.
          </p>
          <Link className="subscription-link" to="/">Vezi ofertele</Link>
        </section>
      ) : (
        <section aria-label="Ofertele mele favorite">
          <div className="feed-toolbar feed-toolbar-row">
            <FilterDropdown
              label="Branduri"
              allLabel="Toate brandurile"
              options={brandOptions}
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
            <span className="feed-count">
              {list.count} {list.count === 1 ? 'ofertă salvată' : 'oferte salvate'}
            </span>
          </div>

          {list.results.length === 0 ? (
            <section className="offers-empty">
              <span className="empty-icon"><HeartIcon /></span>
              <h2>Nicio ofertă găsită</h2>
              <p>
                {search
                  ? `Nicio ofertă salvată nu are „${search}” în titlu. Încearcă alt cuvânt sau schimbă filtrele.`
                  : 'Nicio ofertă salvată nu se potrivește filtrelor alese.'}
              </p>
              <button className="subscription-link" type="button" onClick={clearFilters}>
                Șterge filtrele
              </button>
            </section>
          ) : (
            <>
              <div className="offers-grid">
                {list.results.map((offer) => (
                  <OfferCard
                    offer={offer}
                    key={offer.id}
                    onFavoriteChange={handleFavoriteChange}
                  />
                ))}
              </div>
              {pageCount > 1 && (
                <nav className="pagination" aria-label="Paginare oferte favorite">
                  <button type="button" disabled={page <= 1} onClick={() => changePage(page - 1)}>
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
  );
}

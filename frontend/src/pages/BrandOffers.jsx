import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import OfferCard from '../components/OfferCard';
import FilterDropdown from '../components/FilterDropdown';
import { useAuth } from '../AuthContext';
import { discountBandKey, discountLabel, discountOrder } from '../discounts';
import { normalizeText } from '../text';
import { formatErrors, getBrandSubscriptions, getMyOffers } from '../api';

export default function BrandOffers() {
  const { brandId } = useParams();
  const { token } = useAuth();
  const [offers, setOffers] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [selectedCategoryIds, setSelectedCategoryIds] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedDiscounts, setSelectedDiscounts] = useState([]);
  const [collapsedIds, setCollapsedIds] = useState([]);
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
  const subscribedCategories = subscription?.categories ?? [];

  const searchedOffers = useMemo(() => {
    const query = normalizeText(search.trim());
    return query
      ? offers.filter((offer) => normalizeText(offer.title).includes(query))
      : offers;
  }, [offers, search]);

  const discountOptions = useMemo(() => {
    const counts = new Map();
    searchedOffers.forEach((offer) => {
      const key = discountBandKey(offer.discount_percentage);
      counts.set(key, (counts.get(key) || 0) + 1);
    });
    selectedDiscounts.forEach((key) => {
      if (!counts.has(key)) counts.set(key, 0);
    });
    return [...counts.entries()]
      .sort(([first], [second]) => discountOrder(first) - discountOrder(second))
      .map(([key, count]) => ({ id: key, name: discountLabel(key), count }));
  }, [searchedOffers, selectedDiscounts]);

  const filteredOffers = useMemo(
    () =>
      selectedDiscounts.length
        ? searchedOffers.filter((offer) =>
            selectedDiscounts.includes(discountBandKey(offer.discount_percentage)),
          )
        : searchedOffers,
    [searchedOffers, selectedDiscounts],
  );
  const hasActiveFilters = search.trim() !== '' || selectedDiscounts.length > 0;

  const groupedOffers = useMemo(() => {
    const groups = new Map();
    const uncategorized = [];

    filteredOffers.forEach((offer) => {
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
  }, [filteredOffers]);
  const availableCategoryIds = groupedOffers.map((group) => group.id);
  const activeCategoryIds = selectedCategoryIds.filter((id) =>
    availableCategoryIds.includes(id),
  );
  const visibleGroups = activeCategoryIds.length
    ? groupedOffers.filter((group) => activeCategoryIds.includes(group.id))
    : groupedOffers;
  const categoryOptions = groupedOffers.map((group) => ({
    id: group.id,
    name: group.name,
    count: group.offers.length,
  }));
  // The dropdowns only appear when the brand actually has something to filter by.
  const hasCategories = offers.some((offer) => offer.categories.length > 0);
  const hasDiscounts = offers.some((offer) => offer.discount_percentage != null);
  const collapsible = visibleGroups.length > 1;
  const allCollapsed =
    collapsible && visibleGroups.every((group) => collapsedIds.includes(group.id));

  function toggleCollapsed(groupId) {
    setCollapsedIds((current) =>
      current.includes(groupId)
        ? current.filter((id) => id !== groupId)
        : [...current, groupId],
    );
  }

  function toggleAllCollapsed() {
    setCollapsedIds(allCollapsed ? [] : visibleGroups.map((group) => group.id));
  }

  function clearFilters() {
    setSearch('');
    setSelectedDiscounts([]);
  }

  const backLink = (
    <Link className="back-link" to="/brands">
      <span className="back-link-arrow" aria-hidden="true">←</span>
      Brandurile urmărite
    </Link>
  );

  return (
    <>
      <main className="offers-page">
        {error && <p className="error offers-error" role="alert">{error}</p>}
        {loading ? (
          <p className="offers-status" role="status">Se încarcă ofertele...</p>
        ) : error ? (
          <section className="offers-empty">
            <h1>Ofertele nu au putut fi încărcate</h1>
            <p>Verifică dacă serverul este disponibil și încearcă din nou.</p>
            <div className="offers-empty-actions">{backLink}</div>
          </section>
        ) : !subscription ? (
          <section className="offers-empty">
            <h1>Brandul nu este în abonamentele tale</h1>
            <p>Abonează-te la acest brand pentru a vedea ofertele.</p>
            <Link className="subscription-link" to="/subscriptions">Gestionează abonamentele</Link>
            <div className="offers-empty-actions">{backLink}</div>
          </section>
        ) : (
          <>
            <header className="brand-heading">
              <div className="brand-heading-main">
                <span className="brand-avatar brand-avatar-large" aria-hidden="true">
                  {brandName?.[0]?.toUpperCase()}
                </span>
                <div>
                  <p className="offers-eyebrow">OFERTE DE LA BRAND</p>
                  <h1>{brandName}</h1>
                  <p className="brand-heading-meta">
                    {offers.length} {offers.length === 1 ? 'ofertă activă' : 'oferte active'}
                    {subscribedCategories.length > 0 && (
                      <> · Categorii urmărite: {subscribedCategories.map((category) => category.name).join(', ')}</>
                    )}
                  </p>
                </div>
              </div>
              {backLink}
            </header>
            {offers.length === 0 ? (
              <section className="offers-empty">
                <h2>Nicio ofertă momentan</h2>
                <p>Nu am găsit oferte active pentru acest brand. Revino mai târziu.</p>
              </section>
            ) : (
              <>
                <div className="feed-toolbar feed-toolbar-row">
                  {hasCategories && (
                    <FilterDropdown
                      label="Categorii"
                      allLabel="Toate categoriile"
                      options={categoryOptions}
                      selectedIds={activeCategoryIds}
                      onChange={setSelectedCategoryIds}
                      emptyText="Nicio categorie disponibilă."
                    />
                  )}
                  {hasDiscounts && (
                    <FilterDropdown
                      label="Reducere"
                      allLabel="Toate reducerile"
                      options={discountOptions}
                      selectedIds={selectedDiscounts}
                      onChange={setSelectedDiscounts}
                      emptyText="Nicio reducere disponibilă."
                    />
                  )}
                  <input
                    className="feed-search"
                    type="search"
                    placeholder="Caută în titlul ofertelor..."
                    aria-label="Caută în titlul ofertelor"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                  <span className="feed-count">
                    {filteredOffers.length} {filteredOffers.length === 1 ? 'ofertă' : 'oferte'}
                  </span>
                </div>
                {filteredOffers.length === 0 ? (
                  <section className="offers-empty">
                    <h2>Nicio ofertă găsită</h2>
                    <p>Nicio ofertă nu se potrivește filtrelor alese. Încearcă alt cuvânt sau altă reducere.</p>
                    {hasActiveFilters && (
                      <button className="subscription-link" type="button" onClick={clearFilters}>
                        Șterge filtrele
                      </button>
                    )}
                  </section>
                ) : (
                  <>
                    {collapsible && (
                      <div className="sections-bar">
                        <span>
                          {visibleGroups.length} categorii
                        </span>
                        <button className="collapse-all" type="button" onClick={toggleAllCollapsed}>
                          {allCollapsed ? 'Extinde toate' : 'Restrânge toate'}
                        </button>
                      </div>
                    )}
                    <section className="offer-category-groups" aria-label={`Oferte ${brandName} pe categorii`}>
                      {visibleGroups.map((group) => {
                        const isCollapsed = collapsible && collapsedIds.includes(group.id);
                        const count = `${group.offers.length} ${group.offers.length === 1 ? 'ofertă' : 'oferte'}`;
                        const bodyId = `category-body-${group.id}`;
                        return (
                          <section className="offer-category-group" key={group.id}>
                            {collapsible ? (
                              <h2 className="offer-category-heading">
                                <button
                                  className={`offer-category-toggle${isCollapsed ? ' collapsed' : ''}`}
                                  type="button"
                                  aria-expanded={!isCollapsed}
                                  aria-controls={bodyId}
                                  onClick={() => toggleCollapsed(group.id)}
                                >
                                  <span className="offer-category-chevron" aria-hidden="true">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                                      <path d="M6 9l6 6 6-6" />
                                    </svg>
                                  </span>
                                  <span className="offer-category-name">{group.name}</span>
                                  <span className="offer-category-line" aria-hidden="true" />
                                  <span className="offer-category-count">{count}</span>
                                </button>
                              </h2>
                            ) : (
                              <h2 className="offer-category-heading offer-category-static">
                                <span className="offer-category-name">{group.name}</span>
                                <span className="offer-category-line" aria-hidden="true" />
                                <span className="offer-category-count">{count}</span>
                              </h2>
                            )}
                            {!isCollapsed && (
                              <div className="offers-grid" id={bodyId}>
                                {group.offers.map((offer) => (
                                  <OfferCard offer={offer} key={`${group.id}-${offer.id}`} />
                                ))}
                              </div>
                            )}
                          </section>
                        );
                      })}
                    </section>
                  </>
                )}
              </>
            )}
          </>
        )}
      </main>
    </>
  );
}

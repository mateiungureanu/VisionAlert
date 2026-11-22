import { useEffect, useState } from 'react';
import { useAuth } from '../AuthContext';
import {
  deleteBrandSubscription,
  formatErrors,
  getBrandSubscriptions,
  getBrands,
  saveBrandSubscription,
} from '../api';

export default function BrandSubscriptions() {
  const { token } = useAuth();
  const [brands, setBrands] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [selectedBrandId, setSelectedBrandId] = useState('');
  const [selectedCategoryIds, setSelectedCategoryIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    Promise.all([getBrands(token), getBrandSubscriptions(token)])
      .then(([brandList, subscriptionList]) => {
        setBrands(brandList);
        setSubscriptions(subscriptionList);
        if (brandList.length > 0) {
          setSelectedBrandId(String(brandList[0].id));
          const currentSubscription = subscriptionList.find(
            (subscription) => subscription.brand.id === brandList[0].id,
          );
          setSelectedCategoryIds(
            currentSubscription?.categories.map((category) => category.id) ?? [],
          );
        }
      })
      .catch((requestError) => setError(formatErrors(requestError)))
      .finally(() => setLoading(false));
  }, [token]);

  const selectedBrand = brands.find((brand) => String(brand.id) === selectedBrandId);
  const currentSubscription = subscriptions.find(
    (subscription) => subscription.brand.id === Number(selectedBrandId),
  );

  function chooseBrand(event) {
    const brandId = event.target.value;
    setSelectedBrandId(brandId);
    const subscription = subscriptions.find(
      (item) => item.brand.id === Number(brandId),
    );
    setSelectedCategoryIds(subscription?.categories.map((category) => category.id) ?? []);
    setMessage('');
    setError('');
  }

  function toggleCategory(categoryId) {
    setSelectedCategoryIds((current) => (
      current.includes(categoryId)
        ? current.filter((id) => id !== categoryId)
        : [...current, categoryId]
    ));
  }

  async function submitSubscription(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setMessage('');
    try {
      const savedSubscription = await saveBrandSubscription({
        brand_id: Number(selectedBrandId),
        category_ids: selectedCategoryIds,
      }, token);
      setSubscriptions((current) => [
        ...current.filter((item) => item.id !== savedSubscription.id),
        savedSubscription,
      ]);
      setMessage('Abonamentul a fost salvat.');
    } catch (requestError) {
      setError(formatErrors(requestError));
    } finally {
      setSaving(false);
    }
  }

  async function unsubscribe(brandId) {
    setError('');
    setMessage('');
    try {
      await deleteBrandSubscription(brandId, token);
      setSubscriptions((current) => current.filter((item) => item.brand.id !== brandId));
      if (Number(selectedBrandId) === brandId) {
        setSelectedCategoryIds([]);
      }
      setMessage('Te-ai dezabonat de la brand.');
    } catch (requestError) {
      setError(formatErrors(requestError));
    }
  }

  return (
    <main className="offers-page">
      <header className="offers-heading">
        <div>
          <p className="offers-eyebrow">ABONAMENTE</p>
          <h1>Abonamente la branduri</h1>
          <p>Alege brandurile și categoriile pentru care vrei să primești alerte.</p>
        </div>
      </header>

      {error && <p className="notice error" role="alert">{error}</p>}
      {message && <p className="notice success" role="status">{message}</p>}

      {loading ? (
        <div className="sub-layout" role="status" aria-label="Se încarcă brandurile">
          <div className="panel-skeleton" aria-hidden="true" />
          <div className="panel-skeleton" aria-hidden="true" />
        </div>
      ) : (
        <div className="sub-layout">
          <section className="sub-panel" aria-labelledby="sub-form-title">
            <h2 id="sub-form-title">
              {currentSubscription ? 'Preferințele tale' : 'Abonează-te la un brand'}
            </h2>
            {brands.length === 0 ? (
              <p className="sub-empty">Nu există momentan branduri disponibile.</p>
            ) : (
              <form className="sub-form" onSubmit={submitSubscription}>
                <div>
                  <label className="field-label" htmlFor="brand-select">Brand</label>
                  <select
                    id="brand-select"
                    className="select-field"
                    value={selectedBrandId}
                    onChange={chooseBrand}
                  >
                    {brands.map((brand) => (
                      <option key={brand.id} value={brand.id}>{brand.name}</option>
                    ))}
                  </select>
                </div>

                <fieldset className="sub-categories">
                  <legend className="field-label">Categorii</legend>
                  {!selectedBrand?.categories.length ? (
                    <p className="sub-hint">
                      Acest brand nu are categorii configurate. Abonamentul va include toate ofertele.
                    </p>
                  ) : (
                    <>
                      <div className="choice-chips">
                        {selectedBrand.categories.map((category) => {
                          const checked = selectedCategoryIds.includes(category.id);
                          return (
                            <label
                              className={`choice-chip${checked ? ' selected' : ''}`}
                              key={category.id}
                            >
                              <input
                                type="checkbox"
                                checked={checked}
                                onChange={() => toggleCategory(category.id)}
                              />
                              {category.name}
                            </label>
                          );
                        })}
                      </div>
                      <p className="sub-hint">
                        {selectedCategoryIds.length === 0
                          ? 'Nicio categorie aleasă: vei primi toate ofertele brandului.'
                          : `${selectedCategoryIds.length} ${selectedCategoryIds.length === 1 ? 'categorie aleasă' : 'categorii alese'}.`}
                      </p>
                    </>
                  )}
                </fieldset>

                <button className="primary-button" type="submit" disabled={saving}>
                  {saving
                    ? 'Se salvează...'
                    : currentSubscription
                      ? 'Salvează preferințele'
                      : 'Abonează-te'}
                </button>
              </form>
            )}
          </section>

          <section className="sub-panel" aria-labelledby="sub-list-title">
            <h2 id="sub-list-title">
              Abonamentele mele
              {subscriptions.length > 0 && (
                <span className="sub-count">{subscriptions.length}</span>
              )}
            </h2>
            {subscriptions.length === 0 ? (
              <p className="sub-empty">Nu ești abonat la niciun brand.</p>
            ) : (
              <ul className="sub-list">
                {subscriptions.map((subscription) => (
                  <li className="sub-row" key={subscription.id}>
                    <span className="brand-avatar" aria-hidden="true">
                      {subscription.brand.name[0]?.toUpperCase()}
                    </span>
                    <div className="sub-row-info">
                      <strong>{subscription.brand.name}</strong>
                      <span>
                        {subscription.categories.length
                          ? subscription.categories.map((category) => category.name).join(', ')
                          : 'Toate categoriile'}
                      </span>
                    </div>
                    <button
                      className="ghost-danger"
                      type="button"
                      onClick={() => unsubscribe(subscription.brand.id)}
                    >
                      Dezabonează-te
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </main>
  );
}

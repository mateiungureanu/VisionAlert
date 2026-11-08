import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
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
    <>
      <Navbar />
      <main className="subscriptions-page">
        <Link to="/" className="back-link">← Înapoi la Home</Link>
        <h1>Abonamente la branduri</h1>
        <p>Alege brandurile și categoriile pentru care vrei să primești alerte.</p>

        {error && <p className="error" role="alert">{error}</p>}
        {message && <p className="success-message" role="status">{message}</p>}

        {loading ? (
          <p>Se încarcă brandurile...</p>
        ) : (
          <div className="subscriptions-layout">
            <section className="subscription-panel">
              <h2>{currentSubscription ? 'Preferințele tale' : 'Abonează-te la un brand'}</h2>
              {brands.length === 0 ? (
                <p>Nu există momentan branduri disponibile.</p>
              ) : (
                <form onSubmit={submitSubscription}>
                  <label className="subscription-label" htmlFor="brand-select">Brand</label>
                  <select
                    id="brand-select"
                    className="brand-select"
                    value={selectedBrandId}
                    onChange={chooseBrand}
                  >
                    {brands.map((brand) => (
                      <option key={brand.id} value={brand.id}>{brand.name}</option>
                    ))}
                  </select>

                  <fieldset className="category-list">
                    <legend>Categorii</legend>
                    {!selectedBrand?.categories.length ? (
                      <p>Acest brand nu are categorii configurate. Abonamentul va include toate ofertele.</p>
                    ) : (
                      selectedBrand.categories.map((category) => (
                        <label className="category-option" key={category.id}>
                          <input
                            type="checkbox"
                            checked={selectedCategoryIds.includes(category.id)}
                            onChange={() => toggleCategory(category.id)}
                          />
                          {category.name}
                        </label>
                      ))
                    )}
                  </fieldset>

                  <button type="submit" disabled={saving}>
                    {saving
                      ? 'Se salvează...'
                      : currentSubscription
                        ? 'Salvează preferințele'
                        : 'Abonează-te'}
                  </button>
                </form>
              )}
            </section>

            <section className="subscription-panel">
              <h2>Abonamentele mele</h2>
              {subscriptions.length === 0 ? (
                <p>Nu ești abonat la niciun brand.</p>
              ) : (
                <ul className="subscription-list">
                  {subscriptions.map((subscription) => (
                    <li className="subscription-item" key={subscription.id}>
                      <div>
                        <strong>{subscription.brand.name}</strong>
                        <p>
                          {subscription.categories.length
                            ? subscription.categories.map((category) => category.name).join(', ')
                            : 'Toate categoriile'}
                        </p>
                      </div>
                      <button
                        className="secondary-button"
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
    </>
  );
}

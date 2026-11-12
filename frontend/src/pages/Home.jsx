import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../AuthContext';
import { formatErrors, getBrandSubscriptions, getMyOffers } from '../api';

export default function Home() {
  const { token, user } = useAuth();
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
    offers: offersByBrand[subscription.brand.id]?.offers || [],
  }));
  const totalOffers = offers.length;

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

  return (
    <>
      <Navbar />
      <main className="offers-page">
        <header className="offers-heading">
          <div>
            <p className="offers-eyebrow">PERSONALIZAT PENTRU TINE</p>
            <h1>Ofertele mele{user?.first_name ? `, ${user.first_name}` : ''}</h1>
            <p>Promoții de la brandurile și categoriile pe care le urmărești.</p>
          </div>
          <Link className="subscription-link" to="/subscriptions">
            Gestionează abonamentele
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
        ) : (
          <section aria-label="Oferte grupate pe brand">
            <div className="offers-total">
              <span>Total oferte active</span>
              <strong>{totalOffers}</strong>
            </div>
            {offers.length === 0 && (
              <p className="offers-status">Nu există oferte active momentan.</p>
            )}
            <div className="brand-offers-grid">
              {subscribedBrands.map((brand) => (
                <Link
                  className="brand-offers-card"
                  key={brand.id}
                  to={`/offers/${brand.id}`}
                >
                  <span className="brand-offers-count">{brand.offers.length}</span>
                  <span className="brand-offers-name">{brand.name}</span>
                  <span className="brand-offers-label">
                    {brand.offers.length === 1 ? 'ofertă' : 'oferte'}
                  </span>
                  <span className="brand-offers-action">Vezi ofertele <span aria-hidden="true">→</span></span>
                </Link>
              ))}
            </div>
          </section>
        )}
      </main>
    </>
  );
}
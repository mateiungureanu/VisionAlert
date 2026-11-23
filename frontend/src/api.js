const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

async function request(path, { method = 'GET', body, token } = {}) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) throw { status: res.status, data };
  return data;
}

export const registerUser = (body) => request('/auth/register/', { method: 'POST', body });
export const loginUser = (body) => request('/auth/login/', { method: 'POST', body });
export const getMe = (token) => request('/auth/me/', { token });
export const deleteAccount = (token) => request('/auth/me/delete/', { method: 'DELETE', token });
export const getBrands = (token) => request('/brands/', { token });
export const getBrandSubscriptions = (token) => request('/subscriptions/', { token });
export const getMyOffers = (token) => request('/offers/mine/', { token });
export const setBrandFavorite = (brandId, isFavorite, token) => request(`/subscriptions/${brandId}/favorite/`, { method: 'PATCH', body: { is_favorite: isFavorite }, token });
function favoriteOfferParams({ page, brandIds = [], search = '', discounts = [] }) {
  const params = new URLSearchParams();
  if (page) params.set('page', String(page));
  if (brandIds.length) params.set('brands', brandIds.join(','));
  if (search.trim()) params.set('search', search.trim());
  if (discounts.length) params.set('discounts', discounts.join(','));
  return params;
}
export const getFavoriteOffers = (token, filters = {}) => request(`/offers/favorites/?${favoriteOfferParams({ page: 1, ...filters })}`, { token });
export const getFavoriteOfferDiscounts = (token, filters = {}) => request(`/offers/favorites/discounts/?${favoriteOfferParams({ ...filters, page: 0 })}`, { token });
export const addFavoriteOffer = (offerId, token) => request(`/favorite-offers/${offerId}/`, { method: 'PUT', token });
export const removeFavoriteOffer = (offerId, token) => request(`/favorite-offers/${offerId}/`, { method: 'DELETE', token });
export const getFavoriteOfferList = (token, filters = {}) => request(`/favorite-offers/?${favoriteOfferParams({ page: 1, ...filters })}`, { token });
export const getFavoriteOfferBrands = (token, filters = {}) => request(`/favorite-offers/brands/?${favoriteOfferParams({ ...filters, page: 0 })}`, { token });
export const getFavoriteOfferDiscountBands = (token, filters = {}) => request(`/favorite-offers/discounts/?${favoriteOfferParams({ ...filters, page: 0 })}`, { token });
export const saveBrandSubscription = (body, token) => request('/subscriptions/', { method: 'POST', body, token });
export const deleteBrandSubscription = (brandId, token) => request(`/subscriptions/${brandId}/`, { method: 'DELETE', token });

export function formatErrors(err) {
  const d = err?.data;
  if (!d) return 'Nu m-am putut conecta la server.';
  if (d.detail) return d.detail;
  return Object.entries(d)
    .map(([k, v]) => `${k}: ${[].concat(v).join(' ')}`)
    .join('\n');
}
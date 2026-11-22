// Discount bands shared by the home feed and the brand page. The keys match
// the backend: '0' = below 10%, '10'..'40' = 10-point bands, '50' = 50% or
// more and 'none' = offers without a discount.
const BAND_SIZE = 10;
const TOP_BAND = 50;

export function discountBandKey(value) {
  if (value == null) return 'none';
  const band = Math.floor(Number(value) / BAND_SIZE) * BAND_SIZE;
  return String(Math.min(Math.max(band, 0), TOP_BAND));
}

export function discountLabel(key) {
  if (key === 'none') return 'Fără reducere specificată';
  const start = Number(key);
  if (start === 0) return 'Sub 10%';
  if (start >= TOP_BAND) return '50% sau mai mult';
  return `${start}–${start + BAND_SIZE - 1}%`;
}

export function discountOrder(key) {
  return key === 'none' ? Infinity : Number(key);
}

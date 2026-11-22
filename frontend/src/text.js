// Lowercases and strips diacritics so searches match "înghețată" with "inghetata".
export function normalizeText(value) {
  return value
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase();
}

const API = import.meta.env.VITE_API_URL;

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

export function formatErrors(err) {
  const d = err?.data;
  if (!d) return 'Nu m-am putut conecta la server.';
  if (d.detail) return d.detail;
  return Object.entries(d)
    .map(([k, v]) => `${k}: ${[].concat(v).join(' ')}`)
    .join('\n');
}
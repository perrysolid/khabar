const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

function getErrorMessage(payload, fallback) {
  const detail = payload?.detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message || JSON.stringify(item))
      .join(", ");
  }
  if (detail && typeof detail === "object") {
    return detail.msg || detail.message || JSON.stringify(detail);
  }
  if (typeof payload?.message === "string") {
    return payload.message;
  }
  return fallback;
}

export function getToken() {
  return localStorage.getItem("token");
}

export function setToken(token) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers
  };

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 401) {
    clearToken();
    if (window.location.pathname !== "/login") {
      window.location.assign("/login");
    }
    throw new Error("Please log in again");
  }
  return response;
}

async function authenticate(path, email, password) {
  const response = await request(path, {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(getErrorMessage(payload, "Authentication failed"));
  }
  const data = await response.json();
  setToken(data.access_token);
  return data;
}

export function signup(email, password) {
  return authenticate("/auth/signup", email, password);
}

export function login(email, password) {
  return authenticate("/auth/login", email, password);
}

export async function getTodayDigest() {
  const response = await request("/api/digest/today");
  if (!response.ok) {
    throw new Error("Could not load digest");
  }
  return response.json();
}

export async function sendFeedback(articleId, feedback) {
  const response = await request("/api/feedback", {
    method: "POST",
    body: JSON.stringify({ article_id: articleId, feedback })
  });
  if (!response.ok) {
    throw new Error("Could not send feedback");
  }
  return response.json();
}

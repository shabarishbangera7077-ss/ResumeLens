const API_BASE = "";

function authToken() {
  return localStorage.getItem("resumelens_token");
}

async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = authToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 401) {
    localStorage.removeItem("resumelens_token");
    if (!location.pathname.endsWith("/login.html")) location.href = "/static/login.html";
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch (error) {
      if (!(error instanceof SyntaxError)) throw error;
    }
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

function requireLogin() {
  if (!authToken()) location.href = "/static/login.html";
}

function showError(target, message) {
  target.textContent = message;
  target.classList.add("visible");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

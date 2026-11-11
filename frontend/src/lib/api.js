const BASE = (import.meta.env.VITE_API_BASE ?? "/api").replace(/\/$/, "");

async function request(path, signal) {
  const response = await fetch(`${BASE}${path}`, {
    signal,
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* Keep the status-based message. */
    }
    throw new Error(detail);
  }

  return response.json();
}

function queryString(params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      search.set(key, String(value));
    }
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const api = {
  health: (signal) => request("/health", signal),
  overview: (signal) => request("/overview", signal),
  alerts: (filters, signal) => request(`/alerts${queryString(filters)}`, signal),
  alertFilters: (signal) => request("/alerts/filters", signal),
  evidence: (alertId, signal) => request(`/alerts/${alertId}/evidence`, signal),
  incidents: (signal) => request("/incidents", signal),
  incident: (incidentId, signal) => request(`/incidents/${incidentId}`, signal),
  timeline: (incidentId, signal) => request(`/incidents/${incidentId}/timeline`, signal),
};

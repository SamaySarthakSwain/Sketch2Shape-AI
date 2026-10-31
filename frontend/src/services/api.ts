/**
 * Central API Client for Sketch2Shape AI
 */

const API_BASE = ''; // Relies on Vite proxy to http://127.0.0.1:8000

export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = new Headers(options.headers || {});
  
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || JSON.stringify(errorJson);
    } catch {
      // Fallback to text
      const text = await response.text();
      if (text) errorDetail = text;
    }
    throw new Error(errorDetail || `API request failed with status ${response.status}`);
  }

  return response.json();
}

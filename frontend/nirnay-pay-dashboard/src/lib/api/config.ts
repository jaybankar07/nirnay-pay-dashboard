/**
 * Centralised API configuration.
 *
 * Point the app at the real backend by setting:
 *   VITE_API_BASE_URL=http://localhost:8000/api/v1
 *   VITE_MERCHANT_ID=merchant_001
 *   VITE_USE_FIXTURES=false
 */

const env = import.meta.env as Record<string, string | undefined>;

export const API_BASE_URL = env['VITE_API_BASE_URL'] ?? "http://localhost:8000/api/v1";

export const MERCHANT_ID = env['VITE_MERCHANT_ID'] ?? "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";

/**
 * Check if fixture mode is currently enabled (supports localStorage override).
 */
export function isUseFixtures(): boolean {
  if (typeof window !== "undefined") {
    const local = localStorage.getItem("VITE_USE_FIXTURES");
    if (local !== null) {
      return local === "true";
    }
  }
  return (env['VITE_USE_FIXTURES'] ?? "false") === "true";
}

/**
 * Dynamically toggle between Live FastAPI Backend Mode and Fixture Mode.
 */
export function setUseFixtures(useFixtures: boolean): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("VITE_USE_FIXTURES", String(useFixtures));
    window.location.reload();
  }
}

export const USE_FIXTURES = isUseFixtures();

/**
 * Hook point for authentication headers once auth exists on the backend.
 */
export function getAuthHeaders(): Record<string, string> {
  return {};
}

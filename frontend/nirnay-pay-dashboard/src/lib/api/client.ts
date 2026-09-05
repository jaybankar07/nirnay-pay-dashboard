import { API_BASE_URL, MERCHANT_ID, isUseFixtures, getAuthHeaders } from "./config";
import { fixtureTransport } from "./fixture-transport";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function friendlyMessage(status: number): string {
  if (status === 404) return "We couldn't find that record.";
  if (status === 401 || status === 403) return "You don't have access to this resource.";
  if (status === 409) return "This request conflicts with the current state of the case.";
  if (status >= 500) return "The recovery service is temporarily unavailable.";
  return "The request could not be completed.";
}

type Query = Record<string, string | number | boolean | null | undefined>;

function buildUrl(path: string, query?: Query): string {
  const url = `${API_BASE_URL.replace(/\/$/, "")}${path}`;
  if (!query) return url;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === null || value === undefined || value === "") continue;
    params.set(key, String(value));
  }
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}

async function request<T>(
  method: "GET" | "POST",
  path: string,
  options: { query?: Query; body?: unknown } = {},
): Promise<T> {
  if (isUseFixtures()) {
    return fixtureTransport<T>(method, path, options.query, options.body);
  }

  let response: Response;
  try {
    const fetchHeaders = {
      "content-type": "application/json",
      ...getAuthHeaders(),
    };
    const fetchOptions: RequestInit = {
      method,
      headers: fetchHeaders,
    };
    if (options.body !== undefined) {
      fetchOptions.body = JSON.stringify(options.body);
    }
    response = await fetch(buildUrl(path, options.query), fetchOptions);
  } catch {
    throw new ApiError("Unable to reach the recovery service.", 0);
  }

  if (!response.ok) {
    // Never surface raw backend stack traces to the UI.
    throw new ApiError(friendlyMessage(response.status), response.status);
  }

  if (response.status === 204) return undefined as T;
  const json = await response.json();
  return (json?.data !== undefined ? json.data : json) as T;
}

export const api = {
  get: <T>(path: string, query?: Query) => {
    const opts: { query?: Query; body?: unknown } = {};
    if (query !== undefined) opts.query = query;
    return request<T>("GET", path, opts);
  },
  post: <T>(path: string, body?: unknown, query?: Query) => {
    const opts: { query?: Query; body?: unknown } = {};
    if (body !== undefined) opts.body = body;
    if (query !== undefined) opts.query = query;
    return request<T>("POST", path, opts);
  },
  merchantId: MERCHANT_ID,
};

const defaultBaseUrl = "http://localhost:8000";

export const AUTH_TOKEN_KEY = "pawcare_access_token";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || defaultBaseUrl;

export function getStoredToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function storeAuthToken(token: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  }
}

export function clearAuthToken() {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(AUTH_TOKEN_KEY);
  }
}

export async function apiRequest<T>(
  path: string,
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" = "GET",
  body?: Record<string, unknown> | FormData,
  token?: string | null,
): Promise<T> {
  const headers: Record<string, string> = {};

  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    cache: "no-store",
    headers,
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      typeof payload?.detail === "string"
        ? payload.detail
        : `Request failed for ${path}: ${response.status}`,
    );
  }

  return payload as T;
}

export async function apiGet<T>(path: string, token?: string | null): Promise<T> {
  return apiRequest<T>(path, "GET", undefined, token);
}

export async function apiPost<T>(
  path: string,
  body: Record<string, unknown>,
  token?: string | null,
): Promise<T> {
  return apiRequest<T>(path, "POST", body, token);
}

export async function apiPut<T>(
  path: string,
  body: Record<string, unknown>,
  token?: string | null,
): Promise<T> {
  return apiRequest<T>(path, "PUT", body, token);
}

export async function apiDelete<T>(
  path: string,
  token?: string | null,
): Promise<T> {
  return apiRequest<T>(path, "DELETE", undefined, token);
}

export async function apiUpload<T>(
  path: string,
  formData: FormData,
  token?: string | null,
): Promise<T> {
  return apiRequest<T>(path, "POST", formData, token);
}

export function getAttachmentUrl(url: string | null | undefined): string {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }
  const cleanBase = API_BASE_URL.replace(/\/+$/, "");
  const cleanPath = url.startsWith("/") ? url : `/${url}`;
  return `${cleanBase}${cleanPath}`;
}


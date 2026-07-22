// ============================================================
// Centralized API Client for AI BI OS
// All pages import from here — never call fetch() directly
// ============================================================

export const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// The access token is short-lived (30 min, app/core/security.py). The backend already
// issues a long-lived httpOnly refresh_token cookie on login and exposes POST /auth/refresh
// to mint a fresh access_token cookie from it — the frontend just never called it, so every
// request just failed outright once the token aged out mid-session. This does one shared
// refresh attempt (not one per in-flight request) and retries the original call on success.
let refreshInFlight: Promise<boolean> | null = null;

function refreshSession(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = fetch(`${BASE_URL}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
    })
      .then((res) => res.ok)
      .catch(() => false)
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

const AUTH_ENDPOINTS = ["/api/v1/auth/login", "/api/v1/auth/signup", "/api/v1/auth/refresh", "/api/v1/auth/2fa/login-verify"];

async function request<T>(path: string, options?: RequestInit, isRetry = false): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: 'include',
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "Authorization": `Bearer ${token}` } : {}),
      ...(options?.headers ?? {}),
    },
  });
  if (!res.ok) {
    if (res.status === 401 && !isRetry && !AUTH_ENDPOINTS.some((p) => path.startsWith(p))) {
      const refreshed = await refreshSession();
      if (refreshed) {
        return request<T>(path, options, true);
      }
    }

    const errorText = await res.text();
    let errorMessage = errorText;
    try {
      const errorJson = JSON.parse(errorText);
      if (errorJson.detail) {
        errorMessage = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch (e) {
      // Not JSON, use raw text
    }
    // Refresh failed too (or this was already a retry) — the session is genuinely over.
    // Bounce to login instead of letting every caller render the raw 401 as if it were
    // its own feature failing (chat, KPI cards, etc. all hit this the same way).
    // Auth-action endpoints are excluded: a 401 there (e.g. wrong login password)
    // is the endpoint's normal response, not a sign the current session died.
    if (res.status === 401 && typeof window !== "undefined" && !AUTH_ENDPOINTS.some((p) => path.startsWith(p))) {
      localStorage.removeItem("access_token");
      if (window.location.pathname !== "/login" && window.location.pathname !== "/signup") {
        window.location.href = "/login";
      }
    }
    throw new Error(errorMessage || `Request failed with status ${res.status}`);
  }
  return res.json();
}

const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),

  // Multipart file upload
  upload: async <T>(path: string, formData: FormData): Promise<T> => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    const res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      credentials: 'include',
      body: formData,
      headers: {
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
      },
    });
    if (!res.ok) {
      const errorText = await res.text();
      let errorMessage = errorText;
      try {
        const errorJson = JSON.parse(errorText);
        if (errorJson.detail) {
          errorMessage = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch (e) {
        // Not JSON, use raw text
      }
      throw new Error(errorMessage || `Upload failed with status ${res.status}`);
    }
    return res.json();
  },
};
export default api;

// ============================================================
// Typed endpoint helpers
// ============================================================

// Auth / account (Settings page)
interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  created_at?: string;
  totp_enabled?: boolean;
  has_avatar?: boolean;
  email_verified?: boolean;
  phone?: string | null;
}

export function avatarUrl(userId: string, cacheBust?: number) {
  return `${BASE_URL}/api/v1/auth/avatar/${userId}${cacheBust ? `?v=${cacheBust}` : ""}`;
}

export interface SessionInfo {
  id: string;
  device: string;
  ip_address: string;
  created_at: string;
  last_active_at: string;
  is_current: boolean;
}

export interface LoginResult {
  message?: string;
  access_token?: string;
  token_type?: string;
  requires_2fa?: boolean;
  pre_auth_token?: string;
  verification_email_sent?: boolean;
}

export const authApi = {
  me: () => api.get<UserProfile>("/api/v1/auth/me"),
  updateProfile: (full_name: string, phone?: string | null) =>
    api.patch<UserProfile>("/api/v1/auth/me", { full_name, phone }),
  resendVerification: () => api.post<{ message: string }>("/api/v1/auth/resend-verification", {}),
  verifyEmail: (token: string) => api.post<{ message: string }>("/api/v1/auth/verify-email", { token }),
  changePassword: (current_password: string, new_password: string) =>
    api.post<{ message: string }>("/api/v1/auth/change-password", { current_password, new_password }),
  deleteAccount: () => api.delete<{ message: string }>("/api/v1/auth/me"),
  uploadAvatar: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.upload<UserProfile>("/api/v1/auth/avatar", formData);
  },
  removeAvatar: () => api.delete<UserProfile>("/api/v1/auth/avatar"),
  listSessions: () => api.get<SessionInfo[]>("/api/v1/auth/sessions"),
  revokeSession: (id: string) => api.delete<{ message: string }>(`/api/v1/auth/sessions/${id}`),
  revokeOtherSessions: () => api.delete<{ message: string }>("/api/v1/auth/sessions"),
  exportData: () => api.get<Record<string, unknown>>("/api/v1/auth/export-data"),
  login: (email: string, password: string) =>
    api.post<LoginResult>("/api/v1/auth/login", { email, password }),
  verify2FALogin: (pre_auth_token: string, code: string) =>
    api.post<LoginResult>("/api/v1/auth/2fa/login-verify", { pre_auth_token, code }),
  setup2FA: () => api.post<{ secret: string; qr_code: string }>("/api/v1/auth/2fa/setup", {}),
  enable2FA: (code: string) =>
    api.post<{ message: string; recovery_codes: string[] }>("/api/v1/auth/2fa/enable", { code }),
  disable2FA: (password: string) =>
    api.post<{ message: string }>("/api/v1/auth/2fa/disable", { password }),
};

// Datasets (Module 1, 2)
export const datasetsApi = {
  list: (workspace_id = "workspace-123") =>
    api.get<import("./types").Dataset[]>(
      `/api/v1/datasets?workspace_id=${workspace_id}`
    ),
  get: (id: string) => api.get<import("./types").Dataset>(`/api/v1/datasets/${id}`),
  upload: (formData: FormData) =>
    api.upload<{ job_id: string; status: string }>("/api/v1/datasets/upload", formData),
  uploadStatus: (jobId: string) =>
    api.get<import("./types").UploadJob>(`/api/v1/datasets/upload/status/${jobId}`),
  delete: (id: string) => api.delete(`/api/v1/datasets/${id}`),
  getActive: () => api.get<import("./types").ActiveDatasetInfo | null>("/api/v1/datasets/active"),
  activate: (id: string) => api.post(`/api/v1/datasets/${id}/activate`, {}),
  download: async (id: string) => {
    const res = await fetch(`${BASE_URL}/api/v1/datasets/${id}/download`, { credentials: 'include' });
    if (!res.ok) throw new Error("Failed to download dataset");
    const blob = await res.blob();
    const contentDisposition = res.headers.get('Content-Disposition');
    let filename = 'dataset.csv';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) filename = match[1];
    }
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },
};

// Schema (Module 3)
export const schemaApi = {
  get: (datasetVersionId: string) =>
    api.get<import("./types").SchemaInfo>(`/api/v1/schema/${datasetVersionId}`),
};

// Profiling (Module 4)
export const profileApi = {
  get: (datasetVersionId: string) =>
    api.get<import("./types").DataProfile>(`/api/v1/profile/${datasetVersionId}`),
};

// Quality (Module 5)
export const qualityApi = {
  get: (datasetVersionId: string) =>
    api.get<import("./types").QualityReport>(`/api/v1/quality/${datasetVersionId}`),
};

// Cleaning (Module 6)
export const cleaningApi = {
  get: (datasetVersionId: string) =>
    api.get<import("./types").CleaningReport>(`/api/v1/cleaning/${datasetVersionId}`),
  trigger: (body: { dataset_version_id: string; workspace_id: string }) =>
    api.post("/api/v1/cleaning/run", body),
};

// Privacy (Module 7)
export const privacyApi = {
  report: (datasetVersionId: string) =>
    api.get<import("./types").PrivacyReport>(
      `/api/v1/privacy/${datasetVersionId}/report`
    ),
};

// Semantic Intelligence (Module 8)
export const semanticApi = {
  get: (datasetVersionId: string) =>
    api.get<import("./types").SemanticProfile>(
      `/api/v1/semantic/${datasetVersionId}`
    ),
};

// Metadata Catalog (Module 9)
export const catalogApi = {
  list: (workspace_id = "workspace-123") =>
    api.get<import("./types").CatalogEntry[]>(
      `/api/v1/catalog?workspace_id=${workspace_id}`
    ),
  search: (query: string) =>
    api.get<import("./types").CatalogEntry[]>(
      `/api/v1/catalog/search?q=${encodeURIComponent(query)}`
    ),
};

// Query Engine (Module 10)
export const queryApi = {
  execute: (body: { sql: string; dataset_version_id: string; workspace_id: string }) =>
    api.post<import("./types").QueryResult>("/api/v1/query/execute", body),
};

// Analytics Engine (Module 11)
export const analyticsApi = {
  prefetch: () => api.get<{ active_dataset: any; kpis: any }>("/api/v1/analytics/prefetch"),
  kpis: () => api.get<import("./types").AnalyticsKPIs>("/api/v1/analytics/kpis"),
  kpiCenter: () => api.get<any>("/api/v1/analytics/kpi-center"),
  eda: () => api.get<any>("/api/v1/analytics/eda"),
  edaColumn: (column: string) => api.get<any>(`/api/v1/analytics/eda/column/${encodeURIComponent(column)}`),
  statistics: () => api.get<any>("/api/v1/analytics/statistics"),
  correlation: () => api.get<any>("/api/v1/analytics/correlation"),
  distribution: () => api.get<any>("/api/v1/analytics/distribution"),
  outliers: () => api.get<any>("/api/v1/analytics/outliers"),
  timeseries: (metric?: string) => api.get<any>(`/api/v1/analytics/timeseries${metric ? `?metric=${metric}` : ''}`),
  trend: () => api.get<any>("/api/v1/analytics/trend"),
  confidence: () => api.get<{
    insights: { verified: number; unverified: number };
    recommendations: { verified: number; unverified: number };
    audit_trail: any[];
  }>("/api/v1/analytics/confidence"),
  forecast: (metric?: string) => api.get<any>(`/api/v1/analytics/forecast${metric ? `?metric=${metric}` : ''}`),
  regressionModels: () => api.get<any[]>("/api/v1/analytics/regression/models"),
  regressionQualitySummary: () => api.get<any>("/api/v1/analytics/regression/quality-summary"),
  trends: (datasetVersionId: string) =>
    api.get<import("./types").TrendData[]>(
      `/api/v1/analytics/trends?dataset_version_id=${datasetVersionId}`
    ),
};


// Insights (Module 12)
export const insightsApi = {
  list: (datasetVersionId?: string) =>
    api.get<import("./types").Insight[]>(
      `/api/v1/insights${datasetVersionId ? `?dataset_version_id=${datasetVersionId}` : ""}`
    ),
  executiveSummary: () =>
    api.get<{ summary: string; highlights?: string[]; verified: boolean }>(
      "/api/v1/insights/executive-summary"
    ),
  deepAnalyze: () =>
    api.post<{ success: boolean; insights: any[] }>("/api/v1/insights/deep-analyze", {}),
};

// Rules (Module 14)
export const rulesApi = {
  list: () =>
    api.get<import("./types").BusinessRule[]>(
      `/api/v1/rules`
    ),
  create: (body: Partial<import("./types").BusinessRule>) =>
    api.post<{id: string, success: boolean}>("/api/v1/rules", body),
  update: (id: string, body: Partial<import("./types").BusinessRule>) =>
    api.patch<{success: boolean}>(`/api/v1/rules/${id}`, body),
  delete: (id: string) =>
    api.delete<{success: boolean}>(`/api/v1/rules/${id}`),
  parseText: (text: string) =>
    api.post<{success: boolean, parsed: any, error?: string}>("/api/v1/rules/parse-text", { text }),
};

// Recommendations (Module 15)
export const recommendationsApi = {
  list: (datasetVersionId?: string) =>
    api.get<import("./types").Recommendation[]>(
      `/api/v1/recommendations${datasetVersionId ? `?dataset_version_id=${datasetVersionId}` : ""}`
    ),
  generate: (force: boolean = false) =>
    api.post<any>(`/api/v1/recommendations/generate${force ? "?force=true" : ""}`, {}),
};

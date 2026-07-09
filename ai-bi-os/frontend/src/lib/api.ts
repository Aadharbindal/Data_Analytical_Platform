// ============================================================
// Centralized API Client for AI BI OS
// All pages import from here — never call fetch() directly
// ============================================================

export const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),

  // Multipart file upload
  upload: async <T>(path: string, formData: FormData): Promise<T> => {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const error = await res.text();
      throw new Error(error || `Upload failed with status ${res.status}`);
    }
    return res.json();
  },
};

// ============================================================
// Typed endpoint helpers
// ============================================================

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
  kpis: () => api.get<import("./types").AnalyticsKPIs>("/api/v1/analytics/kpis"),
  kpiCenter: () => api.get<any>("/api/v1/analytics/kpi-center"),
  eda: () => api.get<any>("/api/v1/analytics/eda"),
  statistics: () => api.get<any>("/api/v1/analytics/statistics"),
  correlation: () => api.get<any>("/api/v1/analytics/correlation"),
  distribution: () => api.get<any>("/api/v1/analytics/distribution"),
  outliers: () => api.get<any>("/api/v1/analytics/outliers"),
  timeseries: (metric: string) => api.get<any>(`/api/v1/analytics/timeseries?metric=${metric}`),
  trend: () => api.get<any>("/api/v1/analytics/trend"),
  forecast: (metric: string) => api.get<any>(`/api/v1/analytics/forecast?metric=${metric}`),
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
};

// Rules (Module 14)
export const rulesApi = {
  list: (workspaceId = "workspace-123") =>
    api.get<import("./types").BusinessRule[]>(
      `/api/v1/rules?workspace_id=${workspaceId}`
    ),
  create: (body: Partial<import("./types").BusinessRule>) =>
    api.post<import("./types").BusinessRule>("/api/v1/rules", body),
};

// Recommendations (Module 15)
export const recommendationsApi = {
  list: (datasetVersionId?: string) =>
    api.get<import("./types").Recommendation[]>(
      `/api/v1/recommendations${datasetVersionId ? `?dataset_version_id=${datasetVersionId}` : ""}`
    ),
};

import api from "../lib/api";

// ---------------------------------------------------------
// Types
// ---------------------------------------------------------
export interface AnalyticsSummary {
  run_id: string;
  dataset_id: string;
  dataset_version_id: string;
  kpis_analyzed: number;
  metrics_analyzed: number;
}

export interface KPI {
  id: string;
  name: string;
  current_value: number;
  previous_value: number;
  growth_percentage: number;
  trend: "UP" | "DOWN" | "FLAT";
  history: Array<{ date: string; value: number }>;
}

export interface BusinessMetric {
  id: string;
  name: string;
  value: number;
  unit: string;
  trend: string;
}

export interface EDAProfile {
  dataset_version_id: string;
  row_count: number;
  column_count: number;
  missing_cells: number;
  duplicate_rows: number;
  columns: Array<{
    name: string;
    type: string;
    null_count: number;
    mean?: number;
    min?: number;
    max?: number;
  }>;
}

export interface CorrelationData {
  features: string[];
  matrix: number[][];
  strong_pairs: Array<{ feature1: string; feature2: string; correlation: number }>;
}

export interface StatisticalTest {
  test_name: string;
  p_value: number;
  is_significant: boolean;
  details: string;
}

export interface RegressionModel {
  model_name: string;
  r2_score: number;
  rmse: number;
  coefficients: Record<string, number>;
}

export interface ValidationScore {
  trust_score: number;
  reliability: string;
  warnings: string[];
}

export interface DistributionProfile {
  column_name: string;
  distribution_type: string;
  histogram: Array<{ bin: string; count: number }>;
}

export interface OutlierData {
  column_name: string;
  outliers: Array<{ value: number; severity: string; index: number }>;
}

export interface TimeSeriesSummary {
  column_name: string;
  frequency: string;
  gaps_detected: number;
  continuity_score: number;
}

export interface TrendSummary {
  column_name: string;
  overall_trend: "INCREASING" | "DECREASING" | "STABLE";
  change_points_count: number;
}

export interface ForecastSummary {
  column_name: string;
  selected_model: string;
  rmse: number;
}

export interface GovernanceSummary {
  model_id: string;
  name: string;
  version: string;
  approval_status: string;
  deployment_status: string;
  quality_score: number;
  trust_score: number;
}

// ---------------------------------------------------------
// API Client
// ---------------------------------------------------------
export const advancedAnalyticsApi = {
  // M18: KPI Engine (Dashboard uses analyticsApi.kpis() in lib/api.ts, this one is extra)
  getKpis: (datasetId: string) => api.get<KPI[]>(`/api/v1/analytics/kpis`),
  
  // M19: Business Metrics Engine (Not implemented in backend yet, stub)
  getBusinessMetrics: (datasetId: string) => api.get<BusinessMetric[]>(`/api/v1/analytics/metrics`),
  
  // M20: EDA Engine
  getEDAProfile: (datasetVersionId: string) => api.get<EDAProfile>(`/api/v1/analytics/eda`),
  
  // M21: Correlation Engine
  getCorrelations: (datasetVersionId: string) => api.get<CorrelationData>(`/api/v1/analytics/correlation`),
  
  // M22: Statistical Inference Engine
  getStatistics: (datasetVersionId: string) => api.get<StatisticalTest[]>(`/api/v1/analytics/statistics`),
  
  // M23: Regression Engine (Not implemented yet, stub)
  getRegression: (datasetVersionId: string) => api.get<RegressionModel[]>(`/api/v1/analytics/regression`),
  
  // M24: Confidence & Validation Engine (Not implemented yet, stub)
  getValidation: (datasetVersionId: string) => api.get<ValidationScore>(`/api/v1/analytics/validation`),
  
  // M25: Distribution Analytics Engine
  getDistributions: (datasetId: string) => api.get<DistributionProfile[]>(`/api/v1/analytics/distribution`),
  
  // M26: Outlier Analysis Engine
  getOutliers: (datasetId: string) => api.get<OutlierData[]>(`/api/v1/analytics/outliers`),
  
  // M27: Time Series Analytics Engine (defaults to revenue)
  getTimeSeries: (datasetId: string) => api.get<TimeSeriesSummary[]>(`/api/v1/analytics/timeseries?metric=revenue`),
  
  // M28: Trend & Change Detection Engine
  getTrends: (datasetId: string) => api.get<TrendSummary[]>(`/api/v1/analytics/trend`),
  
  // M29: Forecasting Engine (defaults to revenue)
  getForecasts: (datasetId: string) => api.get<ForecastSummary[]>(`/api/v1/analytics/forecast?metric=revenue`),
  
  // M30: Forecast Governance Engine (Not implemented yet, stub)
  getGovernance: (modelId: string) => api.get<GovernanceSummary>(`/api/v1/analytics/governance`),
};

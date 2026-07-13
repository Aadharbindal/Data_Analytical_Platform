// ============================================================
// Shared TypeScript types mirroring backend Pydantic models
// ============================================================

export interface SemanticDict {
  domain: string;
  semantic_dictionary: {
    date_columns: string[];
    numeric_metrics: string[];
    categorical_fields: string[];
    entity_identifiers: string[];
    status_fields: string[];
    geographic_fields: string[];
  };
  business_terminology: {
    dashboard_title: string;
    primary_metric: string;
    primary_metric_label: string;
    primary_metric_op: string;
    primary_metric_type: "currency" | "count" | "percent" | "generic";
    entity_col: string;
    entity_count_label: string;
    secondary_metric?: string;
    secondary_metric_label?: string;
    secondary_metric_op?: string;
    secondary_metric_type?: "currency" | "count" | "percent" | "generic";
    status_col?: string;
    status_metric_label?: string;
    status_healthy_regex?: string;
    status_unhealthy_regex?: string;
    chart_title: string;
  };
}

export interface Dataset {
  id: string;
  workspace_id: string;
  name: string;
  description?: string;
  status: "active" | "archived" | "deleted" | "processing";
  owner_id?: string;
  project_id?: string;
  created_at: string;
  updated_at?: string;
  latest_version?: DatasetVersion;
  skipped_rows?: number;
  sheet_name?: string;
  version?: number;
  quality_score?: number;
  quality_breakdown?: {
    completeness: number;
    uniqueness: number;
    type_consistency: number;
    validity: number;
  };
  domain?: string;
  semantic_dict?: SemanticDict;
}

export interface ActiveDatasetInfo {
  id: string;
  name: string;
  row_count?: number;
  columns?: any[];
  skipped_rows?: number;
  sheet_name?: string;
  version?: number;
  quality_score?: number;
  quality_breakdown?: {
    completeness: number;
    uniqueness: number;
    type_consistency: number;
    validity: number;
  };
  domain?: string;
  semantic_dict?: SemanticDict;
}

export interface DatasetVersion {
  id: string;
  dataset_id: string;
  version_number: number;
  file_path: string;
  row_count?: number;
  file_size_bytes?: number;
  status: string;
  created_at: string;
}

export interface UploadJob {
  id: string;
  status: "pending" | "processing" | "completed" | "failed";
  filename?: string;
  progress?: number;
  error?: string;
  dataset_id?: string;
  created_at: string;
}

export interface SchemaColumn {
  name: string;
  data_type: string;
  is_nullable?: boolean;
  sample_values?: string[];
}

export interface SchemaInfo {
  id: string;
  dataset_version_id: string;
  columns: SchemaColumn[];
  total_columns: number;
}

export interface ColumnProfile {
  name: string;
  data_type: string;
  null_count: number;
  null_percentage: number;
  distinct_count: number;
  min?: string;
  max?: string;
  mean?: number;
  std?: number;
}

export interface DataProfile {
  id: string;
  dataset_version_id: string;
  row_count: number;
  column_count: number;
  completeness_score: number;
  columns: ColumnProfile[];
}

export interface QualityIssue {
  column?: string;
  rule: string;
  severity: "low" | "medium" | "high" | "critical";
  count: number;
  description: string;
}

export interface QualityReport {
  id: string;
  dataset_version_id: string;
  overall_score: number;
  completeness_score: number;
  validity_score: number;
  issues: QualityIssue[];
  created_at: string;
}

export interface CleaningOperation {
  operation_type: string;
  column?: string;
  description: string;
  affected_rows?: number;
}

export interface CleaningReport {
  id: string;
  dataset_version_id: string;
  status: string;
  operations: CleaningOperation[];
  created_at: string;
}

export interface PIIColumn {
  column_name: string;
  pii_types: string[];
  confidence: number;
  masking_strategy: string;
}

export interface PrivacyReport {
  id: string;
  dataset_version_id: string;
  pii_columns: PIIColumn[];
  risk_level: "low" | "medium" | "high" | "critical";
  compliance_status: string;
  created_at: string;
}

export interface SemanticProfile {
  id: string;
  dataset_version_id: string;
  business_domain?: string;
  business_entity?: string;
  column_labels: Record<string, string>;
  tags: string[];
}

export interface CatalogEntry {
  id: string;
  workspace_id: string;
  name: string;
  description?: string;
  business_domain?: string;
  owner?: string;
  tags: string[];
  column_count: number;
  last_updated?: string;
  dataset_version_id?: string;
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  execution_time_ms: number;
}

export interface AnalyticsKPIs {
  kpis?: Array<{ name: string; value: number; trend?: number }>;
  chart_data?: Array<{ name: string; value: number | null; previous?: number | null; forecast?: number | null }>;
}

export interface TrendData {
  period: string;
  value: number;
}

export interface InsightScore {
  confidence: number;
  impact?: number | string;
}

export interface Insight {
  id: string;
  title: string;
  description?: string;
  category: string;
  metric_name?: string;
  metric_value?: number;
  insight_level?: string;
  confidence?: number;
  impact?: number | string;
  recommendation?: string;
  verified?: boolean;
  audit_sql?: string;
  score?: InsightScore;
  dataset_version_id?: string;
  created_at: string;
}

export interface BusinessRule {
  id: string;
  workspace_id?: string;
  name: string;
  metric_column?: string;
  condition: string;
  threshold?: number;
  window?: string;
  is_active?: boolean;
  status?: string;
  current_value?: number;
  created_at: string;
}

export interface Recommendation {
  id: string;
  title: string;
  rationale?: string;
  category: string;
  priority: string;
  verified?: boolean;
  dataset_version_id?: string;
  created_at: string;
}

export interface ExecutiveSummary {
  verified: boolean;
  summary: string;
  highlights?: string[];
}

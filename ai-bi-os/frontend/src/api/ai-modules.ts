/**
 * AI Modules API Client — Modules 40–50
 * All admin dashboards import from this file.
 * No mock data, no setTimeout. All calls go to the backend.
 */

import { api } from "../lib/api";

const WS = "workspace-123"; // Default workspace — replace with session/auth context

// ─── Module 40: RAG ────────────────────────────────────────────────────────────
export interface RAGDocument {
  id: string;
  title: string;
  content: string;
  source_type: string;
  created_at: string;
}
export interface RAGSearchResult {
  document_id: string;
  score: number;
  content_snippet: string;
}
export const ragApi = {
  listDocuments: () => api.get<RAGDocument[]>(`/rag/documents?workspace_id=${WS}`),
  search: (query: string, top_k = 5) =>
    api.post<RAGSearchResult[]>("/rag/search", { workspace_id: WS, query, top_k }),
  ingest: (title: string, content: string, source_type = "TEXT") =>
    api.post<RAGDocument>("/rag/ingest", { workspace_id: WS, title, content, source_type }),
};

// ─── Module 41: Vector Store ──────────────────────────────────────────────────
export interface EmbeddingRecord {
  id: string;
  source_id: string;
  model_name: string;
  created_at: string;
}
export interface SimilarityResult {
  id: string;
  score: number;
}
export const vectorApi = {
  listEmbeddings: () => api.get<EmbeddingRecord[]>(`/vector/embeddings?workspace_id=${WS}`),
  search: (query: string, top_k = 5, model = "all-MiniLM-L6-v2") =>
    api.post<SimilarityResult[]>("/vector/search", { workspace_id: WS, query, top_k, model }),
};

// ─── Module 42: AI Memory ─────────────────────────────────────────────────────
export interface MemoryObject {
  id: string;
  memory_type: string;
  content: string;
  importance_score: number;
  created_at: string;
}
export const memoryApi = {
  list: () => api.get<MemoryObject[]>(`/memory/memories?workspace_id=${WS}`),
  getTimeline: () => api.get<MemoryObject[]>(`/memory/timeline?workspace_id=${WS}`),
  getSummary: () => api.get<{ total_memories: number; types: Record<string, number> }>(`/memory/summary?workspace_id=${WS}`),
};

// ─── Module 43: Conversation ──────────────────────────────────────────────────
export interface ConversationSession {
  id: string;
  title: string;
  status: string;
  created_at: string;
  message_count: number;
}
export interface ConversationMessage {
  id: string;
  session_id: string;
  role: string;
  content: string;
  created_at: string;
}
export const conversationApi = {
  listSessions: () => api.get<ConversationSession[]>(`/conversation/sessions?workspace_id=${WS}`),
  getMessages: (session_id: string) =>
    api.get<ConversationMessage[]>(`/conversation/sessions/${session_id}/messages`),
  getSummary: () =>
    api.get<{ total_sessions: number; active_sessions: number; avg_messages: number }>(`/conversation/summary?workspace_id=${WS}`),
  createSession: (title: string) =>
    api.post<ConversationSession>("/conversation/sessions", { workspace_id: WS, title }),
};

// ─── Module 44: Insight Generation ───────────────────────────────────────────
export interface InsightObject {
  id: string;
  headline: string;
  detailed_narrative: string;
  business_domain: string;
  insight_type: string;
  confidence_score: number;
  business_impact_score: number;
  severity: string;
  created_at: string;
}
export interface InsightSummary {
  total_insights: number;
  avg_confidence: number;
  avg_business_impact: number;
  top_domains: string[];
}
export const insightApi = {
  list: () => api.get<InsightObject[]>(`/insights/list?workspace_id=${WS}`),
  getSummary: () => api.get<InsightSummary>(`/insights/summary?workspace_id=${WS}`),
  generate: (dataset_id: string, insight_type = "TREND", domain = "general", evidence_references: {reference_id: string}[] = [{reference_id:"auto"}]) =>
    api.post<InsightObject>("/insights/generate", {
      workspace_id: WS,
      dataset_id,
      insight_type,
      business_domain: domain,
      evidence_references,
      context_references: []
    }),
};

// ─── Module 45: Recommendation ────────────────────────────────────────────────
export interface RecommendationObject {
  id: string;
  title: string;
  executive_summary: string;
  detailed_recommendation: string;
  business_domain: string;
  recommendation_type: string;
  confidence_score: number;
  priority: number;
  status: string;
  created_at: string;
}
export interface RecommendationSummary {
  total_recommendations: number;
  avg_confidence: number;
  avg_roi: number;
}
export const recommendationApi = {
  list: () => api.get<RecommendationObject[]>(`/recommendations/list?workspace_id=${WS}`),
  getSummary: () => api.get<RecommendationSummary>(`/recommendations/summary?workspace_id=${WS}`),
  generate: (insight_id: string, domain = "general") =>
    api.post<RecommendationObject>("/recommendations/generate", {
      workspace_id: WS,
      insight_id,
      business_domain: domain,
      recommendation_type: "STRATEGIC",
      evidence_references: [{ reference_id: insight_id }],
      insight_references: []
    }),
};

// ─── Module 46: Decision Intelligence ────────────────────────────────────────
export interface DecisionObject {
  id: string;
  decision_summary: string;
  selected_strategy: string;
  decision_type: string;
  business_objective: string;
  expected_roi: number;
  expected_risk: string;
  confidence_score: number;
  approval_status: string;
  created_at: string;
}
export const decisionApi = {
  list: () => api.get<DecisionObject[]>(`/decisions/list?workspace_id=${WS}`),
  generate: (recommendation_ids: string[], objective = "maximize roi") =>
    api.post<DecisionObject>("/decisions/generate", {
      workspace_id: WS,
      decision_type: "OPERATIONAL",
      business_objective: objective,
      recommendation_ids
    }),
};

// ─── Module 47: Business Rule Engine ─────────────────────────────────────────
export interface BusinessRule {
  id: string;
  name: string;
  description: string;
  rule_category: string;
  status: string;
  created_at: string;
}
export const businessRuleApi = {
  list: () => api.get<BusinessRule[]>(`/business-rules/rules?workspace_id=${WS}`),
  getExecutionHistory: () => api.get<any[]>(`/business-rules/executions?workspace_id=${WS}`),
};

// ─── Module 48: AI Validation ─────────────────────────────────────────────────
export interface ValidationObject {
  id: string;
  response_id: string;
  validation_type: string;
  overall_status: string;
  confidence_score: number;
  created_at: string;
}
export interface ValidationSummary {
  total_validations: number;
  passed: number;
  failed: number;
  avg_confidence: number;
}
export const aiValidationApi = {
  list: () => api.get<ValidationObject[]>(`/ai-validation/validations?workspace_id=${WS}`),
  getSummary: () => api.get<ValidationSummary>(`/ai-validation/summary?workspace_id=${WS}`),
};

// ─── Module 49: AI Evaluation ─────────────────────────────────────────────────
export interface EvaluationObject {
  id: string;
  evaluation_type: string;
  target_module: string;
  overall_score: number;
  quality_score: number;
  cost_score: number;
  latency_score: number;
  created_at: string;
}
export interface LeaderboardEntry {
  id: string;
  entity_name: string;
  category: string;
  aggregated_score: number;
  overall_rank: number;
}
export const aiEvaluationApi = {
  list: () => api.get<EvaluationObject[]>("/ai-evaluation/evaluations"),
  getLeaderboard: () =>
    api.get<{ MODEL: LeaderboardEntry[]; PROMPT: LeaderboardEntry[]; WORKFLOW: LeaderboardEntry[] }>(
      `/ai-evaluation/leaderboard?workspace_id=${WS}`
    ),
  getRegressions: () => api.get<any[]>(`/ai-evaluation/regressions?workspace_id=${WS}`),
  runBenchmark: (target_module: string, evaluation_type = "WORKFLOW") =>
    api.post<EvaluationObject>("/ai-evaluation/benchmark", {
      workspace_id: WS,
      suite_id: "default-suite",
      evaluation_type,
      target_module,
      model_version: "v1",
      prompt_version: "v1"
    }),
};

// ─── Module 50: Multi-Agent Coordinator ──────────────────────────────────────
export interface AgentDefinition {
  id: string;
  name: string;
  description: string;
  version: string;
  status: string;
  health: string;
  created_at: string;
}
export interface WorkflowExecution {
  id: string;
  workspace_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  nodes: WorkflowNode[];
  unified_response: Record<string, any> | null;
}
export interface WorkflowNode {
  id: string;
  task_name: string;
  status: string;
  agent_id: string;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}
export const multiAgentApi = {
  listAgents: () => api.get<AgentDefinition[]>("/multi-agent/agents"),
  listWorkflows: () => api.get<{ workflows: WorkflowExecution[]; total: number }>("/multi-agent/workflow/history"),
  getWorkflow: (id: string) => api.get<WorkflowExecution>(`/multi-agent/workflow/${id}`),
  executeWorkflow: (query: string, intent = "generic_query") =>
    api.post<WorkflowExecution>("/multi-agent/workflow/execute", {
      workspace_id: WS,
      request_payload: { query, intent }
    }),
  registerAgent: (name: string, description: string, capabilities: string[]) =>
    api.post<AgentDefinition>("/multi-agent/agents/register", {
      workspace_id: WS,
      name,
      description,
      version: "1.0.0",
      capabilities,
      input_schema: {},
      output_schema: {}
    }),
};

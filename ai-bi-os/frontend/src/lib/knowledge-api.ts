import axios from 'axios';
import { BASE_URL } from './api';

const API_BASE_URL = `${BASE_URL}/rag`;

export interface DocumentIndexRequest {
  workspace_id: string;
  dataset_id?: string;
  filename: string;
  file_type: string;
  content: string;
}

export interface DocumentResponse {
  id: string;
  workspace_id: string;
  dataset_id?: string;
  filename: string;
  file_type: string;
  status: string;
  created_at: string;
}

export interface RetrievalRequest {
  workspace_id: string;
  query: string;
  top_k?: number;
  metadata_filters?: Record<string, any>;
}

export interface ChunkResponse {
  id: string;
  document_id: string;
  sequence_number: number;
  text_content: string;
  similarity_score?: number;
}

export interface RetrievalResponse {
  retrieval_id: string;
  workspace_id: string;
  query: string;
  chunks: ChunkResponse[];
  retrieval_time_ms: number;
  cache_hit: boolean;
}

export interface SearchRequest {
  workspace_id: string;
  query: string;
  top_k?: number;
}

export interface HistoryResponse {
  id: string;
  workspace_id: string;
  query_text: string;
  retrieved_count: number;
  created_at: string;
}

export const knowledgeApi = {
  indexDocument: async (request: DocumentIndexRequest): Promise<DocumentResponse> => {
    const response = await axios.post(`${API_BASE_URL}/index`, request);
    return response.data;
  },

  retrieve: async (request: RetrievalRequest): Promise<RetrievalResponse> => {
    const response = await axios.post(`${API_BASE_URL}/retrieve`, request);
    return response.data;
  },

  search: async (request: SearchRequest): Promise<ChunkResponse[]> => {
    const response = await axios.post(`${API_BASE_URL}/search`, request);
    return response.data;
  },

  getDocuments: async (workspaceId: string): Promise<DocumentResponse[]> => {
    const response = await axios.get(`${API_BASE_URL}/documents?workspace_id=${workspaceId}`);
    return response.data;
  },

  getChunks: async (workspaceId: string): Promise<ChunkResponse[]> => {
    const response = await axios.get(`${API_BASE_URL}/chunks?workspace_id=${workspaceId}`);
    return response.data;
  },

  getHistory: async (workspaceId: string): Promise<HistoryResponse[]> => {
    const response = await axios.get(`${API_BASE_URL}/history?workspace_id=${workspaceId}`);
    return response.data;
  },

  reindex: async (workspaceId: string): Promise<any> => {
    const response = await axios.post(`${API_BASE_URL}/reindex?workspace_id=${workspaceId}`);
    return response.data;
  }
};

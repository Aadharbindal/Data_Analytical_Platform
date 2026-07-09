import axios from 'axios';
import { BASE_URL } from './api';

const API_BASE_URL = `${BASE_URL}/python`;

export interface WorkflowStep {
  step_id: string;
  operation: string;
  parameters: Record<string, any>;
}

export interface WorkflowDefinition {
  intent: string;
  dataset_id: string;
  steps: WorkflowStep[];
}

export interface ExecutionArtifact {
  artifact_id: string;
  artifact_type: string;
  name: string;
  content_uri: string;
}

export interface ExecutionResponse {
  execution_id: string;
  workflow_id: string;
  status: string;
  error_message?: string;
  execution_time_ms?: number;
  started_at: string;
  completed_at?: string;
  artifacts: ExecutionArtifact[];
}

export const pythonApi = {
  executeWorkflow: async (workspaceId: string, workflowDef: WorkflowDefinition): Promise<ExecutionResponse> => {
    const response = await axios.post(`${API_BASE_URL}/execute`, {
      workspace_id: workspaceId,
      workflow_definition: workflowDef
    });
    return response.data;
  },

  validateWorkflow: async (workflowDef: WorkflowDefinition): Promise<{is_safe: boolean, reason: string}> => {
    const response = await axios.post(`${API_BASE_URL}/validate`, {
      workflow_definition: workflowDef
    });
    return response.data;
  },

  getHistory: async (workspaceId: string): Promise<ExecutionResponse[]> => {
    const response = await axios.get(`${API_BASE_URL}/history/${workspaceId}`);
    return response.data;
  },

  getExecution: async (id: string): Promise<ExecutionResponse> => {
    const response = await axios.get(`${API_BASE_URL}/execution/${id}`);
    return response.data;
  },

  getArtifacts: async (id: string): Promise<ExecutionArtifact[]> => {
    const response = await axios.get(`${API_BASE_URL}/artifacts/${id}`);
    return response.data;
  },

  cancelExecution: async (id: string): Promise<any> => {
    const response = await axios.post(`${API_BASE_URL}/cancel/${id}`);
    return response.data;
  }
};

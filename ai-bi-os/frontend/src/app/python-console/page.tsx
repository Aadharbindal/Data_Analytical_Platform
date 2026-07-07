"use client";

import React, { useState, useEffect } from 'react';
import { pythonApi, ExecutionResponse, WorkflowDefinition } from '@/lib/python-api';

export default function PythonAnalyticsConsole() {
  const [executions, setExecutions] = useState<ExecutionResponse[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<ExecutionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const workspaceId = "default-workspace"; // mock for MVP

  useEffect(() => {
    fetchExecutions();
  }, []);

  const fetchExecutions = async () => {
    try {
      setLoading(true);
      const data = await pythonApi.getHistory(workspaceId);
      setExecutions(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    try {
      setLoading(true);
      const mockWorkflow: WorkflowDefinition = {
        intent: "Cluster",
        dataset_id: "mock-dataset",
        steps: [
          {
            step_id: "1",
            operation: "FIT_KMEANS",
            parameters: { n_clusters: 3, columns: ["A", "B"] }
          }
        ]
      };
      
      await pythonApi.executeWorkflow(workspaceId, mockWorkflow);
      await fetchExecutions();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const viewDetails = async (id: string) => {
    try {
      setLoading(true);
      const details = await pythonApi.getExecution(id);
      setSelectedExecution(details);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Python Analytics Console (Module 39)</h1>
      
      {error && <div className="bg-red-100 text-red-700 p-4 rounded mb-6">{error}</div>}
      
      <div className="mb-6 flex gap-4">
        <button 
          onClick={handleExecute}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Mock Run KMeans Workflow
        </button>
        <button 
          onClick={fetchExecutions}
          disabled={loading}
          className="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300 disabled:opacity-50"
        >
          Refresh History
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-xl font-semibold mb-4">Execution History</h2>
          {loading && !executions.length ? (
            <p>Loading...</p>
          ) : (
            <div className="bg-white rounded border overflow-hidden">
              <table className="w-full text-left">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="p-3">ID</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Time (ms)</th>
                    <th className="p-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {executions.map(exec => (
                    <tr key={exec.execution_id} className="border-b">
                      <td className="p-3 truncate max-w-[150px]">{exec.execution_id}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          exec.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                          exec.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {exec.status}
                        </span>
                      </td>
                      <td className="p-3">{exec.execution_time_ms || '-'}</td>
                      <td className="p-3">
                        <button 
                          onClick={() => viewDetails(exec.execution_id)}
                          className="text-blue-600 hover:underline text-sm"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                  {executions.length === 0 && (
                    <tr>
                      <td colSpan={4} className="p-4 text-center text-gray-500">No executions found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-4">Execution Details</h2>
          {selectedExecution ? (
            <div className="bg-white rounded border p-6">
              <div className="mb-4">
                <strong>ID:</strong> {selectedExecution.execution_id}
              </div>
              <div className="mb-4">
                <strong>Status:</strong> {selectedExecution.status}
              </div>
              {selectedExecution.error_message && (
                <div className="mb-4 text-red-600">
                  <strong>Error:</strong> {selectedExecution.error_message}
                </div>
              )}
              <div className="mb-4">
                <strong>Execution Time:</strong> {selectedExecution.execution_time_ms} ms
              </div>
              
              <h3 className="font-semibold mt-6 mb-2">Artifacts Generated</h3>
              {selectedExecution.artifacts && selectedExecution.artifacts.length > 0 ? (
                <ul className="list-disc pl-5">
                  {selectedExecution.artifacts.map(a => (
                    <li key={a.artifact_id} className="mb-2">
                      <div className="font-medium">{a.name} ({a.artifact_type})</div>
                      <div className="text-xs bg-gray-100 p-2 mt-1 rounded overflow-x-auto">
                        <pre>{JSON.stringify(JSON.parse(a.content_uri), null, 2)}</pre>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500 text-sm">No artifacts found.</p>
              )}
            </div>
          ) : (
            <div className="bg-gray-50 border border-dashed rounded p-8 text-center text-gray-500">
              Select an execution to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

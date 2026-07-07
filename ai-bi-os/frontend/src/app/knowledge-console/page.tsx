"use client";

import React, { useState, useEffect } from 'react';
import { knowledgeApi, DocumentResponse, HistoryResponse, ChunkResponse } from '@/lib/knowledge-api';

export default function KnowledgeConsole() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [history, setHistory] = useState<HistoryResponse[]>([]);
  const [searchResults, setSearchResults] = useState<ChunkResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [indexContent, setIndexContent] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  
  const workspaceId = "default-workspace";

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const docs = await knowledgeApi.getDocuments(workspaceId);
      const hist = await knowledgeApi.getHistory(workspaceId);
      setDocuments(docs);
      setHistory(hist);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleIndex = async () => {
    try {
      setLoading(true);
      await knowledgeApi.indexDocument({
        workspace_id: workspaceId,
        filename: `Doc_${new Date().getTime()}.txt`,
        file_type: "txt",
        content: indexContent
      });
      setIndexContent("");
      await fetchData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    try {
      setLoading(true);
      const results = await knowledgeApi.search({
        workspace_id: workspaceId,
        query: searchQuery,
        top_k: 5
      });
      setSearchResults(results);
      // also refresh history
      const hist = await knowledgeApi.getHistory(workspaceId);
      setHistory(hist);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Knowledge Management Console (Module 40)</h1>
      
      {error && <div className="bg-red-100 text-red-700 p-4 rounded mb-6">{error}</div>}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        
        {/* Indexing Section */}
        <div className="bg-white rounded border p-6">
          <h2 className="text-xl font-semibold mb-4">Ingest Document</h2>
          <textarea
            value={indexContent}
            onChange={(e) => setIndexContent(e.target.value)}
            placeholder="Paste document text here to index..."
            className="w-full h-32 border rounded p-2 mb-4"
          />
          <button 
            onClick={handleIndex}
            disabled={loading || !indexContent}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Index Document
          </button>
        </div>

        {/* Search Section */}
        <div className="bg-white rounded border p-6">
          <h2 className="text-xl font-semibold mb-4">Test Knowledge Retrieval</h2>
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search knowledge base..."
              className="flex-1 border rounded p-2"
            />
            <button 
              onClick={handleSearch}
              disabled={loading || !searchQuery}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              Search
            </button>
          </div>
          
          <div className="max-h-48 overflow-y-auto">
            {searchResults.map((chunk, idx) => (
              <div key={idx} className="bg-gray-50 border rounded p-3 mb-2 text-sm">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Doc: {chunk.document_id.substring(0, 8)}...</span>
                  <span>Score: {chunk.similarity_score}</span>
                </div>
                <div className="line-clamp-3">{chunk.text_content}</div>
              </div>
            ))}
            {searchResults.length === 0 && searchQuery && !loading && (
              <div className="text-gray-500 text-sm">No chunks found.</div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Documents */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Indexed Documents</h2>
          <div className="bg-white rounded border overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="p-3">Filename</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {documents.map(doc => (
                  <tr key={doc.id} className="border-b">
                    <td className="p-3">{doc.filename}</td>
                    <td className="p-3 uppercase">{doc.file_type}</td>
                    <td className="p-3">
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                        {doc.status}
                      </span>
                    </td>
                  </tr>
                ))}
                {documents.length === 0 && (
                  <tr>
                    <td colSpan={3} className="p-4 text-center text-gray-500">No documents indexed yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* History */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Retrieval History</h2>
          <div className="bg-white rounded border overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="p-3">Query</th>
                  <th className="p-3">Chunks Retrieved</th>
                  <th className="p-3">Time</th>
                </tr>
              </thead>
              <tbody>
                {history.map(hist => (
                  <tr key={hist.id} className="border-b">
                    <td className="p-3 truncate max-w-[150px]">{hist.query_text}</td>
                    <td className="p-3">{hist.retrieved_count}</td>
                    <td className="p-3 text-gray-500">{new Date(hist.created_at).toLocaleString()}</td>
                  </tr>
                ))}
                {history.length === 0 && (
                  <tr>
                    <td colSpan={3} className="p-4 text-center text-gray-500">No retrieval history yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}

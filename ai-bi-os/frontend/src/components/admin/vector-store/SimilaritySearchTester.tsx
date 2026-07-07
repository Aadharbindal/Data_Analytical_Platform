"use client";

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, Search } from "lucide-react";
import { vectorApi, SimilarityResult } from "@/api/ai-modules";

export function SimilaritySearchTester() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<SimilarityResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async () => {
        if (!query.trim()) return;
        setLoading(true);
        setError(null);
        try {
            const data = await vectorApi.search(query, 5);
            setResults(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle className="flex items-center">
                    <Search className="mr-2 h-5 w-5 text-indigo-500" /> Similarity Search Tester
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex space-x-2 mb-4">
                    <input
                        type="text"
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && handleSearch()}
                        placeholder="Enter a query to find similar embeddings..."
                        className="flex-1 text-sm border rounded px-3 py-2"
                    />
                    <button
                        onClick={handleSearch}
                        disabled={loading}
                        className="px-4 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50"
                    >
                        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
                    </button>
                </div>

                {error && <p className="text-red-500 text-sm mb-3">{error}</p>}

                {results.length > 0 && (
                    <div className="space-y-2">
                        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Results</h3>
                        {results.map((r, i) => (
                            <div key={r.id} className="flex items-center justify-between p-2 border rounded text-sm">
                                <span className="font-mono text-xs text-muted-foreground">#{i + 1} {r.id.slice(0, 12)}…</span>
                                <span className="font-bold text-indigo-600">{(r.score * 100).toFixed(2)}%</span>
                            </div>
                        ))}
                    </div>
                )}

                {!loading && results.length === 0 && query && (
                    <p className="text-sm text-muted-foreground">No similar embeddings found.</p>
                )}
            </CardContent>
        </Card>
    );
}

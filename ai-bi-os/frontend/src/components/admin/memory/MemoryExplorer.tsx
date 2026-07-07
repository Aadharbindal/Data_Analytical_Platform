"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, Brain } from "lucide-react";
import { memoryApi, MemoryObject } from "@/api/ai-modules";

export function MemoryExplorer() {
    const [memories, setMemories] = useState<MemoryObject[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        memoryApi.list()
            .then(data => setMemories(data.slice(0, 20)))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card>
                <CardHeader><CardTitle>Memory Explorer</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin" /></CardContent>
            </Card>
        );
    }
    if (error) return <Card><CardContent className="text-red-500 p-4">{error}</CardContent></Card>;

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center">
                    <Brain className="mr-2 h-5 w-5 text-purple-500" /> Memory Explorer
                </CardTitle>
            </CardHeader>
            <CardContent>
                {memories.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No memory objects stored yet.</p>
                ) : (
                    <div className="space-y-3">
                        {memories.map(mem => (
                            <div key={mem.id} className="p-3 border rounded-lg text-sm">
                                <div className="flex justify-between items-start mb-1">
                                    <span className="font-mono text-xs text-muted-foreground">{mem.memory_type}</span>
                                    <span className="text-xs font-bold text-indigo-600">
                                        {(mem.importance_score * 100).toFixed(0)}% importance
                                    </span>
                                </div>
                                <p className="text-sm line-clamp-2">{mem.content}</p>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

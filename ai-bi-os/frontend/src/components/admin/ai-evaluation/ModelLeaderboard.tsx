"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { aiEvaluationApi, LeaderboardEntry } from "@/api/ai-modules";

export function ModelLeaderboard() {
    const [leaderboard, setLeaderboard] = useState<{ MODEL: LeaderboardEntry[]; PROMPT: LeaderboardEntry[]; WORKFLOW: LeaderboardEntry[] } | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [tab, setTab] = useState<"MODEL" | "PROMPT" | "WORKFLOW">("MODEL");

    useEffect(() => {
        aiEvaluationApi.getLeaderboard()
            .then(setLeaderboard)
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card>
                <CardHeader><CardTitle>Model Leaderboard</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin" /></CardContent>
            </Card>
        );
    }
    if (error) return <Card><CardContent className="text-red-500 p-4">{error}</CardContent></Card>;

    const entries = leaderboard?.[tab] ?? [];

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle>Leaderboard</CardTitle>
                    <div className="flex space-x-1">
                        {(["MODEL", "PROMPT", "WORKFLOW"] as const).map(t => (
                            <button
                                key={t}
                                onClick={() => setTab(t)}
                                className={`px-2 py-1 text-xs rounded ${tab === t ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
                            >
                                {t}
                            </button>
                        ))}
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {entries.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No leaderboard entries yet. Run a benchmark to populate.</p>
                ) : (
                    <div className="space-y-2">
                        {entries.sort((a, b) => a.overall_rank - b.overall_rank).map(entry => (
                            <div key={entry.id} className="flex items-center justify-between p-3 border rounded-lg">
                                <div className="flex items-center space-x-3">
                                    <span className="text-lg font-bold text-muted-foreground">#{entry.overall_rank}</span>
                                    <span className="font-medium text-sm">{entry.entity_name}</span>
                                </div>
                                <span className="font-bold text-sm">{(entry.aggregated_score * 100).toFixed(1)}%</span>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

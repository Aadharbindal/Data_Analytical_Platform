"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, HeartPulse } from "lucide-react";
import { multiAgentApi, AgentDefinition } from "@/api/ai-modules";

export function AgentHealthTracker() {
    const [agents, setAgents] = useState<AgentDefinition[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        multiAgentApi.listAgents()
            .then(data => setAgents(data))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card className="h-full">
                <CardHeader><CardTitle>Agent Health Monitor</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin" /></CardContent>
            </Card>
        );
    }
    if (error) return <Card><CardContent className="text-red-500 p-4">{error}</CardContent></Card>;

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle className="flex items-center">
                    <HeartPulse className="mr-2 h-5 w-5 text-rose-500" /> Agent Health Monitor
                </CardTitle>
            </CardHeader>
            <CardContent>
                {agents.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No agents registered. Use the API to register agents.</p>
                ) : (
                    <div className="space-y-4">
                        {agents.map(ag => (
                            <div key={ag.id} className={`p-3 border rounded-lg bg-white shadow-sm flex flex-col ${ag.health === 'DEGRADED' ? 'border-amber-300 bg-amber-50' : 'border-slate-100'}`}>
                                <div className="flex justify-between items-start mb-2">
                                    <h3 className="font-semibold text-sm">{ag.name}</h3>
                                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                                        ag.health === 'HEALTHY' ? 'bg-green-100 text-green-700' :
                                        ag.health === 'DOWN' ? 'bg-red-100 text-red-700' :
                                        'bg-amber-200 text-amber-800'
                                    }`}>{ag.health}</span>
                                </div>
                                <div className="flex items-center justify-between text-xs mt-1 text-slate-500">
                                    <span>Version <span className="font-mono">{ag.version}</span></span>
                                    <span>Status: <span className="font-semibold">{ag.status}</span></span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

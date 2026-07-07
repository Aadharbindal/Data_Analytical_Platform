"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, MessageSquare, Clock, Zap, AlertTriangle } from "lucide-react";

export function SessionHealthMetrics() {
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                // Mock API call
                setTimeout(() => {
                    setStats({
                        active_conversations: 128,
                        avg_duration_min: 14.5,
                        streaming_latency_ms: 120,
                        failure_rate_pct: 0.2
                    });
                    setLoading(false);
                }, 500);
            } catch (err) {
                console.error(err);
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    if (loading) return <div className="flex justify-center p-4"><Loader2 className="animate-spin" /></div>;
    if (!stats) return null;

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Conversations</CardTitle>
                    <MessageSquare className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{stats.active_conversations.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">Currently connected sessions</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg Session Duration</CardTitle>
                    <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{stats.avg_duration_min} min</div>
                    <p className="text-xs text-muted-foreground">Time spent per active user</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Streaming Latency</CardTitle>
                    <Zap className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{stats.streaming_latency_ms} ms</div>
                    <p className="text-xs text-muted-foreground">Time to first token (TTFT)</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Failure Rate</CardTitle>
                    <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{stats.failure_rate_pct}%</div>
                    <p className="text-xs text-muted-foreground">Orchestrator timeout/errors</p>
                </CardContent>
            </Card>
        </div>
    );
}

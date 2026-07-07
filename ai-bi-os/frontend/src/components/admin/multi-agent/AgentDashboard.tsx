"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, Server, Workflow, Activity, Clock } from "lucide-react";
import { multiAgentApi } from "@/api/ai-modules";

export function AgentDashboard() {
    const [agents, setAgents] = useState<any[]>([]);
    const [workflows, setWorkflows] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        Promise.all([multiAgentApi.listAgents(), multiAgentApi.listWorkflows()])
            .then(([agentList, wfData]) => {
                setAgents(agentList);
                setWorkflows(wfData.workflows ?? []);
            })
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="flex justify-center p-4"><Loader2 className="animate-spin" /></div>;
    if (error) return <div className="text-red-500 text-sm p-4">Failed to load: {error}</div>;

    const totalWorkflows = workflows.length;
    const completed = workflows.filter(w => w.status === "COMPLETED").length;
    const successRate = totalWorkflows > 0 ? ((completed / totalWorkflows) * 100).toFixed(1) : "N/A";
    const avgLatency = "—"; // Requires metrics endpoint

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Registered Agents</CardTitle>
                    <Server className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{agents.length}</div>
                    <p className="text-xs text-muted-foreground">Active and healthy</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Workflows Executed</CardTitle>
                    <Workflow className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{totalWorkflows.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">Orchestrated DAGs</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">System Success Rate</CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold text-green-600">{successRate}%</div>
                    <p className="text-xs text-muted-foreground">Completed without conflicts</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg Workflow Latency</CardTitle>
                    <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{avgLatency}</div>
                    <p className="text-xs text-muted-foreground">End-to-End aggregation time</p>
                </CardContent>
            </Card>
        </div>
    );
}

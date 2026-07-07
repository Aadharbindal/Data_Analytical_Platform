"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, GitMerge } from "lucide-react";
import { multiAgentApi, WorkflowExecution } from "@/api/ai-modules";

export function WorkflowViewer() {
    const [workflows, setWorkflows] = useState<WorkflowExecution[]>([]);
    const [selected, setSelected] = useState<WorkflowExecution | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        multiAgentApi.listWorkflows()
            .then(data => {
                const wfs = data.workflows ?? [];
                setWorkflows(wfs);
                if (wfs.length > 0) setSelected(wfs[0]);
            })
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card className="h-full">
                <CardHeader><CardTitle>Live Execution DAG</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin" /></CardContent>
            </Card>
        );
    }
    if (error) return <Card><CardContent className="text-red-500 p-4">{error}</CardContent></Card>;

    const nodes = selected?.nodes ?? [];

    return (
        <Card className="h-full">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center">
                        <GitMerge className="mr-2 h-5 w-5 text-indigo-500" /> Execution DAG
                    </CardTitle>
                    <select
                        className="text-xs border rounded px-2 py-1"
                        onChange={e => setSelected(workflows.find(w => w.id === e.target.value) ?? null)}
                        value={selected?.id ?? ""}
                    >
                        {workflows.map(wf => (
                            <option key={wf.id} value={wf.id}>
                                {wf.id.slice(0, 8)}… — {wf.status}
                            </option>
                        ))}
                    </select>
                </div>
            </CardHeader>
            <CardContent>
                {nodes.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No nodes. Run a workflow to see the execution graph.</p>
                ) : (
                    <div className="relative border-l-2 border-slate-200 ml-4 space-y-6 pb-4">
                        {nodes.map((node, index) => (
                            <div key={node.id} className="relative pl-6">
                                <div className={`absolute -left-2 top-1.5 h-4 w-4 rounded-full border-2 border-white ${
                                    node.status === 'COMPLETED' ? 'bg-green-500' :
                                    node.status === 'RUNNING' ? 'bg-blue-500 animate-pulse' :
                                    node.status === 'FAILED' ? 'bg-red-500' :
                                    'bg-slate-300'
                                }`} />
                                <div className="p-3 border rounded-lg bg-slate-50 hover:bg-white transition-colors">
                                    <div className="flex justify-between items-center mb-1">
                                        <h3 className="font-semibold text-sm">{node.task_name}</h3>
                                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                            node.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                                            node.status === 'RUNNING' ? 'bg-blue-100 text-blue-800' :
                                            node.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                                            'bg-slate-200 text-slate-800'
                                        }`}>
                                            {node.status}
                                        </span>
                                    </div>
                                    <div className="text-xs text-muted-foreground flex justify-between">
                                        <span>Node {index + 1}</span>
                                        {node.error_message && <span className="text-red-500 truncate max-w-[200px]">{node.error_message}</span>}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

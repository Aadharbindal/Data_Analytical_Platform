"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, Zap, BarChart3, AlertTriangle, ShieldCheck } from "lucide-react";
import { decisionApi, DecisionObject } from "@/api/ai-modules";

export function DecisionDashboard() {
    const [decisions, setDecisions] = useState<DecisionObject[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        decisionApi.list()
            .then(setDecisions)
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="flex justify-center p-4"><Loader2 className="animate-spin" /></div>;
    if (error) return <div className="text-red-500 text-sm p-4">Failed to load: {error}</div>;

    const total = decisions.length;
    const pending = decisions.filter(d => d.approval_status === "DRAFT").length;
    const avgRoi = total > 0
        ? (decisions.reduce((s, d) => s + d.expected_roi, 0) / total).toFixed(1)
        : "—";
    const risks = decisions.map(d => d.expected_risk);
    const dominantRisk = risks.includes("HIGH") ? "HIGH" : risks.includes("MEDIUM") ? "MEDIUM" : "LOW";

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Decisions</CardTitle>
                    <Zap className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{total}</div>
                    <p className="text-xs text-muted-foreground">AI-generated, policy-checked</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
                    <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold text-amber-600">{pending}</div>
                    <p className="text-xs text-muted-foreground">Awaiting stakeholder sign-off</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg Expected ROI</CardTitle>
                    <BarChart3 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{avgRoi}%</div>
                    <p className="text-xs text-muted-foreground">Projected return on execution</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Portfolio Risk</CardTitle>
                    <ShieldCheck className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className={`text-2xl font-bold ${dominantRisk === "LOW" ? "text-green-600" : dominantRisk === "MEDIUM" ? "text-amber-500" : "text-red-600"}`}>
                        {dominantRisk}
                    </div>
                    <p className="text-xs text-muted-foreground">Aggregate decision risk level</p>
                </CardContent>
            </Card>
        </div>
    );
}

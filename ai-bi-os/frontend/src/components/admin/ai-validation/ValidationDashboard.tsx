"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, ShieldCheck, ShieldAlert, BarChart, Activity } from "lucide-react";
import { aiValidationApi, ValidationSummary } from "@/api/ai-modules";

export function ValidationDashboard() {
    const [summary, setSummary] = useState<ValidationSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        aiValidationApi.getSummary()
            .then(setSummary)
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="flex justify-center p-4"><Loader2 className="animate-spin" /></div>;
    if (error) return <div className="text-red-500 text-sm p-4">Failed to load: {error}</div>;
    if (!summary) return null;

    const passRate = summary.total_validations > 0
        ? ((summary.passed / summary.total_validations) * 100).toFixed(1)
        : "N/A";

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Validations</CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{summary.total_validations.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">AI responses evaluated</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Passed</CardTitle>
                    <ShieldCheck className="h-4 w-4 text-green-600" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold text-green-600">{summary.passed.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">Safe & grounded responses</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Rejected</CardTitle>
                    <ShieldAlert className="h-4 w-4 text-red-500" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold text-red-500">{summary.failed.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">Flagged violations</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Pass Rate</CardTitle>
                    <BarChart className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{passRate}%</div>
                    <p className="text-xs text-muted-foreground">Avg Confidence: {(summary.avg_confidence * 100).toFixed(1)}%</p>
                </CardContent>
            </Card>
        </div>
    );
}

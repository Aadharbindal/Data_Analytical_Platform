"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, Lightbulb, TrendingUp, AlertCircle, CheckCircle } from "lucide-react";
import { insightApi, InsightSummary } from "@/api/ai-modules";

export function ExecutiveSummaryCard() {
    const [summary, setSummary] = useState<InsightSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        insightApi.getSummary()
            .then(setSummary)
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="flex justify-center p-4"><Loader2 className="animate-spin" /></div>;
    if (error) return <div className="text-red-500 text-sm p-4">Failed to load: {error}</div>;
    if (!summary) return null;

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Insights Generated</CardTitle>
                    <Lightbulb className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{summary.total_insights.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">Valid, evidence-backed narratives</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg Business Impact</CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{summary.avg_business_impact.toFixed(1)} / 100</div>
                    <p className="text-xs text-muted-foreground">Based on financial & strategic value</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
                    <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{(summary.avg_confidence * 100).toFixed(1)}%</div>
                    <p className="text-xs text-muted-foreground">Data reliability score</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Top Domains</CardTitle>
                    <AlertCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-lg font-semibold truncate">
                        {summary.top_domains.length > 0 ? summary.top_domains.join(", ") : "—"}
                    </div>
                    <p className="text-xs text-muted-foreground">Areas with most activity</p>
                </CardContent>
            </Card>
        </div>
    );
}

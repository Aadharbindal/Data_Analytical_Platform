"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { insightApi, InsightObject } from "@/api/ai-modules";

function Badge({ children, className, variant = "default" }: any) {
    const base = "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold";
    const bg = variant === "destructive" ? "bg-red-500 text-white" : "bg-primary text-primary-foreground";
    return <span className={`${base} ${bg} ${className}`}>{children}</span>;
}

export function TopInsightsList() {
    const [insights, setInsights] = useState<InsightObject[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        insightApi.list()
            .then(data => setInsights(data.slice(0, 10)))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card>
                <CardHeader><CardTitle>Top Ranked Insights</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin" /></CardContent>
            </Card>
        );
    }
    if (error) return <Card><CardContent className="text-red-500 p-4">{error}</CardContent></Card>;

    return (
        <Card>
            <CardHeader>
                <CardTitle>Top Ranked Insights</CardTitle>
            </CardHeader>
            <CardContent>
                {insights.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No insights generated yet. Upload a dataset and trigger insight generation.</p>
                ) : (
                    <div className="space-y-4">
                        {insights.map(insight => (
                            <div key={insight.id} className="p-4 border rounded-lg hover:bg-slate-50 transition-colors">
                                <div className="flex justify-between items-start mb-2">
                                    <h3 className="font-semibold text-sm">{insight.headline}</h3>
                                    <Badge variant={insight.severity === "HIGH" ? "destructive" : "default"}>
                                        {insight.severity}
                                    </Badge>
                                </div>
                                <div className="flex space-x-4 text-xs text-muted-foreground">
                                    <span>Domain: {insight.business_domain}</span>
                                    <span>Impact: {insight.business_impact_score.toFixed(1)}</span>
                                    <span>Confidence: {(insight.confidence_score * 100).toFixed(0)}%</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

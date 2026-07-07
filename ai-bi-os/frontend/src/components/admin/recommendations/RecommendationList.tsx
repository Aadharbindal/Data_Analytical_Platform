"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { recommendationApi, RecommendationObject } from "@/api/ai-modules";

export function RecommendationList() {
    const [recommendations, setRecommendations] = useState<RecommendationObject[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        recommendationApi.list()
            .then(data => setRecommendations(data.slice(0, 10)))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card>
                <CardHeader><CardTitle>Recommendations</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin" /></CardContent>
            </Card>
        );
    }
    if (error) return <Card><CardContent className="text-red-500 p-4">{error}</CardContent></Card>;

    return (
        <Card>
            <CardHeader><CardTitle>Active Recommendations</CardTitle></CardHeader>
            <CardContent>
                {recommendations.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No recommendations yet. Generate insights first.</p>
                ) : (
                    <div className="space-y-4">
                        {recommendations.map(rec => (
                            <div key={rec.id} className="p-4 border rounded-lg hover:bg-slate-50 transition-colors">
                                <div className="flex justify-between items-start mb-1">
                                    <h3 className="font-semibold text-sm">{rec.title}</h3>
                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${rec.status === 'OPEN' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                                        {rec.status}
                                    </span>
                                </div>
                                <p className="text-xs text-muted-foreground mb-2">{rec.executive_summary}</p>
                                <div className="flex space-x-4 text-xs text-muted-foreground">
                                    <span>Domain: {rec.business_domain}</span>
                                    <span>Confidence: {(rec.confidence_score * 100).toFixed(0)}%</span>
                                    <span>Priority: P{rec.priority}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

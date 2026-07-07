"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { aiEvaluationApi } from "@/api/ai-modules";

export function RegressionReports() {
    const [regressions, setRegressions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        aiEvaluationApi.getRegressions()
            .then(setRegressions)
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card>
                <CardHeader><CardTitle>Regression Reports</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin" /></CardContent>
            </Card>
        );
    }
    if (error) return <Card><CardContent className="text-red-500 p-4">{error}</CardContent></Card>;

    return (
        <Card>
            <CardHeader><CardTitle>Regression Reports</CardTitle></CardHeader>
            <CardContent>
                {regressions.length === 0 ? (
                    <p className="text-sm text-green-700 font-medium">✓ No regressions detected. All models performing within baseline.</p>
                ) : (
                    <div className="space-y-3">
                        {regressions.map((reg: any) => (
                            <div key={reg.id} className="p-3 border border-amber-200 bg-amber-50 rounded-lg text-sm">
                                <div className="flex justify-between items-start">
                                    <span className="font-semibold">{reg.metric_name}</span>
                                    <span className="text-amber-700 font-bold text-xs">−{reg.degradation_percentage?.toFixed(1)}%</span>
                                </div>
                                <div className="text-xs text-muted-foreground mt-1">
                                    Previous: {reg.previous_value?.toFixed(3)} → Current: {reg.current_value?.toFixed(3)}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

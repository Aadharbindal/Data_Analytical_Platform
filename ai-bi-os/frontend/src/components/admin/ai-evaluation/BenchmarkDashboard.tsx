"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, Award, Target, TrendingUp, Cpu } from "lucide-react";
import { aiEvaluationApi, EvaluationObject } from "@/api/ai-modules";

export function BenchmarkDashboard() {
    const [evaluations, setEvaluations] = useState<EvaluationObject[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        aiEvaluationApi.list()
            .then(setEvaluations)
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="flex justify-center p-4"><Loader2 className="animate-spin" /></div>;
    if (error) return <div className="text-red-500 text-sm p-4">Failed to load: {error}</div>;

    const total = evaluations.length;
    const avgQuality = total > 0 ? (evaluations.reduce((s, e) => s + e.quality_score, 0) / total).toFixed(1) : "—";
    const avgOverall = total > 0 ? (evaluations.reduce((s, e) => s + e.overall_score, 0) / total).toFixed(1) : "—";

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Benchmarks Run</CardTitle>
                    <Cpu className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{total.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">Evaluation suites executed</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg Quality Score</CardTitle>
                    <Award className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{avgQuality}</div>
                    <p className="text-xs text-muted-foreground">Out of 100</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg Overall Score</CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{avgOverall}</div>
                    <p className="text-xs text-muted-foreground">Quality + Cost + Latency</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Modules Evaluated</CardTitle>
                    <Target className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{new Set(evaluations.map(e => e.target_module)).size}</div>
                    <p className="text-xs text-muted-foreground">Distinct AI modules</p>
                </CardContent>
            </Card>
        </div>
    );
}

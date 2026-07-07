import React from 'react';
import { BenchmarkDashboard } from '@/components/admin/ai-evaluation/BenchmarkDashboard';
import { ModelLeaderboard } from '@/components/admin/ai-evaluation/ModelLeaderboard';
import { RegressionReports } from '@/components/admin/ai-evaluation/RegressionReports';
import { Activity } from "lucide-react";

export default function AIEvaluationAdminPage() {
    return (
        <div className="container mx-auto py-8 space-y-8">
            <div className="flex items-center space-x-3">
                <div className="p-2 bg-indigo-100 rounded-lg">
                    <Activity className="h-8 w-8 text-indigo-700" />
                </div>
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">AI Evaluation & Benchmarking</h1>
                    <p className="text-muted-foreground mt-1">
                        Track historical performance, benchmark models, and detect regressions across the entire platform.
                    </p>
                </div>
            </div>

            <section>
                <BenchmarkDashboard />
            </section>

            <div className="grid gap-8 lg:grid-cols-2">
                <section>
                    <ModelLeaderboard />
                </section>
                <section>
                    <RegressionReports />
                </section>
            </div>
        </div>
    );
}

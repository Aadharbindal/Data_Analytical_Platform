"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, ShieldAlert, Activity, CheckCircle, FileText } from "lucide-react";

export function PolicyDashboard() {
    const [summary, setSummary] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSummary = async () => {
            try {
                // Mock API call
                setTimeout(() => {
                    setSummary({
                        total_rules: 1250,
                        active_policies: 48,
                        execution_count: 8520,
                        violation_rate: 1.2
                    });
                    setLoading(false);
                }, 500);
            } catch (err) {
                console.error(err);
                setLoading(false);
            }
        };
        fetchSummary();
    }, []);

    if (loading) return <div className="flex justify-center p-4"><Loader2 className="animate-spin" /></div>;
    if (!summary) return null;

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Rules</CardTitle>
                    <FileText className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{summary.total_rules.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">Active definitions deployed</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Policies</CardTitle>
                    <ShieldAlert className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{summary.active_policies}</div>
                    <p className="text-xs text-muted-foreground">Constraint groups enforcing limits</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Executions (24h)</CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{summary.execution_count.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">Evaluations run successfully</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Violation Rate</CardTitle>
                    <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold text-red-600">{summary.violation_rate}%</div>
                    <p className="text-xs text-muted-foreground">Requests rejected or warned</p>
                </CardContent>
            </Card>
        </div>
    );
}

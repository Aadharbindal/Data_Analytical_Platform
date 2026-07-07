"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

export function ExecutionHistory() {
    const [executions, setExecutions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Mock API call
        setTimeout(() => {
            const data = [
                { id: "exec-101", rule_name: "CapEx Limit > $500k", result: "FAIL", action: "REQUIRE_APPROVAL", time: "2 mins ago" },
                { id: "exec-102", rule_name: "Discount > 20%", result: "PASS", action: "NONE", time: "15 mins ago" },
                { id: "exec-103", rule_name: "GDPR Data Processing", result: "FAIL", action: "REJECT", time: "1 hour ago" },
            ];
            setExecutions(data);
            setLoading(false);
        }, 500);
    }, []);

    if (loading) {
        return (
            <Card className="h-full">
                <CardHeader><CardTitle>Execution Log</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin" /></CardContent>
            </Card>
        );
    }

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle>Execution Log</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {executions.map(exec => (
                        <div key={exec.id} className="p-3 border rounded-lg bg-white flex justify-between items-center">
                            <div>
                                <h3 className="font-semibold text-sm">{exec.rule_name}</h3>
                                <p className="text-xs text-muted-foreground">{exec.time} • Action: {exec.action.replace('_', ' ')}</p>
                            </div>
                            <div>
                                <span className={`text-xs font-bold ${exec.result === 'PASS' ? 'text-green-600' : 'text-red-600'}`}>
                                    {exec.result}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}

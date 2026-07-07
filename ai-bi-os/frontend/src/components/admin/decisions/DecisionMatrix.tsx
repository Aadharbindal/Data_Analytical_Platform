"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

export function DecisionMatrix() {
    const [decisions, setDecisions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Mock API call
        setTimeout(() => {
            const data = [
                { id: "dec-1", objective: "Maximize ROI", strategy: "Phased Rollout in EMEA", roi: 320, risk: "LOW", status: "PENDING_APPROVAL" },
                { id: "dec-2", objective: "Minimize Risk", strategy: "Maintain Current Vendor Pipeline", roi: 120, risk: "LOW", status: "APPROVED" },
                { id: "dec-3", objective: "Market Expansion", strategy: "Aggressive Launch in APAC", roi: 450, risk: "HIGH", status: "DRAFT" },
            ];
            setDecisions(data);
            setLoading(false);
        }, 500);
    }, []);

    if (loading) {
        return (
            <Card>
                <CardHeader><CardTitle>Optimized Decision Matrix</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin" /></CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Optimized Decision Matrix</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {decisions.map(dec => (
                        <div key={dec.id} className="p-4 border rounded-lg hover:bg-slate-50 transition-colors cursor-pointer">
                            <div className="flex justify-between items-start mb-2">
                                <div>
                                    <h3 className="font-semibold text-lg">{dec.strategy}</h3>
                                    <p className="text-sm text-muted-foreground">Objective: {dec.objective}</p>
                                </div>
                                <StatusBadge status={dec.status} />
                            </div>
                            <div className="flex space-x-6 text-sm mt-3">
                                <span className="font-medium text-green-600">Expected ROI: {dec.roi}%</span>
                                <span className={`font-medium ${dec.risk === 'HIGH' ? 'text-red-600' : 'text-blue-600'}`}>Risk: {dec.risk}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}

function StatusBadge({ status }: { status: string }) {
    let bg = "bg-slate-200 text-slate-800";
    if (status === "APPROVED") bg = "bg-green-100 text-green-800";
    if (status === "PENDING_APPROVAL") bg = "bg-amber-100 text-amber-800";
    if (status === "REJECTED") bg = "bg-red-100 text-red-800";
    
    return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${bg}`}>{status.replace('_', ' ')}</span>;
}

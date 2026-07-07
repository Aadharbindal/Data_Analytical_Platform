"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, AlertCircle } from "lucide-react";
import { aiValidationApi, ValidationObject } from "@/api/ai-modules";

export function RejectedResponses() {
    const [rejections, setRejections] = useState<ValidationObject[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        aiValidationApi.list()
            .then(data => setRejections(data.filter(v => v.overall_status === "FAILED").slice(0, 20)))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card className="h-full border-red-200">
                <CardHeader><CardTitle className="text-red-800">Rejected Outputs Explorer</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin text-red-600" /></CardContent>
            </Card>
        );
    }
    if (error) return <Card><CardContent className="text-red-500 p-4">{error}</CardContent></Card>;

    return (
        <Card className="h-full border-red-200 bg-red-50/30">
            <CardHeader>
                <CardTitle className="text-red-800 flex items-center">
                    <AlertCircle className="mr-2 h-5 w-5" /> Rejected Outputs Explorer
                </CardTitle>
            </CardHeader>
            <CardContent>
                {rejections.length === 0 ? (
                    <p className="text-sm text-green-700 font-medium">✓ No rejections found. All validations passed.</p>
                ) : (
                    <div className="space-y-4">
                        {rejections.map(rej => (
                            <div key={rej.id} className="p-3 border border-red-100 bg-white rounded-lg shadow-sm">
                                <div className="flex justify-between items-start mb-2">
                                    <h3 className="font-semibold text-sm">
                                        {rej.id.slice(0, 8)}… <span className="text-xs font-normal text-muted-foreground">({rej.validation_type})</span>
                                    </h3>
                                    <span className="text-[10px] uppercase font-bold text-red-600 bg-red-100 px-2 py-0.5 rounded">
                                        {rej.overall_status}
                                    </span>
                                </div>
                                <div className="text-xs text-slate-600">
                                    Confidence: {(rej.confidence_score * 100).toFixed(1)}%
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

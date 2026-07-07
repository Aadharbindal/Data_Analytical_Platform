"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { aiValidationApi, ValidationObject } from "@/api/ai-modules";

export function ValidationQueue() {
    const [validations, setValidations] = useState<ValidationObject[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        aiValidationApi.list()
            .then(data => setValidations(data.slice(0, 20)))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card>
                <CardHeader><CardTitle>Validation Queue</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin" /></CardContent>
            </Card>
        );
    }
    if (error) return <Card><CardContent className="text-red-500 p-4">{error}</CardContent></Card>;

    return (
        <Card>
            <CardHeader><CardTitle>Validation Queue</CardTitle></CardHeader>
            <CardContent>
                {validations.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No validations on record yet.</p>
                ) : (
                    <div className="space-y-2">
                        {validations.map(v => (
                            <div key={v.id} className="flex items-center justify-between p-3 border rounded-lg text-sm">
                                <div>
                                    <span className="font-mono text-xs text-muted-foreground">{v.id.slice(0, 8)}…</span>
                                    <span className="ml-2">{v.validation_type}</span>
                                </div>
                                <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                                    v.overall_status === 'PASSED' ? 'bg-green-100 text-green-800' :
                                    v.overall_status === 'FAILED' ? 'bg-red-100 text-red-800' :
                                    'bg-amber-100 text-amber-800'
                                }`}>
                                    {v.overall_status}
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { businessRuleApi, BusinessRule } from "@/api/ai-modules";

export function RuleExplorer() {
    const [rules, setRules] = useState<BusinessRule[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        businessRuleApi.list()
            .then(setRules)
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card className="h-full">
                <CardHeader><CardTitle>Rule Definitions</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin" /></CardContent>
            </Card>
        );
    }
    if (error) return <Card><CardContent className="text-red-500 p-4">{error}</CardContent></Card>;

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle>Rule Definitions</CardTitle>
            </CardHeader>
            <CardContent>
                {rules.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No rules defined yet.</p>
                ) : (
                    <div className="space-y-3">
                        {rules.map(rule => (
                            <div key={rule.id} className="p-3 border rounded-lg hover:bg-slate-50 transition-colors">
                                <div className="flex justify-between items-start mb-1">
                                    <h3 className="font-semibold text-sm">{rule.name}</h3>
                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                        rule.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
                                        rule.status === 'DRAFT' ? 'bg-amber-100 text-amber-800' :
                                        'bg-slate-200 text-slate-700'
                                    }`}>
                                        {rule.status}
                                    </span>
                                </div>
                                <div className="text-xs text-muted-foreground">
                                    Category: {rule.rule_category}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

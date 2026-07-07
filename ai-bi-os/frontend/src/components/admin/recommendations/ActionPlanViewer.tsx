"use client";

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export function ActionPlanViewer() {
    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle>Action Plan & Scenarios</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-6">
                    {/* Action Plan */}
                    <div>
                        <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-3">Implementation Roadmap</h4>
                        <div className="space-y-4 text-sm">
                            <div className="border-l-4 border-blue-500 pl-3">
                                <span className="font-semibold block mb-1">Immediate (Next 48h)</span>
                                <ul className="list-disc list-inside text-muted-foreground space-y-1">
                                    <li>Analyze detailed breakdown of metrics</li>
                                    <li>Alert regional managers</li>
                                </ul>
                            </div>
                            <div className="border-l-4 border-amber-500 pl-3">
                                <span className="font-semibold block mb-1">Short-term (1-2 Weeks)</span>
                                <ul className="list-disc list-inside text-muted-foreground space-y-1">
                                    <li>Adjust resource allocation for next week</li>
                                </ul>
                            </div>
                            <div className="border-l-4 border-green-500 pl-3">
                                <span className="font-semibold block mb-1">Medium-term (1-3 Months)</span>
                                <ul className="list-disc list-inside text-muted-foreground space-y-1">
                                    <li>Revise monthly targets based on new baseline</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    {/* Scenarios */}
                    <div>
                        <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-3">Scenario Analysis</h4>
                        <div className="grid grid-cols-3 gap-3">
                            <div className="bg-red-50 p-3 rounded border border-red-100">
                                <div className="font-semibold text-xs text-red-800 mb-1">Worst Case</div>
                                <div className="text-sm">Continued degradation of metric.</div>
                                <div className="font-mono text-xs mt-2 text-red-600">Impact: -$50k</div>
                            </div>
                            <div className="bg-blue-50 p-3 rounded border border-blue-100">
                                <div className="font-semibold text-xs text-blue-800 mb-1">Expected</div>
                                <div className="text-sm">Baseline recovery within 3 weeks.</div>
                                <div className="font-mono text-xs mt-2 text-blue-600">Impact: +$150k</div>
                            </div>
                            <div className="bg-green-50 p-3 rounded border border-green-100">
                                <div className="font-semibold text-xs text-green-800 mb-1">Best Case</div>
                                <div className="text-sm">Immediate correction and growth.</div>
                                <div className="font-mono text-xs mt-2 text-green-600">Impact: +$300k</div>
                            </div>
                        </div>
                    </div>

                    {/* Meta */}
                    <div>
                        <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-2">Required Resources & Tracking</h4>
                        <div className="bg-slate-50 p-3 rounded-md text-xs font-mono text-slate-700 space-y-1">
                            <div>Resources: 2 Data Analysts, $5k Budget</div>
                            <div>Dependencies: Approval from Finance, Data engineering bandwidth</div>
                            <div>KPIs: Daily active usage, Weekly revenue</div>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

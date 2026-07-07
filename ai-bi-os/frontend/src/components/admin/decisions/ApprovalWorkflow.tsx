"use client";

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Check, X, Clock } from "lucide-react";

export function ApprovalWorkflow() {
    return (
        <Card className="h-full border-amber-200 bg-amber-50/30">
            <CardHeader>
                <CardTitle className="text-amber-900">Approval Workflow (Pending)</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-6">
                    <div>
                        <h4 className="text-sm font-bold text-amber-900 uppercase tracking-wider mb-2">Decision Context</h4>
                        <p className="text-sm leading-relaxed text-amber-800">
                            <strong>Objective:</strong> Maximize ROI<br/>
                            <strong>Selected Strategy:</strong> Phased Rollout in EMEA<br/>
                            <strong>Constraints Verified:</strong> Budget Cap ($500k) - PASSED
                        </p>
                    </div>
                    
                    <div className="space-y-3">
                        <h4 className="text-sm font-bold text-amber-900 uppercase tracking-wider mb-2">Simulation Impact</h4>
                        <div className="grid grid-cols-2 gap-3">
                            <div className="bg-white p-3 rounded shadow-sm border border-amber-100">
                                <div className="text-xs font-semibold text-slate-500 mb-1">Expected ROI</div>
                                <div className="text-xl font-bold text-green-600">320%</div>
                            </div>
                            <div className="bg-white p-3 rounded shadow-sm border border-amber-100">
                                <div className="text-xs font-semibold text-slate-500 mb-1">Risk Exposure</div>
                                <div className="text-xl font-bold text-blue-600">LOW</div>
                            </div>
                        </div>
                    </div>

                    <div className="pt-4 border-t border-amber-200 flex space-x-3">
                        <Button className="w-full bg-green-600 hover:bg-green-700">
                            <Check className="mr-2 h-4 w-4" /> Approve
                        </Button>
                        <Button variant="outline" className="w-full border-red-200 text-red-600 hover:bg-red-50">
                            <X className="mr-2 h-4 w-4" /> Reject
                        </Button>
                    </div>
                    
                    <div className="text-xs text-center text-amber-700/70 flex items-center justify-center">
                        <Clock className="mr-1 h-3 w-3" /> Awaiting sign-off by Executive Sponsor
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

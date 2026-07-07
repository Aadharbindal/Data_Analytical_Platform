import React from 'react';
import { PolicyDashboard } from '@/components/admin/business-rules/PolicyDashboard';
import { RuleExplorer } from '@/components/admin/business-rules/RuleExplorer';
import { ExecutionHistory } from '@/components/admin/business-rules/ExecutionHistory';
import { ShieldCheck } from "lucide-react";

export default function BusinessRulesAdminPage() {
    return (
        <div className="container mx-auto py-8 space-y-8">
            <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                    <ShieldCheck className="h-8 w-8 text-blue-700" />
                </div>
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Enterprise Rule Management</h1>
                    <p className="text-muted-foreground mt-1">
                        Define, monitor, and enforce deterministic business logic and compliance policies across the AI BI OS.
                    </p>
                </div>
            </div>

            <section>
                <PolicyDashboard />
            </section>

            <div className="grid gap-8 lg:grid-cols-2">
                <section>
                    <RuleExplorer />
                </section>
                <section>
                    <ExecutionHistory />
                </section>
            </div>
        </div>
    );
}

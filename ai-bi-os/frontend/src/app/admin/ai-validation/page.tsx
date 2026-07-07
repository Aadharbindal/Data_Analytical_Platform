import React from 'react';
import { ValidationDashboard } from '@/components/admin/ai-validation/ValidationDashboard';
import { ValidationQueue } from '@/components/admin/ai-validation/ValidationQueue';
import { RejectedResponses } from '@/components/admin/ai-validation/RejectedResponses';
import { ShieldAlert } from "lucide-react";

export default function AIValidationAdminPage() {
    return (
        <div className="container mx-auto py-8 space-y-8">
            <div className="flex items-center space-x-3">
                <div className="p-2 bg-indigo-100 rounded-lg">
                    <ShieldAlert className="h-8 w-8 text-indigo-700" />
                </div>
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">AI Validation Center</h1>
                    <p className="text-muted-foreground mt-1">
                        Monitor the final guardrails engine validating Insights, Recommendations, and Decisions against hallucinations and policy violations.
                    </p>
                </div>
            </div>

            <section>
                <ValidationDashboard />
            </section>

            <div className="grid gap-8 lg:grid-cols-2">
                <section>
                    <ValidationQueue />
                </section>
                <section>
                    <RejectedResponses />
                </section>
            </div>
        </div>
    );
}

import React from 'react';
import { DecisionDashboard } from '@/components/admin/decisions/DecisionDashboard';
import { DecisionMatrix } from '@/components/admin/decisions/DecisionMatrix';
import { ApprovalWorkflow } from '@/components/admin/decisions/ApprovalWorkflow';

export default function DecisionsAdminPage() {
    return (
        <div className="container mx-auto py-8 space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Enterprise Decision Center</h1>
                <p className="text-muted-foreground mt-2">
                    Review simulated strategies, optimize for business constraints, and formally approve major decisions.
                </p>
            </div>

            {/* Dashboards / Overview */}
            <section>
                <DecisionDashboard />
            </section>

            <div className="grid gap-8 lg:grid-cols-2">
                {/* Left Column: Explorer */}
                <section>
                    <DecisionMatrix />
                </section>

                {/* Right Column: Detailed View */}
                <section>
                    <ApprovalWorkflow />
                </section>
            </div>
        </div>
    );
}

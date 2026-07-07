import React from 'react';
import { AgentDashboard } from '@/components/admin/multi-agent/AgentDashboard';
import { WorkflowViewer } from '@/components/admin/multi-agent/WorkflowViewer';
import { AgentHealthTracker } from '@/components/admin/multi-agent/AgentHealthTracker';
import { Network } from "lucide-react";

export default function MultiAgentAdminPage() {
    return (
        <div className="container mx-auto py-8 space-y-8">
            <div className="flex items-center space-x-3">
                <div className="p-2 bg-indigo-100 rounded-lg">
                    <Network className="h-8 w-8 text-indigo-700" />
                </div>
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Enterprise Agent Operations Center</h1>
                    <p className="text-muted-foreground mt-1">
                        Monitor, coordinate, and orchestrate complex DAG workflows across specialized AI modules.
                    </p>
                </div>
            </div>

            <section>
                <AgentDashboard />
            </section>

            <div className="grid gap-8 lg:grid-cols-2">
                <section>
                    <WorkflowViewer />
                </section>
                <section>
                    <AgentHealthTracker />
                </section>
            </div>
        </div>
    );
}

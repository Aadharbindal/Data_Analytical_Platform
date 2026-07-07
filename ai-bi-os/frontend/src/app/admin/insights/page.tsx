import React from 'react';
import { ExecutiveSummaryCard } from '@/components/admin/insights/ExecutiveSummaryCard';
import { TopInsightsList } from '@/components/admin/insights/TopInsightsList';
import { InsightDetailPanel } from '@/components/admin/insights/InsightDetailPanel';

export default function InsightsAdminPage() {
    return (
        <div className="container mx-auto py-8 space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Enterprise Insights Center</h1>
                <p className="text-muted-foreground mt-2">
                    Review and explore generated business narratives backed by validated analytics and evidence.
                </p>
            </div>

            {/* Health Metrics */}
            <section>
                <ExecutiveSummaryCard />
            </section>

            <div className="grid gap-8 lg:grid-cols-2">
                {/* Left Column: Explorer */}
                <section>
                    <TopInsightsList />
                </section>

                {/* Right Column: Timeline / Details */}
                <section>
                    <InsightDetailPanel />
                </section>
            </div>
        </div>
    );
}

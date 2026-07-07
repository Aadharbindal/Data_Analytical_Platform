import React from 'react';
import { RecommendationDashboard } from '@/components/admin/recommendations/RecommendationDashboard';
import { RecommendationList } from '@/components/admin/recommendations/RecommendationList';
import { ActionPlanViewer } from '@/components/admin/recommendations/ActionPlanViewer';

export default function RecommendationsAdminPage() {
    return (
        <div className="container mx-auto py-8 space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Enterprise Recommendation Center</h1>
                <p className="text-muted-foreground mt-2">
                    Review, prioritize, and action business recommendations backed by validated insights and evidence.
                </p>
            </div>

            {/* Dashboards / Overview */}
            <section>
                <RecommendationDashboard />
            </section>

            <div className="grid gap-8 lg:grid-cols-2">
                {/* Left Column: Explorer */}
                <section>
                    <RecommendationList />
                </section>

                {/* Right Column: Detailed View */}
                <section>
                    <ActionPlanViewer />
                </section>
            </div>
        </div>
    );
}

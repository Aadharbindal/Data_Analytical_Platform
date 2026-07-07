import React from 'react';
import { MemoryHealthMetrics } from '@/components/admin/memory/MemoryHealthMetrics';
import { MemoryExplorer } from '@/components/admin/memory/MemoryExplorer';
import { MemoryTimeline } from '@/components/admin/memory/MemoryTimeline';

export default function MemoryAdminPage() {
    return (
        <div className="container mx-auto py-8 space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Enterprise AI Memory Engine</h1>
                <p className="text-muted-foreground mt-2">
                    Manage persistent workspace, conversation, and user memories. Monitor health and retention policies.
                </p>
            </div>

            {/* Health Metrics */}
            <section>
                <MemoryHealthMetrics />
            </section>

            <div className="grid gap-8 lg:grid-cols-3">
                {/* Left Column: Explorer (Spans 2 columns) */}
                <section className="lg:col-span-2">
                    <MemoryExplorer />
                </section>

                {/* Right Column: Timeline */}
                <section className="lg:col-span-1">
                    <MemoryTimeline />
                </section>
            </div>
        </div>
    );
}

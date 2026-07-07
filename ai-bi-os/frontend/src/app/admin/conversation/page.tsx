import React from 'react';
import { SessionHealthMetrics } from '@/components/admin/conversation/SessionHealthMetrics';
import { ConversationExplorer } from '@/components/admin/conversation/ConversationExplorer';
import { ConversationTimeline } from '@/components/admin/conversation/ConversationTimeline';

export default function ConversationAdminPage() {
    return (
        <div className="container mx-auto py-8 space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Enterprise Conversation Engine</h1>
                <p className="text-muted-foreground mt-2">
                    Manage active sessions, stream states, and message routing across the platform.
                </p>
            </div>

            {/* Health Metrics */}
            <section>
                <SessionHealthMetrics />
            </section>

            <div className="grid gap-8 lg:grid-cols-3">
                {/* Left Column: Explorer (Spans 2 columns) */}
                <section className="lg:col-span-2">
                    <ConversationExplorer />
                </section>

                {/* Right Column: Timeline */}
                <section className="lg:col-span-1">
                    <ConversationTimeline />
                </section>
            </div>
        </div>
    );
}

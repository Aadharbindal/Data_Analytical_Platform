"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

export function ConversationTimeline() {
    const [events, setEvents] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Mocking history API call
        setTimeout(() => {
            setEvents([
                { id: 1, action: "CREATED", detail: "Conversation initialized", timestamp: "5 mins ago" },
                { id: 2, action: "STATE_CHANGE", detail: "Idle -> Executing", timestamp: "4 mins ago" },
                { id: 3, action: "STREAMING", detail: "Started SSE connection", timestamp: "4 mins ago" },
                { id: 4, action: "STATE_CHANGE", detail: "Executing -> Completed", timestamp: "3 mins ago" },
                { id: 5, action: "CHECKPOINT", detail: "Auto-saved context state", timestamp: "3 mins ago" }
            ]);
            setLoading(false);
        }, 600);
    }, []);

    return (
        <Card>
            <CardHeader>
                <CardTitle>Conversation Lifecycle</CardTitle>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="flex justify-center p-4"><Loader2 className="animate-spin" /></div>
                ) : (
                    <div className="space-y-4">
                        {events.map(event => (
                            <div key={event.id} className="flex flex-col border-l-2 border-primary pl-4 relative">
                                <span className="absolute -left-[5px] top-1 h-2 w-2 rounded-full bg-primary" />
                                <div className="text-sm font-semibold">{event.action}</div>
                                <div className="text-xs text-muted-foreground mb-1">{event.timestamp}</div>
                                <div className="text-sm">{event.detail}</div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

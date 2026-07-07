"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

export function MemoryTimeline() {
    const [events, setEvents] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Mocking history API call
        setTimeout(() => {
            setEvents([
                { id: 1, action: "CREATED", memory: "User prefers dark mode", timestamp: "10 mins ago" },
                { id: 2, action: "UPDATED", memory: "Q3 Sales context added", timestamp: "1 hour ago" },
                { id: 3, action: "ARCHIVED", memory: "Old fiscal year data", timestamp: "2 days ago" },
                { id: 4, action: "CONSOLIDATED", memory: "Merged 5 overlapping dataset memories", timestamp: "1 week ago" }
            ]);
            setLoading(false);
        }, 600);
    }, []);

    return (
        <Card>
            <CardHeader>
                <CardTitle>Memory Event Timeline</CardTitle>
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
                                <div className="text-sm">{event.memory}</div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

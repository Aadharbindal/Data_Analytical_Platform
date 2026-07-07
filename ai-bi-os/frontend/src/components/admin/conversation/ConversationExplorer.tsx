"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, MessageSquare } from "lucide-react";
import { conversationApi, ConversationSession } from "@/api/ai-modules";

export function ConversationExplorer() {
    const [sessions, setSessions] = useState<ConversationSession[]>([]);
    const [selected, setSelected] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        conversationApi.listSessions()
            .then(data => {
                setSessions(data);
                if (data.length > 0) setSelected(data[0].id);
            })
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <Card>
                <CardHeader><CardTitle>Conversation Explorer</CardTitle></CardHeader>
                <CardContent className="flex justify-center p-8"><Loader2 className="animate-spin" /></CardContent>
            </Card>
        );
    }
    if (error) return <Card><CardContent className="text-red-500 p-4">{error}</CardContent></Card>;

    const selectedSession = sessions.find(s => s.id === selected);

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center">
                    <MessageSquare className="mr-2 h-5 w-5 text-blue-500" /> Conversation Explorer
                </CardTitle>
            </CardHeader>
            <CardContent>
                {sessions.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No conversation sessions yet.</p>
                ) : (
                    <div className="space-y-4">
                        <select
                            className="w-full text-sm border rounded px-3 py-2"
                            value={selected ?? ""}
                            onChange={e => setSelected(e.target.value)}
                        >
                            {sessions.map(s => (
                                <option key={s.id} value={s.id}>
                                    {s.title || s.id.slice(0, 12) + "…"} — {s.status}
                                </option>
                            ))}
                        </select>
                        {selectedSession && (
                            <div className="p-3 border rounded-lg bg-slate-50 text-sm space-y-1">
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Status</span>
                                    <span className="font-medium">{selectedSession.status}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Messages</span>
                                    <span className="font-medium">{selectedSession.message_count ?? "—"}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Created</span>
                                    <span className="font-mono text-xs">{new Date(selectedSession.created_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

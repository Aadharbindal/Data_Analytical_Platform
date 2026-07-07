"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

export function EmbeddingModelsTable() {
    const [models, setModels] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchModels = async () => {
            try {
                // Mock API call for now since we don't have the backend running during this dev session
                // const res = await fetch('/api/embeddings/models');
                // const data = await res.json();
                const data = [
                    { id: "1", name: "text-embedding-3-small", provider: "OpenAI", dimensions: 1536, is_active: true },
                    { id: "2", name: "text-embedding-3-large", provider: "OpenAI", dimensions: 3072, is_active: true },
                    { id: "3", name: "all-MiniLM-L6-v2", provider: "Local", dimensions: 384, is_active: true },
                ];
                setModels(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchModels();
    }, []);

    if (loading) return <div className="flex justify-center p-4"><Loader2 className="animate-spin" /></div>;

    return (
        <Card>
            <CardHeader>
                <CardTitle>Embedding Models</CardTitle>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Provider</TableHead>
                            <TableHead>Dimensions</TableHead>
                            <TableHead>Status</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {models.map((model: any) => (
                            <TableRow key={model.id}>
                                <TableCell className="font-medium">{model.name}</TableCell>
                                <TableCell>{model.provider}</TableCell>
                                <TableCell>{model.dimensions}</TableCell>
                                <TableCell>
                                    <Badge variant={model.is_active ? "default" : "secondary"}>
                                        {model.is_active ? "Active" : "Inactive"}
                                    </Badge>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
}

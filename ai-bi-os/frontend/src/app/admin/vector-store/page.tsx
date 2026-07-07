import React from 'react';
import { IndexHealthMetrics } from '@/components/admin/vector-store/IndexHealthMetrics';
import { EmbeddingModelsTable } from '@/components/admin/vector-store/EmbeddingModelsTable';
import { SimilaritySearchTester } from '@/components/admin/vector-store/SimilaritySearchTester';

export default function VectorStoreAdminPage() {
    return (
        <div className="container mx-auto py-8 space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Vector Store & Embedding Engine</h1>
                <p className="text-muted-foreground mt-2">
                    Manage embedding models, monitor vector indices, and test semantic search capabilities.
                </p>
            </div>

            {/* Health Metrics Row */}
            <section>
                <IndexHealthMetrics />
            </section>

            <div className="grid gap-8 md:grid-cols-2">
                {/* Left Column: Tester */}
                <section>
                    <SimilaritySearchTester />
                </section>

                {/* Right Column: Models */}
                <section>
                    <EmbeddingModelsTable />
                </section>
            </div>
        </div>
    );
}

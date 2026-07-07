"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { catalogApi } from "@/lib/api";
import type { CatalogEntry } from "@/lib/types";
import { motion } from "framer-motion";
import { Search, Database, Tag, Clock, Layers } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState, detectErrorType } from "@/components/ui/error-state";

function CatalogCard({ entry }: { entry: CatalogEntry }) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="glass-card rounded-[20px] p-5 flex flex-col gap-3 cursor-pointer group hover:border-primary/30 transition-colors"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 border border-primary/20">
            <Database className="h-4 w-4 text-primary" />
          </div>
          <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
            {entry.name}
          </h3>
        </div>
        {entry.business_domain && (
          <span className="text-xs bg-surface border border-border/60 px-2 py-0.5 rounded-full text-muted-foreground">
            {entry.business_domain}
          </span>
        )}
      </div>

      {entry.description && (
        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
          {entry.description}
        </p>
      )}

      <div className="flex items-center gap-4 text-xs text-muted-foreground mt-auto pt-2 border-t border-border/40">
        <span className="flex items-center gap-1">
          <Layers className="h-3 w-3" />
          {entry.column_count} columns
        </span>
        {entry.last_updated && (
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {new Date(entry.last_updated).toLocaleDateString()}
          </span>
        )}
        {entry.owner && (
          <span className="ml-auto text-xs text-muted-foreground/70">{entry.owner}</span>
        )}
      </div>

      {entry.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {entry.tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-primary/8 text-primary border border-primary/15"
            >
              <Tag className="h-2.5 w-2.5" />
              {tag}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 26 } },
};

export default function DataCatalogPage() {
  const [searchQuery, setSearchQuery] = useState("");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["catalog"],
    queryFn: () => catalogApi.list(),
  });

  const filtered = (data ?? []).filter((entry) =>
    !searchQuery ||
    entry.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    entry.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    entry.business_domain?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">Data Catalog</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Discover and explore your organization's data assets with semantic context.
          </p>
        </div>
        <span className="text-sm text-muted-foreground">{filtered.length} entries</span>
      </div>

      {/* Search */}
      <div className="relative max-w-lg">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search by name, domain, or description..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full h-10 bg-surface border border-border/80 rounded-xl pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
        />
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-3 gap-5">
          {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} lines={3} />)}
        </div>
      ) : isError ? (
        <ErrorState 
          onRetry={refetch} 
          errorType={detectErrorType(error)}
          developerDetails={error instanceof Error ? error.message : String(error)}
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No catalog entries found"
          description={searchQuery ? `No results for "${searchQuery}"` : "Run the Metadata Catalog engine on a dataset to populate entries here."}
        />
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="grid grid-cols-3 gap-5"
        >
          {filtered.map((entry) => (
            <motion.div key={entry.id} variants={itemVariants}>
              <CatalogCard entry={entry} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}

"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { catalogApi, datasetsApi } from "@/lib/api";
import type { CatalogEntry } from "@/lib/types";
import { motion } from "framer-motion";
import { Search, Database, Tag, Clock, Layers } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState, detectErrorType } from "@/components/ui/error-state";

function CatalogCard({ entry }: { entry: CatalogEntry }) {
  const handleDownload = async () => {
    try {
      await datasetsApi.download(entry.id);
    } catch (err) {
      console.error("Failed to download dataset", err);
      alert("Failed to download the original file.");
    }
  };

  return (
    <motion.div
      whileHover={{ y: -2 }}
      onClick={handleDownload}
      className="glass-card rounded-[20px] p-5 flex flex-col md:flex-row items-start md:items-center gap-4 md:gap-6 cursor-pointer group hover:border-primary/30 transition-colors"
    >
      <div className="flex items-center gap-3 min-w-0 md:w-1/3">
        <div className="flex shrink-0 h-10 w-10 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
          <Database className="h-5 w-5 text-primary" />
        </div>
        <div className="min-w-0 flex flex-col">
          <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors truncate" title={entry.name}>
            {entry.name}
          </h3>
          {entry.business_domain && (
            <span className="text-xs text-muted-foreground mt-1">
              {entry.business_domain}
            </span>
          )}
        </div>
      </div>

      <div className="flex-1 min-w-0 w-full md:w-auto">
        {entry.description && (
          <p className="text-sm text-muted-foreground leading-relaxed line-clamp-1 break-words">
            {entry.description}
          </p>
        )}
        {entry.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {entry.tags.map((tag) => (
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
      </div>

      <div className="flex items-center gap-4 text-xs text-muted-foreground shrink-0 border-t md:border-t-0 md:border-l border-border/40 pt-3 md:pt-0 md:pl-6 w-full md:w-auto justify-between md:justify-end">
        <span className="flex items-center gap-1.5">
          <Layers className="h-3.5 w-3.5" />
          {entry.column_count} cols
        </span>
        {entry.last_updated && (
          <span className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            {new Date(entry.last_updated).toLocaleDateString()}
          </span>
        )}
        {entry.owner && (
          <span className="hidden md:inline-block ml-2 text-xs text-muted-foreground/70">{entry.owner}</span>
        )}
      </div>
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
      {/* Search and Entries */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative w-full max-w-lg">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by name, domain, or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-10 bg-surface border border-border/80 rounded-xl pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
          />
        </div>
        <span className="text-sm text-muted-foreground whitespace-nowrap">{filtered.length} entries</span>
      </div>

      {/* List */}
      {isLoading ? (
        <div className="flex flex-col gap-4">
          {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} lines={2} />)}
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
          className="flex flex-col gap-4"
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

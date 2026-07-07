"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { recommendationsApi } from "@/lib/api";
import type { Recommendation } from "@/lib/types";
import { motion } from "framer-motion";
import { Zap, TrendingUp, AlertTriangle, CheckCircle } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState, detectErrorType } from "@/components/ui/error-state";

const priorityConfig: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  critical: {
    color: "border-l-error",
    icon: <AlertTriangle className="h-4 w-4 text-error" />,
    label: "bg-error/10 text-error border-error/20",
  },
  high: {
    color: "border-l-warning",
    icon: <TrendingUp className="h-4 w-4 text-warning" />,
    label: "bg-warning/10 text-warning border-warning/20",
  },
  medium: {
    color: "border-l-primary",
    icon: <Zap className="h-4 w-4 text-primary" />,
    label: "bg-primary/10 text-primary border-primary/20",
  },
  low: {
    color: "border-l-success",
    icon: <CheckCircle className="h-4 w-4 text-success" />,
    label: "bg-success/10 text-success border-success/20",
  },
};

function RecommendationCard({ rec }: { rec: Recommendation }) {
  const config = priorityConfig[rec.priority] ?? priorityConfig.medium;
  const confidence = Math.round((rec.confidence ?? 0.75) * 100);

  return (
    <motion.div
      whileHover={{ x: 2 }}
      className={`glass-card rounded-[20px] p-5 flex gap-4 border-l-2 ${config.color}`}
    >
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/[0.03] border border-border/40 mt-0.5">
        {config.icon}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="text-sm font-semibold text-foreground leading-tight">{rec.title}</h3>
          <span className={`shrink-0 text-[11px] font-medium border px-2 py-0.5 rounded-full capitalize ${config.label}`}>
            {rec.priority}
          </span>
        </div>

        {rec.description && (
          <p className="text-xs text-muted-foreground leading-relaxed mb-3">{rec.description}</p>
        )}

        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          {rec.roi_estimate != null && (
            <span className="flex items-center gap-1 text-success font-medium">
              <TrendingUp className="h-3 w-3" />
              +${rec.roi_estimate.toLocaleString()} est. ROI
            </span>
          )}
          <span>Category: {rec.category}</span>
          <span className="ml-auto">Confidence: {confidence}%</span>
        </div>

        {/* Confidence bar */}
        <div className="mt-2 h-1 rounded-full bg-white/[0.05] overflow-hidden">
          <div
            className="h-full rounded-full bg-primary/60 transition-all duration-500"
            style={{ width: `${confidence}%` }}
          />
        </div>
      </div>
    </motion.div>
  );
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07 } },
};
const itemVariants = {
  hidden: { opacity: 0, x: -12 },
  show: { opacity: 1, x: 0, transition: { type: "spring" as const, stiffness: 300, damping: 26 } },
};

export default function RecommendationsPage() {
  const { data: recommendations, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => recommendationsApi.list(),
  });

  const sorted = [...(recommendations ?? [])].sort((a, b) => {
    const order = { critical: 0, high: 1, medium: 2, low: 3 };
    return (order[a.priority] ?? 3) - (order[b.priority] ?? 3);
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">Recommendations</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Prioritized, evidence-backed actions generated from your business data.
          </p>
        </div>
        <span className="text-sm text-muted-foreground">{sorted.length} recommendations</span>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => <CardSkeleton key={i} lines={3} />)}
        </div>
      ) : isError ? (
        <ErrorState 
          onRetry={refetch} 
          errorType={detectErrorType(error)}
          developerDetails={error instanceof Error ? error.message : String(error)}
        />
      ) : sorted.length === 0 ? (
        <EmptyState
          icon={<Zap className="h-7 w-7 text-muted-foreground/50" />}
          title="No recommendations yet"
          description="Run the Recommendation Engine on your analytical insights to generate action items."
        />
      ) : (
        <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-4">
          {sorted.map((rec) => (
            <motion.div key={rec.id} variants={itemVariants}>
              <RecommendationCard rec={rec} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}

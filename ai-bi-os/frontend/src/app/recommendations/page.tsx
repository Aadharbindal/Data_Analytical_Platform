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
  Critical: {
    color: "border-l-error",
    icon: <AlertTriangle className="h-4 w-4 text-error" />,
    label: "bg-error/10 text-error border-error/20",
  },
  High: {
    color: "border-l-warning",
    icon: <TrendingUp className="h-4 w-4 text-warning" />,
    label: "bg-warning/10 text-warning border-warning/20",
  },
  Medium: {
    color: "border-l-primary",
    icon: <Zap className="h-4 w-4 text-primary" />,
    label: "bg-primary/10 text-primary border-primary/20",
  },
  Low: {
    color: "border-l-success",
    icon: <CheckCircle className="h-4 w-4 text-success" />,
    label: "bg-success/10 text-success border-success/20",
  },
};

function RecommendationCard({ rec }: { rec: Recommendation }) {
  const config = priorityConfig[rec.priority] ?? priorityConfig.Medium;
  const colorPrefix = config.color.replace('border-l-', 'bg-');

  return (
    <motion.div
      className={`glass-card h-full rounded-[20px] p-5 flex flex-col relative bg-gradient-to-br from-white/[0.03] to-transparent border border-white/[0.08] shadow-sm hover:shadow-md transition-all duration-300 border-l-4 ${config.color}`}
    >
      {/* Decorative gradient blob */}
      <div className={`absolute -right-12 -top-12 w-40 h-40 blur-3xl opacity-[0.06] pointer-events-none ${colorPrefix}`} />

      {/* Top area: Title and badges */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-3 flex-1 min-w-0 z-10">
          <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/[0.06] border border-white/[0.05] shadow-inner`}>
            {config.icon}
          </div>
          <div className="flex flex-col min-w-0">
            <h3 className="text-base font-semibold text-foreground leading-snug line-clamp-2">
              {rec.title}
            </h3>
            
            {/* Badges directly under title */}
            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
              <span className={`text-[10px] font-semibold tracking-wide uppercase px-2 py-0.5 rounded-full border ${config.label}`}>
                {rec.priority}
              </span>
              {rec.verified && (
                <span className="flex items-center gap-1 text-[10px] font-semibold tracking-wide uppercase text-success bg-success/10 px-2 py-0.5 rounded-full">
                  <CheckCircle className="h-3 w-3" />
                  Verified Fact
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Rationale / Description */}
      {rec.rationale && (
        <div className="mb-4 z-10">
          <p className="text-[13px] text-muted-foreground leading-relaxed">
            {rec.rationale}
          </p>
        </div>
      )}

      {/* Growing flex area so footer sticks to bottom */}
      <div className="flex-grow flex flex-col gap-4 z-10">
         {/* Could put extra data here in future */}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 mt-4 border-t border-border/40 gap-3 z-10">
        <span className="inline-flex items-center text-[11px] font-medium text-muted-foreground/70 tracking-wide uppercase">
          Category: <span className="text-foreground/90 ml-1.5 font-semibold">{rec.category}</span>
        </span>
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
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => recommendationsApi.generate(),
  });

  const isApiError = data && typeof data === 'object' && !Array.isArray(data) && data.success === false;
  const recommendations = Array.isArray(data) ? data : [];

  const sorted = [...recommendations].sort((a, b) => {
    const order: Record<string, number> = { Critical: 0, High: 1, Medium: 2, Low: 3 };
    return (order[a.priority] ?? 3) - (order[b.priority] ?? 3);
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">Recommendations</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Prioritized, deterministic evidence-backed actions generated from your business data.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">{sorted.length} recommendations</span>
          <button 
            onClick={() => refetch()} 
            className="text-sm px-4 py-1.5 bg-primary/10 hover:bg-primary/20 text-primary font-medium rounded-full transition-colors border border-primary/20"
          >
            Regenerate
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => <CardSkeleton key={i} lines={3} />)}
        </div>
      ) : isError || isApiError ? (
        <ErrorState 
          onRetry={refetch} 
          errorType={detectErrorType(error)}
          developerDetails={isApiError ? data.message : (error instanceof Error ? error.message : String(error))}
        />
      ) : sorted.length === 0 ? (
        <EmptyState
          icon={<Zap className="h-7 w-7 text-muted-foreground/50" />}
          title="No recommendations yet"
          description="Upload a dataset to generate recommendations based on deterministic data evaluation."
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

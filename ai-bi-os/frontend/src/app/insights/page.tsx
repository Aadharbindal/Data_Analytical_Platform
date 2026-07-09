"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { insightsApi } from "@/lib/api";
import type { Insight } from "@/lib/types";
import { motion } from "framer-motion";
import { Lightbulb, TrendingUp, TrendingDown, AlertCircle, Info } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState, detectErrorType } from "@/components/ui/error-state";

const categoryColors: Record<string, string> = {
  revenue: "bg-success/10 text-success border-success/20",
  risk: "bg-error/10 text-error border-error/20",
  opportunity: "bg-primary/10 text-primary border-primary/20",
  warning: "bg-warning/10 text-warning border-warning/20",
  trend: "bg-purple-500/10 text-purple-400 border-purple-500/20",
};

function formatRelativeTime(dateString?: string) {
  if (!dateString) return "Just now";
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return "Just now";
  
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) return "Just now";
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  return `${Math.floor(diffInSeconds / 86400)} days ago`;
}

function InsightCard({ insight }: { insight: Insight }) {
  const confidence = Math.round((insight.score?.confidence ?? 0.75) * 100);
  const colorKey =
    confidence > 85 ? "risk" :
    insight.category?.toLowerCase().includes("revenue") ? "revenue" :
    insight.category?.toLowerCase().includes("opportunity") ? "opportunity" :
    "trend";
  const categoryColor = categoryColors[colorKey] ?? categoryColors.trend;

  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="glass-card rounded-[20px] p-5 flex flex-col gap-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
            <Lightbulb className="h-4 w-4 text-primary" />
          </div>
          <h3 className="text-sm font-semibold text-foreground leading-tight">{insight.title}</h3>
        </div>
        <span className={`shrink-0 text-[11px] font-medium border px-2 py-0.5 rounded-full ${categoryColor}`}>
          {insight.category}
        </span>
      </div>

      {insight.description && (
        <p className="text-xs text-muted-foreground leading-relaxed">{insight.description}</p>
      )}

      {insight.metric_name && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/[0.02] border border-border/40">
          <span className="text-xs text-muted-foreground">{insight.metric_name}</span>
          <span className="text-sm font-semibold text-foreground tabular-metrics ml-auto">
            {insight.metric_value?.toLocaleString() ?? "–"}
          </span>
        </div>
      )}

      {/* Confidence Bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Confidence</span>
          <span className="font-semibold text-foreground">{confidence}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-white/[0.05] overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              confidence > 80 ? "bg-success" : confidence > 60 ? "bg-warning" : "bg-error"
            }`}
            style={{ width: `${confidence}%` }}
          />
        </div>
      </div>

      <p className="text-[11px] text-muted-foreground/60 mt-auto">
        {formatRelativeTime(insight.created_at)}
      </p>
    </motion.div>
  );
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 26 } },
};

export default function InsightsPage() {
  const { data: insights, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["insights"],
    queryFn: () => insightsApi.list(),
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">Insights</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Automatically detected business intelligence findings from your data.
          </p>
        </div>
        <span className="text-sm text-muted-foreground">
          {insights?.length ?? 0} insights
        </span>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-3 gap-5">
          {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} lines={4} />)}
        </div>
      ) : isError ? (
        <ErrorState 
          onRetry={refetch} 
          errorType={detectErrorType(error)}
          developerDetails={error instanceof Error ? error.message : String(error)}
        />
      ) : !insights || insights.length === 0 ? (
        <EmptyState
          icon={<Lightbulb className="h-7 w-7 text-muted-foreground/50" />}
          title="No insights yet"
          description="Run the Insight Detection Engine on a dataset to automatically discover business findings."
        />
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="grid grid-cols-3 gap-5"
        >
          {insights.map((insight) => (
            <motion.div key={insight.id} variants={itemVariants}>
              <InsightCard insight={insight} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}

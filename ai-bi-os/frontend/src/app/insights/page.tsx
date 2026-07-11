"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { insightsApi } from "@/lib/api";
import type { Insight } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import { Lightbulb, Database, CheckCircle, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState, detectErrorType } from "@/components/ui/error-state";
import { Button } from "@/components/ui/button";

const categoryColors: Record<string, string> = {
  revenue: "bg-success/10 text-success border-success/20",
  risk: "bg-error/10 text-error border-error/20",
  opportunity: "bg-primary/10 text-primary border-primary/20",
  trend: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  anomaly: "bg-warning/10 text-warning border-warning/20",
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
  const [showSql, setShowSql] = useState(false);
  const confidence = Math.round((insight.confidence ?? (insight.score?.confidence ?? 0.75)) * 100);
  
  const colorKey = (insight.category?.toLowerCase() || "trend");
  const categoryColor = categoryColors[colorKey] || categoryColors.trend;

  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="glass-card rounded-[20px] p-5 flex flex-col gap-4 relative overflow-hidden"
    >
      {/* Decorative gradient blob */}
      <div className={`absolute -right-10 -top-10 w-32 h-32 blur-3xl opacity-[0.03] pointer-events-none ${categoryColor.split(' ')[0]}`} />

      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
            <Lightbulb className="h-4 w-4 text-primary" />
          </div>
          <h3 className="text-sm font-semibold text-foreground leading-tight">{insight.title}</h3>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className={`shrink-0 text-[11px] font-medium border px-2 py-0.5 rounded-full ${categoryColor}`}>
            {insight.category}
          </span>
          {insight.verified && (
            <span className="flex items-center gap-1 text-[10px] font-medium text-success">
              <CheckCircle className="h-3 w-3" />
              Verified
            </span>
          )}
        </div>
      </div>

      {insight.description && (
        <p className="text-xs text-muted-foreground leading-relaxed">{insight.description}</p>
      )}

      {insight.impact !== undefined && insight.impact > 0 && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/[0.02] border border-border/40">
          <span className="text-xs text-muted-foreground">Impact Value</span>
          <span className="text-sm font-semibold text-foreground tabular-metrics ml-auto">
            {insight.impact.toLocaleString()}
          </span>
        </div>
      )}

      {insight.recommendation && (
        <div className="text-xs p-3 rounded-xl bg-primary/5 border border-primary/10">
          <span className="font-semibold text-primary block mb-1">Recommendation:</span>
          <span className="text-muted-foreground">{insight.recommendation}</span>
        </div>
      )}

      {/* Confidence Bar */}
      <div className="space-y-1.5 mt-auto">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">AI Confidence</span>
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

      <div className="flex items-center justify-between pt-2 border-t border-border/50">
        <p className="text-[11px] text-muted-foreground/60">
          {formatRelativeTime(insight.created_at)}
        </p>
        
        {insight.audit_sql && (
          <button
            onClick={() => setShowSql(!showSql)}
            className="text-[11px] font-medium text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
          >
            <Database className="h-3 w-3" />
            {showSql ? "Hide SQL" : "View SQL"}
            {showSql ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </button>
        )}
      </div>

      <AnimatePresence>
        {showSql && insight.audit_sql && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-3 bg-black/40 border border-border/50 rounded-xl mt-2 text-[10px] font-mono text-muted-foreground whitespace-pre-wrap overflow-x-auto">
              {insight.audit_sql}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
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
  const queryClient = useQueryClient();
  const { data: insights, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["insights"],
    queryFn: () => insightsApi.list(),
  });

  const deepAnalyze = useMutation({
    mutationFn: () => insightsApi.deepAnalyze(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insights"] });
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">Deep Insights Engine</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Agentic AI automatically asks questions, runs queries, and surfaces verified business findings.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">
            {insights?.length ?? 0} insights
          </span>
          <Button 
            onClick={() => deepAnalyze.mutate()}
            disabled={deepAnalyze.isPending}
            className="bg-primary hover:bg-primary/90 text-primary-foreground gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${deepAnalyze.isPending ? 'animate-spin' : ''}`} />
            {deepAnalyze.isPending ? "Analyzing Data..." : "Regenerate Insights"}
          </Button>
        </div>
      </div>

      {isLoading || deepAnalyze.isPending ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} lines={5} />)}
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
          description="Click Regenerate Insights to run the agentic pipeline on your active dataset."
          action={
            <Button onClick={() => deepAnalyze.mutate()} className="bg-primary hover:bg-primary/90 text-primary-foreground gap-2">
              <RefreshCw className="h-4 w-4" />
              Regenerate Insights
            </Button>
          }
        />
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
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

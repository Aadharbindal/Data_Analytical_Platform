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
import { formatNumber } from "@/lib/utils";

const categoryColors: Record<string, { border: string; bg: string; text: string }> = {
  revenue: { border: "border-success", bg: "bg-success/10", text: "text-success" },
  risk: { border: "border-error", bg: "bg-error/10", text: "text-error" },
  opportunity: { border: "border-primary", bg: "bg-primary/10", text: "text-primary" },
  trend: { border: "border-purple-500", bg: "bg-purple-500/10", text: "text-purple-500" },
  anomaly: { border: "border-amber-500", bg: "bg-amber-500/10", text: "text-amber-500" },
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
  const [expanded, setExpanded] = useState(false);
  const confidence = Math.round((insight.confidence ?? (insight.score?.confidence ?? 0.75)) * 100);
  
  const colorKey = (insight.category?.toLowerCase() || "trend");
  const categoryColor = categoryColors[colorKey] || categoryColors.trend;

  // Smart impact formatting
  const titleLower = (insight.title || "").toLowerCase();
  const isCurrency = titleLower.includes('revenue') || titleLower.includes('cost') || titleLower.includes('price') || titleLower.includes('sales') || (insight.impact !== undefined && insight.impact % 1 !== 0) || (insight.impact !== undefined && insight.impact > 10000);
  const isPercent = titleLower.includes('percentage') || titleLower.includes('rate');
  const unit = isCurrency ? "" : isPercent ? "%" : (titleLower.includes('quantity') || titleLower.includes('units') || titleLower.includes('count') ? " units" : "");
  
  const formatImpact = (val: number) => {
    if (isCurrency) return `$${formatNumber(val)}`;
    if (isPercent) return `${val}%`;
    return `${val.toLocaleString()}${unit}`;
  };

  const confidenceColor = confidence >= 80 ? "bg-success" : confidence >= 50 ? "bg-warning" : "bg-error";

  return (
    <div
      className={`glass-card h-full rounded-[20px] p-5 flex flex-col relative bg-gradient-to-br from-white/[0.03] to-transparent border border-white/[0.08] shadow-sm hover:shadow-md transition-all duration-300 border-l-4 ${categoryColor.border}`}
    >
      {/* Decorative gradient blob */}
      <div className={`absolute -right-12 -top-12 w-40 h-40 blur-3xl opacity-[0.06] pointer-events-none ${categoryColor.bg.split('/')[0].replace('bg-', '')}`} />

      {/* Top area: Title and badges */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${categoryColor.bg}`}>
            <Lightbulb className={`h-4 w-4 ${categoryColor.text}`} />
          </div>
          <div className="flex flex-col min-w-0">
            <h3 
              className="text-base font-semibold text-foreground leading-snug line-clamp-2"
              title={insight.title}
            >
              {insight.title}
            </h3>
            
            {/* Badges directly under title */}
            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
              <span className={`text-[10px] font-semibold tracking-wide uppercase px-2 py-0.5 rounded-full ${categoryColor.bg} ${categoryColor.text}`}>
                {insight.category}
              </span>
              {insight.verified && (
                <span className="flex items-center gap-1 text-[10px] font-semibold tracking-wide uppercase text-success bg-success/10 px-2 py-0.5 rounded-full">
                  <CheckCircle className="h-3 w-3" />
                  Verified
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Description */}
      {insight.description && (
        <div className="mb-4">
          <p className={`text-[13px] text-muted-foreground leading-relaxed ${expanded ? "" : "line-clamp-3"}`}>
            {insight.description}
          </p>
          {insight.description.length > 120 && (
            <button 
              onClick={() => setExpanded(!expanded)} 
              className="text-xs text-primary hover:underline mt-1 font-medium"
            >
              {expanded ? "Show less" : "Read more"}
            </button>
          )}
        </div>
      )}

      {/* Growing flex area so footer sticks to bottom */}
      <div className="flex-grow flex flex-col gap-4">
        {/* Impact Value */}
        {insight.impact !== undefined && insight.impact > 0 && (
          <div className="self-start inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.05]">
            <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Impact</span>
            <span className="text-sm font-semibold text-foreground tabular-metrics" title={insight.impact.toString()}>
              {formatImpact(insight.impact)}
            </span>
          </div>
        )}

        {/* Recommendation */}
        {insight.recommendation && (
          <div className="text-[13px] p-3 rounded-xl bg-primary/5 border border-primary/10 leading-relaxed mt-auto">
            <span className="font-semibold text-primary flex items-center gap-1.5 mb-1">
              <Lightbulb className="h-3.5 w-3.5" /> Recommendation
            </span>
            <span className="text-muted-foreground/90">{insight.recommendation}</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 mt-4 border-t border-border/40 gap-3">
        {/* Confidence scale + % */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="flex gap-0.5 h-1.5 w-8 rounded-full overflow-hidden bg-black/20">
             <div className={`h-full w-full ${confidenceColor}`} />
          </div>
          <span className={`text-[11px] font-bold ${confidenceColor.replace('bg-', 'text-')}`}>{confidence}%</span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[10px] font-medium text-muted-foreground/60 whitespace-nowrap">
            {formatRelativeTime(insight.created_at)}
          </span>
          {insight.audit_sql && (
            <button
              onClick={() => setShowSql(!showSql)}
              className="text-[10px] font-semibold tracking-wide uppercase text-muted-foreground/70 hover:text-foreground flex items-center gap-1 transition-colors whitespace-nowrap"
            >
              <Database className="h-3 w-3" />
              {showSql ? "Hide SQL" : "View SQL"}
            </button>
          )}
        </div>
      </div>

      <AnimatePresence>
        {showSql && insight.audit_sql && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-3 bg-black/40 border border-white/[0.05] rounded-xl mt-3 text-[10px] font-mono text-muted-foreground/80 whitespace-pre-wrap overflow-x-auto shadow-inner">
              {insight.audit_sql}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
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
        <div className="grid grid-cols-[repeat(auto-fit,minmax(320px,1fr))] gap-6">
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
          className="grid grid-cols-[repeat(auto-fit,minmax(320px,1fr))] gap-6"
        >
          {insights.map((insight) => (
            <motion.div key={insight.id} variants={itemVariants} className="h-full">
              <InsightCard insight={insight} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}

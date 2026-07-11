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
      whileHover={{ y: -4, boxShadow: "0 12px 30px -10px rgba(0,0,0,0.3)" }}
      className="glass-card h-full rounded-[24px] p-6 flex flex-col gap-5 relative overflow-hidden bg-gradient-to-br from-white/[0.05] to-transparent border border-white/[0.08] shadow-lg backdrop-blur-xl transition-all duration-300"
    >
      {/* Decorative gradient blob */}
      <div className={`absolute -right-12 -top-12 w-40 h-40 blur-3xl opacity-[0.06] pointer-events-none ${categoryColor.split(' ')[0]}`} />

      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[14px] bg-white/[0.06] border border-white/[0.05] shadow-inner">
            <Lightbulb className={`h-5 w-5 ${categoryColor.split(' ')[1] || "text-primary"}`} />
          </div>
          <h3 className="text-base font-semibold text-foreground/90 leading-tight tracking-tight">{insight.title}</h3>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <span className={`text-[11px] font-semibold tracking-wide uppercase border px-2.5 py-0.5 rounded-full ${categoryColor}`}>
            {insight.category}
          </span>
          {insight.verified && (
            <span className="flex items-center gap-1 text-[10px] font-semibold tracking-wide uppercase text-success/80">
              <CheckCircle className="h-3 w-3" />
              Verified
            </span>
          )}
        </div>
      </div>

      {insight.description && (
        <p className="text-[13px] text-muted-foreground/80 leading-relaxed font-light">{insight.description}</p>
      )}

      {insight.impact !== undefined && insight.impact > 0 && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-2xl bg-white/[0.03] border border-white/[0.04]">
          <span className="text-[11px] font-medium text-muted-foreground/70 tracking-wide uppercase">Impact Value</span>
          <span className="text-lg font-semibold text-foreground tabular-metrics ml-auto">
            {insight.impact.toLocaleString(undefined, { maximumFractionDigits: 2 })}
          </span>
        </div>
      )}

      {insight.recommendation && (
        <div className="text-[13px] p-4 rounded-2xl bg-primary/[0.03] border border-primary/[0.08] leading-relaxed">
          <span className="font-semibold text-primary/90 flex items-center gap-1.5 mb-1.5">
            <Lightbulb className="h-4 w-4" /> Recommendation
          </span>
          <span className="text-muted-foreground/90">{insight.recommendation}</span>
        </div>
      )}

      {/* Confidence Bar */}
      <div className="space-y-2 mt-auto pt-2">
        <div className="flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider">
          <span className="text-muted-foreground/60">AI Confidence</span>
          <span className="text-foreground/80">{confidence}%</span>
        </div>
        <div className="h-2 rounded-full bg-black/40 overflow-hidden shadow-inner border border-white/[0.02]">
          <div
            className={`h-full rounded-full transition-all duration-1000 ease-out ${
              confidence > 80 ? "bg-success" : confidence > 60 ? "bg-warning" : "bg-error"
            }`}
            style={{ width: `${confidence}%` }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between pt-3 mt-1 border-t border-border/40">
        <p className="text-[11px] font-medium text-muted-foreground/50">
          {formatRelativeTime(insight.created_at)}
        </p>
        
        {insight.audit_sql && (
          <button
            onClick={() => setShowSql(!showSql)}
            className="text-[11px] font-semibold tracking-wide uppercase text-muted-foreground/70 hover:text-foreground flex items-center gap-1.5 transition-colors"
          >
            <Database className="h-3.5 w-3.5" />
            {showSql ? "Hide SQL" : "View SQL"}
            {showSql ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
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
            <div className="p-4 bg-black/40 border border-white/[0.05] rounded-2xl mt-3 text-[11px] font-mono text-muted-foreground/80 whitespace-pre-wrap overflow-x-auto shadow-inner">
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
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
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

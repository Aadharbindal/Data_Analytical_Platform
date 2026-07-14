"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { insightsApi } from "@/lib/api";
import type { Insight } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import {
  Lightbulb, Database, CheckCircle, RefreshCw,
  TrendingUp, AlertTriangle, Zap, Activity, ShieldAlert, BarChart2, Sparkles
} from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState, detectErrorType } from "@/components/ui/error-state";
import { Button } from "@/components/ui/button";
import { formatNumber } from "@/lib/utils";

// ─── Category theme map ────────────────────────────────────────────────────
const CATEGORY_THEMES: Record<string, {
  accent: string;        // Tailwind border colour
  glow: string;          // box-shadow style value
  iconBg: string;        // icon wrapper background
  iconText: string;      // icon colour
  pillBg: string;        // category pill background
  pillText: string;      // category pill text colour
  bannerFrom: string;    // gradient start
  icon: React.ReactNode;
}> = {
  revenue:     { accent: "border-emerald-500",  glow: "0 0 0 1px rgba(16,185,129,.25), 0 4px 24px rgba(16,185,129,.08)",  iconBg: "bg-emerald-500/15",  iconText: "text-emerald-400",  pillBg: "bg-emerald-500/10", pillText: "text-emerald-400", bannerFrom: "from-emerald-500/10", icon: <TrendingUp className="h-4 w-4" /> },
  risk:        { accent: "border-rose-500",     glow: "0 0 0 1px rgba(244,63,94,.25),  0 4px 24px rgba(244,63,94,.08)",   iconBg: "bg-rose-500/15",     iconText: "text-rose-400",     pillBg: "bg-rose-500/10",    pillText: "text-rose-400",    bannerFrom: "from-rose-500/10",    icon: <ShieldAlert className="h-4 w-4" /> },
  opportunity: { accent: "border-violet-500",   glow: "0 0 0 1px rgba(139,92,246,.25), 0 4px 24px rgba(139,92,246,.08)", iconBg: "bg-violet-500/15",   iconText: "text-violet-400",   pillBg: "bg-violet-500/10",  pillText: "text-violet-400",  bannerFrom: "from-violet-500/10",  icon: <Zap className="h-4 w-4" /> },
  trend:       { accent: "border-purple-500",   glow: "0 0 0 1px rgba(168,85,247,.25), 0 4px 24px rgba(168,85,247,.08)", iconBg: "bg-purple-500/15",   iconText: "text-purple-400",   pillBg: "bg-purple-500/10",  pillText: "text-purple-400",  bannerFrom: "from-purple-500/10",  icon: <Activity className="h-4 w-4" /> },
  anomaly:     { accent: "border-amber-500",    glow: "0 0 0 1px rgba(245,158,11,.25), 0 4px 24px rgba(245,158,11,.08)", iconBg: "bg-amber-500/15",    iconText: "text-amber-400",    pillBg: "bg-amber-500/10",   pillText: "text-amber-400",   bannerFrom: "from-amber-500/10",   icon: <AlertTriangle className="h-4 w-4" /> },
  default:     { accent: "border-sky-500",      glow: "0 0 0 1px rgba(14,165,233,.25),  0 4px 24px rgba(14,165,233,.08)",  iconBg: "bg-sky-500/15",      iconText: "text-sky-400",      pillBg: "bg-sky-500/10",     pillText: "text-sky-400",     bannerFrom: "from-sky-500/10",     icon: <BarChart2 className="h-4 w-4" /> },
};

function getCategoryTheme(category?: string) {
  const key = (category ?? "").toLowerCase();
  return CATEGORY_THEMES[key] ?? CATEGORY_THEMES.default;
}

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

// ─── Segmented confidence bar (5 blocks) ───────────────────────────────────
function ConfidenceBar({ pct }: { pct: number }) {
  const filled = Math.round((pct / 100) * 5);
  const color = pct >= 80 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-400" : "bg-rose-500";
  const textColor = pct >= 80 ? "text-emerald-400" : pct >= 50 ? "text-amber-400" : "text-rose-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex gap-[3px]">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className={`h-[5px] w-[10px] rounded-sm transition-all duration-300 ${
              i < filled ? color : "bg-white/10"
            }`}
          />
        ))}
      </div>
      <span className={`text-[11px] font-bold tabular-nums ${textColor}`}>{pct}%</span>
    </div>
  );
}

// ─── Main card ─────────────────────────────────────────────────────────────
function InsightCard({ insight }: { insight: Insight }) {
  const [showSql, setShowSql] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const confidence = Math.round(
    (insight.confidence ?? (insight.score?.confidence ?? 0.75)) * 100
  );
  const theme = getCategoryTheme(insight.category);

  // ── Smart impact formatting
  const titleLower = (insight.title || "").toLowerCase();
  const isCurrency =
    titleLower.includes("revenue") ||
    titleLower.includes("cost") ||
    titleLower.includes("price") ||
    titleLower.includes("sales") ||
    (insight.impact !== undefined && Number(insight.impact) > 10_000);
  const isPercent =
    titleLower.includes("percentage") || titleLower.includes("rate");
  const isCount =
    titleLower.includes("count") ||
    titleLower.includes("units") ||
    titleLower.includes("quantity");

  const formatImpact = (val: number) => {
    if (isCurrency) {
      if (val >= 1_00_00_000) return `₹${(val / 1_00_00_000).toFixed(1)}Cr`;
      if (val >= 1_00_000) return `₹${(val / 1_00_000).toFixed(1)}L`;
      if (val >= 1_000) return `₹${(val / 1_000).toFixed(1)}K`;
      return `₹${val.toLocaleString()}`;
    }
    if (isPercent) return `${val.toFixed(1)}%`;
    if (isCount) {
      if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
      if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
      return val.toLocaleString();
    }
    return formatNumber(val);
  };

  const hasImpact = insight.impact !== undefined && Number(insight.impact) > 0;

  return (
    <div
      className="relative flex flex-col overflow-hidden rounded-2xl border border-white/[0.08] bg-[hsl(var(--card))] transition-all duration-300 hover:-translate-y-[2px] hover:border-white/[0.14] shadow-sm hover:shadow-md"
    >

      <div className="relative flex flex-col gap-0 p-5">

        {/* ── Header row ── */}
        <div className="flex items-start gap-3 mb-4">
          {/* Icon badge */}
          <div
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
              theme.iconBg
            } ring-1 ring-white/10`}
          >
            <span className={theme.iconText}>{theme.icon}</span>
          </div>

          <div className="flex-1 min-w-0">
            {/* Category pill */}
            <span
              className={`inline-flex items-center gap-1 text-[9px] font-bold tracking-[0.12em] uppercase px-2 py-0.5 rounded-full mb-1.5 ${
                theme.pillBg
              } ${theme.pillText}`}
            >
              {insight.category || "Insight"}
            </span>

            {/* Title */}
            <h3
              className="text-[15px] font-semibold text-foreground leading-snug"
              title={insight.title}
            >
              {insight.title}
            </h3>
          </div>

          {/* Verified badge — top-right */}
          {insight.verified && (
            <span className="shrink-0 flex items-center gap-1 text-[9px] font-bold tracking-widest uppercase text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-1 rounded-full">
              <CheckCircle className="h-2.5 w-2.5" />
              Verified
            </span>
          )}
        </div>

        {/* ── Description ── */}
        {insight.description && (
          <div className="mb-4">
            <p
              className={`text-[13px] text-muted-foreground leading-relaxed ${
                expanded ? "" : "line-clamp-3"
              }`}
            >
              {insight.description}
            </p>
            {insight.description.length > 160 && (
              <button
                onClick={() => setExpanded(!expanded)}
                className={`text-[11px] font-semibold mt-1.5 ${theme.pillText} hover:underline`}
              >
                {expanded ? "Show less ↑" : "Read more ↓"}
              </button>
            )}
          </div>
        )}

        {/* ── Impact + Recommendation row ── */}
        <div className="flex flex-col gap-3 flex-grow">
          {hasImpact && (
            <div className="flex items-center gap-2 self-start">
              <div className="flex items-center gap-1.5 rounded-lg border border-white/[0.07] bg-white/[0.03] px-3 py-1.5">
                <Sparkles className={`h-3 w-3 ${theme.iconText}`} />
                <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Business Impact
                </span>
                <span className="text-sm font-bold text-foreground tabular-nums ml-1">
                  {formatImpact(Number(insight.impact!))}
                </span>
              </div>
            </div>
          )}

          {insight.recommendation && (
            <div
              className={`mt-auto rounded-xl border px-4 py-3 ${
                theme.pillBg
              } border-current/10`}
              style={{ borderColor: "rgba(255,255,255,0.06)" }}
            >
              <p className={`text-[10px] font-bold uppercase tracking-widest mb-1 ${theme.pillText}`}>
                💡 Recommendation
              </p>
              <p className="text-[12.5px] text-muted-foreground/90 leading-relaxed">
                {insight.recommendation}
              </p>
            </div>
          )}
        </div>

        {/* ── Footer ── */}
        <div className="flex items-center justify-between pt-3 mt-4 border-t border-white/[0.06]">
          <ConfidenceBar pct={confidence} />

          <div className="flex items-center gap-3">
            <span className="text-[10px] text-muted-foreground/50 font-medium">
              {formatRelativeTime(insight.created_at)}
            </span>
            {insight.audit_sql && (
              <button
                onClick={() => setShowSql(!showSql)}
                className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60 hover:text-foreground transition-colors"
              >
                <Database className="h-3 w-3" />
                {showSql ? "Hide SQL" : "SQL"}
              </button>
            )}
          </div>
        </div>

        {/* ── SQL block ── */}
        <AnimatePresence>
          {showSql && insight.audit_sql && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <pre className="mt-3 rounded-xl border border-white/[0.05] bg-black/50 p-3 text-[10px] font-mono text-muted-foreground/80 whitespace-pre-wrap overflow-x-auto shadow-inner">
                {insight.audit_sql}
              </pre>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
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
        <div className="grid grid-cols-1 gap-6">
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
          className="grid grid-cols-1 md:grid-cols-2 gap-5"
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

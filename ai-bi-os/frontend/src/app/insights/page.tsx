"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { insightsApi } from "@/lib/api";
import type { Insight } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import {
  Lightbulb,
  Database,
  CheckCircle,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  Zap,
  Activity,
  ShieldAlert,
  BarChart2,
  Sparkles,
  ChevronDown,
} from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState, detectErrorType } from "@/components/ui/error-state";
import { Button } from "@/components/ui/button";
import { formatNumber } from "@/lib/utils";

// ─── Category theme map ────────────────────────────────────────────────────
const CATEGORY_THEMES: Record<
  string,
  {
    accent: string;
    glowBg: string;
    iconBg: string;
    iconText: string;
    pillBg: string;
    pillText: string;
    bannerFrom: string;
    icon: React.ReactNode;
  }
> = {
  revenue: {
    accent: "border-emerald-500",
    glowBg: "bg-emerald-500",
    iconBg: "bg-emerald-500/10",
    iconText: "text-emerald-400",
    pillBg: "bg-emerald-500/10",
    pillText: "text-emerald-400",
    bannerFrom: "from-emerald-500/10",
    icon: <TrendingUp className="h-5 w-5" />,
  },
  risk: {
    accent: "border-rose-500",
    glowBg: "bg-rose-500",
    iconBg: "bg-rose-500/10",
    iconText: "text-rose-400",
    pillBg: "bg-rose-500/10",
    pillText: "text-rose-400",
    bannerFrom: "from-rose-500/10",
    icon: <ShieldAlert className="h-5 w-5" />,
  },
  opportunity: {
    accent: "border-violet-500",
    glowBg: "bg-violet-500",
    iconBg: "bg-violet-500/10",
    iconText: "text-violet-400",
    pillBg: "bg-violet-500/10",
    pillText: "text-violet-400",
    bannerFrom: "from-violet-500/10",
    icon: <Zap className="h-5 w-5" />,
  },
  trend: {
    accent: "border-purple-500",
    glowBg: "bg-purple-500",
    iconBg: "bg-purple-500/10",
    iconText: "text-purple-400",
    pillBg: "bg-purple-500/10",
    pillText: "text-purple-400",
    bannerFrom: "from-purple-500/10",
    icon: <Activity className="h-5 w-5" />,
  },
  anomaly: {
    accent: "border-amber-500",
    glowBg: "bg-amber-500",
    iconBg: "bg-amber-500/10",
    iconText: "text-amber-400",
    pillBg: "bg-amber-500/10",
    pillText: "text-amber-400",
    bannerFrom: "from-amber-500/10",
    icon: <AlertTriangle className="h-5 w-5" />,
  },
  default: {
    accent: "border-sky-500",
    glowBg: "bg-sky-500",
    iconBg: "bg-sky-500/10",
    iconText: "text-sky-400",
    pillBg: "bg-sky-500/10",
    pillText: "text-sky-400",
    bannerFrom: "from-sky-500/10",
    icon: <BarChart2 className="h-5 w-5" />,
  },
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
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min ago`;
  if (diffInSeconds < 86400)
    return `${Math.floor(diffInSeconds / 3600)} hrs ago`;
  return `${Math.floor(diffInSeconds / 86400)} days ago`;
}

// ─── Segmented confidence bar (5 blocks) ───────────────────────────────────
function ConfidenceBar({ pct }: { pct: number }) {
  const filled = Math.round((pct / 100) * 5);
  const color =
    pct >= 80
      ? "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)]"
      : pct >= 50
        ? "bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.8)]"
        : "bg-rose-400 shadow-[0_0_10px_rgba(244,63,94,0.8)]";
  const textColor =
    pct >= 80
      ? "text-emerald-400"
      : pct >= 50
        ? "text-amber-400"
        : "text-rose-400";
  return (
    <div className="flex items-center gap-3">
      <div className="flex gap-1.5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className={`h-[6px] w-6 rounded-full transition-all duration-300 ${
              i < filled ? color : "bg-white/10"
            }`}
          />
        ))}
      </div>
      <span
        className={`text-[13px] font-mono font-bold tracking-wide ${textColor}`}
      >
        {pct}% confidence
      </span>
    </div>
  );
}

// ─── Main card ─────────────────────────────────────────────────────────────
function InsightCard({ insight }: { insight: Insight }) {
  const [showSql, setShowSql] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const confidence = Math.round(
    (insight.confidence ?? insight.score?.confidence ?? 0.75) * 100,
  );
  const theme = getCategoryTheme(insight.category);

  const renderDescription = (text: string, colorClass: string) => {
    if (!text) return null;
    const parts = text.split(/([+-]?₹?[\d,]+(?:\.\d+)?(?:%|[a-zA-Z]+)?)/g);
    return parts.map((part, i) => {
      if (/[0-9]/.test(part)) {
        return (
          <span key={i} className={`font-bold ${colorClass}`}>
            {part}
          </span>
        );
      }
      return part;
    });
  };

  return (
    <div className="relative flex flex-col overflow-hidden rounded-[20px] border border-white/[0.05] bg-[#0c0c0e] transition-all duration-300 hover:-translate-y-1 hover:border-white/[0.1] shadow-xl w-full">
      {/* Subtle radial glow based on category */}
      <div
        className={`absolute -top-32 -left-32 w-64 h-64 rounded-full opacity-10 blur-3xl pointer-events-none ${theme.glowBg}`}
      />

      <div className="relative flex flex-col gap-0 px-6 pt-5 pb-5">
        {/* ── Header row ── */}
        <div
          className="flex items-center justify-between cursor-pointer group/header"
          onClick={() => setIsOpen(!isOpen)}
        >
          <div className="flex items-center gap-4">
            {/* Icon badge */}
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${theme.iconBg} ring-1 ring-white/5 transition-transform group-hover/header:scale-105`}
            >
              <span className={theme.iconText}>{theme.icon}</span>
            </div>

            {/* Category pill */}
            <span
              className={`inline-flex items-center gap-1.5 text-[10px] font-bold tracking-widest uppercase px-2.5 py-1 rounded-md ${theme.pillBg} ${theme.pillText}`}
            >
              {insight.category || "Insight"}
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* Verified badge — top-right */}
            {insight.verified && (
              <span className="shrink-0 flex items-center gap-1.5 text-[10px] font-bold tracking-widest uppercase text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full">
                <CheckCircle className="h-3.5 w-3.5" />
                Verified
              </span>
            )}
          </div>
        </div>

        <AnimatePresence initial={false}>
          {isOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="overflow-hidden"
            >
              <div className="pt-5">
                {/* Title */}
                <h3
                  className="text-[20px] font-bold text-white mb-3"
                  title={insight.title}
                >
                  {insight.title}
                </h3>

                {/* ── Description ── */}
                {insight.description && (
                  <div className="mb-6">
                    <p
                      className={`text-[15px] text-[#A1A1AA] leading-relaxed font-medium ${expanded ? "" : "line-clamp-2"}`}
                    >
                      {renderDescription(insight.description, theme.iconText)}
                    </p>
                    {insight.description.length > 200 && (
                      <button
                        onClick={() => setExpanded(!expanded)}
                        className={`text-[12px] font-bold mt-2 ${theme.pillText} hover:underline`}
                      >
                        {expanded ? "Show less ↑" : "Read more ↓"}
                      </button>
                    )}
                  </div>
                )}

                {/* ── Recommendation row ── */}
                {insight.recommendation && (
                  <div className="mb-8 rounded-xl border border-white/5 bg-white/[0.02] p-5 relative overflow-hidden group">
                    {/* Subtle background gradient on the recommendation box */}
                    <div
                      className={`absolute top-0 left-0 w-full h-full opacity-5 bg-gradient-to-r ${theme.bannerFrom} to-transparent pointer-events-none group-hover:opacity-10 transition-opacity`}
                    />

                    <p
                      className={`relative text-[11px] font-bold uppercase tracking-[0.15em] mb-2.5 flex items-center gap-2 ${theme.pillText}`}
                    >
                      <Lightbulb className="h-4 w-4" />
                      Recommendation
                    </p>
                    <p className="relative text-[14px] text-[#D4D4D8] leading-relaxed font-medium">
                      {insight.recommendation}
                    </p>
                  </div>
                )}

                {/* ── Footer ── */}
                <div className="flex items-center justify-between pt-1">
                  <ConfidenceBar pct={confidence} />

                  <div className="flex items-center gap-4">
                    <span className="text-[12px] text-muted-foreground/60 font-medium italic">
                      {formatRelativeTime(insight.created_at)}
                    </span>
                    {insight.audit_sql && (
                      <button
                        onClick={() => setShowSql(!showSql)}
                        className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-widest text-muted-foreground/60 hover:text-white transition-colors"
                      >
                        <Database className="h-3.5 w-3.5" />
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
                      className="overflow-hidden mt-4"
                    >
                      <pre className="rounded-xl border border-white/[0.05] bg-black/80 p-4 text-[11px] font-mono text-muted-foreground/90 whitespace-pre-wrap overflow-x-auto shadow-inner leading-relaxed">
                        {insight.audit_sql}
                      </pre>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Toggle Strip ── */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-center py-1 bg-white/[0.03] hover:bg-white/[0.08] transition-all`}
      >
        <ChevronDown
          strokeWidth={1.25}
          className={`h-4 w-4 text-white/50 transition-transform duration-300 ${isOpen ? "rotate-180" : ""}`}
        />
      </button>
    </div>
  );
}

const pageVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.05 },
  },
};

const headerVariants = {
  hidden: { opacity: 0, y: -20, filter: "blur(10px)" },
  show: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { type: "spring", stiffness: 250, damping: 20 },
  },
};

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30, scale: 0.95, filter: "blur(5px)" },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    filter: "blur(0px)",
    transition: { type: "spring" as const, stiffness: 250, damping: 20 },
  },
};

export default function InsightsPage() {
  const queryClient = useQueryClient();
  const {
    data: insights,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
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
    <motion.div
      variants={pageVariants}
      initial="hidden"
      animate="show"
      className="flex flex-col gap-6"
    >
      <motion.div
        variants={headerVariants}
        className="relative mb-6"
      >

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 className="text-[34px] font-bold tracking-tight text-white mb-2">
              Deep Insights Engine
            </h1>
            <p className="text-[15px] text-muted-foreground/80 max-w-2xl leading-relaxed">
              Agentic AI automatically asks questions, runs queries, and
              surfaces verified business findings.
            </p>
          </div>
          <div className="flex items-center gap-5 shrink-0">
            <span className="text-[13px] font-medium text-white/50 bg-white/5 px-3.5 py-1.5 rounded-full border border-white/5">
              {insights?.length ?? 0} insights generated
            </span>
            <Button
              onClick={() => deepAnalyze.mutate()}
              disabled={deepAnalyze.isPending}
              className="bg-blue-600 hover:bg-blue-500 text-white border-0 shadow-[0_0_20px_rgba(37,99,235,0.25)] hover:shadow-[0_0_30px_rgba(37,99,235,0.4)] gap-2.5 h-10 px-5 rounded-xl transition-all"
            >
              <RefreshCw
                className={`h-4 w-4 ${deepAnalyze.isPending ? "animate-spin" : ""}`}
              />
              {deepAnalyze.isPending
                ? "Analyzing Data..."
                : "Regenerate Insights"}
            </Button>
          </div>
        </div>
      </motion.div>

      {isLoading || deepAnalyze.isPending ? (
        <div className="grid grid-cols-1 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} lines={5} />
          ))}
        </div>
      ) : isError ? (
        <ErrorState
          onRetry={refetch}
          errorType={detectErrorType(error)}
          developerDetails={
            error instanceof Error ? error.message : String(error)
          }
        />
      ) : !insights || insights.length === 0 ? (
        <EmptyState
          icon={<Lightbulb className="h-7 w-7 text-muted-foreground/50" />}
          title="No insights yet"
          description="Click Regenerate Insights to run the agentic pipeline on your active dataset."
          action={
            <Button
              onClick={() => deepAnalyze.mutate()}
              className="bg-primary hover:bg-primary/90 text-primary-foreground gap-2"
            >
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
          className="flex flex-col gap-6"
        >
          {insights.map((insight) => (
            <motion.div key={insight.id} variants={itemVariants}>
              <InsightCard insight={insight} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
}

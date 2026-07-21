"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { recommendationsApi } from "@/lib/api";
import type { Recommendation } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  RefreshCw,
} from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState, detectErrorType } from "@/components/ui/error-state";
import { Button } from "@/components/ui/button";

const priorityConfig: Record<
  string,
  {
    glowBg: string;
    iconBg: string;
    iconText: string;
    icon: React.ReactNode;
    pillBg: string;
    pillText: string;
  }
> = {
  Critical: {
    glowBg: "bg-red-500",
    iconBg: "bg-red-500/10",
    iconText: "text-red-400",
    icon: <AlertTriangle className="h-5 w-5" />,
    pillBg: "bg-red-500/10",
    pillText: "text-red-400",
  },
  High: {
    glowBg: "bg-orange-500",
    iconBg: "bg-orange-500/10",
    iconText: "text-orange-400",
    icon: <TrendingUp className="h-5 w-5" />,
    pillBg: "bg-orange-500/10",
    pillText: "text-orange-400",
  },
  Medium: {
    glowBg: "bg-blue-500",
    iconBg: "bg-blue-500/10",
    iconText: "text-blue-400",
    icon: <Zap className="h-5 w-5" />,
    pillBg: "bg-blue-500/10",
    pillText: "text-blue-400",
  },
  Low: {
    glowBg: "bg-emerald-500",
    iconBg: "bg-emerald-500/10",
    iconText: "text-emerald-400",
    icon: <CheckCircle className="h-5 w-5" />,
    pillBg: "bg-emerald-500/10",
    pillText: "text-emerald-400",
  },
};

function RecommendationCard({ rec }: { rec: Recommendation }) {
  const [isOpen, setIsOpen] = useState(false);
  const theme = priorityConfig[rec.priority] ?? priorityConfig.Medium;

  return (
    <div className="relative flex flex-col overflow-hidden rounded-[20px] border border-white/[0.05] bg-[#0c0c0e] transition-all duration-300 hover:-translate-y-1 hover:border-white/[0.1] shadow-xl w-full">
      {/* Subtle radial glow based on priority */}
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

            {/* Priority pill */}
            <span
              className={`inline-flex items-center gap-1.5 text-[10px] font-bold tracking-widest uppercase px-2.5 py-1 rounded-md ${theme.pillBg} ${theme.pillText}`}
            >
              {rec.priority || "Medium"} Priority
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* Verified badge — top-right */}
            {rec.verified && (
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
                  title={rec.title}
                >
                  {rec.title}
                </h3>

                {/* ── Rationale / Description ── */}
                {rec.rationale && (
                  <div className="mb-6">
                    <p
                      className={`text-[15px] text-[#A1A1AA] leading-relaxed font-medium`}
                    >
                      {rec.rationale}
                    </p>
                  </div>
                )}

                {/* Footer details */}
                <div className="flex items-center pt-3 border-t border-white/5 gap-3">
                  <span className="inline-flex items-center text-[11px] font-medium text-muted-foreground/70 tracking-wide uppercase">
                    Category:{" "}
                    <span className="text-white/90 ml-1.5 font-semibold">
                      {rec.category}
                    </span>
                  </span>
                </div>
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
    transition: { staggerChildren: 0.1 },
  },
};
const headerVariants = {
  hidden: { opacity: 0, y: -20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

export default function RecommendationsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => recommendationsApi.generate(false),
  });

  const deepAnalyze = useMutation({
    mutationFn: () => recommendationsApi.generate(true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });

  const isApiError =
    data &&
    typeof data === "object" &&
    !Array.isArray(data) &&
    data.success === false;
  const recommendations = Array.isArray(data) ? data : [];

  const sorted = [...recommendations].sort((a, b) => {
    const order: Record<string, number> = {
      Critical: 0,
      High: 1,
      Medium: 2,
      Low: 3,
    };
    return (order[a.priority] ?? 3) - (order[b.priority] ?? 3);
  });

  return (
    <motion.div
      variants={pageVariants}
      initial="hidden"
      animate="show"
      className="flex flex-col gap-6"
    >
      <motion.div variants={headerVariants} className="relative mb-6">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 className="text-[34px] font-bold tracking-tight text-white mb-2">
              Recommendations
            </h1>
            <p className="text-[15px] text-muted-foreground/80 max-w-2xl leading-relaxed">
              Prioritized, deterministic evidence-backed actions generated from
              your business data.
            </p>
          </div>
          <div className="flex items-center gap-5 shrink-0">
            <span className="text-[13px] font-medium text-white/50 bg-white/5 px-3.5 py-1.5 rounded-full border border-white/5">
              {sorted?.length ?? 0} recommendations generated
            </span>
            <Button
              onClick={() => deepAnalyze.mutate()}
              disabled={deepAnalyze.isPending}
              className="bg-blue-600 hover:bg-blue-500 text-white border-0 shadow-[0_0_20px_rgba(37,99,235,0.25)] hover:shadow-[0_0_30px_rgba(37,99,235,0.4)] gap-2.5 h-10 px-5 rounded-xl transition-all"
            >
              <RefreshCw
                className={`h-4 w-4 ${deepAnalyze.isPending ? "animate-spin" : ""}`}
              />
              {deepAnalyze.isPending ? "Generating..." : "Regenerate"}
            </Button>
          </div>
        </div>
      </motion.div>

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <CardSkeleton key={i} lines={3} />
          ))}
        </div>
      ) : isError || isApiError ? (
        <ErrorState
          onRetry={refetch}
          errorType={detectErrorType(error)}
          developerDetails={
            isApiError
              ? (data as any).message
              : error instanceof Error
                ? error.message
                : String(error)
          }
        />
      ) : sorted.length === 0 ? (
        <EmptyState
          icon={<Zap className="h-7 w-7 text-muted-foreground/50" />}
          title="No recommendations yet"
          description="Upload a dataset to generate recommendations based on deterministic data evaluation."
        />
      ) : (
        <motion.div
          variants={pageVariants}
          initial="hidden"
          animate="show"
          className="space-y-4"
        >
          {sorted.map((rec) => (
            <motion.div key={rec.id} variants={itemVariants}>
              <RecommendationCard rec={rec} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
}

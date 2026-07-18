"use client";

import React, { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { ErrorState, detectErrorType } from "@/components/ui/error-state";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { StudioPage } from "@/components/analytics/StudioPage";
import { motion, useMotionValue, useTransform, animate, AnimatePresence } from "framer-motion";
import { AlertTriangle, ChevronDown } from "lucide-react";

// ── Animated Number ────────────────────────────────────────────────────────────
function AnimatedNumber({ value, isPercent = false }: { value: number; isPercent?: boolean }) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) =>
    isPercent ? `${Math.round(latest)}%` : Math.round(latest).toString()
  );
  useEffect(() => {
    const controls = animate(count, value, { duration: 1.1, ease: "easeOut" });
    return controls.stop;
  }, [count, value]);
  return <motion.span>{rounded}</motion.span>;
}

// ── Expandable Audit Row ───────────────────────────────────────────────────────
function ExpandableAuditRow({ row, index }: { row: any; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const confPercent = Math.round(row.confidence * 100);

  return (
    <>
      <div
        className="relative grid grid-cols-[2.4fr_1.1fr_1fr_0.9fr] items-center px-6 py-4 border-b border-border/30 transition-colors hover:bg-white/[0.03] group"
        style={{ animation: `ccRowIn 0.5s ease ${0.3 + index * 0.1}s both` }}
      >
        {/* Hover left accent line */}
        <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-primary scale-y-0 origin-center transition-transform duration-200 group-hover:scale-y-100 rounded-r" />

        <div className="flex flex-col gap-1 pl-1">
          <span className="text-sm font-medium text-foreground line-clamp-1 group-hover:line-clamp-none transition-all leading-snug">
            {row.title}
          </span>
          <span className="text-[11px] text-muted-foreground font-mono">
            {row.id || `rec_${index.toString().padStart(4, "0")}`}
          </span>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="flex-1 max-w-[70px] h-[4px] rounded-full bg-border overflow-hidden">
            <div
              className="h-full bg-emerald-500"
              style={{
                width: `${confPercent}%`,
                animation: `ccBarFill 1.2s cubic-bezier(0.3, 0, 0.2, 1) ${0.1 * index}s both`,
              }}
            />
          </div>
          <span className="text-xs text-muted-foreground font-mono tabular-nums">{confPercent}%</span>
        </div>

        <div>
          {row.verified ? (
            <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="m20 6-11 11-5-5" />
              </svg>
              Verified
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2.5 py-1 rounded-full">
              <AlertTriangle className="h-2.5 w-2.5" strokeWidth={3} />
              Unverified
            </span>
          )}
        </div>

        <div className="text-right">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs font-mono inline-flex items-center gap-1 text-primary hover:text-primary/80 transition-colors"
          >
            view
            <motion.div animate={{ rotate: expanded ? 180 : 0 }}>
              <ChevronDown className="h-3 w-3" />
            </motion.div>
          </button>
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden bg-surface/40"
          >
            <div className="px-6 py-4 border-b border-border/30">
              <div className="p-3.5 bg-background/60 border border-border/40 rounded-xl text-xs text-muted-foreground font-mono">
                <strong className="text-foreground/70 block mb-2 font-sans text-[10px] uppercase tracking-wider font-semibold">
                  SQL Audit Query
                </strong>
                <pre className="whitespace-pre-wrap break-words leading-relaxed">
                  {row.audit_sql || row.description || "No SQL available."}
                </pre>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({
  title,
  verified,
  unverified,
  iconSvg,
  accentColor,
  delay = "0s",
}: {
  title: string;
  verified: number;
  unverified: number;
  iconSvg: React.ReactNode;
  accentColor: string;
  delay?: string;
}) {
  const total = verified + unverified;
  const pct = total === 0 ? 0 : Math.round((verified / total) * 100);
  const circ = 276.5; // 2 * π * 44
  const strokeDashoffset = circ - (pct / 100) * circ;

  return (
    <motion.div
      initial={{ opacity: 0, y: 14, filter: "blur(6px)" }}
      animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      transition={{ duration: 0.5, delay: parseFloat(delay), ease: "easeOut" }}
      className="glass-card rounded-[20px] p-6 overflow-hidden relative"
    >
      {/* Top shimmer line */}
      <div
        className="absolute top-0 left-0 right-0 h-[1px]"
        style={{
          background: `linear-gradient(90deg, transparent, ${accentColor}88, transparent)`,
          animation: `ccLineGlow 3s ease-in-out infinite ${delay}`,
        }}
      />
      {/* Shimmer sweep */}
      <div
        className="absolute top-0 left-0 h-full w-[40%] pointer-events-none"
        style={{
          background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.04), transparent)",
          animation: `ccSweep 4s ease-in-out infinite ${delay}`,
        }}
      />

      {/* Header */}
      <div className="flex items-center justify-between mb-6 relative z-10">
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-[10px] flex items-center justify-center border"
            style={{
              background: `${accentColor}18`,
              borderColor: `${accentColor}30`,
              color: accentColor,
            }}
          >
            {iconSvg}
          </div>
          <h3 className="text-base font-semibold text-foreground">{title}</h3>
        </div>
        <span
          className="text-[11px] font-semibold px-3 py-1.5 rounded-full border font-mono"
          style={{
            color: accentColor,
            background: `${accentColor}18`,
            borderColor: `${accentColor}35`,
          }}
        >
          {pct}% verified
        </span>
      </div>

      {/* Body: circle + counters */}
      <div className="flex items-center gap-6 relative z-10">
        {/* Circular progress */}
        <div className="relative w-[100px] h-[100px] shrink-0">
          <svg width="100" height="100" viewBox="0 0 104 104" className="-rotate-90">
            <circle cx="52" cy="52" r="44" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="9" />
            <motion.circle
              cx="52"
              cy="52"
              r="44"
              fill="none"
              stroke={accentColor}
              strokeWidth="9"
              strokeLinecap="round"
              strokeDasharray={circ}
              initial={{ strokeDashoffset: circ }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1.1, ease: [0.4, 0, 0.2, 1], delay: parseFloat(delay) + 0.2 }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-xl font-bold text-foreground font-mono leading-none">
              <AnimatedNumber value={pct} isPercent />
            </div>
            <div className="text-[9px] tracking-widest text-muted-foreground mt-1 uppercase">
              Total {total}
            </div>
          </div>
        </div>

        {/* Verified / Unverified pills */}
        <div className="flex-1 flex flex-col gap-3">
          <div
            className="flex items-center justify-between px-4 py-3 border rounded-xl"
            style={{ background: `${accentColor}0A`, borderColor: `${accentColor}25` }}
          >
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full" style={{ background: accentColor }} />
              <span className="text-[11px] tracking-widest text-muted-foreground font-medium uppercase">
                Verified
              </span>
            </div>
            <div className="text-xl font-bold font-mono leading-none" style={{ color: accentColor }}>
              <AnimatedNumber value={verified} />
            </div>
          </div>

          <div className="flex items-center justify-between px-4 py-3 border border-rose-500/20 bg-rose-500/[0.06] rounded-xl">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-rose-400" />
              <span className="text-[11px] tracking-widest text-muted-foreground font-medium uppercase">
                Unverified
              </span>
            </div>
            <div className="text-xl font-bold text-rose-400 font-mono leading-none">
              <AnimatedNumber value={unverified} />
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function ConfidenceCenter() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["confidence"],
    queryFn: () => analyticsApi.confidence(),
  });

  if (isError) {
    return (
      <StudioPage title="Confidence Center">
        <ErrorState onRetry={refetch} errorType={detectErrorType(error)} />
      </StudioPage>
    );
  }

  return (
    <StudioPage title="Confidence Center" isLoading={isLoading}>
      {!data ? null : (
        <div className="flex flex-col gap-6">
          {/* Stat Cards */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
            <StatCard
              title="Insights"
              verified={data.insights.verified}
              unverified={data.insights.unverified}
              accentColor="#7aa2f7"
              delay="0s"
              iconSvg={
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.1v.2h6v-.2c0-.8.4-1.6 1-2.1A7 7 0 0 0 12 2Z" />
                </svg>
              }
            />
            <StatCard
              title="Recommendations"
              verified={data.recommendations.verified}
              unverified={data.recommendations.unverified}
              accentColor="#34d399"
              delay="0.08s"
              iconSvg={
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z" />
                </svg>
              }
            />
          </div>

          {/* Audit Trail */}
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.18, ease: "easeOut" }}
            className="glass-card rounded-[20px] overflow-hidden flex flex-col"
          >
            {/* Audit header */}
            <div className="px-6 py-5 flex items-start justify-between gap-4 border-b border-border/40">
              <div className="flex gap-3 items-start">
                <div className="w-9 h-9 rounded-[10px] flex items-center justify-center bg-muted border border-border text-muted-foreground shrink-0 mt-0.5">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <ellipse cx="12" cy="5" rx="8" ry="3" />
                    <path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
                  </svg>
                </div>
                <div>
                  <div className="text-sm font-semibold text-foreground">Insights Audit Trail</div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    Recent insights and their underlying SQL queries used for deterministic verification.
                  </div>
                </div>
              </div>
              <span className="text-[11px] text-muted-foreground font-mono px-3 py-1.5 border border-border rounded-lg bg-surface/50 whitespace-nowrap">
                {data.audit_trail.length} records
              </span>
            </div>

            {/* Column headers */}
            <div className="grid grid-cols-[2.4fr_1.1fr_1fr_0.9fr] px-6 py-3 bg-surface/50 text-[10.5px] tracking-[0.12em] text-muted-foreground font-semibold uppercase border-b border-border/30">
              <div>Insight Title</div>
              <div>Confidence</div>
              <div>Status</div>
              <div className="text-right">SQL Audit</div>
            </div>

            {/* Rows */}
            <div className="flex-1 overflow-y-auto [&::-webkit-scrollbar]:hidden">
              {data.audit_trail.length === 0 ? (
                <div className="px-6 py-12 text-center text-muted-foreground text-sm">
                  No insights generated yet.
                </div>
              ) : (
                data.audit_trail.map((row: any, i: number) => (
                  <ExpandableAuditRow key={row.id || i} row={row} index={i} />
                ))
              )}
            </div>
          </motion.div>
        </div>
      )}
    </StudioPage>
  );
}

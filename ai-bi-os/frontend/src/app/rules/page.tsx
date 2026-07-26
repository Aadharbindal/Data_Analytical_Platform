"use client";

import React, { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AreaChart, Area, ResponsiveContainer, ReferenceLine } from "recharts";
import { rulesApi, datasetsApi, analyticsApi } from "@/lib/api";
import type { BusinessRule, RuleEvent } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import {
  GitBranch, Plus, CheckCircle, AlertCircle, X, Loader2, Trash2, History, RefreshCw, Clock,
  TrendingUp, MoreVertical, Sparkles, Sparkle, ArrowRight, Save, Pencil, BarChart3, Hash, Check,
  ArrowUpRight, ArrowDownRight, ChevronDown, Search, Filter, CalendarDays,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

// Backend timestamps are naive UTC strings (datetime.utcnow().isoformat()),
// with no trailing "Z" or offset. `new Date()` treats a date-time string
// with no timezone as *local* time, not UTC — without this normalization,
// every relative time is off by however far the browser's timezone is from
// UTC (e.g. "5h ago" for something that just happened, in UTC+5:30).
function parseUtc(iso: string): Date {
  return new Date(/[Zz]|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : `${iso}Z`);
}

function relativeTime(iso: string): string {
  const diffMs = Date.now() - parseUtc(iso).getTime();
  const min = Math.floor(diffMs / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  if (day < 7) return `${day}d ago`;
  return parseUtc(iso).toLocaleDateString();
}

// Rules are stored with the raw keyword the form saved ("pct_change_gt",
// "gt", ...) since that's what the backend's condition-alias map expects —
// but showing that literal keyword on a card reads as a bug. Display the
// comparison symbol instead, same mapping the backend uses to evaluate it.
const CONDITION_SYMBOLS: Record<string, string> = {
  gt: ">", lt: "<", pct_change_gt: ">", pct_change_lt: "<", eq: "==",
};
function conditionSymbol(condition: string): string {
  return CONDITION_SYMBOLS[condition.toLowerCase()] ?? condition;
}

function RuleHistoryPanel({ rule, onClose }: { rule: BusinessRule; onClose: () => void }) {
  const { data: events, isLoading } = useQuery({
    queryKey: ["rule-history", rule.id],
    queryFn: () => rulesApi.history(rule.id),
  });

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ x: 32, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 32, opacity: 0 }}
        transition={{ type: "spring", stiffness: 320, damping: 32 }}
        className="flex h-full w-full max-w-md flex-col rounded-[24px] border border-border/60 bg-background shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border/40 px-5 py-4">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-foreground">{rule.name}</p>
            <p className="text-[11px] text-muted-foreground">Trigger history</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-16 animate-pulse rounded-xl bg-white/[0.03]" />
              ))}
            </div>
          ) : !events || events.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center gap-3 py-20 text-center"
            >
              <div className="relative flex h-14 w-14 items-center justify-center">
                <motion.div
                  animate={{ scale: [1, 1.25, 1], opacity: [0.5, 0.15, 0.5] }}
                  transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute inset-0 rounded-2xl bg-primary/40 blur-md"
                />
                <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-blue-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_16px_-3px_var(--primary)]">
                  <History className="h-6 w-6 text-white" />
                </div>
                {[
                  { top: "-6px", left: "8px", size: 10, delay: 0 },
                  { top: "8px", right: "-10px", size: 8, delay: 0.5 },
                  { bottom: "6px", left: "-8px", size: 7, delay: 1 },
                ].map((s, i) => (
                  <motion.div
                    key={i}
                    animate={{ opacity: [0.2, 1, 0.2], scale: [0.8, 1.15, 0.8] }}
                    transition={{ duration: 2.2, repeat: Infinity, delay: s.delay, ease: "easeInOut" }}
                    className="absolute text-primary/70"
                    style={{ top: s.top, left: s.left, right: s.right, bottom: s.bottom }}
                  >
                    <Sparkle className="fill-current" style={{ width: s.size, height: s.size }} />
                  </motion.div>
                ))}
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">This is your trigger history</p>
                <p className="mt-1 max-w-[220px] text-xs text-muted-foreground">
                  We&apos;ll show all the times this rule gets triggered.
                </p>
              </div>
            </motion.div>
          ) : (
            <div className="relative space-y-4 pl-5">
              <div className="absolute left-[7px] top-1 bottom-1 w-px bg-border/50" />
              {events.map((event: RuleEvent, idx: number) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.04 }}
                  className="relative"
                >
                  <span className="absolute -left-5 top-1 h-3.5 w-3.5 rounded-full border-2 border-background bg-error shadow-[0_0_8px_rgba(239,68,68,0.6)]" />
                  <div className="rounded-xl border border-border/40 bg-white/[0.02] px-3.5 py-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="inline-flex items-center gap-1 rounded-full border border-error/20 bg-error/10 px-2 py-0.5 text-[10px] font-medium text-error">
                        <AlertCircle className="h-2.5 w-2.5" /> TRIGGERED
                      </span>
                      <span className="text-[10px] text-muted-foreground/60">{relativeTime(event.created_at)}</span>
                    </div>
                    <p className="mt-2 text-[12px] leading-relaxed text-foreground/80">{event.message}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

function RuleCard({ rule, onViewHistory }: { rule: BusinessRule; onViewHistory: () => void }) {
  const qc = useQueryClient();
  const deleteMut = useMutation({
    mutationFn: () => rulesApi.delete(rule.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });
  const updateMut = useMutation({
    mutationFn: (data: Partial<BusinessRule>) => rulesApi.update(rule.id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });

  const isMoM = rule.window === "MoM";
  // Only fetched for MoM rules — a sparkline behind a "latest" rule (a running
  // total, not a period series) would visually imply a trend that isn't real.
  const { data: series } = useQuery({
    queryKey: ["rule-series", rule.id],
    queryFn: () => rulesApi.series(rule.id),
    enabled: isMoM,
  });

  const isTriggered = rule.status === "TRIGGERED";
  const isOk = rule.status === "OK";
  const isErrorStatus = rule.status?.startsWith("ERROR") || false;
  const isPending = rule.status?.startsWith("PENDING") || false;
  const isInactive = !rule.is_active || rule.status === "INACTIVE";

  const hasValue = rule.current_value !== null && rule.current_value !== undefined;
  const isPositiveTrend = hasValue && rule.current_value! >= 0;
  const trendColor = isPositiveTrend ? "#22c55e" : "#ef4444";

  return (
    <motion.div
      whileHover={{ y: -3 }}
      transition={{ type: "spring", stiffness: 300, damping: 24 }}
      className={`relative glass-card rounded-[20px] p-6 flex flex-col gap-5 border-l-2 transition-colors ${
      isInactive ? 'opacity-50 border-l-muted' :
      isTriggered ? 'border-l-error' :
      isOk ? 'border-l-success' :
      isErrorStatus ? 'border-l-amber-500' :
      isPending ? 'border-l-primary' : 'border-l-muted'
    }`}>
      {isTriggered && (
        <motion.div
          animate={{ opacity: [0.5, 0.15, 0.5] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
          className="pointer-events-none absolute inset-0 rounded-[20px] bg-error/[0.04]"
        />
      )}

      <div className="flex flex-wrap items-center justify-between gap-y-3 gap-x-4">
        <div className="flex min-w-0 flex-1 items-center gap-3.5">
          <div className="relative flex h-11 w-11 shrink-0 items-center justify-center">
            <motion.div
              animate={{ scale: [1, 1.25, 1], opacity: [0.5, 0.15, 0.5] }}
              transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
              className="absolute inset-0 rounded-full bg-primary/40 blur-md"
            />
            <div className="relative flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-br from-primary to-blue-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_14px_-3px_var(--primary)]">
              <TrendingUp className="h-4.5 w-4.5 text-white" />
            </div>
          </div>
          <h3 className="min-w-0 flex-1 truncate text-base font-semibold text-foreground" title={rule.name}>{rule.name}</h3>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button
            onClick={() => updateMut.mutate({ is_active: !rule.is_active })}
            className={`w-9 h-5 rounded-full transition-colors relative focus:outline-none ${rule.is_active ? 'bg-primary' : 'bg-muted-foreground/30'}`}
          >
            <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${rule.is_active ? 'translate-x-4' : 'translate-x-0'}`} />
          </button>
          <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border whitespace-nowrap ${
            isInactive ? "bg-muted/10 text-muted-foreground border-border/40" :
            isTriggered ? "bg-error/10 text-error border-error/20" :
            isOk ? "bg-success/10 text-success border-success/20" :
            isErrorStatus ? "bg-amber-500/10 text-amber-500 border-amber-500/20" :
            isPending ? "bg-primary/10 text-primary border-primary/20" :
            "bg-muted/10 text-muted-foreground border-border/40"
          }`}>
            {isInactive ? <span className="h-2 w-2 rounded-full bg-muted-foreground/50" /> :
             isTriggered ? <AlertCircle className="h-2.5 w-2.5" /> :
             isOk ? <CheckCircle className="h-2.5 w-2.5" /> :
             isPending ? <Clock className="h-2.5 w-2.5" /> :
             <AlertCircle className="h-2.5 w-2.5" />}
            {rule.status}
          </span>
          <DropdownMenu>
            <DropdownMenuTrigger className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground outline-none transition-colors hover:bg-white/5 hover:text-foreground">
              <MoreVertical className="h-3.5 w-3.5" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              <DropdownMenuItem onClick={onViewHistory} className="cursor-pointer gap-2">
                <History className="h-3.5 w-3.5" /> View history
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => deleteMut.mutate()} variant="destructive" className="cursor-pointer gap-2">
                <Trash2 className="h-3.5 w-3.5" /> Delete rule
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <div className="border-t border-border/40" />

      <div className="grid grid-cols-3 gap-3">
        <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="flex min-w-0 items-center gap-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-blue-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_10px_-3px_var(--primary)]">
            <BarChart3 className="h-3.5 w-3.5 text-white" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground/60 mb-0.5">Metric</p>
            <p className="truncate text-sm font-medium text-foreground">{rule.metric_column}</p>
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="flex min-w-0 items-center gap-2.5 border-x border-border/30 px-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-blue-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_10px_-3px_var(--primary)]">
            <Filter className="h-3.5 w-3.5 text-white" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground/60 mb-0.5">Condition</p>
            <p className="truncate font-mono text-sm font-medium text-foreground">{conditionSymbol(rule.condition)} {rule.threshold}</p>
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="flex min-w-0 items-center gap-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-blue-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_10px_-3px_var(--primary)]">
            <CalendarDays className="h-3.5 w-3.5 text-white" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground/60 mb-0.5">Window</p>
            <p className="truncate text-sm font-medium text-foreground">{isMoM ? "MoM" : "Latest"}</p>
          </div>
        </motion.div>
      </div>

      {hasValue && (
        <div className={cn(
          "flex items-center justify-between gap-5 rounded-2xl border px-4 py-4 transition-colors",
          isMoM
            ? isPositiveTrend
              ? "border-success/20 bg-gradient-to-br from-success/[0.07] via-transparent to-transparent"
              : "border-error/20 bg-gradient-to-br from-error/[0.07] via-transparent to-transparent"
            : "border-border/40 bg-white/[0.02]"
        )}>
          <div className="min-w-0">
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground/60 mb-1">Current Value</p>
            <motion.span
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
              className="inline-block text-2xl font-semibold text-foreground tabular-nums leading-none"
            >
              {isMoM ? `${rule.current_value!.toFixed(2)}%` : rule.current_value!.toLocaleString()}
            </motion.span>
            {isMoM && (
              <div className="mt-2 flex items-center gap-2">
                <span className={`inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[11px] font-medium ${isPositiveTrend ? 'bg-success/10 text-success' : 'bg-error/10 text-error'}`}>
                  {isPositiveTrend ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                  {rule.current_value! >= 0 ? "+" : ""}{rule.current_value!.toFixed(2)}%
                </span>
                <span className="text-[11px] text-muted-foreground/50">vs last period</span>
              </div>
            )}
          </div>
          {isMoM && series && series.length > 1 && (
            <div className="h-20 w-full max-w-[200px] shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={series} margin={{ top: 10, right: 6, bottom: 10, left: 6 }}>
                  <defs>
                    <linearGradient id={`spark-${rule.id}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={trendColor} stopOpacity={0.45} />
                      <stop offset="60%" stopColor={trendColor} stopOpacity={0.1} />
                      <stop offset="100%" stopColor={trendColor} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <ReferenceLine y={series[0].value ?? undefined} stroke="currentColor" className="text-border" strokeDasharray="3 3" />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke={trendColor}
                    strokeWidth={2.25}
                    strokeLinecap="round"
                    fill={`url(#spark-${rule.id})`}
                    animationDuration={900}
                    animationEasing="ease-out"
                    style={{ filter: `drop-shadow(0 0 5px ${trendColor}99)` }}
                    dot={(props: { cx?: number; cy?: number; index?: number; key?: string }) => {
                      const { key, ...rest } = props;
                      if (rest.index === series.length - 1) {
                        return (
                          <g key={key}>
                            <motion.circle
                              cx={rest.cx}
                              cy={rest.cy}
                              fill={trendColor}
                              animate={{ r: [4, 10, 4], opacity: [0.5, 0, 0.5] }}
                              transition={{ duration: 1.8, repeat: Infinity, ease: "easeOut" }}
                            />
                            <circle cx={rest.cx} cy={rest.cy} r={3.5} fill={trendColor} stroke="var(--background)" strokeWidth={1.5} />
                          </g>
                        );
                      }
                      if (rest.index === 0) {
                        return <circle key={key} cx={rest.cx} cy={rest.cy} r={3} fill={trendColor} stroke="var(--background)" strokeWidth={1.5} />;
                      }
                      return <React.Fragment key={key} />;
                    }}
                    activeDot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      <div className="flex items-center justify-between gap-3 mt-auto">
        <div className="flex min-w-0 items-center gap-2 text-xs text-muted-foreground/60">
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-blue-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_8px_-3px_var(--primary)]">
            <CalendarDays className="h-3 w-3 text-white" />
          </div>
          <span className="truncate">
            Created on {parseUtc(rule.created_at).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })}
            {" • "}
            {parseUtc(rule.created_at).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}
          </span>
        </div>
        {rule.last_triggered_at && (
          <span className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground/60">
            <Clock className="h-3 w-3" /> {relativeTime(rule.last_triggered_at)}
          </span>
        )}
      </div>
    </motion.div>
  );
}

function MetricColumnPicker({
  value, onChange, columns,
}: { value: string; onChange: (col: string) => void; columns: string[] }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const filtered = columns.filter((c) => c.toLowerCase().includes(search.toLowerCase()));

  return (
    <div ref={ref} className="relative">
      <motion.button
        type="button"
        whileTap={{ scale: 0.98 }}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "relative flex w-full items-center gap-2 rounded-lg border bg-surface p-2.5 pl-9 pr-8 text-left text-sm text-foreground transition-colors focus:outline-none",
          open ? "border-primary/60 ring-2 ring-primary/20" : "border-border/80"
        )}
      >
        <BarChart3 className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <span className={cn("truncate", !value && "text-muted-foreground/70")}>
          {value || "Select a column..."}
        </span>
        <ChevronDown className={cn("absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground transition-transform", open && "rotate-180")} />
      </motion.button>

      {open && (
        <motion.div
          initial={{ opacity: 0, y: -6, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.16, ease: "easeOut" }}
          className="absolute z-20 mt-1.5 w-full overflow-hidden rounded-xl border border-border/60 bg-popover shadow-xl"
        >
          <div className="relative border-b border-border/40 p-2">
            <Search className="pointer-events-none absolute left-[18px] top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              autoFocus
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search columns..."
              className="w-full rounded-lg border border-border/60 bg-surface/60 py-1.5 pl-8 pr-2 text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-none"
            />
          </div>
          {columns.length > 0 && (
            <p className="px-3 pb-1 pt-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/50">
              Numeric Columns
            </p>
          )}
          <div className="max-h-48 overflow-y-auto pb-1">
            {filtered.length === 0 ? (
              <p className="px-3 py-3 text-xs text-muted-foreground">No matching columns.</p>
            ) : (
              filtered.map((col, idx) => (
                <motion.button
                  key={col}
                  type="button"
                  initial={{ opacity: 0, x: -4 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.02 }}
                  whileHover={{ x: 2 }}
                  onClick={() => { onChange(col); setOpen(false); setSearch(""); }}
                  className={cn(
                    "flex w-full items-center gap-2 px-3 py-2 text-left text-xs transition-colors hover:bg-white/5",
                    value === col ? "text-primary" : "text-foreground"
                  )}
                >
                  <span className="flex h-4 w-6 shrink-0 items-center justify-center rounded bg-primary/10 text-[9px] font-bold text-primary">123</span>
                  <span className="truncate">{col}</span>
                </motion.button>
              ))
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
}

function StyledSelect({
  value, onChange, options, icon: Icon, placeholder = "Select...",
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  icon?: React.ComponentType<{ className?: string }>;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const selected = options.find((o) => o.value === value);

  return (
    <div ref={ref} className="relative">
      <motion.button
        type="button"
        whileTap={{ scale: 0.98 }}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "relative flex w-full items-center gap-2 rounded-lg border bg-surface p-2.5 pr-8 text-left text-sm text-foreground transition-colors focus:outline-none",
          Icon && "pl-9",
          open ? "border-primary/60 ring-2 ring-primary/20" : "border-border/80"
        )}
      >
        {Icon && <Icon className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />}
        <span className={cn("truncate", !selected && "text-muted-foreground/70")}>
          {selected ? selected.label : placeholder}
        </span>
        <ChevronDown className={cn("absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground transition-transform", open && "rotate-180")} />
      </motion.button>

      {open && (
        <motion.div
          initial={{ opacity: 0, y: -6, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.16, ease: "easeOut" }}
          className="absolute z-20 mt-1.5 w-full overflow-hidden rounded-xl border border-border/60 bg-popover shadow-xl"
        >
          {options.map((opt, idx) => (
            <motion.button
              key={opt.value}
              type="button"
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.02 }}
              whileHover={{ x: 2 }}
              onClick={() => { onChange(opt.value); setOpen(false); }}
              className={cn(
                "flex w-full items-center px-3 py-2.5 text-left text-xs transition-colors hover:bg-white/5",
                value === opt.value ? "bg-primary/5 text-primary" : "text-foreground"
              )}
            >
              {opt.label}
            </motion.button>
          ))}
        </motion.div>
      )}
    </div>
  );
}

function NewRuleModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [tab, setTab] = useState<"nl" | "manual">("nl");
  
  const [nlText, setNlText] = useState("");
  const [parsedRule, setParsedRule] = useState<any>(null);

  const [manualForm, setManualForm] = useState({
    name: "",
    metric_column: "",
    condition: ">",
    threshold: 0,
    window: "latest"
  });

  const { data: edaData } = useQuery({
    queryKey: ["eda"],
    queryFn: () => analyticsApi.eda(),
    enabled: tab === "manual",
  });

  // GET /analytics/eda returns { summary: [{ column, mean?, min?, max?, ... }] },
  // not a `schema` map — numeric columns are the ones with a computed mean.
  const numericColumns: string[] = Array.isArray(edaData?.summary)
    ? edaData.summary.filter((c: { mean?: number }) => c.mean != null).map((c: { column: string }) => c.column)
    : [];

  const parseMut = useMutation({
    mutationFn: () => rulesApi.parseText(nlText),
    onSuccess: (res) => {
      if (res.success) setParsedRule(res.parsed);
      else alert("Could not parse rule: " + res.error);
    }
  });

  const createMut = useMutation({
    mutationFn: (ruleData: any) => rulesApi.create(ruleData),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["rules"] }); onClose(); },
  });

  const handleManualSubmit = () => {
    if (!manualForm.name || !manualForm.metric_column) {
      alert("Please fill out name and select a metric column.");
      return;
    }
    createMut.mutate(manualForm);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6 overflow-y-auto"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.96, y: 8 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.96, y: 8 }}
        className="bg-background border border-border/60 rounded-[24px] p-6 w-full max-w-lg shadow-2xl my-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-foreground">New Deterministic Rule</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
        </div>

        <div className="flex items-center rounded-full border border-border/60 bg-muted/20 p-1 mb-6">
          <motion.button
            whileTap={{ scale: 0.97 }}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-full py-2 text-sm font-medium transition-all",
              tab === "nl" ? "bg-gradient-to-r from-primary to-blue-600 text-white shadow-md" : "text-muted-foreground hover:text-foreground"
            )}
            onClick={() => setTab("nl")}
          >
            <span className={cn(
              "flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold",
              tab === "nl" ? "bg-white/20" : "bg-border/60 text-muted-foreground"
            )}>
              {tab === "manual" ? <Check className="h-3 w-3" /> : "1"}
            </span>
            Describe in English
          </motion.button>
          <motion.button
            whileTap={{ scale: 0.97 }}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-full py-2 text-sm font-medium transition-all",
              tab === "manual" ? "bg-gradient-to-r from-primary to-blue-600 text-white shadow-md" : "text-muted-foreground hover:text-foreground"
            )}
            onClick={() => setTab("manual")}
          >
            <span className={cn(
              "flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold",
              tab === "manual" ? "bg-white/20" : "bg-border/60 text-muted-foreground"
            )}>
              2
            </span>
            Manual Setup
          </motion.button>
        </div>

        {tab === "nl" ? (
          !parsedRule ? (
            <motion.div
              key="nl-input"
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.22, ease: "easeOut" }}
              className="space-y-4"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary to-blue-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_10px_-3px_var(--primary)]">
                  <Sparkles className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-foreground">Describe your rule in plain English</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Our AI will help you convert it into a precise rule.</p>
                </div>
              </div>
              <textarea
                value={nlText}
                onChange={(e) => setNlText(e.target.value)}
                placeholder="e.g., Alert me if revenue drops by more than 10% MoM"
                className="w-full h-24 bg-surface border border-border/80 rounded-xl p-3 text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none"
              />
              <div className="flex gap-3 mt-6">
                <Button variant="outline" className="flex-1 rounded-full" onClick={onClose}>Cancel</Button>
                <Button
                  className="flex-1 gap-2 rounded-full bg-gradient-to-r from-primary to-blue-600 text-white shadow-lg shadow-primary/20 hover:opacity-90"
                  onClick={() => parseMut.mutate()}
                  disabled={parseMut.isPending || !nlText}
                >
                  {parseMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <>Continue <ArrowRight className="h-4 w-4" /></>}
                </Button>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="nl-confirm"
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.22, ease: "easeOut" }}
              className="space-y-4"
            >
              <div className="p-4 bg-primary/5 rounded-xl border border-primary/20 space-y-2">
                <p className="text-xs font-semibold text-primary">Parsed Rule Confirmation</p>
                <div className="text-sm"><strong>Name:</strong> {parsedRule.name}</div>
                <div className="text-sm"><strong>Metric Column:</strong> {parsedRule.metric_column}</div>
                <div className="text-sm"><strong>Condition:</strong> {parsedRule.condition}</div>
                <div className="text-sm"><strong>Threshold:</strong> {parsedRule.threshold}</div>
                <div className="text-sm"><strong>Window:</strong> {parsedRule.window}</div>
              </div>
              <div className="flex gap-3 mt-6">
                <Button variant="outline" className="flex-1 rounded-full" onClick={() => setParsedRule(null)}>Edit Prompt</Button>
                <Button
                  className="flex-1 gap-2 rounded-full bg-gradient-to-r from-primary to-blue-600 text-white shadow-lg shadow-primary/20 hover:opacity-90"
                  onClick={() => createMut.mutate(parsedRule)}
                  disabled={createMut.isPending}
                >
                  {createMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Save className="h-4 w-4" /> Save Active Rule</>}
                </Button>
              </div>
            </motion.div>
          )
        ) : (
          <motion.div
            key="manual"
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="space-y-4"
          >
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Rule Name</label>
              <div className="relative">
                <Pencil className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  value={manualForm.name}
                  onChange={e => setManualForm({...manualForm, name: e.target.value})}
                  placeholder="e.g. Revenue Drop Alert"
                  className="w-full bg-surface border border-border/80 rounded-lg p-2.5 pl-9 text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Metric Column</label>
                <MetricColumnPicker
                  value={manualForm.metric_column}
                  onChange={(col) => setManualForm({...manualForm, metric_column: col})}
                  columns={numericColumns}
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Threshold</label>
                <div className="relative">
                  <Hash className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="number"
                    value={manualForm.threshold}
                    onChange={e => setManualForm({...manualForm, threshold: parseFloat(e.target.value) || 0})}
                    className="w-full bg-surface border border-border/80 rounded-lg p-2.5 pl-9 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Condition</label>
                <StyledSelect
                  value={manualForm.condition}
                  onChange={(v) => setManualForm({...manualForm, condition: v})}
                  options={[
                    { value: ">", label: "> (Greater than)" },
                    { value: "<", label: "< (Less than)" },
                    { value: ">=", label: ">= (Greater or eq)" },
                    { value: "<=", label: "<= (Less or eq)" },
                    { value: "==", label: "== (Equals)" },
                    { value: "pct_change_gt", label: "% Change >" },
                    { value: "pct_change_lt", label: "% Change <" },
                  ]}
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Time Window (Optional)</label>
                <StyledSelect
                  value={manualForm.window}
                  onChange={(v) => setManualForm({...manualForm, window: v})}
                  icon={Clock}
                  options={[
                    { value: "latest", label: "Latest Value" },
                    { value: "MoM", label: "Month over Month (MoM)" },
                  ]}
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <Button variant="outline" className="flex-1 rounded-full" onClick={onClose}>Cancel</Button>
              <Button
                className="flex-1 gap-2 rounded-full bg-gradient-to-r from-primary to-blue-600 text-white shadow-lg shadow-primary/20 hover:opacity-90"
                onClick={handleManualSubmit}
                disabled={createMut.isPending}
              >
                {createMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Save className="h-4 w-4" /> Save Rule</>}
              </Button>
            </div>
          </motion.div>
        )}
      </motion.div>
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

function RulesEmptyState({ onNewRule }: { onNewRule: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-20 px-6 text-center"
    >
      <div className="relative flex h-14 w-14 items-center justify-center">
        <motion.div
          animate={{ scale: [1, 1.25, 1], opacity: [0.5, 0.15, 0.5] }}
          transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
          className="absolute inset-0 rounded-full bg-primary/40 blur-md"
        />
        <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-blue-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_16px_-3px_var(--primary)]">
          <GitBranch className="h-6 w-6 text-white" />
        </div>
      </div>

      <h3 className="mt-6 text-base font-semibold text-foreground">No rules yet</h3>
      <p className="mt-2 max-w-sm text-sm leading-relaxed text-muted-foreground">
        Create your first business rule to automatically monitor metrics and get alerts.
      </p>

      <motion.button
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        onClick={onNewRule}
        className="mt-6 flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-blue-600 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-primary/20"
      >
        <Plus className="h-4 w-4" /> New Rule
      </motion.button>
    </motion.div>
  );
}

export default function RulesPage() {
  const qc = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [historyRule, setHistoryRule] = useState<BusinessRule | null>(null);

  const { data: activeDataset } = useQuery({
    queryKey: ["activeDataset"],
    queryFn: () => datasetsApi.getActive(),
  });

  const { data: rules, isLoading, isError, refetch } = useQuery({
    queryKey: ["rules", activeDataset?.id],
    queryFn: () => rulesApi.list(),
    enabled: !!activeDataset?.id,
  });

  const evaluateMut = useMutation({
    mutationFn: () => rulesApi.evaluate(),
    onSuccess: (updated) => {
      qc.setQueryData(["rules", activeDataset?.id], updated);
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div></div>
        {rules && rules.length > 0 && (
          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              onClick={() => evaluateMut.mutate()}
              disabled={evaluateMut.isPending}
              className="gap-2"
            >
              <motion.span
                animate={evaluateMut.isPending ? { rotate: 360 } : { rotate: 0 }}
                transition={evaluateMut.isPending ? { duration: 0.8, repeat: Infinity, ease: "linear" } : {}}
                className="flex"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </motion.span>
              Run checks now
            </Button>
            <Button onClick={() => setShowModal(true)} className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
              <Plus className="h-4 w-4" /> New Rule
            </Button>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} lines={4} />)}
        </div>
      ) : isError ? (
        <ErrorState onRetry={refetch} />
      ) : !rules || rules.length === 0 ? (
        <RulesEmptyState onNewRule={() => setShowModal(true)} />
      ) : (
        <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {rules.map((rule) => (
            <motion.div key={rule.id} variants={itemVariants}>
              <RuleCard rule={rule} onViewHistory={() => setHistoryRule(rule)} />
            </motion.div>
          ))}
        </motion.div>
      )}

      <AnimatePresence>
        {showModal && <NewRuleModal onClose={() => setShowModal(false)} />}
      </AnimatePresence>
      {/* Not AnimatePresence-wrapped: unmounting here must track React state
          directly. Gating removal on an exit animation's onComplete firing
          has left stale slide-over panels behind before (see ChatUI.tsx /
          CustomizeDashboardModal.tsx) — the panel's own mount-in transition
          still plays via its `animate` prop regardless. */}
      {historyRule && <RuleHistoryPanel rule={historyRule} onClose={() => setHistoryRule(null)} />}
    </div>
  );
}

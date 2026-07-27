"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { BarChart3, Loader2, ShieldAlert, Lock, ArrowRight, Clock } from "lucide-react";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { InsightPanel } from "@/components/dashboard/InsightPanel";
import { BASE_URL } from "@/lib/api";
import { formatIndianCurrency } from "@/lib/utils";

interface SharedData {
  dataset_name: string;
  row_count: number;
  kpis: { name: string; value: number; trend?: number; type?: string }[];
  chart_data: { name: string; value: number | null; forecast?: number | null }[];
  insights: { title: string; description: string; impact: number | null; confidence: number; category: string }[];
}

function formatKpiValue(value: number, type?: string): string {
  const isNegative = value < 0;
  const abs = Math.abs(value);
  const sign = isNegative ? "-" : "";
  if (type === "count" || type === "generic") {
    if (abs >= 1_000_000) return `${sign}${(abs / 1_000_000).toFixed(1)}M`;
    if (abs >= 1_000) return `${sign}${(abs / 1_000).toFixed(1)}K`;
    return `${sign}${abs}`;
  }
  if (type === "percent") return `${sign}${abs.toFixed(1)}%`;
  return `${sign}${formatIndianCurrency(abs)}`;
}

type ViewState =
  | { kind: "loading" }
  | { kind: "password"; wrongAttempt: boolean }
  | { kind: "expired" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: SharedData };

async function loadSharedDashboard(token: string, pwd?: string): Promise<ViewState> {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/share/${token}/data`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: pwd ?? null }),
    });
    if (res.status === 410) {
      return { kind: "expired" };
    }
    if (res.status === 401) {
      const body = await res.json().catch(() => null);
      const code = body?.detail?.error;
      return { kind: "password", wrongAttempt: code === "incorrect_password" };
    }
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      const detail = typeof body?.detail === "string" ? body.detail : "This share link is invalid or has been revoked.";
      return { kind: "error", message: detail };
    }
    const json = await res.json();
    return { kind: "ready", data: json };
  } catch {
    return { kind: "error", message: "Could not load this shared dashboard." };
  }
}

export function SharedDashboardClient({ token }: { token: string }) {
  const [state, setState] = useState<ViewState>({ kind: "loading" });
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    loadSharedDashboard(token).then((result) => {
      if (!cancelled) setState(result);
    });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) return;
    setSubmitting(true);
    const result = await loadSharedDashboard(token, password);
    setState(result);
    setSubmitting(false);
  };

  if (state.kind === "loading") {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (state.kind === "password") {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-background gap-5 px-6 text-center">
        <motion.div
          initial={{ scale: 0.5, opacity: 0, rotate: -12 }}
          animate={{ scale: 1, opacity: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 380, damping: 18 }}
          className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-blue-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_20px_-4px_var(--primary)]"
        >
          <Lock className="h-6 w-6 text-white" strokeWidth={2.5} />
        </motion.div>
        <div>
          <h1 className="text-lg font-semibold text-foreground">This dashboard is password protected</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">Enter the password the owner shared with you.</p>
        </div>
        <form onSubmit={handlePasswordSubmit} className="flex w-full max-w-xs flex-col gap-3">
          <input
            type="password"
            autoFocus
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="h-11 rounded-xl border border-border/60 bg-surface/60 px-4 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
          <AnimatePresence>
            {state.wrongAttempt && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="text-xs text-error"
              >
                Incorrect password. Try again.
              </motion.p>
            )}
          </AnimatePresence>
          <button
            type="submit"
            disabled={submitting || !password}
            className="flex h-11 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary to-blue-600 text-sm font-medium text-white shadow-lg shadow-primary/20 transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <>Unlock <ArrowRight className="h-4 w-4" /></>}
          </button>
        </form>
      </div>
    );
  }

  if (state.kind === "expired") {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-background gap-3 text-center px-6">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-500/10 border border-amber-500/20">
          <Clock className="h-6 w-6 text-amber-500" />
        </div>
        <h1 className="text-lg font-semibold text-foreground">This link has expired</h1>
        <p className="max-w-sm text-sm text-muted-foreground">
          Ask the dashboard owner to share a fresh link.
        </p>
      </div>
    );
  }

  if (state.kind === "error") {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-background gap-3 text-center px-6">
        <ShieldAlert className="h-10 w-10 text-muted-foreground/60" />
        <h1 className="text-lg font-semibold text-foreground">Link unavailable</h1>
        <p className="text-sm text-muted-foreground max-w-sm">{state.message}</p>
      </div>
    );
  }

  const data = state.data;
  const metricCards = data.kpis.slice(0, 4).map((k) => ({
    title: k.name,
    value: formatKpiValue(k.value, k.type),
    trend: k.trend !== undefined && k.trend !== null ? `${k.trend > 0 ? "+" : ""}${k.trend.toFixed(1)}%` : "–",
    trendDown: (k.trend ?? 0) < 0,
  }));

  return (
    <div className="h-screen w-full overflow-y-auto bg-background text-foreground">
      <header className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 bg-background/80 backdrop-blur-md border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          <span className="text-sm font-semibold">DataMind</span>
          <span className="text-xs text-muted-foreground border border-border/50 rounded-full px-2 py-0.5 ml-2">
            Shared read-only view
          </span>
        </div>
        <div className="text-xs text-muted-foreground">
          {data.dataset_name} · {data.row_count.toLocaleString()} rows
        </div>
      </header>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="max-w-7xl mx-auto p-6 flex flex-col gap-6"
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {metricCards.length > 0 ? (
            metricCards.map((card, idx) => <MetricCard key={card.title} index={idx} {...card} />)
          ) : (
            <div className="col-span-4 text-sm text-muted-foreground">No metrics available for this dataset.</div>
          )}
        </div>

        {data.chart_data.length > 0 && (
          <div className="glass-card rounded-[20px] border border-border/50 p-5">
            <h3 className="text-sm font-medium text-muted-foreground mb-4">Performance Over Time</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.chart_data} margin={{ top: 10, right: 20, bottom: 5, left: 5 }}>
                  <defs>
                    <linearGradient id="sharedValueGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2f6bff" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#2f6bff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: "#666", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#666", fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#1a1a1a", borderColor: "#333" }} />
                  <Area type="monotone" dataKey="value" stroke="#2f6bff" strokeWidth={2} fill="url(#sharedValueGradient)" connectNulls />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {data.insights.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-3">Key Insights</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {data.insights.slice(0, 3).map((ins, i) => (
                <InsightPanel
                  key={`${ins.title}-${i}`}
                  title={ins.title}
                  severity={ins.confidence > 0.85 ? "high" : ins.confidence > 0.65 ? "medium" : "low"}
                  confidence={Math.round((ins.confidence ?? 0) * 100)}
                  impact={ins.impact ?? undefined}
                  description={ins.description ?? ""}
                  category={ins.category || "Insight"}
                  verified
                  index={i}
                />
              ))}
            </div>
          </div>
        )}

        <p className="text-center text-xs text-muted-foreground/60 pt-4 pb-8">
          This is a read-only view shared by the dataset owner. Powered by DataMind.
        </p>
      </motion.div>
    </div>
  );
}

"use client";

import { Suspense, useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { analyticsApi } from "@/lib/api";
import { ChevronDown, TrendingUp, TrendingDown, Target, Info, AlertTriangle } from "lucide-react";
import { ErrorState } from "@/components/ui/error-state";
import { ResponsiveContainer, ComposedChart, CartesianGrid, XAxis, YAxis, Tooltip, Area, Line, ReferenceLine } from "recharts";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber } from "@/lib/utils";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";

const GRANULARITIES = [
  { value: "D", label: "Daily" },
  { value: "W", label: "Weekly" },
  { value: "M", label: "Monthly" },
  { value: "Q", label: "Quarterly" },
] as const;

const HORIZONS = [3, 6, 12, 24];

/** MAPE is error, so lower is better — bucket it into plain language. */
function accuracyBand(mape: number | null | undefined) {
  if (mape === null || mape === undefined) return { label: "Not scored", tone: "text-muted-foreground" };
  if (mape < 5) return { label: "Excellent", tone: "text-success" };
  if (mape < 10) return { label: "Good", tone: "text-success" };
  if (mape < 20) return { label: "Fair", tone: "text-warning" };
  return { label: "Weak", tone: "text-error" };
}

function Pill({
  label,
  value,
  onSelect,
  options,
}: {
  label: string;
  value: string;
  onSelect: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-1.5 bg-surface border border-border text-xs font-medium text-foreground rounded-lg px-3 py-1.5 outline-none hover:bg-white/5 transition-colors focus:ring-2 focus:ring-primary/30 shadow-sm cursor-pointer">
        <span className="text-muted-foreground/70">{label}</span>
        {options.find((o) => o.value === value)?.label ?? value}
        <ChevronDown className="h-3 w-3 text-muted-foreground ml-1 shrink-0" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40 max-h-[300px] overflow-y-auto">
        {options.map((o) => (
          <DropdownMenuItem key={o.value} onClick={() => onSelect(o.value)} className="text-xs cursor-pointer">
            {o.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function StatCard({
  label,
  value,
  sub,
  icon,
  tone,
}: {
  label: string;
  value: string;
  sub?: string;
  icon?: React.ReactNode;
  tone?: string;
}) {
  return (
    <div className="glass-card rounded-xl border border-white/[0.05] bg-surface/30 p-4 flex flex-col gap-1.5">
      <div className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
        {icon}
        {label}
      </div>
      <div className={`text-xl font-semibold tabular-metrics ${tone ?? "text-foreground"}`}>{value}</div>
      {sub && <div className="text-[11px] text-muted-foreground/70">{sub}</div>}
    </div>
  );
}

// useSearchParams() must be wrapped in Suspense for production builds
// (works fine without it in dev, which is why this is easy to miss).
export default function ForecastCenter() {
  return (
    <Suspense fallback={<div className="p-6 text-center text-muted-foreground py-8">Loading...</div>}>
      <ForecastCenterInner />
    </Suspense>
  );
}

function ForecastCenterInner() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const { data: statsData } = useQuery({
    queryKey: ["statistics"],
    queryFn: () => analyticsApi.statistics(),
  });

  // Kept in the URL so a configured projection can be bookmarked or handed to
  // someone else, the same way /datasets/compare carries its two dataset ids.
  const [metric, setMetric] = useState<string>(searchParams.get("metric") || "");
  const [freq, setFreq] = useState<string>(searchParams.get("freq") || "M");
  const [periods, setPeriods] = useState<number>(Number(searchParams.get("periods")) || 6);

  useEffect(() => {
    if (statsData?.stats?.length > 0 && !metric) {
      setMetric(statsData.stats[0].column);
    }
  }, [statsData, metric]);

  useEffect(() => {
    if (!metric) return;
    const qs = new URLSearchParams({ metric, freq, periods: String(periods) });
    router.replace(`/analytics/forecast?${qs}`, { scroll: false });
  }, [metric, freq, periods, router]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["forecast", metric, freq, periods],
    queryFn: () => analyticsApi.forecast(metric, { periods, freq }),
    enabled: !!metric,
    placeholderData: (prev) => prev,
  });

  const chartData: Record<string, unknown>[] = [];
  let boundaryLabel: string | undefined;
  if (data?.historical && data?.forecast) {
    const historical = data.historical.map((d) => ({ date: d.date, value: d.value }));
    const forecast = data.forecast.map((d) => ({
      date: d.date,
      forecast: d.forecast,
      lower: d.lower,
      upper: d.upper,
    }));

    // Bridge the two series so the dashed forecast line starts where the solid
    // actual line ends, instead of leaving a visual gap at the seam.
    if (historical.length > 0 && forecast.length > 0) {
      const last = historical[historical.length - 1] as Record<string, unknown>;
      last.forecast = last.value;
      last.lower = last.value;
      last.upper = last.value;
      boundaryLabel = historical[historical.length - 1].date;
    }

    chartData.push(...historical, ...forecast);
  }

  const summary = data?.summary;
  const acc = data?.accuracy;
  const band = accuracyBand(acc?.mape);
  const unitLabel = data?.freq_label ?? "period";
  const rising = (summary?.change_pct ?? 0) >= 0;

  const toolbar = (
    <div className="flex items-center gap-2">
      {statsData?.stats && statsData.stats.length > 0 && (
        <Pill
          label="Metric"
          value={metric}
          onSelect={setMetric}
          options={statsData.stats.map((s: { column: string }) => ({ value: s.column, label: s.column }))}
        />
      )}
      <Pill label="Every" value={freq} onSelect={setFreq} options={GRANULARITIES.map((g) => ({ ...g }))} />
      <Pill
        label="Next"
        value={String(periods)}
        onSelect={(v) => setPeriods(Number(v))}
        options={HORIZONS.map((h) => ({ value: String(h), label: `${h} ${unitLabel}s` }))}
      />
    </div>
  );

  return (
    <StudioPage title="Forecast Center" isLoading={isLoading && !data} toolbar={toolbar}>
      {isError ? (
        <ErrorState />
      ) : !data || data.available === false ? (
        <div className="text-muted-foreground text-sm">
          {data?.reason || "No forecast data found. Make sure your dataset has a date column."}
        </div>
      ) : (
        <div className="flex flex-col gap-4 h-full">
          {/* Headline projection */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <StatCard
              label={summary?.next_is_in_progress ? `${unitLabel} in progress` : `Next ${unitLabel}`}
              value={formatNumber(summary?.next_value ?? 0)}
              sub={summary?.next_is_in_progress ? `${summary.next_label} · projected total` : summary?.next_label}
              icon={<Target className="h-3 w-3" />}
            />
            <StatCard
              label={`vs last full ${unitLabel}`}
              value={summary?.change_pct === null || summary?.change_pct === undefined ? "–" : `${rising ? "+" : ""}${summary.change_pct}%`}
              sub={`from ${formatNumber(summary?.last_actual ?? 0)}`}
              icon={rising ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              tone={rising ? "text-success" : "text-error"}
            />
            <StatCard
              label={`Next ${periods} ${unitLabel}s`}
              value={formatNumber(summary?.horizon_total ?? 0)}
              sub="projected total"
              icon={<TrendingUp className="h-3 w-3" />}
            />
            <StatCard
              label="Backtest accuracy"
              value={acc?.mape !== null && acc?.mape !== undefined ? `${acc.mape}% error` : "Not scored"}
              sub={
                acc
                  ? `${band.label} · held out last ${acc.holdout_periods} ${unitLabel}${acc.holdout_periods === 1 ? "" : "s"}`
                  : "Too little history to score"
              }
              icon={<Info className="h-3 w-3" />}
              tone={band.tone}
            />
          </div>

          {/* Method + caveats */}
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
            <span className="rounded-full border border-border/60 bg-surface/40 px-2.5 py-1">
              Model: <span className="text-foreground/80">{data.method}</span>
            </span>
            <span className="rounded-full border border-border/60 bg-surface/40 px-2.5 py-1">
              {summary?.history_periods} {unitLabel}s of history
            </span>
            {acc && (
              <span className="rounded-full border border-border/60 bg-surface/40 px-2.5 py-1">
                RMSE {formatNumber(acc.rmse)}
              </span>
            )}
            {data.partial_period_dropped && (
              <span className="flex items-center gap-1.5 rounded-full border border-warning/25 bg-warning/10 px-2.5 py-1 text-warning">
                <AlertTriangle className="h-3 w-3" />
                {summary?.next_is_in_progress
                  ? `${data.partial_period_dropped} is still in progress — projected, not counted as history`
                  : `Excluded ${data.partial_period_dropped} — incomplete ${unitLabel}`}
              </span>
            )}
          </div>

          {/* Projection chart */}
          <div className="glass-card rounded-xl p-6 flex flex-col gap-4 border border-white/[0.05] bg-surface/30 flex-1 min-h-[380px]">
            <div className="flex items-center justify-between gap-2 pb-2">
              <span className="text-[14px] font-semibold text-foreground">
                {metric} — next {periods} {unitLabel}s
              </span>
              <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <span className="h-0.5 w-4 rounded bg-[#0070F3]" />
                  Actual
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-0.5 w-4 rounded bg-[#8b5cf6]" style={{ backgroundImage: "repeating-linear-gradient(90deg,#8b5cf6 0 4px,transparent 4px 7px)" }} />
                  Forecast
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-4 rounded-sm bg-[#6366f1]/25" />
                  95% range
                </span>
              </div>
            </div>

            {/* ResponsiveContainer sizes itself with height:100%, which CSS only
                resolves against a parent with an explicitly specified height —
                a flex-derived height is not enough and collapses it to zero.
                Anchoring it to a positioned box sidesteps that entirely. */}
            <div className="relative flex-1 w-full mt-2 min-h-0">
              <div className="absolute inset-0">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <defs>
                    <linearGradient id="fcBand" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#6366f1" stopOpacity={0.28} />
                      <stop offset="100%" stopColor="#6366f1" stopOpacity={0.06} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: "#80848E", fontWeight: 500 }}
                    axisLine={false}
                    tickLine={false}
                    dy={15}
                    minTickGap={24}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#80848E", fontWeight: 500 }}
                    tickFormatter={(value) => formatNumber(value)}
                    axisLine={false}
                    tickLine={false}
                    dx={-10}
                  />
                  <Tooltip
                    cursor={{ stroke: "rgba(255,255,255,0.1)", strokeWidth: 1, strokeDasharray: "4 4" }}
                    contentStyle={{
                      backgroundColor: "rgba(19, 23, 34, 0.85)",
                      backdropFilter: "blur(12px)",
                      border: "1px solid rgba(255,255,255,0.08)",
                      borderRadius: "12px",
                      boxShadow: "0 8px 32px -8px rgba(0,0,0,0.5)",
                      color: "#fff",
                      fontSize: "12px",
                      fontWeight: 500,
                      padding: "8px 12px",
                    }}
                    itemStyle={{ color: "#fff", fontWeight: 600, fontSize: "13px" }}
                    formatter={(value: number, name: string) => [formatNumber(value), name]}
                  />

                  {/* Confidence band: draw the upper edge, then knock out everything
                      below the lower edge with the panel colour. */}
                  <Area type="monotone" dataKey="upper" stroke="none" fill="url(#fcBand)" activeDot={false} name="Upper" />
                  <Area type="monotone" dataKey="lower" stroke="none" fill="#131722" fillOpacity={1} activeDot={false} name="Lower" />

                  {boundaryLabel && (
                    <ReferenceLine
                      x={boundaryLabel}
                      stroke="rgba(255,255,255,0.22)"
                      strokeDasharray="3 3"
                      label={{ value: "now", position: "insideTopRight", fill: "#80848E", fontSize: 10 }}
                    />
                  )}

                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#0070F3"
                    strokeWidth={2.5}
                    dot={false}
                    name="Actual"
                    activeDot={{ r: 5, fill: "#0B0D12", stroke: "#0070F3", strokeWidth: 2 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="forecast"
                    stroke="#8b5cf6"
                    strokeWidth={2.5}
                    strokeDasharray="5 5"
                    dot={false}
                    name="Forecast"
                    activeDot={{ r: 5, fill: "#0B0D12", stroke: "#8b5cf6", strokeWidth: 2 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}
    </StudioPage>
  );
}

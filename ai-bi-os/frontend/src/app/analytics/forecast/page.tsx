"use client";

import { Suspense, useState, useEffect, useMemo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence, useMotionValue, animate } from "framer-motion";
import { analyticsApi } from "@/lib/api";
import { formatNumber } from "@/lib/utils";
import { StudioPage } from "@/components/analytics/StudioPage";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";

const GRANULARITIES = [
  { value: "D", label: "Daily" },
  { value: "W", label: "Weekly" },
  { value: "M", label: "Monthly" },
  { value: "Q", label: "Quarterly" },
];

const HORIZONS = [3, 6, 12, 24];

// Every color below resolves against the app's actual light/dark CSS
// variables (globals.css) via Tailwind's bg-surface/border-border/etc, or
// via var(--x) directly for the SVG (which can't take Tailwind classes for
// stroke/fill). Nothing here is a fixed hex, so the page matches whichever
// theme the rest of the app is in — same convention as every other
// analytics page (see Confidence Center).
const tint = (color: string, pct: number) => `color-mix(in srgb, ${color} ${pct}%, transparent)`;
const PRIMARY = "var(--primary)";
const FORECAST = "#8b5cf6"; // established "prediction" accent (GuidedTourModal AI cards, prior chart)

const EASE = [0.22, 1, 0.36, 1] as const;

function accuracyBand(mape: number | null | undefined) {
  if (mape === null || mape === undefined) return { label: "Not scored", color: "var(--muted-foreground)", accent: tint("var(--muted-foreground)", 50) };
  if (mape < 5) return { label: "Excellent", color: "var(--success)", accent: tint("var(--success)", 60) };
  if (mape < 10) return { label: "Good", color: "var(--success)", accent: tint("var(--success)", 60) };
  if (mape < 20) return { label: "Fair", color: "var(--warning)", accent: tint("var(--warning)", 60) };
  return { label: "Weak", color: "var(--error)", accent: tint("var(--error)", 60) };
}

// ── Smooth-curve SVG path helpers (Catmull-Rom to Bezier) ───────────────────
type Pt = { x: number; y: number };

function catmullSegs(pts: Pt[]): string {
  let d = "";
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[i + 2] || p2;
    const t = 0.2;
    const c1x = p1.x + (p2.x - p0.x) * t;
    const c1y = p1.y + (p2.y - p0.y) * t;
    const c2x = p2.x - (p3.x - p1.x) * t;
    const c2y = p2.y - (p3.y - p1.y) * t;
    d += ` C ${c1x.toFixed(1)} ${c1y.toFixed(1)} ${c2x.toFixed(1)} ${c2y.toFixed(1)} ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
  }
  return d;
}

function lineD(pts: Pt[]): string {
  if (pts.length === 0) return "";
  return `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}` + catmullSegs(pts);
}

function niceNum(range: number, round: boolean): number {
  if (!(range > 0)) return 1;
  const exp = Math.floor(Math.log10(range));
  const f = range / Math.pow(10, exp);
  let nf: number;
  if (round) nf = f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10;
  else nf = f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10;
  return nf * Math.pow(10, exp);
}

const X0 = 76, X1 = 1216, Y0 = 28, Y1 = 430;

type HoverPoint = { x: number; y: number; date: string; isForecast: boolean; value?: number; lower?: number; upper?: number };

// ── Pill control (Metric / Every / Next dropdowns) — same trigger styling
// every other analytics toolbar on this app uses, plus a little life on
// press. ──────────────────────────────────────────────────────────────────
function ControlPill({
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
      <DropdownMenuTrigger className="group flex items-center gap-2 rounded-xl border border-border bg-surface px-3.5 py-2 text-[13px] font-medium text-foreground shadow-sm outline-none transition-all duration-150 hover:-translate-y-px hover:bg-white/5 focus:ring-2 focus:ring-primary/30 active:scale-95">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold text-foreground">{options.find((o) => o.value === value)?.label ?? value}</span>
        <span className="text-muted-foreground transition-transform duration-200 group-data-open:rotate-180">▾</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[180px]">
        {options.map((o) => (
          <DropdownMenuItem key={o.value} onClick={() => onSelect(o.value)} className="flex cursor-pointer items-center justify-between gap-2.5 rounded-lg py-2 text-[13px]">
            <span className={o.value === value ? "font-semibold text-foreground" : "text-muted-foreground"}>{o.label}</span>
            <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: o.value === value ? PRIMARY : tint("var(--muted-foreground)", 30) }} />
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// ── Stat card: entrance handled by the parent's stagger variants, value
// counts up on its own via a motion value (same technique as Confidence
// Center's AnimatedNumber). ─────────────────────────────────────────────────
const cardVariants = {
  hidden: { opacity: 0, y: 18, scale: 0.97 },
  show: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.5, ease: EASE } },
};

function StatCard({
  label,
  icon,
  sub,
  color,
  accent,
  raw,
  format,
}: {
  label: string;
  icon: string;
  sub: string;
  color: string;
  accent: string;
  raw: number;
  format: (v: number) => string;
}) {
  const mv = useMotionValue(0);
  const [display, setDisplay] = useState(format(0));

  useEffect(() => {
    // Resetting the counter's start value before kicking off the imperative
    // count-up is the same "trigger an animation" effect use case React's
    // own docs treat as legitimate.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDisplay(format(0));
    const controls = animate(mv, raw, {
      duration: 1,
      delay: 0.15,
      ease: EASE,
      onUpdate: (v) => setDisplay(format(v)),
    });
    return controls.stop;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [raw]);

  return (
    <motion.div
      variants={cardVariants}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="relative overflow-hidden rounded-[20px] border border-border bg-surface/60 p-5 shadow-sm"
    >
      <motion.div
        style={{ position: "absolute", top: 0, left: 0, right: 0, height: 3, background: `linear-gradient(90deg, transparent, ${accent}, transparent)` }}
        initial={{ opacity: 0, scaleX: 0.3 }}
        animate={{ opacity: 0.9, scaleX: 1 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      />
      <div className="mb-3 flex items-center gap-2.5">
        <span
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[13px]"
          style={{ background: tint(color, 16), color }}
        >
          {icon}
        </span>
        <span className="text-[11.5px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">{label}</span>
      </div>
      <div style={{ fontSize: 32, fontWeight: 700, letterSpacing: "-0.02em", lineHeight: 1, color, fontVariantNumeric: "tabular-nums" }}>
        {display}
      </div>
      <div className="mt-2.5 text-[13px] text-muted-foreground">{sub}</div>
    </motion.div>
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

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07, delayChildren: 0.05 } },
};
const rowVariants = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: EASE } },
};
const chipVariants = {
  hidden: { opacity: 0, x: -8 },
  show: { opacity: 1, x: 0, transition: { duration: 0.35, ease: EASE } },
};

function ForecastCenterInner() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const { data: statsData } = useQuery({
    queryKey: ["statistics"],
    queryFn: () => analyticsApi.statistics(),
  });

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

  const { data, isLoading } = useQuery({
    queryKey: ["forecast", metric, freq, periods],
    queryFn: () => analyticsApi.forecast(metric, { periods, freq }),
    enabled: !!metric,
    // No placeholderData: keeping the previous query's numbers on screen while
    // switching Metric/Every/Next made stale figures flash under the new
    // controls for a moment before snapping to the real ones. Dropping it
    // means React Query clears `data` between keys, StudioPage's spinner
    // covers that gap, and only the correct numbers for the current
    // selection ever render.
  });

  const unitLabel = data?.freq_label ?? "period";
  const summary = data?.summary;
  const acc = data?.accuracy;
  const band = accuracyBand(acc?.mape);
  const rising = (summary?.change_pct ?? 0) >= 0;

  const cards = useMemo(() => {
    if (!data?.available || !summary) return [];
    return [
      {
        label: summary.next_is_in_progress ? `${unitLabel.toUpperCase()} IN PROGRESS` : `NEXT ${unitLabel.toUpperCase()}`,
        icon: "◎",
        color: "var(--foreground)",
        accent: tint(PRIMARY, 60),
        sub: summary.next_is_in_progress ? `${summary.next_label} · projected total` : summary.next_label,
        raw: summary.next_value,
        format: (v: number) => formatNumber(v),
      },
      {
        label: `VS LAST FULL ${unitLabel.toUpperCase()}`,
        icon: rising ? "↗" : "↘",
        color: rising ? "var(--success)" : "var(--error)",
        accent: tint(rising ? "var(--success)" : "var(--error)", 60),
        sub: `from ${formatNumber(summary.last_actual)}`,
        raw: summary.change_pct ?? 0,
        format: (v: number) => `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`,
      },
      {
        label: `NEXT ${periods} ${unitLabel.toUpperCase()}S`,
        icon: "↗",
        color: "var(--foreground)",
        accent: tint(PRIMARY, 60),
        sub: "projected total",
        raw: summary.horizon_total,
        format: (v: number) => formatNumber(v),
      },
      {
        label: "BACKTEST ACCURACY",
        icon: "ⓘ",
        color: band.color,
        accent: band.accent,
        sub: acc ? `${band.label} · held out last ${acc.holdout_periods} ${unitLabel}${acc.holdout_periods === 1 ? "" : "s"}` : "Too little history to score",
        raw: acc?.mape ?? 0,
        format: (v: number) => (acc?.mape != null ? `${v.toFixed(2)}% error` : "—"),
      },
    ];
  }, [data, summary, acc, band, unitLabel, periods, rising]);

  const chips = useMemo(() => {
    if (!data?.available) return [];
    const base: { text: string; icon?: string; warn?: boolean }[] = [
      { text: `Model: ${data.method}` },
      { text: `${summary?.history_periods ?? 0} ${unitLabel}s of history` },
    ];
    if (acc) base.push({ text: `RMSE ${formatNumber(acc.rmse)}` });
    if (data.partial_period_dropped) {
      base.push({
        icon: "⚠",
        warn: true,
        text: summary?.next_is_in_progress
          ? `${data.partial_period_dropped} is still in progress — projected, not counted as history`
          : `Excluded ${data.partial_period_dropped} — incomplete ${unitLabel}`,
      });
    }
    return base;
  }, [data, summary, acc, unitLabel]);

  const geometry = useMemo(() => {
    if (!data?.historical || !data?.forecast || data.historical.length === 0 || data.forecast.length === 0) return null;
    const hist = data.historical;
    const fore = data.forecast;
    const histCount = hist.length;
    const totalSteps = histCount - 1 + fore.length;
    const xAt = (i: number) => X0 + (i / totalSteps) * (X1 - X0);

    const allVals = [...hist.map((h) => h.value), ...fore.map((f) => f.upper), ...fore.map((f) => f.lower)];
    let mn = Math.min(...allVals);
    let mx = Math.max(...allVals);
    if (mn === mx) {
      mn -= 1;
      mx += 1;
    }
    const step = niceNum((mx - mn) / 4, true);
    const nMin = Math.floor(mn / step) * step;
    const nMax = Math.ceil(mx / step) * step;
    const yAt = (v: number) => Y0 + ((nMax - v) / (nMax - nMin)) * (Y1 - Y0);

    const yTicks: { label: string; y: number; ty: number; zero: boolean }[] = [];
    for (let v = nMin; v <= nMax + 1e-9; v += step) {
      const y = yAt(v);
      yTicks.push({ label: formatNumber(v), y, ty: y + 4, zero: Math.abs(v) < 1e-6 });
    }

    const actualPts = hist.map((h, i) => ({ x: xAt(i), y: yAt(h.value) }));
    const lastActual = hist[histCount - 1].value;
    const bridge = { x: xAt(histCount - 1), y: yAt(lastActual) };
    const forePts = [bridge, ...fore.map((f, i) => ({ x: xAt(histCount + i), y: yAt(f.forecast) }))];
    const upPts = [bridge, ...fore.map((f, i) => ({ x: xAt(histCount + i), y: yAt(f.upper) }))];
    const loPtsRev = [bridge, ...fore.map((f, i) => ({ x: xAt(histCount + i), y: yAt(f.lower) }))].reverse();
    const bandD = lineD(upPts) + ` L ${loPtsRev[0].x.toFixed(1)} ${loPtsRev[0].y.toFixed(1)}` + catmullSegs(loPtsRev) + " Z";

    const allDates = [...hist.map((h) => h.date), ...fore.map((f) => f.date)];
    const labelCount = Math.min(9, allDates.length);
    const xLabels = Array.from({ length: labelCount }, (_, k) => {
      const idx = labelCount > 1 ? Math.round((k / (labelCount - 1)) * (allDates.length - 1)) : 0;
      return { label: allDates[idx], x: xAt(idx) };
    });

    const nowX = xAt(histCount - 1);
    const foreEnd = forePts[forePts.length - 1];

    // Hoverable points: real data only (the bridge point is a line-continuity
    // artifact, not an actual reading, so it's excluded from hit-testing).
    const hoverPoints: HoverPoint[] = [
      ...hist.map((h, i) => ({ x: xAt(i), y: yAt(h.value), date: h.date, isForecast: false, value: h.value })),
      ...fore.map((f, i) => ({ x: xAt(histCount + i), y: yAt(f.forecast), date: f.date, isForecast: true, value: f.forecast, lower: f.lower, upper: f.upper })),
    ];

    return {
      actualD: lineD(actualPts),
      foreD: lineD(forePts),
      bandD,
      yTicks,
      xLabels,
      nowX,
      nowDotY: actualPts[histCount - 1].y,
      foreEndX: foreEnd.x,
      foreEndY: foreEnd.y,
      hoverPoints,
    };
  }, [data]);

  const [hover, setHover] = useState<HoverPoint | null>(null);

  const handleChartMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!geometry || geometry.hoverPoints.length === 0) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const relX = (e.clientX - rect.left) / rect.width;
      const dataX = relX * 1240;
      let nearest = geometry.hoverPoints[0];
      let best = Infinity;
      for (const p of geometry.hoverPoints) {
        const d = Math.abs(p.x - dataX);
        if (d < best) {
          best = d;
          nearest = p;
        }
      }
      setHover(nearest);
    },
    [geometry]
  );
  const handleChartLeave = useCallback(() => setHover(null), []);

  const toolbarMetricOptions = (statsData?.stats ?? []).map((s: { column: string }) => ({ value: s.column, label: s.column }));

  const toolbar = (
    <div className="flex items-center gap-2">
      {toolbarMetricOptions.length > 0 && <ControlPill label="Metric" value={metric} onSelect={setMetric} options={toolbarMetricOptions} />}
      <ControlPill label="Every" value={freq} onSelect={setFreq} options={GRANULARITIES} />
      <ControlPill label="Next" value={String(periods)} onSelect={(v) => setPeriods(Number(v))} options={HORIZONS.map((h) => ({ value: String(h), label: `${h} ${unitLabel}s` }))} />
    </div>
  );

  // Remounting the whole animated section whenever the query changes replays
  // every entrance animation automatically — count-up, line draw, band
  // reveal — with no separate "replay" control needed.
  const animKey = `${metric}-${freq}-${periods}-${data?.available ? "ok" : "empty"}`;

  return (
    <StudioPage title="Forecast Center" toolbar={toolbar} isLoading={isLoading && !data}>
      {(!data && !isLoading) || (data && !data.available) ? (
        <div className="py-16 text-center text-[14px] text-muted-foreground">
          {data?.reason || "No forecast data found. Make sure your dataset has a date column."}
        </div>
      ) : (
        <motion.div key={animKey} variants={containerVariants} initial="hidden" animate="show" className="flex flex-col gap-4">
          {/* STAT CARDS */}
          <motion.div variants={containerVariants} className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {cards.map((c) => (
              <StatCard key={c.label} {...c} />
            ))}
          </motion.div>

          {/* CHIPS */}
          <motion.div variants={containerVariants} className="flex flex-wrap gap-2">
            {chips.map((ch) => (
              <motion.div
                key={ch.text}
                variants={chipVariants}
                whileHover={{ y: -1 }}
                className={`flex items-center gap-2 rounded-full border px-4 py-2.5 text-[13px] ${
                  ch.warn ? "border-warning/35 bg-warning/10 text-warning font-semibold" : "border-border bg-surface/50 text-muted-foreground"
                }`}
              >
                {ch.icon && <span className="text-sm">{ch.icon}</span>}
                <span>{ch.text}</span>
              </motion.div>
            ))}
          </motion.div>

          {/* CHART CARD */}
          <motion.div variants={rowVariants} className="rounded-[22px] border border-border bg-surface/30 p-6">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-4">
              <h2 className="text-[18px] font-semibold text-foreground">
                {metric} — next {periods} {unitLabel}s
              </h2>
              <div className="flex items-center gap-5 text-[13px] text-muted-foreground">
                <div className="flex items-center gap-2">
                  <span style={{ width: 18, height: 3, borderRadius: 2, background: PRIMARY }} />
                  <span>Actual</span>
                </div>
                <div className="flex items-center gap-2">
                  <span style={{ width: 18, height: 0, borderTop: `3px dotted ${FORECAST}` }} />
                  <span>Forecast</span>
                </div>
                <div className="flex items-center gap-2">
                  <span style={{ width: 16, height: 11, borderRadius: 3, background: tint(FORECAST, 30), border: `1px solid ${tint(FORECAST, 45)}` }} />
                  <span>95% range</span>
                </div>
              </div>
            </div>

            {geometry && (
              <div
                style={{ position: "relative", width: "100%", height: "clamp(320px,42vh,420px)" }}
                onMouseMove={handleChartMove}
                onMouseLeave={handleChartLeave}
              >
                <svg viewBox="0 0 1240 472" style={{ width: "100%", height: "100%", display: "block", cursor: "crosshair" }} preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="fcActualStroke" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0" stopColor="#22d3ee" />
                      <stop offset="0.5" stopColor={PRIMARY} />
                      <stop offset="1" stopColor={PRIMARY} />
                    </linearGradient>
                    <linearGradient id="fcBandFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0" stopColor={tint(FORECAST, 38)} />
                      <stop offset="1" stopColor={tint(FORECAST, 3)} />
                    </linearGradient>
                    <filter id="fcGlow" x="-20%" y="-40%" width="140%" height="180%">
                      <feGaussianBlur stdDeviation="6" />
                    </filter>
                    <clipPath id="fcReveal">
                      <motion.rect
                        x={geometry.nowX}
                        y={0}
                        height={472}
                        initial={{ width: 0 }}
                        animate={{ width: X1 - geometry.nowX + 10 }}
                        transition={{ duration: 1, ease: EASE, delay: 0.55 }}
                      />
                    </clipPath>
                  </defs>

                  {geometry.yTicks.map((t, i) => (
                    <motion.g key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.1 }}>
                      <line x1={X0} y1={t.y} x2={X1} y2={t.y} stroke={tint("var(--foreground)", t.zero ? 14 : 5)} strokeWidth={1} strokeDasharray={t.zero ? "0" : "5 7"} />
                      <text x={X0 - 14} y={t.ty} textAnchor="end" fill="var(--muted-foreground)" fontSize={13}>
                        {t.label}
                      </text>
                    </motion.g>
                  ))}

                  <g clipPath="url(#fcReveal)">
                    <motion.path d={geometry.bandD} fill="url(#fcBandFill)" stroke={tint(FORECAST, 32)} strokeWidth={1} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.65 }} />
                    <motion.path d={geometry.foreD} fill="none" stroke={FORECAST} strokeWidth={3} strokeLinecap="round" strokeDasharray="1 8" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.7 }} />
                  </g>

                  <motion.path
                    d={geometry.actualD}
                    fill="none"
                    stroke={PRIMARY}
                    strokeWidth={7}
                    strokeLinecap="round"
                    filter="url(#fcGlow)"
                    opacity={0.3}
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 1.1, ease: EASE, delay: 0.15 }}
                  />
                  <motion.path
                    d={geometry.actualD}
                    fill="none"
                    stroke="url(#fcActualStroke)"
                    strokeWidth={3}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 1.1, ease: EASE, delay: 0.15 }}
                  />

                  <motion.line x1={geometry.nowX} y1={Y0} x2={geometry.nowX} y2={Y1} stroke={tint("var(--foreground)", 22)} strokeWidth={1} strokeDasharray="4 5" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.9 }} />
                  <motion.text x={geometry.nowX - 42} y={Y0 + 13} fill="var(--muted-foreground)" fontSize={13} fontWeight={600} initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.95 }}>
                    now
                  </motion.text>

                  <motion.circle cx={geometry.nowX} cy={geometry.nowDotY} r={4} fill={PRIMARY} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ duration: 0.4, delay: 1.1, ease: "backOut" }} />
                  <circle cx={geometry.nowX} cy={geometry.nowDotY} r={4} fill={PRIMARY} className="fc-now-pulse" />

                  <motion.circle cx={geometry.foreEndX} cy={geometry.foreEndY} r={3.5} fill={FORECAST} initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.4, delay: 1.5, ease: "backOut" }} />

                  {geometry.xLabels.map((xl, i) => (
                    <motion.text key={i} x={xl.x} y={458} textAnchor="middle" fill="var(--muted-foreground)" fontSize={13} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.15 }}>
                      {xl.label}
                    </motion.text>
                  ))}

                  {/* Hover crosshair + marker */}
                  <AnimatePresence>
                    {hover && (
                      <motion.g key={hover.date} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.12 }}>
                        <line x1={hover.x} y1={Y0} x2={hover.x} y2={Y1} stroke={tint("var(--foreground)", 18)} strokeWidth={1} />
                        <motion.circle initial={{ scale: 0.5 }} animate={{ scale: 1 }} cx={hover.x} cy={hover.y} r={6} fill="none" stroke={hover.isForecast ? FORECAST : PRIMARY} strokeWidth={2} />
                        <circle cx={hover.x} cy={hover.y} r={3} fill={hover.isForecast ? FORECAST : PRIMARY} />
                      </motion.g>
                    )}
                  </AnimatePresence>
                </svg>

                {/* HTML tooltip — positioned via the same 0..1240/0..472 ratio
                    the SVG uses, since preserveAspectRatio="none" stretches it
                    1:1 to the box below. */}
                <AnimatePresence>
                  {hover && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.92, y: 4 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.92 }}
                      transition={{ duration: 0.14 }}
                      className="pointer-events-none absolute z-10 rounded-2xl border border-border bg-popover px-4 py-3 shadow-lg"
                      style={{
                        left: `${(hover.x / 1240) * 100}%`,
                        top: `${(hover.y / 472) * 100}%`,
                        transform: hover.x > 1240 * 0.75 ? "translate(-100%, -120%)" : "translate(-8%, -120%)",
                        minWidth: 165,
                      }}
                    >
                      <div className="text-[12px] font-medium text-muted-foreground">{hover.date}</div>
                      <div className="mt-1 flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full" style={{ background: hover.isForecast ? FORECAST : PRIMARY }} />
                        <span className="text-[15px] font-semibold text-foreground">{formatNumber(hover.value ?? 0)}</span>
                        <span className="text-[12px] text-muted-foreground">{hover.isForecast ? "forecast" : "actual"}</span>
                      </div>
                      {hover.isForecast && hover.lower !== undefined && hover.upper !== undefined && (
                        <div className="mt-1 text-[12px] text-muted-foreground">
                          {formatNumber(hover.lower)} – {formatNumber(hover.upper)}
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </StudioPage>
  );
}

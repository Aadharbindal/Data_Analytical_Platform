"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  X,
  ChevronLeft,
  ChevronRight,
  Upload,
  DollarSign,
  Users,
  CreditCard,
  Database,
  Search,
  RefreshCw,
  ChevronDown,
  CheckCircle2,
  BarChart3,
  AlertTriangle,
  TrendingUp,
  Zap,
  Bot,
  Send,
  Activity,
  LineChart,
  Sigma,
  Network,
  Calculator,
  GitBranch,
  Boxes,
  Clock,
  Sparkles,
  Download,
  Share2,
} from "lucide-react";

const SCENE_DURATION_MS = 5800;

const SCENES = [
  {
    eyebrow: "01 · GET STARTED",
    title: "Bring in your data",
    caption: "Drop a CSV, JSON, Parquet or Excel file — DataMind reads the columns and gets to work in seconds.",
  },
  {
    eyebrow: "02 · DASHBOARD",
    title: "Metrics, computed automatically",
    caption: "The moment your data loads, KPI cards, trend charts, and an AI executive summary appear — no dashboard building required.",
  },
  {
    eyebrow: "03 · DATA CATALOG",
    title: "Every dataset, organized",
    caption: "Search across all your datasets by name, domain, or description — with quality and lineage metadata generated automatically.",
  },
  {
    eyebrow: "04 · DEEP INSIGHTS",
    title: "Findings you can trust",
    caption: "Agentic AI asks questions and runs real queries against your data — every finding is marked Verified, or flagged when it isn't.",
  },
  {
    eyebrow: "05 · RECOMMENDATIONS",
    title: "Know what to do next",
    caption: "Prioritized, evidence-backed actions generated straight from your business data — not generic advice.",
  },
  {
    eyebrow: "06 · COPILOT",
    title: "Ask, in plain English",
    caption: "DataMind Copilot queries your data live and answers in seconds, with a reminder to verify anything critical.",
  },
  {
    eyebrow: "07 · ANALYTICS STUDIO",
    title: "A full analytics toolkit",
    caption: "KPI tracking, statistics, regression, classification, clustering, and forecasting — all built in, all in one place.",
  },
];

function Reveal({
  active,
  delay = 0,
  className = "",
  children,
}: {
  active: boolean;
  delay?: number;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={`transition-all duration-500 ${className}`}
      style={{ opacity: active ? 1 : 0, transform: active ? "translateY(0)" : "translateY(8px)", transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}

function ScreenChrome({ children, dark = true }: { children: React.ReactNode; dark?: boolean }) {
  return (
    <div className="h-full w-full overflow-hidden rounded-xl border border-white/10 bg-[#0a0d15]">
      <div className="flex items-center gap-1.5 border-b border-white/[0.06] px-3 py-2">
        <span className="h-2 w-2 rounded-full bg-white/10" />
        <span className="h-2 w-2 rounded-full bg-white/10" />
        <span className="h-2 w-2 rounded-full bg-white/10" />
      </div>
      <div className="h-[calc(100%-29px)] w-full p-3.5">{children}</div>
    </div>
  );
}

function SceneVisual({ index, active }: { index: number; active: boolean }) {
  const scenes = [UploadScene, DashboardScene, CatalogScene, InsightsScene, RecommendationsScene, CopilotScene, AnalyticsScene];
  const Scene = scenes[index] ?? UploadScene;
  return <Scene active={active} />;
}

function UploadScene({ active }: { active: boolean }) {
  return (
    <ScreenChrome>
      <div className="flex h-full flex-col gap-2.5">
        <div className="flex justify-end">
          <span className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[9px] text-[#8b93a3]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#4d8bff]" />0 datasets
          </span>
        </div>
        <Reveal
          active={active}
          className="flex flex-1 flex-col items-center justify-center gap-2 rounded-lg border-[1.5px] border-dashed border-white/15 bg-white/[0.015]"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#0d1526]">
            <Upload className="h-4 w-4 text-[#4d8bff]" />
          </div>
          <div className="text-[11px] font-semibold text-white">
            Drop files here or <span className="text-[#4d8bff]">browse</span>
          </div>
          <div className="text-[9px] text-[#6b7280]">Supports CSV, JSON, Parquet, Excel</div>
        </Reveal>
        <Reveal active={active} delay={400} className="flex flex-col items-center gap-1 py-2 text-center">
          <Database className="h-4 w-4 text-[#3a3f4b]" />
          <div className="text-[10.5px] font-semibold text-white">No datasets yet</div>
          <div className="text-[8.5px] leading-snug text-[#6b7280]">Upload your first file above to get started.</div>
        </Reveal>
      </div>
    </ScreenChrome>
  );
}

function KpiMini({
  icon: Icon,
  label,
  value,
  color,
  bg,
  active,
  delay,
}: {
  icon: any;
  label: string;
  value: string;
  color: string;
  bg: string;
  active: boolean;
  delay: number;
}) {
  return (
    <Reveal active={active} delay={delay} className="rounded-lg border border-white/10 bg-white/[0.03] p-2.5">
      <div className={`mb-2 flex h-6 w-6 items-center justify-center rounded-md ${bg}`}>
        <Icon className={`h-3 w-3 ${color}`} />
      </div>
      <div className="text-[8.5px] text-[#8b93a3]">{label}</div>
      <div className="text-[13px] font-bold text-white">{value}</div>
    </Reveal>
  );
}

function DashboardScene({ active }: { active: boolean }) {
  const path = "0,32 12,20 24,26 36,10 48,18 60,4 72,14 84,8 96,16 100,12";
  return (
    <ScreenChrome>
      <div className="flex h-full flex-col gap-2">
        <div className="grid grid-cols-3 gap-2">
          <KpiMini icon={DollarSign} label="Total Transaction Value" value="₹34.01L" color="text-[#a78bfa]" bg="bg-[#4c1d95]/25" active={active} delay={0} />
          <KpiMini icon={Users} label="Total Transactions" value="971" color="text-[#60a5fa]" bg="bg-[#1e3a8a]/25" active={active} delay={110} />
          <KpiMini icon={CreditCard} label="Payment Clearance Rate" value="65.6%" color="text-[#34d399]" bg="bg-[#064e3b]/25" active={active} delay={220} />
        </div>
        <div className="grid flex-1 grid-cols-[1.5fr_1fr] gap-2">
          <Reveal active={active} delay={380} className="flex flex-col rounded-lg border border-white/10 bg-white/[0.02] p-2.5">
            <div className="text-[9px] font-medium text-[#c5cbd6]">Monthly Transaction Activity</div>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-[13px] font-bold text-white">₹10.16L</span>
              <span className="rounded-full bg-emerald-500/15 px-1.5 py-0.5 text-[7.5px] font-bold text-emerald-300">↑ 0.0%</span>
            </div>
            <svg viewBox="0 0 100 36" className="mt-1 flex-1" preserveAspectRatio="none">
              <polyline
                points={path}
                fill="none"
                stroke="#4d8bff"
                strokeWidth="2"
                style={{ strokeDasharray: 220, strokeDashoffset: active ? 0 : 220, transition: "stroke-dashoffset 1.1s ease" }}
              />
            </svg>
          </Reveal>
          <Reveal active={active} delay={520} className="flex flex-col rounded-lg border border-white/10 bg-white/[0.02] p-2.5">
            <div className="flex items-center gap-1 text-[8.5px] font-bold tracking-wide text-[#4d8bff]">
              <Sparkles className="h-2.5 w-2.5" /> AI SUMMARY
            </div>
            <div className="mt-1.5 line-clamp-4 text-[8px] leading-relaxed text-[#9aa4b5]">
              The dataset contains 971 transactions worth ₹34.01L, indicating a net outflow this period.
            </div>
            <div className="mt-auto flex gap-1 pt-1.5">
              <span className="flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-1.5 py-1 text-[7px] text-[#c5cbd6]">
                <Share2 className="h-2 w-2" /> Share
              </span>
              <span className="flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-1.5 py-1 text-[7px] text-[#c5cbd6]">
                <Download className="h-2 w-2" /> Report
              </span>
            </div>
          </Reveal>
        </div>
      </div>
    </ScreenChrome>
  );
}

function CatalogScene({ active }: { active: boolean }) {
  return (
    <ScreenChrome>
      <div className="flex h-full flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <Reveal active={active} className="flex flex-1 items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1.5">
            <Search className="h-2.5 w-2.5 text-[#6b7280]" />
            <span className="text-[8.5px] text-[#6b7280]">Search by name, domain, or description…</span>
          </Reveal>
          <span className="ml-2 text-[8px] text-[#6b7280]">1 entries</span>
        </div>
        <Reveal active={active} delay={280} className="flex items-center justify-between rounded-lg border border-white/10 bg-white/[0.03] p-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#0d1526]">
              <Database className="h-3.5 w-3.5 text-[#4d8bff]" />
            </div>
            <div>
              <div className="text-[10.5px] font-semibold text-white">dataset (3).csv</div>
              <div className="mt-0.5 max-w-[220px] text-[8px] text-[#8b93a3]">Auto-generated catalog entry. Contains 971 rows and 7 columns.</div>
              <div className="mt-1.5 flex gap-1.5">
                <span className="rounded-full border border-[#4d8bff]/25 bg-[#4d8bff]/10 px-1.5 py-0.5 text-[7px] text-[#8ab8ff]">auto-inferred</span>
                <span className="rounded-full border border-[#4d8bff]/25 bg-[#4d8bff]/10 px-1.5 py-0.5 text-[7px] text-[#8ab8ff]">raw-data</span>
              </div>
            </div>
          </div>
          <div className="shrink-0 text-right text-[7.5px] text-[#6b7280]">
            <div>7 cols</div>
            <div className="mt-0.5">DataMind OS</div>
          </div>
        </Reveal>
      </div>
    </ScreenChrome>
  );
}

function InsightRow({
  icon: Icon,
  label,
  tone,
  active,
  delay,
}: {
  icon: any;
  label: string;
  tone: string;
  active: boolean;
  delay: number;
}) {
  return (
    <Reveal active={active} delay={delay} className="flex items-center justify-between rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2">
      <div className="flex items-center gap-2">
        <div className={`flex h-5 w-5 items-center justify-center rounded-full ${tone.bg}`}>
          <Icon className={`h-2.5 w-2.5 ${tone.icon}`} />
        </div>
        <span className={`rounded-full px-1.5 py-0.5 text-[7px] font-bold tracking-wide ${tone.badge}`}>{label}</span>
      </div>
      <span className="flex items-center gap-1 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-1.5 py-0.5 text-[7px] font-bold text-emerald-300">
        <CheckCircle2 className="h-2 w-2" /> VERIFIED
      </span>
    </Reveal>
  );
}

function InsightsScene({ active }: { active: boolean }) {
  return (
    <ScreenChrome>
      <div className="flex h-full flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[12px] font-extrabold text-white">Deep Insights Engine</div>
            <div className="max-w-[240px] text-[7.5px] leading-snug text-[#8b93a3]">
              Agentic AI automatically asks questions and surfaces verified findings.
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[7px] text-[#8b93a3]">2 generated</span>
            <span className="flex items-center gap-1 rounded-full bg-[#4d8bff] px-2 py-1 text-[7px] font-bold text-white">
              <RefreshCw className="h-2 w-2" /> Regenerate
            </span>
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <InsightRow icon={BarChart3} label="OPERATIONAL" tone={{ bg: "bg-[#1e3a8a]/40", icon: "text-[#60a5fa]", badge: "bg-[#1e3a8a]/30 text-[#8ab8ff]" }} active={active} delay={200} />
          <InsightRow icon={AlertTriangle} label="ANOMALY" tone={{ bg: "bg-[#5a4214]/50", icon: "text-[#FFB020]", badge: "bg-[#5a4214]/40 text-[#FFB020]" }} active={active} delay={380} />
        </div>
      </div>
    </ScreenChrome>
  );
}

function RecommendationsScene({ active }: { active: boolean }) {
  return (
    <ScreenChrome>
      <div className="flex h-full flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[12px] font-extrabold text-white">Recommendations</div>
            <div className="max-w-[240px] text-[7.5px] leading-snug text-[#8b93a3]">Prioritized, deterministic, evidence-backed actions.</div>
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[7px] text-[#8b93a3]">3 generated</span>
            <span className="flex items-center gap-1 rounded-full bg-[#4d8bff] px-2 py-1 text-[7px] font-bold text-white">
              <RefreshCw className="h-2 w-2" /> Regenerate
            </span>
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <InsightRow icon={TrendingUp} label="HIGH PRIORITY" tone={{ bg: "bg-[#7c2d12]/50", icon: "text-[#fb923c]", badge: "bg-[#7c2d12]/40 text-[#fb923c]" }} active={active} delay={200} />
          <InsightRow icon={Zap} label="MEDIUM PRIORITY" tone={{ bg: "bg-[#1e3a8a]/40", icon: "text-[#60a5fa]", badge: "bg-[#1e3a8a]/30 text-[#8ab8ff]" }} active={active} delay={340} />
          <InsightRow icon={Zap} label="MEDIUM PRIORITY" tone={{ bg: "bg-[#1e3a8a]/40", icon: "text-[#60a5fa]", badge: "bg-[#1e3a8a]/30 text-[#8ab8ff]" }} active={active} delay={480} />
        </div>
      </div>
    </ScreenChrome>
  );
}

function CopilotScene({ active }: { active: boolean }) {
  return (
    <ScreenChrome>
      <div className="flex h-full flex-col gap-2.5">
        <div className="flex items-start justify-between">
          <Reveal active={active} className="flex items-start gap-2">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#0d1526]">
              <Bot className="h-3 w-3 text-[#4d8bff]" />
            </div>
            <div className="max-w-[280px] text-[9px] leading-relaxed text-[#c5cbd6]">
              Hello! I am DataMind Copilot. I can query your databases, generate charts, and provide strategic insights. What would you like to know today?
            </div>
          </Reveal>
          <span className="flex shrink-0 items-center gap-1 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-1.5 py-0.5 text-[7px] font-bold text-emerald-300">
            <span className="h-1 w-1 animate-ws-pulse rounded-full bg-emerald-400" /> Connected
          </span>
        </div>
        <div className="flex-1" />
        <Reveal active={active} delay={500} className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2">
          <span className="flex-1 text-[8.5px] text-[#6b7280]">Ask DataMind to query datasets, generate charts, or predict trends…</span>
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#4d8bff]">
            <Send className="h-2.5 w-2.5 text-white" />
          </span>
        </Reveal>
        <Reveal active={active} delay={700} className="text-center text-[7px] text-[#5c6473]">
          AI can make mistakes. Consider verifying critical business metrics.
        </Reveal>
      </div>
    </ScreenChrome>
  );
}

function AnalyticsScene({ active }: { active: boolean }) {
  const navGroups = [
    { label: "OVERVIEW", items: ["Dashboard", "KPI Center", "Metrics Explorer"] },
    { label: "STATISTICAL", items: ["Statistics", "Correlation", "Regression", "Classification", "Clustering"] },
  ];
  const icons: Record<string, any> = {
    Dashboard: Activity,
    "KPI Center": Activity,
    "Metrics Explorer": LineChart,
    Statistics: Sigma,
    Correlation: Network,
    Regression: Calculator,
    Classification: GitBranch,
    Clustering: Boxes,
  };
  return (
    <ScreenChrome>
      <div className="flex h-full gap-2.5">
        <Reveal active={active} className="flex w-[92px] shrink-0 flex-col gap-2 border-r border-white/[0.06] pr-2">
          {navGroups.map((g) => (
            <div key={g.label}>
              <div className="mb-1 text-[6px] font-bold tracking-wider text-[#4d5566]">{g.label}</div>
              <div className="flex flex-col gap-1">
                {g.items.map((item) => {
                  const Icon = icons[item] ?? Activity;
                  const isActive = item === "Regression";
                  return (
                    <div
                      key={item}
                      className={`flex items-center gap-1 rounded px-1 py-0.5 text-[6.5px] ${
                        isActive ? "bg-[#4d8bff]/10 text-[#4d8bff]" : "text-[#8b93a3]"
                      }`}
                    >
                      <Icon className="h-2 w-2 shrink-0" />
                      <span className="truncate">{item}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </Reveal>
        <div className="flex flex-1 flex-col gap-2">
          <div className="grid grid-cols-4 gap-1.5">
            {[
              { label: "KPIs Monitored", value: "3", color: "text-white" },
              { label: "Recent Outliers", value: "1", color: "text-[#FFB020]" },
              { label: "Active Trends", value: "1", color: "text-white" },
              { label: "Forecast Horizons", value: "1", color: "text-white" },
            ].map((c, i) => (
              <Reveal key={c.label} active={active} delay={150 + i * 90} className="rounded-lg border border-white/10 bg-white/[0.03] p-2">
                <div className="text-[6.5px] text-[#8b93a3]">{c.label}</div>
                <div className={`text-[13px] font-bold ${c.color}`}>{c.value}</div>
              </Reveal>
            ))}
          </div>
          <Reveal active={active} delay={550} className="flex-1 rounded-lg border border-white/10 bg-white/[0.02] p-2.5">
            <div className="flex items-center gap-1 text-[8px] font-semibold text-white">
              <Clock className="h-2.5 w-2.5 text-[#34d399]" /> Time-Series Forecasts
            </div>
            <div className="mt-1.5 rounded-md border border-white/[0.06] bg-white/[0.02] p-2">
              <div className="text-[8px] font-semibold text-white">Revenue Forecast</div>
              <div className="mt-0.5 text-[7px] leading-relaxed text-[#8b93a3]">
                Model: Holt linear trend (double exponential smoothing)
                <br />
                Horizon: 3 periods
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </ScreenChrome>
  );
}

export function GuidedTourModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (open) setIndex(0);
  }, [open]);

  const next = () => {
    if (index === SCENES.length - 1) {
      onClose();
    } else {
      setIndex((i) => i + 1);
    }
  };
  const prev = () => setIndex((i) => Math.max(0, i - 1));

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center bg-black/75 backdrop-blur-sm p-6 animate-gt-fade-in"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="animate-gt-modal-in relative flex w-full max-w-[760px] flex-col overflow-hidden rounded-[28px] border border-[rgba(59,130,246,.2)] bg-[rgba(11,15,24,.97)] shadow-[0_30px_80px_-20px_rgba(0,0,0,.7)] backdrop-blur-2xl"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        {/* Progress bars */}
        <div className="flex gap-1.5 p-4 pb-0">
          {SCENES.map((_, i) => (
            <div key={i} className="h-[3px] flex-1 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-[#4d8bff]"
                style={
                  i < index
                    ? { width: "100%" }
                    : i === index
                    ? {
                        width: "100%",
                        transformOrigin: "left",
                        animation: `gtBarFill ${SCENE_DURATION_MS}ms linear forwards`,
                        animationPlayState: paused ? "paused" : "running",
                      }
                    : { width: "0%" }
                }
              />
            </div>
          ))}
        </div>

        <button
          onClick={onClose}
          className="absolute right-4 top-4 z-10 flex h-7 w-7 items-center justify-center rounded-full text-[#8b93a3] transition-all duration-150 hover:scale-110 hover:bg-white/10 hover:text-white active:scale-90"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>

        <SceneTimer key={index} active={!paused} durationMs={SCENE_DURATION_MS} onComplete={next} />

        <div className="flex flex-col gap-4 px-8 pb-8 pt-6">
          <div key={`text-${index}`} className="animate-gt-content-in">
            <div className="text-[11px] font-semibold tracking-[2px] text-[#5c6473]">{SCENES[index].eyebrow}</div>
            <h3 className="mt-1.5 text-[24px] font-extrabold tracking-tight text-white">{SCENES[index].title}</h3>
            <p className="mt-2 text-[13.5px] leading-relaxed text-[#9aa4b5]">{SCENES[index].caption}</p>
          </div>

          <div key={`visual-${index}`} className="animate-gt-content-in relative h-[280px]" style={{ animationDelay: "80ms" }}>
            <SceneVisual index={index} active={true} key={index} />
          </div>

          <div className="flex items-center justify-between">
            <button
              onClick={prev}
              disabled={index === 0}
              className="flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3.5 py-2 text-[12.5px] font-semibold text-[#c5cbd6] transition-all duration-150 hover:bg-white/10 active:scale-95 disabled:cursor-not-allowed disabled:opacity-30 disabled:active:scale-100"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              Back
            </button>
            <span className="text-[11px] font-medium text-[#5c6473] tabular-nums">
              {index + 1} / {SCENES.length}
            </span>
            <button
              onClick={next}
              className="flex items-center gap-1 rounded-full bg-gradient-to-r from-blue-600 to-[#4d8bff] px-4 py-2 text-[12.5px] font-bold text-white shadow-[0_6px_18px_rgba(37,99,235,.35)] transition-all duration-150 hover:-translate-y-0.5 hover:shadow-[0_10px_24px_rgba(37,99,235,.5)] active:scale-95 active:translate-y-0"
            >
              {index === SCENES.length - 1 ? "Done" : "Next"}
              {index < SCENES.length - 1 && <ChevronRight className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Invisible helper that fires onComplete once, driven by the same duration as
// the progress bar — kept separate from the bar's own CSS animation so pause
// (via animationPlayState) and the actual scene-advance stay in sync without
// juggling setInterval/requestAnimationFrame bookkeeping by hand.
function SceneTimer({ durationMs, active, onComplete }: { durationMs: number; active: boolean; onComplete: () => void }) {
  const firedRef = useRef(false);
  const remainingRef = useRef(durationMs);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    firedRef.current = false;
    remainingRef.current = durationMs;
    let timeoutId: any;

    const tick = () => {
      startRef.current = performance.now();
      timeoutId = setTimeout(() => {
        if (!firedRef.current) {
          firedRef.current = true;
          onComplete();
        }
      }, remainingRef.current);
    };

    if (active) tick();

    return () => {
      clearTimeout(timeoutId);
      if (active && startRef.current !== null) {
        remainingRef.current = Math.max(0, remainingRef.current - (performance.now() - startRef.current));
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  return null;
}

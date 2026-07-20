"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import dynamic from "next/dynamic";
const LazyCharts = dynamic(() => import("@/components/charts/LazyCharts"), { ssr: false });
import { Info, TrendingUp, TrendingDown, Minus, Activity, ShieldCheck, FileSearch, HelpCircle, Code, Link, Database, Network, ChevronDown } from "lucide-react";
import { ExecutiveKPIReport } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";

interface ExecutiveKPICardProps {
  kpi: ExecutiveKPIReport;
  index?: number;
}

function formatValue(value: number | null, type: string): string {
  if (value === null || value === undefined) return "N/A";
  
  const isNegative = value < 0;
  const absValue = Math.abs(value);
  const sign = isNegative ? "-" : "";

  if (type === "percent") return `${sign}${absValue.toFixed(1)}%`;
  
  if (type === "count" || type === "generic" || type === "numeric") {
    if (absValue >= 1_000_000) return `${sign}${parseFloat((absValue / 1_000_000).toFixed(1))}M`;
    if (absValue >= 1_000) return `${sign}${parseFloat((absValue / 1_000).toFixed(1))}K`;
    return `${sign}${parseFloat(absValue.toFixed(2))}`;
  }
  
  if (type === "currency") {
    if (absValue >= 1_00_00_000) return `${sign}₹${parseFloat((absValue / 1_00_00_000).toFixed(2))}Cr`;
    if (absValue >= 1_00_000) return `${sign}₹${parseFloat((absValue / 1_00_000).toFixed(2))}L`;
    if (absValue >= 1_000) return `${sign}₹${parseFloat((absValue / 1_000).toFixed(1))}K`;
    return `${sign}₹${absValue.toLocaleString('en-IN')}`;
  }
  
  return `${sign}${parseFloat(absValue.toFixed(2))}`;
}

export const ExecutiveKPICard: React.FC<ExecutiveKPICardProps> = ({ kpi, index = 0 }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [historyView, setHistoryView] = useState<"monthly" | "quarterly" | "yearly">("monthly");
  const [compareMode, setCompareMode] = useState<"default" | "previous_month" | "previous_quarter" | "previous_year" | "dataset_average" | "rolling_average">("default");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [highlightedPeriod, setHighlightedPeriod] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const getThemeColor = () => {
    switch (kpi.category) {
      case "Primary": return "text-blue-500 bg-blue-500/10 border-blue-500/20";
      case "Volume": return "text-indigo-500 bg-indigo-500/10 border-indigo-500/20";
      case "Efficiency": return "text-amber-500 bg-amber-500/10 border-amber-500/20";
      case "Health": return "text-purple-500 bg-purple-500/10 border-purple-500/20";
      default: return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
    }
  };

  const getTrendIcon = () => {
    if (kpi.trend === "up") return <TrendingUp className="w-3 h-3 text-emerald-500" />;
    if (kpi.trend === "down") return <TrendingDown className="w-3 h-3 text-rose-500" />;
    return <Minus className="w-3 h-3 text-muted-foreground" />;
  };

  const getTrendColor = () => {
    if (kpi.trend === "up") return "text-emerald-500";
    if (kpi.trend === "down") return "text-rose-500";
    return "text-muted-foreground";
  };
  
  const sparklineColor = kpi.trend === "up" ? "#10b981" : kpi.trend === "down" ? "#f43f5e" : "#8b5cf6";

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background/95 border border-border p-2 shadow-xl rounded-lg text-xs backdrop-blur-md">
          <p className="font-medium text-foreground mb-1">{payload[0].payload.name}</p>
          <p className="text-muted-foreground">
            Value: <span className="font-semibold text-foreground">{formatValue(payload[0].value, kpi.type)}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  let rawMonthly: any[] = [];
  let rawQuarterly: any[] = [];
  let rawYearly: any[] = [];

  if (Array.isArray(kpi.history)) {
    rawMonthly = kpi.history;
  } else if (kpi.history) {
    rawMonthly = kpi.history.monthly || [];
    rawQuarterly = kpi.history.quarterly || [];
    rawYearly = kpi.history.yearly || [];
  }

  // Fallback: If quarterly or yearly are missing but we have monthly data, aggregate them
  if (rawMonthly.length > 0) {
    if (rawQuarterly.length === 0) {
      const qMap: any = {};
      rawMonthly.forEach((m: any) => {
        const name = m.date || m.name || "";
        if (!name) return;
        const parts = name.split(" ");
        if (parts.length !== 2) return;
        const [month, year] = parts;
        const monthIndex = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].indexOf(month);
        if (monthIndex === -1) return;
        const quarter = Math.floor(monthIndex / 3) + 1;
        const qKey = `Q${quarter} ${year}`;
        if (!qMap[qKey]) qMap[qKey] = { name: qKey, value: 0, count: 0 };
        qMap[qKey].value += m.value;
        qMap[qKey].count += 1;
      });
      rawQuarterly = Object.values(qMap).map((q: any) => ({
        name: q.name, 
        value: kpi.aggregation === "mean" ? q.value / q.count : q.value
      }));
    }
    
    if (rawYearly.length === 0) {
      const yMap: any = {};
      rawMonthly.forEach((m: any) => {
        const name = m.date || m.name || "";
        const parts = name.split(" ");
        const year = parts.length === 2 ? parts[1] : name;
        if (!year) return;
        if (!yMap[year]) yMap[year] = { name: year, value: 0, count: 0 };
        yMap[year].value += m.value;
        yMap[year].count += 1;
      });
      rawYearly = Object.values(yMap).map((y: any) => ({
        name: y.name, 
        value: kpi.aggregation === "mean" ? y.value / y.count : y.value
      }));
    }
  }

  const normalizedHistory = {
    monthly: rawMonthly.slice(-12),
    quarterly: rawQuarterly.slice(-8),
    yearly: rawYearly.slice(-5)
  };

  const sparklineData = normalizedHistory.monthly;
  const chartData = normalizedHistory[historyView as keyof typeof normalizedHistory] || [];

  let highestPoint: any = null;
  let lowestPoint: any = null;
  let sumValues = 0;
  let peakEvent: any = null;
  let recoveryEvent: any = null;
  let declineEvent: any = null;

  if (chartData && chartData.length > 0) {
    highestPoint = chartData.reduce((prev: any, current: any) => (prev.value > current.value) ? prev : current);
    lowestPoint = chartData.reduce((prev: any, current: any) => (prev.value < current.value) ? prev : current);
    sumValues = chartData.reduce((sum: number, current: any) => sum + current.value, 0);

    peakEvent = highestPoint;
    
    let maxIncrease = -Infinity;
    let maxDecrease = Infinity;

    for (let i = 1; i < chartData.length; i++) {
      const diff = chartData[i].value - chartData[i-1].value;
      if (diff > maxIncrease) {
        maxIncrease = diff;
        recoveryEvent = { ...chartData[i], diff };
      }
      if (diff < maxDecrease) {
        maxDecrease = diff;
        declineEvent = { ...chartData[i], diff };
      }
    }
  }
  const averageValue = chartData.length > 0 ? sumValues / chartData.length : 0;

  // Dynamic Comparison Logic
  let dynPrev = kpi.previous;
  let dynPeriod = kpi.comparison_period;
  let dynDiff = kpi.difference;
  let dynPerc = kpi.percentage;

  if (compareMode !== "default") {
    let base = kpi.current;
    let computedPrev: number | null = null;
    let periodName = "";

    const mHist = normalizedHistory.monthly || [];
    const qHist = normalizedHistory.quarterly || [];
    const yHist = normalizedHistory.yearly || [];

    if (compareMode === "previous_month") {
      if (mHist.length > 1) computedPrev = mHist[mHist.length - 2].value;
      periodName = "Previous Month";
    } else if (compareMode === "previous_quarter") {
      if (qHist.length > 1) computedPrev = qHist[qHist.length - 2].value;
      periodName = "Previous Quarter";
    } else if (compareMode === "previous_year") {
      if (yHist.length > 1) computedPrev = yHist[yHist.length - 2].value;
      periodName = "Previous Year";
    } else if (compareMode === "dataset_average") {
      if (mHist.length > 0) computedPrev = mHist.reduce((s: number, a: any) => s + a.value, 0) / mHist.length;
      periodName = "Dataset Avg";
    } else if (compareMode === "rolling_average") {
      if (mHist.length > 0) {
        const last3 = mHist.slice(-3);
        computedPrev = last3.reduce((s: number, a: any) => s + a.value, 0) / last3.length;
      }
      periodName = "3-Mo Avg";
    }

    if (computedPrev !== null) {
      dynPrev = computedPrev;
      dynPeriod = periodName;
      dynDiff = base !== null ? base - computedPrev : null;
      dynPerc = computedPrev !== 0 && dynDiff !== null ? parseFloat(((dynDiff / Math.abs(computedPrev)) * 100).toFixed(1)) : 0;
    } else {
      dynPrev = null;
      dynPeriod = "N/A (" + periodName + ")";
      dynDiff = null;
      dynPerc = null;
    }
  }

  const dynTrend = dynDiff !== null ? (dynDiff > 0 ? "up" : dynDiff < 0 ? "down" : "flat") : kpi.trend;
  const dynTrendColor = dynTrend === "up" ? "text-emerald-500" : dynTrend === "down" ? "text-rose-500" : "text-muted-foreground";
  
  const getDynTrendIcon = () => {
    if (dynTrend === "up") return <TrendingUp className="w-3 h-3 text-emerald-500" />;
    if (dynTrend === "down") return <TrendingDown className="w-3 h-3 text-rose-500" />;
    return <Minus className="w-3 h-3 text-muted-foreground" />;
  };

  const CustomDot = (props: any) => {
    const { cx, cy, payload, index } = props;
    const isCurrent = index === chartData.length - 1;
    const isHighlighted = highlightedPeriod === payload.name;
    
    if (isCurrent || isHighlighted) {
      return (
        <g>
          <circle cx={cx} cy={cy} r={8} fill={sparklineColor} opacity={isHighlighted ? 0.6 : 0.3} className={isCurrent ? "animate-ping" : ""} />
          <circle cx={cx} cy={cy} r={5} fill={sparklineColor} stroke="white" strokeWidth={2} />
          <text x={cx + (isCurrent ? 4 : 0)} y={cy - 16} textAnchor={isCurrent ? "end" : "middle"} fill="white" fontSize={11} fontWeight="bold" className="drop-shadow-md">
            {payload.name} {isCurrent ? "(Current)" : (payload.name === peakEvent?.name ? "(Peak)" : payload.name === recoveryEvent?.name ? "(Recovery)" : payload.name === declineEvent?.name ? "(Decline)" : payload.name === highestPoint.name ? "(High)" : payload.name === lowestPoint.name ? "(Low)" : "")}
          </text>
        </g>
      );
    }
    return null;
  };

  const modalContent = (
    <AnimatePresence>
      {isModalOpen && (
        <div className="absolute inset-0 z-[100] flex items-center justify-center p-4 sm:p-6">
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            exit={{ opacity: 0 }}
            onClick={() => setIsModalOpen(false)}
            className="absolute inset-0 bg-background/80 backdrop-blur-sm"
          />
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative w-full max-w-4xl max-h-[80vh] overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] bg-surface/60 backdrop-blur-2xl border border-white/10 shadow-[0_8px_32px_0_rgba(0,0,0,0.5)] rounded-2xl p-6 sm:p-8"
          >
            <div className="flex items-start justify-between mb-6">
              <div>
                <span className={`text-xs uppercase font-bold tracking-wider px-2 py-1 rounded-full mb-3 inline-block border ${getThemeColor()}`}>
                  {kpi.category} KPI
                </span>
                <h2 className="text-3xl font-semibold text-foreground">{kpi.name}</h2>
              </div>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="p-2 rounded-full hover:bg-white/10 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>

            {/* Top Section: Overview & Insights */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-background/50 border border-border/50 rounded-xl p-5 relative">
                <div className="flex justify-between items-start mb-1 relative">
                  <div className="text-sm font-medium text-muted-foreground">Current Value</div>
                  <div className="relative">
                    <button 
                      onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                      className="flex items-center gap-2 text-xs bg-surface/50 border border-border/50 hover:bg-surface/80 rounded-md px-2 py-1 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      Compare: {
                        compareMode === "default" ? "Default" : 
                        compareMode === "previous_month" ? "Previous Month" :
                        compareMode === "previous_quarter" ? "Previous Quarter" :
                        compareMode === "previous_year" ? "Previous Year" :
                        compareMode === "dataset_average" ? "Dataset Average" : "3-Mo Rolling Avg"
                      }
                      <ChevronDown className="w-3 h-3 opacity-70" />
                    </button>
                    
                    <AnimatePresence>
                      {isDropdownOpen && (
                        <>
                          <div className="fixed inset-0 z-40" onClick={() => setIsDropdownOpen(false)} />
                          <motion.div 
                            initial={{ opacity: 0, y: -5, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: -5, scale: 0.95 }}
                            transition={{ duration: 0.15 }}
                            className="absolute right-0 top-full mt-1 w-44 bg-surface border border-border/60 shadow-xl rounded-lg py-1 z-50 overflow-hidden backdrop-blur-xl"
                          >
                            {[
                              { id: "default", label: "Default" },
                              { id: "previous_month", label: "Previous Month" },
                              { id: "previous_quarter", label: "Previous Quarter" },
                              { id: "previous_year", label: "Previous Year" },
                              { id: "dataset_average", label: "Dataset Average" },
                              { id: "rolling_average", label: "3-Mo Rolling Avg" },
                            ].map((item) => (
                              <button
                                key={item.id}
                                onClick={() => { setCompareMode(item.id as any); setIsDropdownOpen(false); }}
                                className={`w-full text-left px-3 py-2 text-xs transition-colors hover:bg-white/10 ${compareMode === item.id ? "text-foreground font-medium bg-white/5" : "text-muted-foreground"}`}
                              >
                                {item.label}
                              </button>
                            ))}
                          </motion.div>
                        </>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
                <div className="text-4xl font-semibold">{formatValue(kpi.current, kpi.type)}</div>
                {dynPerc !== null && dynPrev !== null ? (
                  <div className="mt-2 flex items-center gap-2">
                    <span className={`flex items-center gap-1 text-sm font-semibold ${dynTrendColor} bg-white/5 px-2 py-1 rounded`}>
                      {getDynTrendIcon()} {dynPerc > 0 ? "+" : ""}{dynPerc}%
                    </span>
                    <span className="text-sm text-muted-foreground">
                      vs {dynPeriod} ({formatValue(dynPrev, kpi.type)})
                    </span>
                  </div>
                ) : (
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">No comparison available for {dynPeriod}</span>
                  </div>
                )}
              </div>

              <div className="bg-background/50 border border-border/50 rounded-xl p-5 flex flex-col justify-center relative overflow-hidden">
                 <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                   <Activity className="w-24 h-24" />
                 </div>
                <div className="flex items-start gap-3 relative z-10">
                  <div className="p-2 bg-primary/10 rounded-lg shrink-0">
                    <Activity className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-foreground mb-1 uppercase tracking-wider text-primary">Insight</h4>
                    <p className="text-sm text-muted-foreground/90 leading-relaxed font-medium">{kpi.insight}</p>
                  </div>
                </div>
              </div>
              </div>

            {/* Historical Trend */}
            <div className="bg-background border border-border/50 rounded-xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="text-xs font-bold text-foreground uppercase tracking-wider">Historical Trend</div>
                
                <div className="flex items-center bg-surface/50 border border-border/50 rounded-lg p-1">
                  <button 
                    onClick={() => setHistoryView("monthly")}
                    className={`px-3 py-1 text-xs rounded-md transition-colors ${historyView === "monthly" ? "bg-primary text-primary-foreground font-medium" : "text-muted-foreground hover:text-foreground"}`}
                  >
                    12 Months
                  </button>
                  <button 
                    onClick={() => setHistoryView("quarterly")}
                    className={`px-3 py-1 text-xs rounded-md transition-colors ${historyView === "quarterly" ? "bg-primary text-primary-foreground font-medium" : "text-muted-foreground hover:text-foreground"}`}
                  >
                    8 Quarters
                  </button>
                  <button 
                    onClick={() => setHistoryView("yearly")}
                    className={`px-3 py-1 text-xs rounded-md transition-colors ${historyView === "yearly" ? "bg-primary text-primary-foreground font-medium" : "text-muted-foreground hover:text-foreground"}`}
                  >
                    5 Years
                  </button>
                </div>
              </div>
              
              <div className="h-[220px] w-full mb-6">
                {chartData && chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 25, right: 15, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id={`gradient-lg-${kpi.query_id}`} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={sparklineColor} stopOpacity={0.2} />
                          <stop offset="95%" stopColor={sparklineColor} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                        <XAxis dataKey="name" stroke="rgba(255,255,255,0.1)" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} tickLine={false} axisLine={false} />
                        <YAxis stroke="rgba(255,255,255,0.1)" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={(val: number) => formatValue(val, kpi.type)} />
                      <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1, strokeDasharray: '4 4' }} />
                      <Area 
                        type="monotone" 
                        dataKey="value" 
                        stroke={sparklineColor} 
                        strokeWidth={2} 
                        fillOpacity={1} 
                        fill={`url(#gradient-lg-${kpi.query_id})`}
                        dot={<CustomDot />}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center border border-dashed border-border/40 rounded-md bg-surface/20">
                    <span className="text-sm text-muted-foreground">No temporal data available for this view</span>
                  </div>
                )}
              </div>

              {chartData && chartData.length > 0 && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
                    <div 
                      onClick={() => setHighlightedPeriod(highlightedPeriod === highestPoint.name ? null : highestPoint.name)}
                      className={`bg-surface/30 border border-border/40 rounded-lg p-3 flex flex-col justify-between cursor-pointer transition-colors ${highlightedPeriod === highestPoint.name ? 'ring-2 ring-emerald-500/50 bg-emerald-500/5' : 'hover:bg-surface/60'}`}
                    >
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Highest</span>
                      <div className="flex items-end justify-between">
                        <span className="text-lg font-semibold text-foreground">{formatValue(highestPoint.value, kpi.type)}</span>
                        <span className="text-xs text-muted-foreground">{highestPoint.name}</span>
                      </div>
                    </div>
                    <div 
                      onClick={() => setHighlightedPeriod(highlightedPeriod === lowestPoint.name ? null : lowestPoint.name)}
                      className={`bg-surface/30 border border-border/40 rounded-lg p-3 flex flex-col justify-between cursor-pointer transition-colors ${highlightedPeriod === lowestPoint.name ? 'ring-2 ring-rose-500/50 bg-rose-500/5' : 'hover:bg-surface/60'}`}
                    >
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Lowest</span>
                      <div className="flex items-end justify-between">
                        <span className="text-lg font-semibold text-foreground">{formatValue(lowestPoint.value, kpi.type)}</span>
                        <span className="text-xs text-muted-foreground">{lowestPoint.name}</span>
                      </div>
                    </div>
                    <div className="bg-surface/30 border border-border/40 rounded-lg p-3 flex flex-col justify-between">
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Average</span>
                      <div className="flex items-end justify-between">
                        <span className="text-lg font-semibold text-foreground">{formatValue(averageValue, kpi.type)}</span>
                        <span className="text-xs text-muted-foreground">Overall</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-border/30">
                    <div className="text-xs font-bold text-foreground uppercase tracking-wider mb-3">Trend Events</div>
                    <div className="flex flex-wrap gap-3">
                      {recoveryEvent && recoveryEvent.diff > 0 && (
                        <div 
                          onClick={() => setHighlightedPeriod(highlightedPeriod === recoveryEvent.name ? null : recoveryEvent.name)}
                          className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors ${highlightedPeriod === recoveryEvent.name ? 'border-emerald-500/50 bg-emerald-500/10' : 'border-border/40 bg-surface/30 hover:bg-surface/60'}`}
                        >
                          <div className={`p-1.5 rounded-md ${highlightedPeriod === recoveryEvent.name ? 'bg-emerald-500/20' : 'bg-emerald-500/10'}`}>
                            <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                          </div>
                          <div className="flex flex-col">
                            <span className="text-xs font-medium text-foreground">Recovery</span>
                            <span className="text-[10px] text-muted-foreground">{recoveryEvent.name}</span>
                          </div>
                        </div>
                      )}
                      
                      {declineEvent && declineEvent.diff < 0 && (
                        <div 
                          onClick={() => setHighlightedPeriod(highlightedPeriod === declineEvent.name ? null : declineEvent.name)}
                          className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors ${highlightedPeriod === declineEvent.name ? 'border-rose-500/50 bg-rose-500/10' : 'border-border/40 bg-surface/30 hover:bg-surface/60'}`}
                        >
                          <div className={`p-1.5 rounded-md ${highlightedPeriod === declineEvent.name ? 'bg-rose-500/20' : 'bg-rose-500/10'}`}>
                            <TrendingDown className="w-3.5 h-3.5 text-rose-500" />
                          </div>
                          <div className="flex flex-col">
                            <span className="text-xs font-medium text-foreground">Decline</span>
                            <span className="text-[10px] text-muted-foreground">{declineEvent.name}</span>
                          </div>
                        </div>
                      )}

                      {peakEvent && (
                        <div 
                          onClick={() => setHighlightedPeriod(highlightedPeriod === peakEvent.name ? null : peakEvent.name)}
                          className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors ${highlightedPeriod === peakEvent.name ? 'border-blue-500/50 bg-blue-500/10' : 'border-border/40 bg-surface/30 hover:bg-surface/60'}`}
                        >
                          <div className={`p-1.5 rounded-md ${highlightedPeriod === peakEvent.name ? 'bg-blue-500/20' : 'bg-blue-500/10'}`}>
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5 text-blue-500">
                              <path fillRule="evenodd" d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.007 5.404.433c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.433 2.082-5.006z" clipRule="evenodd" />
                            </svg>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-xs font-medium text-foreground">Peak</span>
                            <span className="text-[10px] text-muted-foreground">{peakEvent.name}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="mt-5 pt-4 border-t border-border/50 flex items-center justify-between text-xs text-muted-foreground/60">
              <div className="flex items-center gap-4">
                <span>Query ID: {kpi.query_id}</span>
                <span>Data Source: <span className="font-mono">{kpi.source_column}</span></span>
              </div>
              <span>Last Refresh: {kpi.last_refresh}</span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );

  return (
    <>
      <div 
        onClick={() => setIsModalOpen(true)}
        className="group flex flex-col bg-surface/40 backdrop-blur-md border border-border/50 rounded-2xl p-5 hover:border-white/20 hover:shadow-[0_8px_30px_rgb(0,0,0,0.12)] transition-all duration-300 cursor-pointer h-[260px] relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none group-hover:bg-primary/10 transition-colors"></div>
        
        {/* Header */}
        <div className="flex items-center justify-between z-10">
          <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border ${getThemeColor()}`}>
            {kpi.category}
          </span>
          <span className="text-[10px] font-medium text-muted-foreground/60">{kpi.reporting_period}</span>
        </div>

        {/* Metric Name & Value */}
        <div className="mt-3 z-10">
          <h3 className="text-sm font-medium text-muted-foreground truncate" title={kpi.name}>{kpi.name}</h3>
          <div className="flex items-end gap-2 mt-1">
            <span className="text-3xl font-semibold tracking-tight text-foreground font-variant-numeric-tabular">
              <CountUpValue valueString={formatValue(kpi.current, kpi.type)} delayMs={index * 100} />
            </span>
          </div>
        </div>

        {/* Comparison */}
        <div className="mt-2 flex items-center gap-2 z-10">
          {kpi.percentage !== null ? (
            <div className={`flex items-center gap-1 text-[12px] font-semibold ${getTrendColor()} bg-white/5 px-1.5 py-0.5 rounded`}>
              {getTrendIcon()}
              {kpi.percentage > 0 ? "+" : ""}{kpi.percentage}%
            </div>
          ) : (
            <span className="text-[11px] text-muted-foreground/60 bg-white/5 px-1.5 py-0.5 rounded">No history</span>
          )}
          
          {kpi.difference !== null && (
            <span className="text-[11px] text-muted-foreground/70">
              {kpi.difference > 0 ? "+" : ""}{formatValue(kpi.difference, kpi.type)} vs {kpi.comparison_period}
            </span>
          )}
        </div>

        {/* Sparkline */}
        <div className="mt-auto h-[45px] w-full -mx-1 z-10">
          {sparklineData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sparklineData}>
                <defs>
                  <linearGradient id={`gradient-${kpi.query_id}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={sparklineColor} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={sparklineColor} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1, strokeDasharray: '4 4' }} />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke={sparklineColor} 
                  strokeWidth={2} 
                  fillOpacity={1} 
                  fill={`url(#gradient-${kpi.query_id})`}
                  isAnimationActive={true}
                  animationDuration={1500}
                  animationEasing="ease-in-out"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center border border-dashed border-border/40 rounded-md bg-surface/20">
              <span className="text-[10px] text-muted-foreground/40">No temporal data</span>
            </div>
          )}
        </div>
      </div>

      {/* Drill-down Modal via Portal */}
      {mounted ? createPortal(modalContent, document.getElementById('main-layout') || document.body) : null}
    </>
  );
};

function CountUpValue({ valueString, delayMs = 0 }: { valueString: string; delayMs?: number }) {
  const [display, setDisplay] = useState(() => {
    // Initial display is "0" with matching prefix/suffix
    const match = valueString.match(/^([^\d]*)([\d.,]+)([^\d]*)$/);
    if (!match) return valueString;
    const prefix = match[1];
    const numStr = match[2].replace(/,/g, '');
    const suffix = match[3];
    const target = parseFloat(numStr);
    if (isNaN(target)) return valueString;
    const decimalMatch = numStr.match(/\.(\d+)/);
    const decimals = decimalMatch ? decimalMatch[1].length : 0;
    return `${prefix}${(0).toFixed(decimals)}${suffix}`;
  });

  useEffect(() => {
    const match = valueString.match(/^([^\d]*)([\d.,]+)([^\d]*)$/);
    if (!match) {
      setDisplay(valueString);
      return;
    }
    
    const prefix = match[1];
    const numStr = match[2].replace(/,/g, '');
    const suffix = match[3];
    const target = parseFloat(numStr);
    
    if (isNaN(target)) {
      setDisplay(valueString);
      return;
    }
    
    const decimalMatch = numStr.match(/\.(\d+)/);
    const decimals = decimalMatch ? decimalMatch[1].length : 0;
    
    const duration = 1200; // Increased duration for smoother feel
    let start = 0;
    let frameId: number;
    let timeoutId: any;
    
    const step = (timestamp: number) => {
      if (!start) start = timestamp;
      const progress = Math.min(1, (timestamp - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3); // cubic ease-out
      const current = target * eased;
      
      const formattedNum = current.toFixed(decimals);
      setDisplay(`${prefix}${formattedNum}${suffix}`);
      
      if (progress < 1) {
        frameId = requestAnimationFrame(step);
      } else {
        setDisplay(valueString); 
      }
    };
    
    timeoutId = setTimeout(() => {
      frameId = requestAnimationFrame(step);
    }, delayMs);
    
    return () => {
      clearTimeout(timeoutId);
      if (frameId) cancelAnimationFrame(frameId);
    };
  }, [valueString, delayMs]);

  return <>{display}</>;
}

"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { ArrowLeft, Activity, Info, BarChart2, PieChart, ActivitySquare, Calculator, Network, Target, CheckCircle2, AlertTriangle, XCircle, Code2, Layers, Zap, ArrowUpCircle, TrendingUp } from "lucide-react";
import { formatNumber } from "@/lib/utils";
import dynamic from "next/dynamic";
const LazyCharts = dynamic(() => import("@/components/charts/LazyCharts"), { ssr: false });


interface MetricWorkspaceProps {
  metricName: string;
  onBack: () => void;
}

const TABS = [
  { id: "overview", label: "Overview", icon: Info },
  { id: "statistics", label: "Statistical Profile", icon: Calculator },
  { id: "trend", label: "Trend Analysis", icon: Activity },
  { id: "distribution", label: "Distribution", icon: BarChart2 },
  { id: "correlation", label: "Correlation Matrix", icon: Network },
  { id: "forecast", label: "Forecast", icon: Target },
  { id: "quality", label: "Data Quality", icon: CheckCircle2 },
  { id: "calculation", label: "Calculation Logic", icon: Code2 },
];

export function MetricWorkspace({ metricName, onBack }: MetricWorkspaceProps) {
  const [activeTab, setActiveTab] = useState("overview");

  const { data, isLoading, error } = useQuery({
    queryKey: ["metric_intelligence", metricName],
    queryFn: () => api.get<any>(`/api/v1/analytics/metrics/${metricName}/intelligence`),
    retry: false
  });

  if (isLoading) {
    return (
      <div className="flex flex-col h-full p-6 animate-pulse">
        <div className="flex items-center gap-4 mb-8">
          <div className="w-10 h-10 bg-surface rounded-md"></div>
          <div className="w-64 h-8 bg-surface rounded-md"></div>
        </div>
        <div className="flex gap-4 mb-6">
          {TABS.map(t => <div key={t.id} className="w-24 h-8 bg-surface rounded-md"></div>)}
        </div>
        <div className="w-full h-96 bg-surface rounded-md"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex flex-col h-full p-6">
        <button onClick={onBack} className="flex items-center text-muted-foreground hover:text-foreground w-fit mb-6">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Catalog
        </button>
        <div className="p-6 bg-red-500/10 border border-red-500/20 text-red-500 rounded-md">
          Failed to load intelligence for {metricName}.
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-background text-foreground">
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-6 border-b border-border/40">
        <div className="flex items-center gap-4">
          <button 
            onClick={onBack} 
            className="p-2 rounded-md border border-border/50 hover:bg-surface transition-colors"
          >
            <ArrowLeft className="w-4 h-4 text-muted-foreground" />
          </button>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{data?.overview?.name || metricName}</h1>
            <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-sm bg-primary/10 text-primary text-xs font-medium">
                {data?.overview?.category || "Metric"}
              </span>
              <span>•</span>
              <span>{data?.overview?.aggregation || "SUM"} Aggregation</span>
              <span>•</span>
              <span className={(data?.overview?.health || 0) > 80 ? "text-green-500" : "text-amber-500"}>
                {data?.overview?.health || 0}% Health
              </span>
              <div className="relative group ml-1 flex items-center cursor-help">
                <Info className="w-3.5 h-3.5 opacity-60 hover:opacity-100 transition-opacity" />
                <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 hidden group-hover:flex flex-col bg-[#111] border border-white/10 shadow-2xl rounded-lg p-4 text-xs z-50 min-w-[320px] text-white">
                  
                  <div className="mb-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-emerald-400">Health Score</span>
                      <span className="font-mono">{data?.overview?.health || 0}/100</span>
                    </div>
                    <div className="text-[10px] text-gray-400 font-mono mb-1">{data?.overview?.healthBreakdown?.formula || '100 - missing% - (outlier%*0.5) - (dup%*0.25)'}</div>
                  </div>

                  <div className="h-px bg-white/10 my-2" />

                  <div className="mb-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-blue-400">Confidence Level</span>
                      <span className="font-mono">{data?.overview?.confidence || 0}/100</span>
                    </div>
                    {data?.overview?.confidenceBreakdown && Object.entries(data.overview.confidenceBreakdown).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-[10px] text-gray-400 mt-1">
                        <span>{k.replace(/([A-Z])/g, ' $1').trim()}</span>
                        <span className="font-mono text-white/70">{String(v).split(':')[0]}</span>
                      </div>
                    ))}
                  </div>

                  <div className="h-px bg-white/10 my-2" />

                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-purple-400">Business Importance</span>
                      <span className="font-mono">{data?.overview?.importance || 0}/100</span>
                    </div>
                    {data?.overview?.importanceBreakdown && Object.entries(data.overview.importanceBreakdown).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-[10px] text-gray-400 mt-1">
                        <span>{k.replace(/([A-Z])/g, ' $1').trim()}</span>
                        <span className="font-mono text-white/70">{String(v).split(':')[0]}</span>
                      </div>
                    ))}
                  </div>

                </div>
              </div>
            </p>
          </div>
        </div>
        
        <div className="flex items-end gap-3 flex-col text-right">
          <span className="text-sm text-muted-foreground uppercase tracking-wider font-semibold">Current Value</span>
          <span className="text-3xl font-mono font-bold tracking-tight">
            {formatNumber(data?.overview?.currentValue || 0)}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="px-8 pt-4 border-b border-border/40 overflow-x-auto">
        <div className="flex gap-6 min-w-max">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 pb-3 text-sm font-medium transition-colors relative ${
                activeTab === tab.id ? "text-primary" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
              {activeTab === tab.id && (
                <div className="absolute bottom-[-1px] left-0 w-full h-0.5 bg-primary rounded-t-full" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-8 bg-gradient-to-b from-background to-muted/20 dark:from-[#050505] dark:to-[#0a0a0a] relative">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="max-w-5xl mx-auto relative z-10">
          {activeTab === "overview" && <OverviewTab data={data} />}
          {activeTab === "statistics" && <StatisticsTab data={data.statistics} />}
          {activeTab === "trend" && <TrendTab data={data.trend} />}
          {activeTab === "distribution" && <DistributionTab data={data.distribution} />}
          {activeTab === "correlation" && <CorrelationTab data={data.correlation} />}
          {activeTab === "forecast" && <ForecastTab data={data.forecast} />}
          {activeTab === "quality" && <QualityTab data={data.quality} />}
          {activeTab === "calculation" && <CalculationTab data={data.calculation} />}
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------
// TAB COMPONENTS
// ----------------------------------------------------

function Card({ title, children, className = "" }: { title?: string, children: React.ReactNode, className?: string }) {
  return (
    <div className={`relative overflow-hidden bg-white/60 dark:bg-[#111]/60 backdrop-blur-xl border border-border/40 rounded-2xl p-6 shadow-xl dark:shadow-black/50 transition-all duration-300 ${className}`}>
      <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-white/0 dark:from-white/5 dark:to-transparent pointer-events-none" />
      {title && (
        <div className="flex items-center gap-2 mb-6 relative z-10">
          <div className="h-4 w-1 bg-gradient-to-b from-primary to-primary/30 rounded-full" />
          <h3 className="text-xs font-bold tracking-[0.2em] uppercase text-foreground/70">{title}</h3>
        </div>
      )}
      <div className="relative z-10">{children}</div>
    </div>
  );
}

function StatBox({ label, value, highlight = false }: { label: React.ReactNode, value: any, highlight?: boolean }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-widest flex items-center gap-1.5">{label}</span>
      <span className={`text-2xl font-bold tracking-tight ${highlight ? 'bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-500' : 'text-foreground'}`}>
        {typeof value === 'number' ? formatNumber(value) : value || 'N/A'}
      </span>
    </div>
  );
}

function OverviewTab({ data }: { data: any }) {
  return (
    <div className="space-y-6">
      <Card title="Key Findings">
        <ul className="space-y-3">
          {Array.isArray(data?.analystNotes) && data.analystNotes.map((note: string, idx: number) => (
            <li key={idx} className="flex items-start gap-3 text-sm bg-surface/30 p-3 rounded-md border border-border/40">
              <div className="bg-primary/10 p-1 rounded-full shrink-0">
                <CheckCircle2 className="w-4 h-4 text-primary" />
              </div>
              <span className="text-foreground leading-relaxed mt-0.5">{note}</span>
            </li>
          ))}
        </ul>
      </Card>
      
      <div className="flex gap-6">
        <Card className="w-64">
          <StatBox label="Coverage" value={`${data?.overview?.coverage || 0}%`} />
        </Card>
      </div>

      <Card title="Tags">
        <div className="flex flex-wrap gap-2">
          {Array.isArray(data?.overview?.tags) && data.overview.tags.map((t: string) => (
            <span key={t} className="px-3 py-1 bg-surface border border-border/50 rounded-full text-xs font-medium">
              {t}
            </span>
          ))}
          {(!data?.overview?.tags || data.overview.tags.length === 0) && <span className="text-sm text-muted-foreground">No tags</span>}
        </div>
      </Card>
    </div>
  );
}

function StatisticsTab({ data }: { data: any }) {
  const range = (typeof data.max === 'number' && typeof data.min === 'number') 
    ? (data.max - data.min) 
    : "N/A";

  return (
    <div className="space-y-6">
      <Card title="Overview">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
          <StatBox label="Count" value={data.count} />
          <StatBox label="Sum" value={data.sum} />
          <StatBox label="Min" value={data.min} />
          <StatBox label="Max" value={data.max} />
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Central Tendency">
          <div className="flex flex-col gap-6">
            <StatBox label="Mean" value={data.mean} />
            <StatBox label="Median" value={data.median} />
            <StatBox label="Mode" value={data.mode} />
          </div>
        </Card>

        <Card title="Spread">
          <div className="flex flex-col gap-6">
            <StatBox label="Std Dev" value={data.std_dev} />
            <StatBox label="Variance" value={data.variance} />
            <StatBox label="Coeff Var (CV)" value={data.cv} />
            <StatBox label="Range" value={range} />
            <StatBox label="IQR" value={data.iqr} />
          </div>
        </Card>

        <Card title="Percentiles">
          <div className="flex flex-col gap-6">
            <StatBox label="Q1 (25th)" value={data.q1} />
            <StatBox label="Q3 (75th)" value={data.q3} />
            <StatBox label="95th Pct" value={data.p95} />
            <StatBox label="99th Pct" value={data.p99} />
          </div>
        </Card>
      </div>
    </div>
  );
}

function TrendTab({ data }: { data: any }) {
  const [zoomTarget, setZoomTarget] = useState<string | null>(null);

  if (!data?.data || !Array.isArray(data.data) || data.data.length === 0) {
    return <Card>No time series data available for this metric.</Card>;
  }
  
  const renderLabel = (props: any, text: string, color: string) => {
    const { x, y } = props;
    return (
      <text x={x} y={y - 15} fill={color} fontSize={11} fontWeight="bold" textAnchor="middle" className="drop-shadow-md">
        {text}
      </text>
    );
  };
  
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="group relative rounded-2xl transition-all duration-500 hover:-translate-y-1 hover:shadow-2xl hover:shadow-primary/20">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 rounded-2xl transition-opacity duration-500" />
          <Card className="h-full border-primary/10">
            <StatBox label={<><TrendingUp className="w-3.5 h-3.5" /> Trend Strength (R²)</>} value={typeof data.r2 === 'number' ? data.r2.toFixed(2) : data.r2} highlight />
          </Card>
        </div>

        <div 
          className="group relative cursor-pointer rounded-2xl transition-all duration-500 hover:-translate-y-1 hover:shadow-2xl hover:shadow-amber-500/20"
          onClick={() => setZoomTarget(zoomTarget === data.peak?.period ? null : data.peak?.period)}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 rounded-2xl transition-opacity duration-500" />
          <Card className={`h-full transition-colors duration-500 ${zoomTarget === data.peak?.period ? "border-amber-500/50 bg-amber-500/5" : "border-amber-500/10"}`}>
            <StatBox label={<><Zap className="w-3.5 h-3.5 text-amber-500" /> Peak Period</>} value={data.peak?.period || 'N/A'} />
          </Card>
        </div>

        <div 
          className="group relative cursor-pointer rounded-2xl transition-all duration-500 hover:-translate-y-1 hover:shadow-2xl hover:shadow-emerald-500/20"
          onClick={() => setZoomTarget(zoomTarget === data.recovery?.period ? null : data.recovery?.period)}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 rounded-2xl transition-opacity duration-500" />
          <Card className={`h-full transition-colors duration-500 ${zoomTarget === data.recovery?.period ? "border-emerald-500/50 bg-emerald-500/5" : "border-emerald-500/10"}`}>
            <StatBox label={<><ArrowUpCircle className="w-3.5 h-3.5 text-emerald-500" /> Highest Recovery</>} value={data.recovery?.period || 'N/A'} />
          </Card>
        </div>
      </div>
      
      <Card title="Trend Analysis" className="mt-2">
        <div className="h-[400px] w-full mt-6">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.data} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis dataKey="period" stroke="#888" fontSize={11} tickLine={false} axisLine={false} dy={10} />
              <YAxis stroke="#888" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(val) => formatNumber(val)} dx={-10} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', boxShadow: '0 10px 30px -10px rgba(0,0,0,0.5)', padding: '12px 16px' }}
                itemStyle={{ color: '#fff', fontWeight: 600 }}
                formatter={(val: number) => [formatNumber(val), "Value"]}
                labelStyle={{ color: '#9ca3af', marginBottom: '4px', fontSize: '12px' }}
              />
              {zoomTarget && (
                <ReferenceArea 
                  x1={zoomTarget} 
                  x2={zoomTarget} 
                  strokeOpacity={0.3} 
                  fill="rgba(139,92,246,0.15)" 
                  stroke="rgba(139,92,246,0.5)" 
                />
              )}
              {data.peak?.period && (
                <ReferenceDot x={data.peak.period} y={data.peak.value} r={6} fill="#fbbf24" stroke="#000" strokeWidth={2} label={(props: any) => renderLabel(props, "PEAK", "#fbbf24")} />
              )}
              {data.recovery?.period && (
                <ReferenceDot x={data.recovery.period} y={data.data.find((d: any) => d.period === data.recovery.period)?.value} r={6} fill="#10b981" stroke="#000" strokeWidth={2} label={(props: any) => renderLabel(props, "RECOVERY", "#10b981")} />
              )}
              {data.decline?.period && (
                <ReferenceDot x={data.decline.period} y={data.data.find((d: any) => d.period === data.decline.period)?.value} r={6} fill="#ef4444" stroke="#000" strokeWidth={2} label={(props: any) => renderLabel(props, "DECLINE", "#ef4444")} />
              )}
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="url(#colorValue)" 
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#colorValue)"
                activeDot={{ r: 8, stroke: '#fff', strokeWidth: 2 }} 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}

function DistributionTab({ data }: { data: any }) {
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-3 gap-6">
        <Card>
          <StatBox label="Distribution Type" value={data.type} />
        </Card>
        <Card>
          <StatBox label="Skewness" value={data.skewness} />
        </Card>
        <Card>
          <StatBox label="Kurtosis" value={data.kurtosis} />
        </Card>
      </div>
      
      <Card title="Histogram">
        <div className="h-80 w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data?.histogram || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
              <XAxis dataKey="bin" stroke="#888" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                contentStyle={{ backgroundColor: '#111', border: '1px solid #333', borderRadius: '6px' }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-8 pt-6 border-t border-border/40">
          <div className="flex items-center justify-between gap-4">
            <div className={`flex-1 p-3 rounded-lg text-center text-sm font-medium transition-colors ${data?.type?.includes('Normal') ? 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/30' : 'bg-surface/50 text-muted-foreground border border-border/50'}`}>
              Normally Distributed
            </div>
            <div className={`flex-1 p-3 rounded-lg text-center text-sm font-medium transition-colors ${data?.type?.includes('Moderately') ? 'bg-amber-500/20 text-amber-500 border border-amber-500/30' : 'bg-surface/50 text-muted-foreground border border-border/50'}`}>
              Moderately Skewed
            </div>
            <div className={`flex-1 p-3 rounded-lg text-center text-sm font-medium transition-colors ${data?.type?.includes('Highly') ? 'bg-rose-500/20 text-rose-500 border border-rose-500/30' : 'bg-surface/50 text-muted-foreground border border-border/50'}`}>
              Highly Skewed
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

function CorrelationTab({ data }: { data: any[] }) {
  if (!Array.isArray(data) || data.length === 0) {
    return <Card>No strong correlations detected or insufficient data.</Card>;
  }
  
  return (
    <Card title="Top Correlated Metrics">
      <div className="overflow-x-auto mt-4">
        <table className="w-full text-sm text-left">
          <thead className="text-xs uppercase text-muted-foreground border-b border-border/50">
            <tr>
              <th className="py-3 font-semibold">Metric</th>
              <th className="py-3 font-semibold text-right">Coefficient</th>
              <th className="py-3 font-semibold">Relationship</th>
              <th className="py-3 font-semibold">Strength</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/20">
            {data.map((c, i) => (
              <tr key={i} className="hover:bg-surface/30">
                <td className="py-3 font-medium">{c.metric}</td>
                <td className="py-3 font-mono text-right">{c.coefficient.toFixed(3)}</td>
                <td className="py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${c.type === 'Positive' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                    {c.type}
                  </span>
                </td>
                <td className="py-3 text-muted-foreground">{c.strength}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function ForecastTab({ data }: { data: any[] }) {
  if (!Array.isArray(data) || data.length === 0) {
    return <Card>Forecast unavailable because no temporal dimension exists.</Card>;
  }
  
  return (
    <Card title="Linear Projection (Next 3 Periods)">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-4">
        {data.map((f, i) => (
          <div key={i} className="flex flex-col p-4 border border-border/50 rounded bg-surface/20">
            <span className="text-xs text-muted-foreground uppercase">{f.period}</span>
            <span className="text-xl font-mono font-medium mt-1">{formatNumber(f.forecast)}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

function QualityTab({ data }: { data: any }) {
  return (
    <div className="flex flex-col gap-6">
      <Card>
        <div className="flex items-center gap-4 mb-4">
          <div className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${
            data.badge === 'Excellent' ? 'bg-green-500/20 text-green-500' : 
            data.badge === 'Good' ? 'bg-blue-500/20 text-blue-500' : 
            'bg-amber-500/20 text-amber-500'
          }`}>
            {data.badge === 'Excellent' ? <CheckCircle2 className="w-6 h-6" /> : 
             data.badge === 'Good' ? <Info className="w-6 h-6" /> : 
             <AlertTriangle className="w-6 h-6" />}
          </div>
          <div>
            <h3 className="text-lg font-medium">{data.badge} Quality</h3>
            <p className="text-sm text-muted-foreground">Health Score: {data.healthScore}/100</p>
          </div>
        </div>
        <div className="p-3 bg-surface/30 rounded-md border border-border/40 text-xs">
           <span className="font-semibold text-muted-foreground uppercase tracking-wider mb-2 block">Deterministic Formula</span>
           <code className="text-emerald-500 bg-emerald-500/10 px-2 py-1.5 rounded font-mono shadow-sm">
             Health = 100 - missing% - (outlier% * 0.5) - (duplicate% * 0.25)
           </code>
        </div>
      </Card>
      
      <Card title="Quality Metrics">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <StatBox label="Missing" value={`${typeof data.missingPct === 'number' ? data.missingPct.toFixed(1) : data.missingPct}%`} />
          <StatBox label="Duplicates" value={`${typeof data.duplicatePct === 'number' ? data.duplicatePct.toFixed(1) : data.duplicatePct}%`} />
          <StatBox label="Unique" value={`${typeof data.uniquePct === 'number' ? data.uniquePct.toFixed(1) : data.uniquePct}%`} />
          <StatBox label="Outliers" value={`${typeof data.outliersPct === 'number' ? data.outliersPct.toFixed(2) : data.outliersPct}%`} />
        </div>
      </Card>
    </div>
  );
}

function CalculationTab({ data }: { data: any }) {
  return (
    <div className="flex flex-col gap-6">
      <Card title="Logic Definitions">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h4 className="text-xs uppercase text-muted-foreground font-semibold mb-2">Python Expression</h4>
            <div className="p-3 bg-[#1e1e1e] border border-[#333] rounded-md font-mono text-sm text-[#d4d4d4]">
              {data.python}
            </div>
          </div>
          <div>
            <h4 className="text-xs uppercase text-muted-foreground font-semibold mb-2">Equivalent SQL</h4>
            <div className="p-3 bg-[#1e1e1e] border border-[#333] rounded-md font-mono text-sm text-[#569cd6]">
              {data.sql}
            </div>
          </div>
        </div>
      </Card>
      
      <Card title="Execution Metadata">
        <div className="grid grid-cols-3 gap-6">
          <StatBox label="Formula" value={data.formula} />
          <StatBox label="Rows Used" value={data.rowsUsed} />
          <StatBox label="Missing Removed" value={data.missingRemoved} />
        </div>
      </Card>
    </div>
  );
}

function RelationshipsTab({ data }: { data: string[] }) {
  return (
    <Card title="Used In">
      <ul className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-4">
        {Array.isArray(data) && data.map((r, i) => (
          <li key={i} className="flex items-center gap-2 p-3 border border-border/40 rounded bg-surface/20 text-sm font-medium">
            <CheckCircle2 className="w-4 h-4 text-green-500" />
            {r}
          </li>
        ))}
      </ul>
    </Card>
  );
}

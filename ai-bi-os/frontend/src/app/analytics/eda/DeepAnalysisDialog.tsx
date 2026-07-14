"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { formatNumber } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from "recharts";
import { Loader2 } from "lucide-react";

interface DeepAnalysisDialogProps {
  column: string | null;
  onClose: () => void;
}

export function DeepAnalysisDialog({ column, onClose }: DeepAnalysisDialogProps) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['edaColumn', column],
    queryFn: () => column ? analyticsApi.edaColumn(column) : null,
    enabled: !!column,
  });

  return (
    <Dialog open={!!column} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-[95vw] sm:max-w-4xl md:max-w-5xl lg:max-w-6xl bg-surface/95 border-border/50 backdrop-blur-xl max-h-[90vh] overflow-y-auto p-6 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        <DialogHeader>
          <DialogTitle className="text-2xl font-semibold flex items-center gap-3 tracking-tight">
            <span className="text-foreground/90">Column Analysis</span>
            <div className="flex items-center px-3 py-1 rounded-lg bg-white/[0.06] border border-white/[0.1] shadow-sm">
              <span className="text-sm font-mono text-white/90 font-medium tracking-wide">{column}</span>
            </div>
          </DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center h-80">
            <Loader2 className="w-10 h-10 animate-spin text-primary" />
          </div>
        ) : isError || !data ? (
          <div className="flex flex-col items-center justify-center h-80 text-red-400 gap-3 bg-red-500/10 rounded-xl border border-red-500/20">
            <span className="text-lg font-medium">Failed to load deep analysis.</span>
            {error && <span className="text-sm opacity-80 max-w-lg text-center overflow-auto max-h-32 font-mono bg-black/40 p-3 rounded-md">{(error as any).message || String(error)}</span>}
          </div>
        ) : (
          <div className="flex flex-col gap-8 mt-6">
            {/* Chart Area */}
            <div className="h-[450px] w-full bg-slate-900/40 rounded-2xl p-6 border border-white/5 shadow-2xl relative overflow-hidden">
              {/* Subtle background glow */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] h-[80%] bg-blue-500/10 blur-[100px] pointer-events-none rounded-full" />
              
              <ResponsiveContainer width="100%" height="100%" className="relative z-10">
                <BarChart
                  data={data.type === "numeric" ? data.histogram : data.frequencies}
                  margin={{ top: 20, right: 20, left: 0, bottom: 20 }}
                >
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ffffff" stopOpacity={0.8} />
                      <stop offset="100%" stopColor="#ffffff" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis 
                    dataKey={data.type === "numeric" ? "bin_start" : "value"} 
                    stroke="rgba(255,255,255,0.4)" 
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    tickMargin={12} 
                    minTickGap={30}
                    tickFormatter={(val) => {
                      if (data.type === "numeric") return formatNumber(val);
                      if (typeof val !== "string") return String(val);
                      return val.length > 15 ? val.substring(0, 13) + "..." : val;
                    }}
                  />
                  <YAxis 
                    stroke="rgba(255,255,255,0.4)" 
                    fontSize={11} 
                    tickLine={false} 
                    axisLine={false} 
                    tickFormatter={(val) => val >= 1000 ? `${(val / 1000).toFixed(1)}k` : val}
                  />
                  <RechartsTooltip 
                    cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                    contentStyle={{ 
                      backgroundColor: 'rgba(20, 25, 35, 0.7)', 
                      backdropFilter: 'blur(20px)',
                      WebkitBackdropFilter: 'blur(20px)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '16px', 
                      padding: '14px 18px',
                      boxShadow: '0 20px 40px -10px rgba(0,0,0,0.5)',
                    }}
                    itemStyle={{ color: '#fff', fontWeight: 600, fontSize: '15px', padding: '0' }}
                    labelStyle={{ color: 'rgba(255,255,255,0.6)', marginBottom: '6px', fontSize: '12px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}
                    formatter={(val: number) => [formatNumber(val), "Count"]}
                    labelFormatter={(label) => data.type === "numeric" ? `Bin: ${formatNumber(Number(label))}` : `${label}`}
                  />
                  <Bar 
                    dataKey="count" 
                    fill="url(#colorCount)" 
                    radius={[4, 4, 0, 0]}
                    maxBarSize={40}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {Object.entries(data.stats).map(([k, v]) => (
                <div key={k} className="bg-white/[0.03] hover:bg-white/[0.05] transition-colors border border-white/[0.08] rounded-xl p-5 flex flex-col gap-2 shadow-sm">
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wider font-bold">
                    {k}
                  </span>
                  <span className="font-mono text-lg text-foreground font-semibold">
                    {typeof v === 'number' ? formatNumber(v) : (v as string)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

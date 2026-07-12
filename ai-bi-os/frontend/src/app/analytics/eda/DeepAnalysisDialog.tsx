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
          <DialogTitle className="text-2xl font-bold flex items-center gap-2">
            Analysis for <span className="text-primary">`{column}`</span>
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
                  margin={{ top: 20, right: 20, left: -10, bottom: 90 }}
                >
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#60a5fa" stopOpacity={1} />
                      <stop offset="100%" stopColor="#2563eb" stopOpacity={0.4} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                  <XAxis 
                    dataKey={data.type === "numeric" ? "bin_start" : "value"} 
                    stroke="#ffffff50" 
                    fontSize={12}
                    tickMargin={16} 
                    tickFormatter={(val) => {
                      if (data.type === "numeric") return formatNumber(val);
                      if (typeof val !== "string") return String(val);
                      return val.length > 20 ? val.substring(0,18)+"..." : val;
                    }}
                    angle={data.type === "categorical" ? -45 : 0}
                    textAnchor={data.type === "categorical" ? "end" : "middle"}
                  />
                  <YAxis stroke="#ffffff50" fontSize={12} tickLine={false} axisLine={false} />
                  <RechartsTooltip 
                    cursor={{fill: '#ffffff0a'}}
                    contentStyle={{ 
                      backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                      backdropFilter: 'blur(12px)',
                      borderColor: 'rgba(255, 255, 255, 0.1)', 
                      borderRadius: '12px', 
                      padding: '12px 16px',
                      boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)'
                    }}
                    itemStyle={{ color: '#e0f2fe', fontWeight: 600, fontSize: '15px' }}
                    labelStyle={{ color: '#94a3b8', marginBottom: '6px', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.5px' }}
                    formatter={(val: number) => [formatNumber(val), "Count"]}
                    labelFormatter={(label) => data.type === "numeric" ? `Bin: ${formatNumber(Number(label))}` : `${label}`}
                  />
                  <Bar 
                    dataKey="count" 
                    fill="url(#colorCount)" 
                    radius={[6, 6, 0, 0]}
                    barSize={data.type === "numeric" ? undefined : 32}
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

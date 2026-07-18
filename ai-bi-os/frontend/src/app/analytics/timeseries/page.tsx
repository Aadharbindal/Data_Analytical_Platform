"use client";

import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { Clock, ChevronDown } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { motion } from "framer-motion";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber } from "@/lib/utils";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";

export default function TimeSeriesPage() {
  const { data: statsData } = useQuery({
    queryKey: ['statistics'],
    queryFn: () => analyticsApi.statistics()
  });

  const [metric, setMetric] = useState<string>("");

  useEffect(() => {
    if (statsData?.stats?.length > 0 && !metric) {
      setMetric(statsData.stats[0].column);
    }
  }, [statsData, metric]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['timeseries', metric],
    queryFn: () => analyticsApi.timeseries(metric),
    enabled: !!metric
  });

  const toolbar = statsData?.stats && statsData.stats.length > 0 && (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-1.5 bg-surface border border-border text-xs font-medium text-foreground rounded-lg px-3 py-1.5 outline-none hover:bg-white/5 transition-colors focus:ring-2 focus:ring-primary/30 shadow-sm cursor-pointer">
        {metric || "Select Metric"}
        <ChevronDown className="h-3 w-3 text-muted-foreground ml-1 shrink-0" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48 max-h-[300px] overflow-y-auto">
        {statsData.stats.map((s: any) => (
          <DropdownMenuItem 
            key={s.column} 
            onClick={() => setMetric(s.column)}
            className="text-xs cursor-pointer"
          >
            {s.column}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );

  const [timeRange, setTimeRange] = useState<"1Y" | "3Y" | "ALL">("ALL");

  const filteredData = React.useMemo(() => {
    if (!data?.timeseries) return [];
    if (timeRange === "ALL") return data.timeseries;
    const cutoff = new Date();
    cutoff.setFullYear(cutoff.getFullYear() - (timeRange === "1Y" ? 1 : 3));
    return data.timeseries.filter((d: any) => new Date(d.date) >= cutoff);
  }, [data, timeRange]);

  const stats = React.useMemo(() => {
    if (!filteredData || filteredData.length === 0) return null;
    const vals = filteredData.map((d: any) => d.value);
    const peak = Math.max(...vals);
    const average = vals.reduce((a: number, b: number) => a + b, 0) / vals.length;
    const latest = vals[vals.length - 1];
    const previous = vals[vals.length - 2] || latest;
    const trend = previous ? ((latest - previous) / previous) * 100 : 0;
    
    return { peak, average, latest, trend, window: filteredData.length };
  }, [filteredData]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#0b1220] border border-white/[0.05] p-3.5 px-4 rounded-[14px] shadow-2xl flex flex-col gap-1.5 items-start">
          <span className="text-[12px] text-muted-foreground/80 font-mono tracking-wide">{label}</span>
          <span className="text-[18px] font-bold text-white font-mono tracking-tight">{metric.toLowerCase().includes("amount") ? "₹" : ""}{formatNumber(payload[0].value)}</span>
        </div>
      );
    }
    return null;
  };

  return (
    <StudioPage title="Time Series Intelligence" isLoading={isLoading && !data} toolbar={toolbar}>
      {isError ? (
        <ErrorState />
      ) : !data || !data.timeseries || data.timeseries.length === 0 ? (
        <div className="text-muted-foreground text-sm">
          No Time Series data found for the selected metric. Make sure your dataset has a date column.
        </div>
      ) : (
        <motion.div 
          initial={{ opacity: 0, filter: 'blur(4px)' }}
          animate={{ opacity: 1, filter: 'blur(0px)' }}
          transition={{ duration: 0.5 }}
          className="flex flex-col gap-6 h-full"
        >
          <div className="bg-[#0b1220] border border-white/[0.05] rounded-[24px] p-8 flex flex-col gap-2 shadow-2xl relative overflow-hidden">
            
            {/* Top Section */}
            <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-6 relative z-10">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-[6px] h-[6px] rounded-full bg-[#3b82f6] shadow-[0_0_8px_rgba(59,130,246,0.8)]"></div>
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Overview</span>
                </div>
                <h2 className="text-3xl font-bold text-white mb-1.5 tracking-tight capitalize">{metric} over time</h2>
                <p className="text-[13px] text-muted-foreground/70">
                  Monthly transaction volume &bull; {filteredData[0]?.date} &ndash; {filteredData[filteredData.length - 1]?.date}
                </p>
              </div>
              
              {stats && (
                <div className="flex flex-col items-end gap-4">
                  <div className="flex bg-[#131b2c] rounded-[8px] p-1 border border-white/[0.05]">
                    {(['1Y', '3Y', 'ALL'] as const).map(t => (
                      <button 
                        key={t}
                        onClick={() => setTimeRange(t)}
                        className={`px-4 py-1.5 text-[11px] font-bold rounded-[6px] transition-all tracking-wider ${timeRange === t ? 'bg-[#1e293b] text-white shadow-sm' : 'text-muted-foreground hover:text-white'}`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Stats Row */}
            {stats && (
              <div className="flex gap-8 items-center mt-2 mb-6 relative z-10">
                <div className="flex flex-col gap-1.5">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Peak</span>
                  <span className="text-xl font-medium text-white">{metric.toLowerCase().includes("amount") ? "₹" : ""}{formatNumber(stats.peak)}</span>
                </div>
                <div className="w-[1px] h-8 bg-white/[0.08]"></div>
                <div className="flex flex-col gap-1.5">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Average</span>
                  <span className="text-xl font-medium text-white">{metric.toLowerCase().includes("amount") ? "₹" : ""}{formatNumber(stats.average)}</span>
                </div>
                <div className="w-[1px] h-8 bg-white/[0.08]"></div>
                <div className="flex flex-col gap-1.5">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Window</span>
                  <span className="text-xl font-medium text-white font-mono">{stats.window} <span className="text-[14px] text-muted-foreground">mo</span></span>
                </div>
              </div>
            )}
            
            {/* Chart Area */}
            <div className="h-[320px] w-full mt-2 -ml-2 -mb-2 relative z-10">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={filteredData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                  <XAxis dataKey="date" hide />
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Tooltip 
                    content={<CustomTooltip />} 
                    cursor={{ stroke: 'rgba(255,255,255,0.15)', strokeWidth: 1, strokeDasharray: '4 4' }} 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#3b82f6" 
                    strokeWidth={2.5} 
                    fill="url(#colorValue)" 
                    activeDot={{ r: 4, fill: '#0b1220', stroke: '#3b82f6', strokeWidth: 2 }} 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.div>
      )}
    </StudioPage>
  );
}

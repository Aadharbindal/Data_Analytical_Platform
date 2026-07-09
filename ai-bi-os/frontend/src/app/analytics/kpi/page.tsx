"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { Activity, AlertCircle, Info } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber, formatPercent } from "@/lib/utils";
import { AreaChart, Area, ResponsiveContainer } from "recharts";

function Sparkline({ data, trend }: { data?: any[], trend?: number }) {
  if (!data || data.length === 0) {
    return <div className="h-10 w-full flex items-center bg-white/[0.02] rounded-md"><span className="text-[10px] text-muted-foreground/50 mx-auto">No history</span></div>;
  }
  
  const isUp = (trend || 0) >= 0;
  const color = isUp ? "#10b981" : "#f43f5e";
  
  return (
    <div className="h-10 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id={`sparkline-${isUp ? 'up' : 'down'}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke={color} 
            strokeWidth={1.5} 
            fillOpacity={1} 
            fill={`url(#sparkline-${isUp ? 'up' : 'down'})`}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function KPICenter() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['kpiCenter'],
    queryFn: () => analyticsApi.kpiCenter()
  });

  return (
    <StudioPage title="KPI Center" isLoading={isLoading}>
      {isError ? (
        <ErrorState />
      ) : !data ? (
        <div className="text-muted-foreground text-sm">No KPI data found.</div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {data.available_kpis?.map((kpi: any) => (
              <div 
                key={kpi.name} 
                className="glass-card rounded-xl p-4 flex flex-col justify-between h-[140px] hover:border-white/20 hover:-translate-y-[1px] transition-all duration-150"
              >
                {/* Row 1: Name + Trend */}
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[13px] font-medium text-muted-foreground truncate" title={kpi.name}>
                    {kpi.name}
                  </span>
                  {kpi.trend !== null && kpi.trend !== undefined && (
                    <span className={`text-[11px] px-1.5 py-0.5 rounded font-medium shrink-0 ${
                      kpi.trend > 0 ? "bg-emerald-500/10 text-emerald-500" : 
                      kpi.trend < 0 ? "bg-rose-500/10 text-rose-500" : 
                      "bg-muted/50 text-muted-foreground"
                    }`}>
                      {formatPercent(kpi.trend, true)}
                    </span>
                  )}
                </div>
                
                {/* Row 2: Value */}
                <div 
                  className="text-2xl font-semibold tracking-tight text-foreground truncate" 
                  title={typeof kpi.value === 'number' ? kpi.value.toLocaleString() : kpi.value}
                >
                  {typeof kpi.value === 'number' ? formatNumber(kpi.value) : kpi.value}
                </div>
                
                {/* Row 3: Sparkline */}
                <Sparkline data={kpi.history} trend={kpi.trend} />
                
                {/* Row 4: Column Source Chip */}
                <div className="flex items-center gap-1 mt-1">
                  <span className="text-[10px] font-mono text-muted-foreground/70 bg-white/5 px-1.5 py-0.5 rounded truncate" title={kpi.column}>
                    {kpi.column || "Unknown"}
                  </span>
                </div>
              </div>
            ))}
            
            {/* Omitted KPIs (Merged) */}
            {data.omitted_kpis?.length > 0 && (
              <div className="rounded-xl p-4 border border-dashed border-border/40 flex flex-col gap-2 h-[140px] bg-surface/20">
                <div className="flex items-center gap-1.5 text-[13px] font-medium text-muted-foreground/80 mb-2">
                  <AlertCircle className="h-3.5 w-3.5" />
                  <span>Unavailable</span>
                </div>
                <div className="flex flex-col gap-1 overflow-y-auto pr-1 custom-scrollbar">
                  {data.omitted_kpis.map((kpi: any) => (
                    <div key={kpi.name} className="flex items-center justify-between group" title={kpi.reason}>
                      <span className="text-[12px] text-muted-foreground/60 truncate mr-2">{kpi.name}</span>
                      <Info className="h-3 w-3 text-muted-foreground/40 shrink-0 group-hover:text-foreground/70 transition-colors" />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </StudioPage>
  );
}

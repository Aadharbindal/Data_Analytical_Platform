"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber, formatPercent } from "@/lib/utils";

export default function TrendAnalysis() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['trend'],
    queryFn: () => analyticsApi.trend()
  });

  return (
    <StudioPage title="Trend & Change Detection" isLoading={isLoading}>
      {isError ? (
        <ErrorState />
      ) : !data || !data.trend || data.trend.length === 0 ? (
        <div className="text-muted-foreground text-sm">
          No Trend data found. Make sure your dataset has a date column.
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {data.trend.map((trend: any, i: number) => {
              const isUp = trend.trend === 'UP';
              const isDown = trend.trend === 'DOWN';
              
              return (
                <div 
                  key={i} 
                  className="glass-card rounded-xl p-4 flex flex-col gap-4 border border-white/[0.05] hover:border-white/20 hover:-translate-y-[1px] transition-all duration-150 relative overflow-hidden"
                >
                  <div 
                    className="absolute top-0 left-0 w-1 h-full" 
                    style={{ backgroundColor: isUp ? '#10b981' : isDown ? '#f43f5e' : '#64748b' }}
                  />
                  <div className="pl-2 flex items-center justify-between">
                    <h3 className="font-semibold text-[14px] text-foreground/90">{trend.column}</h3>
                    <div className="flex items-center gap-1.5 bg-white/5 border border-white/10 px-2 py-1 rounded-md">
                      {isUp ? <TrendingUp className="h-3.5 w-3.5 text-emerald-500" /> :
                       isDown ? <TrendingDown className="h-3.5 w-3.5 text-rose-500" /> :
                       <Minus className="h-3.5 w-3.5 text-muted-foreground" />}
                      <span className={`text-[11px] font-medium tracking-wide ${
                        isUp ? 'text-emerald-500' :
                        isDown ? 'text-rose-500' :
                        'text-muted-foreground'
                      }`}>
                        {isUp ? 'INCREASING' : isDown ? 'DECREASING' : 'STABLE'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="pl-2 grid grid-cols-2 gap-3 mt-1">
                    <div className="bg-surface/30 p-3 rounded-lg border border-border/20 flex flex-col gap-1">
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Growth Slope</div>
                      <div className="text-[15px] font-medium font-mono">
                        {formatNumber(trend.slope)}
                      </div>
                    </div>
                    <div className="bg-surface/30 p-3 rounded-lg border border-border/20 flex flex-col gap-1">
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wider">R-Value (Confidence)</div>
                      <div className="text-[15px] font-medium font-mono">
                        {trend.r_value != null ? formatPercent(trend.r_value * 100) : "N/A"}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </StudioPage>
  );
}

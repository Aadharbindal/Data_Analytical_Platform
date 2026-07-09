"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";

export default function TrendAnalysis() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['trend'],
    queryFn: () => analyticsApi.trend()
  });

  if (isLoading) return <div className="p-8"><CardSkeleton lines={10} /></div>;
  if (isError) return <div className="p-8"><ErrorState /></div>;
  if (!data || !data.trend || data.trend.length === 0) return <div className="p-8">No Trend data found. Make sure your dataset has a date column.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Trend & Change Detection</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.trend.map((trend: any, i: number) => (
          <div key={i} className="glass-card rounded-[20px] p-6 flex flex-col gap-4 border-t-2" style={{ borderTopColor: trend.trend === 'UP' ? '#10b981' : trend.trend === 'DOWN' ? '#f43f5e' : '#64748b' }}>
            <h3 className="font-semibold text-lg">{trend.column}</h3>
            
            <div className="flex items-center gap-4 bg-surface/50 p-4 rounded-xl border border-border/40">
              <div className="flex-1">
                <div className="text-xs text-muted-foreground mb-1">Overall Direction</div>
                <div className="flex items-center gap-2">
                  {trend.trend === 'UP' ? <TrendingUp className="h-5 w-5 text-emerald-500" /> :
                   trend.trend === 'DOWN' ? <TrendingDown className="h-5 w-5 text-rose-500" /> :
                   <Minus className="h-5 w-5 text-muted-foreground" />}
                  <span className={`font-medium ${
                    trend.trend === 'UP' ? 'text-emerald-500' :
                    trend.trend === 'DOWN' ? 'text-rose-500' :
                    'text-muted-foreground'
                  }`}>{trend.trend === 'UP' ? 'INCREASING' : trend.trend === 'DOWN' ? 'DECREASING' : 'STABLE'}</span>
                </div>
              </div>
              <div className="w-px h-12 bg-border/40"></div>
              <div className="flex-1">
                <div className="text-xs text-muted-foreground mb-1">Growth Slope</div>
                <div className="text-xl font-semibold font-mono">{trend.slope?.toFixed(4) ?? '0.0000'}</div>
              </div>
              <div className="w-px h-12 bg-border/40"></div>
              <div className="flex-1">
                <div className="text-xs text-muted-foreground mb-1">R-Value</div>
                <div className="text-xl font-semibold font-mono">{trend.r_value?.toFixed(2) ?? '0.00'}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

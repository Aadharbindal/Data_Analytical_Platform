"use client";

import { useDatasetAnalytics } from "@/hooks/useAnalytics";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export default function TrendAnalysis() {
  const { trends, isLoading } = useDatasetAnalytics("demo", "v1");

  if (isLoading) return <div className="p-8">Loading Trend Analysis...</div>;

  const data = trends.data;
  if (!data) return <div className="p-8">No Trend data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Trend & Change Detection</h1>
      
      <div className="grid grid-cols-2 gap-4">
        {data.map((trend, i) => (
          <div key={i} className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
            <h3 className="font-semibold text-lg">{trend.column_name}</h3>
            
            <div className="flex items-center gap-4 bg-surface/50 p-4 rounded-xl border border-border/40">
              <div className="flex-1">
                <div className="text-xs text-muted-foreground mb-1">Overall Direction</div>
                <div className="flex items-center gap-2">
                  {trend.overall_trend === 'INCREASING' ? <TrendingUp className="h-5 w-5 text-emerald-500" /> :
                   trend.overall_trend === 'DECREASING' ? <TrendingDown className="h-5 w-5 text-rose-500" /> :
                   <Minus className="h-5 w-5 text-muted-foreground" />}
                  <span className={`font-medium ${
                    trend.overall_trend === 'INCREASING' ? 'text-emerald-500' :
                    trend.overall_trend === 'DECREASING' ? 'text-rose-500' :
                    'text-muted-foreground'
                  }`}>{trend.overall_trend}</span>
                </div>
              </div>
              <div className="w-px h-12 bg-border/40"></div>
              <div className="flex-1">
                <div className="text-xs text-muted-foreground mb-1">Structural Breaks</div>
                <div className="text-xl font-semibold">{trend.change_points_count}</div>
              </div>
            </div>
            
            {trend.change_points_count > 0 && (
              <p className="text-sm text-muted-foreground bg-indigo-500/10 p-3 rounded-lg text-indigo-300">
                Multiple structural breaks detected. Consider utilizing regime-switching models for accurate forecasting.
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

"use client";

import { useDatasetAnalytics } from "@/hooks/useAnalytics";
import { LineChart as LineChartIcon } from "lucide-react";

export default function ForecastCenter() {
  const { forecasts, isLoading } = useDatasetAnalytics("demo", "v1");

  if (isLoading) return <div className="p-8">Loading Forecasts...</div>;

  const data = forecasts.data;
  if (!data) return <div className="p-8">No Forecast data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Forecast Center</h1>
      
      <div className="flex flex-col gap-6">
        {data.map((forecast, i) => (
          <div key={i} className="glass-card rounded-[20px] p-6 flex flex-col gap-4 border-t-4 border-t-indigo-500">
            <div className="flex justify-between items-center border-b border-border/40 pb-4">
              <div className="flex items-center gap-2">
                <LineChartIcon className="h-5 w-5 text-indigo-400" />
                <h3 className="font-semibold text-lg">{forecast.column_name}</h3>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-surface/50 p-4 rounded-xl border border-border/40">
                <div className="text-xs text-muted-foreground mb-1">Algorithm Selected</div>
                <div className="font-medium text-emerald-400">{forecast.selected_model}</div>
                <div className="text-[10px] text-muted-foreground mt-1">Auto-selected via Walk-Forward Validation</div>
              </div>
              <div className="bg-surface/50 p-4 rounded-xl border border-border/40">
                <div className="text-xs text-muted-foreground mb-1">Validation RMSE</div>
                <div className="font-mono font-medium">{forecast.rmse.toFixed(4)}</div>
                <div className="text-[10px] text-muted-foreground mt-1">Out-of-sample error metric</div>
              </div>
            </div>
            
            <div className="mt-4 p-8 border border-dashed border-border/40 rounded-xl flex items-center justify-center text-muted-foreground bg-background/50">
              Interactive Forecast Graph Placeholder (Recharts)
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

"use client";

import { useDatasetAnalytics } from "@/hooks/useAnalytics";
import { Clock } from "lucide-react";

export default function TimeSeriesPage() {
  const { timeseries, isLoading } = useDatasetAnalytics("demo", "v1");

  if (isLoading) return <div className="p-8">Loading Time Series Data...</div>;

  const data = timeseries.data;
  if (!data) return <div className="p-8">No Time Series data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Time Series Intelligence</h1>
      
      <div className="grid grid-cols-2 gap-4">
        {data.map((ts, i) => (
          <div key={i} className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
            <div className="flex items-center gap-2 border-b border-border/40 pb-4">
              <Clock className="h-5 w-5 text-indigo-400" />
              <h3 className="font-semibold text-lg">{ts.column_name}</h3>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-surface/50 p-4 rounded-xl border border-border/40">
                <div className="text-xs text-muted-foreground">Frequency</div>
                <div className="text-lg font-medium">{ts.frequency}</div>
              </div>
              <div className="bg-surface/50 p-4 rounded-xl border border-border/40">
                <div className="text-xs text-muted-foreground">Continuity Score</div>
                <div className={`text-lg font-medium ${ts.continuity_score > 90 ? 'text-emerald-500' : 'text-amber-500'}`}>
                  {ts.continuity_score}%
                </div>
              </div>
            </div>

            {ts.gaps_detected > 0 && (
              <div className="bg-amber-500/10 border border-amber-500/20 text-amber-200/80 p-3 rounded-lg text-sm mt-2">
                Warning: {ts.gaps_detected} missing time periods detected. Imputation recommended before forecasting.
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

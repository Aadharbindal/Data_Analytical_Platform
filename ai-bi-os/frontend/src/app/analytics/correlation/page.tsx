"use client";

import { useDatasetAnalytics } from "@/hooks/useAnalytics";
import { Network } from "lucide-react";

export default function CorrelationStudio() {
  const { correlations, isLoading } = useDatasetAnalytics("demo", "v1");

  if (isLoading) return <div className="p-8">Loading Correlations...</div>;

  const data = correlations.data;
  if (!data) return <div className="p-8">No Correlation data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Correlation Studio</h1>
      
      <div className="glass-card rounded-[20px] p-6">
        <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
          <Network className="h-5 w-5 text-primary" />
          Strongest Relationships
        </h3>
        <div className="grid grid-cols-3 gap-4">
          {data.strong_pairs.map((pair, i) => (
            <div key={i} className="p-4 bg-surface/50 rounded-xl border border-border/40 flex justify-between items-center">
              <div className="flex flex-col gap-1">
                <span className="text-xs text-muted-foreground">{pair.feature1}</span>
                <span className="text-xs text-muted-foreground">{pair.feature2}</span>
              </div>
              <div className={`text-lg font-bold ${pair.correlation > 0.7 ? "text-emerald-500" : "text-amber-500"}`}>
                {pair.correlation.toFixed(2)}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-card rounded-[20px] p-6 overflow-x-auto">
        <h3 className="text-lg font-medium mb-4">Correlation Matrix</h3>
        <table className="w-full text-xs text-center border-collapse">
          <thead>
            <tr>
              <th className="p-2 border-b border-r border-border/40"></th>
              {data.features.map(f => (
                <th key={f} className="p-2 border-b border-border/40 font-medium text-muted-foreground">{f}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.features.map((f, i) => (
              <tr key={f}>
                <td className="p-2 border-r border-border/40 font-medium text-muted-foreground text-left">{f}</td>
                {data.matrix[i].map((val, j) => {
                  const intensity = Math.abs(val);
                  const isPositive = val > 0;
                  return (
                    <td 
                      key={j} 
                      className="p-2 border border-border/10 transition-colors"
                      style={{ 
                        backgroundColor: isPositive 
                          ? `rgba(16, 185, 129, ${intensity * 0.4})` 
                          : `rgba(244, 63, 94, ${intensity * 0.4})` 
                      }}
                    >
                      {val.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

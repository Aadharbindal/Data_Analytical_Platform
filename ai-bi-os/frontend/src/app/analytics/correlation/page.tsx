"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { Network } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";

export default function CorrelationStudio() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['correlation'],
    queryFn: () => analyticsApi.correlation()
  });

  if (isLoading) return <div className="p-8"><CardSkeleton lines={10} /></div>;
  if (isError) return <div className="p-8"><ErrorState /></div>;
  if (!data || !data.correlation || data.correlation.length === 0) return <div className="p-8">No Correlation data found.</div>;

  const features = Array.from(new Set(data.correlation.map((d: any) => d.x))) as string[];
  const strong_pairs: any[] = [];
  
  const matrix = features.map(f1 => {
    return features.map(f2 => {
      const item = data.correlation.find((d: any) => d.x === f1 && d.y === f2);
      const val = item ? item.value : 0;
      
      // Collect strong pairs (only one way to avoid duplicates)
      if (f1 !== f2 && Math.abs(val) > 0.5 && features.indexOf(f1) < features.indexOf(f2)) {
        strong_pairs.push({ feature1: f1, feature2: f2, correlation: val });
      }
      return val;
    });
  });
  
  strong_pairs.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Correlation Studio</h1>
      
      {strong_pairs.length > 0 && (
        <div className="glass-card rounded-[20px] p-6">
          <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
            <Network className="h-5 w-5 text-primary" />
            Strongest Relationships
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {strong_pairs.slice(0, 6).map((pair, i) => (
              <div key={i} className="p-4 bg-surface/50 rounded-xl border border-border/40 flex justify-between items-center">
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-muted-foreground">{pair.feature1}</span>
                  <span className="text-xs text-muted-foreground">{pair.feature2}</span>
                </div>
                <div className={`text-lg font-bold ${pair.correlation > 0.5 ? "text-emerald-500" : "text-amber-500"}`}>
                  {pair.correlation.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="glass-card rounded-[20px] p-6 overflow-x-auto">
        <h3 className="text-lg font-medium mb-4">Correlation Matrix</h3>
        <table className="w-full text-xs text-center border-collapse">
          <thead>
            <tr>
              <th className="p-2 border-b border-r border-border/40"></th>
              {features.map(f => (
                <th key={f} className="p-2 border-b border-border/40 font-medium text-muted-foreground min-w-[80px]">{f}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {features.map((f, i) => (
              <tr key={f}>
                <td className="p-2 border-r border-border/40 font-medium text-muted-foreground text-left">{f}</td>
                {matrix[i].map((val, j) => {
                  const intensity = Math.abs(val);
                  const isPositive = val > 0;
                  return (
                    <td 
                      key={j} 
                      className="p-2 border border-border/10 transition-colors"
                      style={{ 
                        backgroundColor: i === j ? 'transparent' : isPositive 
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

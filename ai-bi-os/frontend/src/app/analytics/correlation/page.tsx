"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { EmptyState } from "@/components/ui/empty-state";

export default function CorrelationStudio() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['correlation'],
    queryFn: () => analyticsApi.correlation()
  });

  return (
    <StudioPage title="Correlation Studio" isLoading={isLoading}>
      {isError ? (
        <ErrorState />
      ) : !data || !data.correlation || data.correlation.length === 0 ? (
        <div className="text-muted-foreground text-sm">No Correlation data found.</div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="rounded-xl border border-white/[0.05] bg-surface/30 p-6 overflow-x-auto custom-scrollbar">
            {(() => {
              const features = Array.from(new Set(data.correlation.map((d: any) => d.x))) as string[];
              
              if (features.length < 2) {
                return (
                  <EmptyState 
                    title="Insufficient Numeric Data"
                    description={`Correlation analysis requires at least 2 numeric columns. Found ${features.length} numeric column(s).`}
                  />
                );
              }

              const matrix = features.map(f1 => {
                return features.map(f2 => {
                  const item = data.correlation.find((d: any) => d.x === f1 && d.y === f2);
                  return item ? item.value : 0;
                });
              });

              return (
                <table className="border-collapse mx-auto" style={{ minWidth: 'max-content' }}>
                  <thead>
                    <tr>
                      <th className="p-0 border-b border-r border-border/10"></th>
                      {features.map((f) => (
                        <th key={f} className="p-0 border-b border-border/10 w-12 min-w-[48px] h-32 relative align-bottom">
                          <div className="absolute bottom-2 left-1/2 origin-bottom-left -rotate-45 translate-x-[-50%] text-[10px] font-medium text-muted-foreground/80 whitespace-nowrap">
                            {f}
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {features.map((f, i) => (
                      <tr key={f}>
                        <td className="p-0 pr-3 border-r border-border/10 text-right text-[10px] font-medium text-muted-foreground/80 whitespace-nowrap h-12">
                          {f}
                        </td>
                        {matrix[i].map((val, j) => {
                          const intensity = Math.abs(val);
                          const isPositive = val > 0;
                          return (
                            <td 
                              key={j} 
                              className="w-12 h-12 min-w-[48px] border border-background transition-colors group relative"
                              title={`${f} × ${features[j]}: ${val.toFixed(2)}`}
                              style={{ 
                                backgroundColor: i === j ? 'transparent' : isPositive 
                                  ? `rgba(59, 130, 246, ${intensity * 0.8})` // Blue for positive
                                  : `rgba(244, 63, 94, ${intensity * 0.8})`  // Red for negative
                              }}
                            >
                              {i !== j && (
                                <div className="absolute inset-0 flex items-center justify-center text-[10px] font-mono text-white/40 opacity-0 group-hover:opacity-100 transition-opacity">
                                  {val.toFixed(2)}
                                </div>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              );
            })()}
          </div>
        </div>
      )}
    </StudioPage>
  );
}

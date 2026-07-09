"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber, formatPercent } from "@/lib/utils";
import { Download } from "lucide-react";

export default function EDAPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['eda'],
    queryFn: () => analyticsApi.eda()
  });

  const toolbar = (
    <button 
      onClick={() => window.open("http://127.0.0.1:8000/api/v1/analytics/export/eda")}
      className="bg-primary/10 text-primary hover:bg-primary/20 px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors"
    >
      <Download className="w-3.5 h-3.5" />
      Export CSV
    </button>
  );

  return (
    <StudioPage title="Dataset Analysis (EDA)" isLoading={isLoading} toolbar={toolbar}>
      {isError ? (
        <ErrorState />
      ) : !data || !data.summary || data.summary.length === 0 ? (
        <div className="text-muted-foreground text-sm">No EDA data found. Upload a dataset first.</div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.summary.map((c: any) => {
              const nullPct = data.rows ? (c.nulls / data.rows) : 0;
              
              return (
                <div key={c.column} className="glass-card rounded-xl p-4 hover:border-white/20 hover:-translate-y-[1px] transition-all duration-150">
                  {/* Header: Name + Type + Nulls */}
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="flex flex-col gap-1.5 overflow-hidden">
                      <div className="flex items-center gap-2">
                        <span className="text-[14px] font-semibold text-foreground truncate" title={c.column}>
                          {c.column}
                        </span>
                        <span className="text-[10px] font-mono text-muted-foreground bg-white/5 px-1.5 py-0.5 rounded border border-white/10 shrink-0">
                          {c.type}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 w-48">
                        <span className="text-[11px] text-muted-foreground shrink-0 w-12">
                          {formatPercent(nullPct * 100)} null
                        </span>
                        <div className="flex-1 h-1.5 bg-surface/50 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full ${nullPct > 0.5 ? 'bg-rose-500/80' : nullPct > 0.1 ? 'bg-amber-500/80' : 'bg-primary/80'}`} 
                            style={{ width: `${Math.min(nullPct * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Key Stats Mini-Table */}
                  <div className="grid grid-cols-2 gap-y-2 gap-x-4 text-[12px] bg-surface/30 rounded-lg p-3 border border-border/20">
                    {c.mean != null ? (
                      <>
                        <div className="text-muted-foreground">Mean</div>
                        <div className="font-mono text-right truncate">{formatNumber(c.mean)}</div>
                        <div className="text-muted-foreground">Min / Max</div>
                        <div className="font-mono text-right truncate">{formatNumber(c.min)} / {formatNumber(c.max)}</div>
                      </>
                    ) : (
                      <>
                        <div className="text-muted-foreground">Unique Values</div>
                        <div className="font-mono text-right truncate">{formatNumber(c.unique)}</div>
                        <div className="text-muted-foreground col-span-2">Top Values</div>
                        <div className="col-span-2 flex flex-wrap gap-1 mt-0.5">
                          {c.top_values ? (
                            Object.entries(c.top_values).slice(0, 3).map(([k,v]) => (
                              <span key={k} className="text-[10px] bg-white/5 px-1.5 py-0.5 rounded text-muted-foreground/90 truncate max-w-[120px]">
                                {k} <span className="opacity-50">({v as React.ReactNode})</span>
                              </span>
                            ))
                          ) : (
                            <span className="text-[10px] text-muted-foreground/50">N/A</span>
                          )}
                        </div>
                      </>
                    )}
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

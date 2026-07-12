"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi, BASE_URL } from "@/lib/api";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber, formatPercent } from "@/lib/utils";
import { Download } from "lucide-react";
import { DeepAnalysisDialog } from "./DeepAnalysisDialog";

export default function EDAPage() {
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null);
  const { data, isLoading, isError } = useQuery({
    queryKey: ['eda'],
    queryFn: () => analyticsApi.eda()
  });

  const toolbar = (
    <button 
      onClick={() => window.open(`${BASE_URL}/api/v1/analytics/export/eda`)}
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
          <div className="flex flex-col gap-4">
            {data.summary.map((c: any) => {
              const nullPct = data.rows ? (c.nulls / data.rows) : 0;
              const isNumeric = c.mean != null;
              
              return (
                <div 
                  key={c.column} 
                  onClick={() => setSelectedColumn(c.column)}
                  className="glass-card rounded-xl p-5 hover:border-white/20 hover:bg-white/[0.04] transition-all duration-150 flex flex-col md:flex-row md:items-center justify-between gap-6 cursor-pointer"
                >
                  
                  {/* Left Section: Identity & Health */}
                  <div className="flex flex-col gap-2 w-full md:w-1/4 shrink-0">
                    <div className="flex items-center gap-2">
                      <span className="text-base font-semibold text-foreground truncate" title={c.column}>
                        {c.column}
                      </span>
                      <span className="text-[10px] font-mono text-muted-foreground bg-white/5 px-2 py-0.5 rounded-full border border-white/10 shrink-0 uppercase tracking-wider">
                        {c.type}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-3 w-full mt-1">
                      <span className="text-[11px] text-muted-foreground shrink-0 w-12 font-medium">
                        {formatPercent(nullPct * 100)} null
                      </span>
                      <div className="flex-1 h-1.5 bg-surface/80 rounded-full overflow-hidden max-w-[120px]">
                        <div 
                          className={`h-full rounded-full ${nullPct > 0.5 ? 'bg-rose-500/80' : nullPct > 0.1 ? 'bg-amber-500/80' : 'bg-emerald-500/80'}`} 
                          style={{ width: `${Math.min(nullPct * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  
                  {/* Right Section: Stats */}
                  <div className="flex-1 w-full bg-surface/30 rounded-lg p-4 border border-border/20 md:border-none md:bg-transparent md:p-0 flex items-center justify-end">
                    {isNumeric ? (
                      <div className="grid grid-cols-4 gap-6 w-full max-w-2xl ml-auto">
                        <div className="flex flex-col gap-1">
                          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Mean</span>
                          <span className="font-mono text-sm text-foreground truncate">{formatNumber(c.mean)}</span>
                        </div>
                        <div className="flex flex-col gap-1">
                          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Min</span>
                          <span className="font-mono text-sm text-foreground truncate">{formatNumber(c.min)}</span>
                        </div>
                        <div className="flex flex-col gap-1">
                          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Max</span>
                          <span className="font-mono text-sm text-foreground truncate">{formatNumber(c.max)}</span>
                        </div>
                        <div className="flex flex-col gap-1">
                          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Unique</span>
                          <span className="font-mono text-sm text-foreground truncate">{formatNumber(c.unique)}</span>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col md:flex-row items-start md:items-center gap-6 w-full max-w-3xl ml-auto">
                        <div className="flex flex-col gap-1 shrink-0 min-w-[80px]">
                          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Unique</span>
                          <span className="font-mono text-sm text-foreground">{formatNumber(c.unique)}</span>
                        </div>
                        
                        <div className="flex flex-col gap-1.5 flex-1 w-full overflow-hidden">
                          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Top Values</span>
                          <div className="flex flex-wrap gap-2">
                            {c.top_values && Object.keys(c.top_values).length > 0 ? (
                              Object.entries(c.top_values).slice(0, 4).map(([k,v]) => (
                                <span key={k} className="text-xs bg-white/[0.03] border border-white/[0.08] px-2.5 py-1 rounded-md text-muted-foreground/90 flex items-center gap-2 hover:bg-white/[0.08] transition-colors">
                                  <span className="truncate max-w-[150px] font-medium text-foreground/80">{k}</span>
                                  <span className="opacity-50 text-[10px] bg-black/30 px-1.5 py-0.5 rounded font-mono">{v as React.ReactNode}</span>
                                </span>
                              ))
                            ) : (
                              <span className="text-xs text-muted-foreground/50">N/A</span>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  
                </div>
              );
            })}
          </div>
        </div>
      )}
      <DeepAnalysisDialog column={selectedColumn} onClose={() => setSelectedColumn(null)} />
    </StudioPage>
  );
}

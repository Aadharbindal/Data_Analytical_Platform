"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber } from "@/lib/utils";

export default function OutlierExplorer() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['outliers'],
    queryFn: () => analyticsApi.outliers()
  });

  return (
    <StudioPage title="Outlier Explorer" isLoading={isLoading}>
      {isError ? (
        <ErrorState />
      ) : !data || !data.outliers || data.outliers.length === 0 ? (
        <div className="text-muted-foreground text-sm">No Outlier data found.</div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="rounded-xl border border-white/[0.05] overflow-hidden bg-surface/30">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[13px]">
                <thead className="bg-white/[0.02] sticky top-0 z-10 backdrop-blur-md">
                  <tr className="border-b border-white/[0.05] text-muted-foreground/80 font-medium">
                    <th className="py-2.5 px-4 w-1/3">Column Name</th>
                    <th className="py-2.5 px-4 text-center">Detection Methods & Results</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.03]">
                  {data.outliers.map((colData: any, i: number) => {
                    const totalOutliers = Math.max(colData.z_score_outliers || 0, colData.iqr_outliers || 0);
                    const hasOutliers = totalOutliers > 0;
                    
                    return (
                      <tr key={i} className="hover:bg-white/[0.02] transition-colors group">
                        <td className="py-3 px-4 font-medium text-foreground/90 whitespace-nowrap border-l-2 border-transparent group-hover:border-primary/50 transition-all">
                          <div className="flex items-center gap-2">
                            {hasOutliers && (
                              <div className="w-1.5 h-1.5 rounded-full bg-amber-500/80 animate-pulse" />
                            )}
                            <span className={hasOutliers ? "text-foreground" : "text-muted-foreground"}>
                              {colData.column}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center justify-center gap-6">
                            {/* Z-Score Badge */}
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-wider bg-white/5 border border-white/10 px-1.5 py-0.5 rounded">
                                Z-Score
                              </span>
                              <span className={`font-mono ${colData.z_score_outliers > 0 ? 'text-amber-500' : 'text-muted-foreground'}`}>
                                {formatNumber(colData.z_score_outliers)}
                              </span>
                            </div>
                            
                            <div className="w-[1px] h-4 bg-white/10" />
                            
                            {/* IQR Badge */}
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-wider bg-white/5 border border-white/10 px-1.5 py-0.5 rounded">
                                IQR
                              </span>
                              <span className={`font-mono ${colData.iqr_outliers > 0 ? 'text-amber-500' : 'text-muted-foreground'}`}>
                                {formatNumber(colData.iqr_outliers)}
                              </span>
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </StudioPage>
  );
}

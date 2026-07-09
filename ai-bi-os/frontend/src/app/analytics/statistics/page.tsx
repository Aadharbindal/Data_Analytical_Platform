"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber } from "@/lib/utils";

export default function StatisticalAnalysis() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['statistics'],
    queryFn: () => analyticsApi.statistics()
  });

  return (
    <StudioPage title="Statistical Analysis" isLoading={isLoading}>
      {isError ? (
        <ErrorState />
      ) : !data || !data.stats || data.stats.length === 0 ? (
        <div className="text-muted-foreground text-sm">No Statistical data found.</div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="rounded-xl border border-white/[0.05] overflow-hidden bg-surface/30">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[13px]">
                <thead className="bg-white/[0.02] sticky top-0 z-10 backdrop-blur-md">
                  <tr className="border-b border-white/[0.05] text-muted-foreground/80 font-medium">
                    <th className="py-2.5 px-4">Column Name</th>
                    <th className="py-2.5 px-4 text-right">Mean</th>
                    <th className="py-2.5 px-4 text-right">Median</th>
                    <th className="py-2.5 px-4 text-right">Std Dev</th>
                    <th className="py-2.5 px-4 text-right">Skewness</th>
                    <th className="py-2.5 px-4 text-right">Kurtosis</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.03]">
                  {data.stats.map((stat: any, i: number) => (
                    <tr key={i} className="hover:bg-white/[0.02] transition-colors group">
                      <td className="py-2.5 px-4 font-medium text-foreground/90 whitespace-nowrap">
                        {stat.column}
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono text-muted-foreground group-hover:text-foreground/90 transition-colors">
                        {formatNumber(stat.mean)}
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono text-muted-foreground group-hover:text-foreground/90 transition-colors">
                        {formatNumber(stat.median)}
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono text-muted-foreground group-hover:text-foreground/90 transition-colors">
                        {formatNumber(stat.std)}
                      </td>
                      <td className={`py-2.5 px-4 text-right font-mono ${Math.abs(stat.skew || 0) > 1 ? 'text-amber-500/80' : 'text-muted-foreground'} group-hover:opacity-100 transition-colors`}>
                        {formatNumber(stat.skew)}
                      </td>
                      <td className={`py-2.5 px-4 text-right font-mono ${Math.abs(stat.kurtosis || 0) > 3 ? 'text-rose-500/80' : 'text-muted-foreground'} group-hover:opacity-100 transition-colors`}>
                        {formatNumber(stat.kurtosis)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </StudioPage>
  );
}

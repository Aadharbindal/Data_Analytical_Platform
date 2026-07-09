"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { Sigma } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";

export default function StatisticalAnalysis() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['statistics'],
    queryFn: () => analyticsApi.statistics()
  });

  if (isLoading) return <div className="p-8"><CardSkeleton lines={10} /></div>;
  if (isError) return <div className="p-8"><ErrorState /></div>;
  if (!data || !data.stats || data.stats.length === 0) return <div className="p-8">No Statistical data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Statistical Inference</h1>
      
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {data.stats.map((stat: any, i: number) => (
          <div key={i} className="glass-card rounded-[20px] p-6 flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Sigma className="h-5 w-5 text-primary" />
              <h3 className="font-semibold text-lg">{stat.column}</h3>
            </div>
            
            <div className="grid grid-cols-2 gap-2 mt-2">
              <div className="flex flex-col bg-background/50 p-2 rounded-lg border border-border/40">
                <span className="text-xs text-muted-foreground">Mean</span>
                <span className="font-mono font-medium">{stat.mean?.toFixed(2)}</span>
              </div>
              <div className="flex flex-col bg-background/50 p-2 rounded-lg border border-border/40">
                <span className="text-xs text-muted-foreground">Median</span>
                <span className="font-mono font-medium">{stat.median?.toFixed(2)}</span>
              </div>
              <div className="flex flex-col bg-background/50 p-2 rounded-lg border border-border/40">
                <span className="text-xs text-muted-foreground">Std Dev</span>
                <span className="font-mono font-medium">{stat.std?.toFixed(2)}</span>
              </div>
              <div className="flex flex-col bg-background/50 p-2 rounded-lg border border-border/40">
                <span className="text-xs text-muted-foreground">Skewness</span>
                <span className="font-mono font-medium text-amber-500">{stat.skew?.toFixed(2)}</span>
              </div>
              <div className="flex flex-col bg-background/50 p-2 rounded-lg border border-border/40 col-span-2">
                <span className="text-xs text-muted-foreground">Kurtosis</span>
                <span className="font-mono font-medium text-rose-500">{stat.kurtosis?.toFixed(2)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

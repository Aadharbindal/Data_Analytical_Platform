"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { AlertTriangle } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";

export default function OutlierExplorer() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['outliers'],
    queryFn: () => analyticsApi.outliers()
  });

  if (isLoading) return <div className="p-8"><CardSkeleton lines={10} /></div>;
  if (isError) return <div className="p-8"><ErrorState /></div>;
  if (!data || !data.outliers || data.outliers.length === 0) return <div className="p-8">No Outlier data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Outlier Explorer</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {data.outliers.map((colData: any, i: number) => {
          const totalOutliers = Math.max(colData.z_score_outliers, colData.iqr_outliers);
          const hasOutliers = totalOutliers > 0;
          
          return (
            <div key={i} className={`glass-card rounded-[20px] p-6 flex flex-col gap-4 border-l-4 ${hasOutliers ? 'border-amber-500' : 'border-emerald-500'}`}>
              <h3 className="font-semibold text-lg flex items-center gap-2">
                <AlertTriangle className={`h-5 w-5 ${hasOutliers ? 'text-amber-500' : 'text-emerald-500'}`} />
                {colData.column}
              </h3>
              
              <div className="grid grid-cols-2 gap-4 mt-2">
                <div className="bg-surface/50 p-4 rounded-xl border border-border/40 text-center">
                  <div className="text-3xl font-bold font-mono mb-1">{colData.z_score_outliers}</div>
                  <div className="text-xs text-muted-foreground uppercase tracking-wider">Z-Score Outliers</div>
                </div>
                <div className="bg-surface/50 p-4 rounded-xl border border-border/40 text-center">
                  <div className="text-3xl font-bold font-mono mb-1">{colData.iqr_outliers}</div>
                  <div className="text-xs text-muted-foreground uppercase tracking-wider">IQR Outliers</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

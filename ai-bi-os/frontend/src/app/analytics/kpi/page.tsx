"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { Activity, AlertCircle } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";

export default function KPICenter() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['kpiCenter'],
    queryFn: () => analyticsApi.kpiCenter()
  });

  if (isLoading) return <div className="p-8"><CardSkeleton lines={10} /></div>;
  if (isError) return <div className="p-8"><ErrorState /></div>;
  if (!data) return <div className="p-8">No KPI data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">KPI Center</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.available_kpis?.map((kpi: any) => (
          <div key={kpi.name} className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-primary" />
                <span className="font-medium text-lg">{kpi.name}</span>
              </div>
              {kpi.trend !== null && kpi.trend !== undefined && (
                <span className={`text-sm px-2 py-1 rounded-md font-medium ${
                  kpi.trend > 0 ? "bg-emerald-500/10 text-emerald-500" : 
                  kpi.trend < 0 ? "bg-rose-500/10 text-rose-500" : 
                  "bg-muted/50 text-muted-foreground"
                }`}>
                  {kpi.trend > 0 ? '+' : ''}{kpi.trend.toFixed(2)}%
                </span>
              )}
            </div>
            <div className="text-4xl font-bold font-mono mt-2">
              {typeof kpi.value === 'number' ? kpi.value.toLocaleString() : kpi.value}
            </div>
            <div className="text-xs text-muted-foreground uppercase tracking-wider mt-auto">
              Status: {kpi.status}
            </div>
          </div>
        ))}
      </div>
      
      {data.omitted_kpis?.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-medium mb-4 flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-muted-foreground" />
            Omitted KPIs
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.omitted_kpis.map((kpi: any) => (
              <div key={kpi.name} className="bg-surface/50 rounded-xl p-4 border border-border/40 flex flex-col gap-2 opacity-70">
                <span className="font-medium">{kpi.name}</span>
                <span className="text-sm text-muted-foreground">{kpi.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

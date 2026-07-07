"use client";

import { useDatasetAnalytics } from "@/hooks/useAnalytics";
import { PieChart } from "lucide-react";

export default function MetricsExplorer() {
  const { metrics, isLoading } = useDatasetAnalytics("demo", "v1");

  if (isLoading) return <div className="p-8">Loading Metrics...</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Business Metrics Explorer</h1>
      <div className="grid grid-cols-4 gap-4">
        {metrics.data?.map(m => (
          <div key={m.id} className="glass-card rounded-[20px] p-6 flex flex-col gap-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <PieChart className="h-4 w-4" />
              <span className="text-sm">{m.name}</span>
            </div>
            <div className="text-2xl font-semibold">
              {m.value.toLocaleString()} <span className="text-sm font-normal text-muted-foreground">{m.unit}</span>
            </div>
            <div className="text-xs text-muted-foreground mt-2">Trend: {m.trend}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

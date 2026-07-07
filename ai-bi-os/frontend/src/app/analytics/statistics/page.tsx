"use client";

import { useDatasetAnalytics } from "@/hooks/useAnalytics";
import { Sigma } from "lucide-react";

export default function StatisticalAnalysis() {
  const { statistics, isLoading } = useDatasetAnalytics("demo", "v1");

  if (isLoading) return <div className="p-8">Loading Statistics...</div>;

  const data = statistics.data;
  if (!data) return <div className="p-8">No Statistical data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Statistical Inference</h1>
      
      <div className="grid grid-cols-2 gap-4">
        {data.map((test, i) => (
          <div key={i} className="glass-card rounded-[20px] p-6 flex flex-col gap-3 border-l-4" style={{ borderLeftColor: test.is_significant ? "#10b981" : "#64748b" }}>
            <div className="flex items-center gap-2">
              <Sigma className="h-5 w-5 text-primary" />
              <h3 className="font-semibold text-lg">{test.test_name}</h3>
            </div>
            <div className="flex justify-between items-center bg-background/50 p-3 rounded-lg border border-border/40">
              <span className="text-sm text-muted-foreground">P-Value</span>
              <span className="font-mono font-medium">{test.p_value < 0.001 ? "< 0.001" : test.p_value.toFixed(4)}</span>
            </div>
            <div className="flex justify-between items-center bg-background/50 p-3 rounded-lg border border-border/40">
              <span className="text-sm text-muted-foreground">Significance</span>
              <span className={`font-semibold ${test.is_significant ? "text-emerald-500" : "text-muted-foreground"}`}>
                {test.is_significant ? "Significant" : "Not Significant"}
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-2">{test.details}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

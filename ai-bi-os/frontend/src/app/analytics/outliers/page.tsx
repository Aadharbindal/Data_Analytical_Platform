"use client";

import { useDatasetAnalytics } from "@/hooks/useAnalytics";
import { AlertTriangle } from "lucide-react";

export default function OutlierExplorer() {
  const { outliers, isLoading } = useDatasetAnalytics("demo", "v1");

  if (isLoading) return <div className="p-8">Loading Outliers...</div>;

  const data = outliers.data;
  if (!data) return <div className="p-8">No Outlier data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Outlier Explorer</h1>
      
      <div className="flex flex-col gap-6">
        {data.map((colData, i) => (
          <div key={i} className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
            <h3 className="font-semibold text-lg border-b border-border/40 pb-3 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Feature: {colData.column_name}
              <span className="ml-auto text-sm font-normal text-muted-foreground bg-surface px-2 py-1 rounded-md">
                {colData.outliers.length} Outliers Detected
              </span>
            </h3>
            
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-border/40 text-muted-foreground">
                    <th className="py-2 px-4">Row Index</th>
                    <th className="py-2 px-4">Value</th>
                    <th className="py-2 px-4">Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {colData.outliers.map((outlier, j) => (
                    <tr key={j} className="border-b border-border/10 hover:bg-white/[0.01]">
                      <td className="py-2 px-4 font-mono text-muted-foreground">#{outlier.index}</td>
                      <td className="py-2 px-4 font-mono font-medium">{outlier.value}</td>
                      <td className="py-2 px-4">
                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                          outlier.severity === 'HIGH' ? 'bg-rose-500/10 text-rose-500' : 
                          outlier.severity === 'MEDIUM' ? 'bg-amber-500/10 text-amber-500' : 
                          'bg-sky-500/10 text-sky-500'
                        }`}>
                          {outlier.severity}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

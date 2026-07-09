"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber } from "@/lib/utils";
import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";
import { Search } from "lucide-react";

export default function MetricsExplorer() {
  const [search, setSearch] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["metrics_explorer"],
    queryFn: () => api.get<any[]>("/api/v1/analytics/metrics"),
  });

  const filteredData = React.useMemo(() => {
    if (!data) return [];
    if (!search) return data;
    return data.filter((m: any) => m.metric.toLowerCase().includes(search.toLowerCase()));
  }, [data, search]);

  return (
    <StudioPage title="Metrics Explorer" isLoading={isLoading}>
      <div className="flex flex-col gap-6">
        
        {/* Search */}
        <div className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search metrics..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-surface/50 border border-border rounded-md pl-10 pr-4 py-2 text-sm text-foreground outline-none focus:border-primary transition-colors"
          />
        </div>

        {/* Table */}
        <div className="rounded-xl border border-border/40 overflow-hidden bg-surface/30">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13px]">
              <thead className="bg-white/[0.02] sticky top-0 z-10 backdrop-blur-md">
                <tr className="border-b border-border/40 text-muted-foreground/80 font-medium">
                  <th className="py-3 px-4">Metric</th>
                  <th className="py-3 px-4 text-right">Sum / Total</th>
                  <th className="py-3 px-4 text-right">Mean</th>
                  <th className="py-3 px-4 text-right">Min</th>
                  <th className="py-3 px-4 text-right">Max</th>
                  <th className="py-3 px-4 w-48 text-center">Trend (Monthly)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {filteredData?.map((m: any) => (
                  <tr key={m.metric} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="py-3 px-4 font-medium text-foreground/90 whitespace-nowrap">
                      {m.metric}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-muted-foreground group-hover:text-foreground/90 transition-colors">
                      {formatNumber(m.sum)}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-muted-foreground group-hover:text-foreground/90 transition-colors">
                      {formatNumber(m.mean)}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-muted-foreground group-hover:text-foreground/90 transition-colors">
                      {formatNumber(m.min)}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-muted-foreground group-hover:text-foreground/90 transition-colors">
                      {formatNumber(m.max)}
                    </td>
                    <td className="py-1 px-4 text-center align-middle">
                      {m.sparkline && m.sparkline.length > 0 ? (
                        <div className="h-8 w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={m.sparkline.map((v: number, i: number) => ({ i, v }))}>
                              <YAxis domain={['auto', 'auto']} hide />
                              <Line 
                                type="monotone" 
                                dataKey="v" 
                                stroke="#8b5cf6" 
                                strokeWidth={1.5} 
                                dot={false} 
                                isAnimationActive={false} 
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      ) : (
                        <span className="text-muted-foreground/50 text-xs">N/A</span>
                      )}
                    </td>
                  </tr>
                ))}
                {filteredData?.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-muted-foreground">
                      No metrics found matching your search.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </StudioPage>
  );
}

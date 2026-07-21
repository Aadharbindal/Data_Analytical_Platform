"use client";

import React, { Suspense, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import api, { datasetsApi } from "@/lib/api";
import { StudioPage } from "@/components/analytics/StudioPage";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { formatNumber } from "@/lib/utils";
import { ArrowRightLeft } from "lucide-react";

// useSearchParams() must be wrapped in Suspense for production builds
// (works fine without it in dev, which is why this was easy to miss).
export default function CompareDatasets() {
  return (
    <Suspense fallback={<StudioPage title="Dataset Comparison"><div className="text-center text-muted-foreground py-8">Loading...</div></StudioPage>}>
      <CompareDatasetsInner />
    </Suspense>
  );
}

function CompareDatasetsInner() {
  const searchParams = useSearchParams();
  // Pre-fills from ?a=<id>&b=<id> when reached via "Compare Selected" on the
  // Datasets page; falls back to manual dropdown selection otherwise.
  const [idA, setIdA] = useState<string>(searchParams.get("a") || "");
  const [idB, setIdB] = useState<string>(searchParams.get("b") || "");

  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => datasetsApi.list(),
  });

  const { data: diff, isLoading: diffLoading } = useQuery({
    queryKey: ["dataset_compare", idA, idB],
    queryFn: () => api.get<any>(`/api/v1/datasets/compare?id_a=${idA}&id_b=${idB}`),
    enabled: !!idA && !!idB,
  });

  return (
    <StudioPage title="Dataset Comparison">
      <div className="flex flex-col gap-6">
        
        {/* Selectors */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Select Datasets to Compare</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col md:flex-row gap-6 items-center">
            <div className="flex-1 w-full">
              <label className="block text-sm font-medium mb-2 text-muted-foreground">Dataset A (Baseline)</label>
              <select 
                className="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                value={idA}
                onChange={(e) => setIdA(e.target.value)}
              >
                <option value="">Select...</option>
                {datasets?.map((d: any) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            
            <div className="hidden md:flex mt-6 text-muted-foreground">
              <ArrowRightLeft className="w-5 h-5" />
            </div>

            <div className="flex-1 w-full">
              <label className="block text-sm font-medium mb-2 text-muted-foreground">Dataset B (Comparison)</label>
              <select 
                className="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                value={idB}
                onChange={(e) => setIdB(e.target.value)}
              >
                <option value="">Select...</option>
                {datasets?.map((d: any) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {diffLoading && <div className="text-center text-muted-foreground py-8">Comparing datasets...</div>}
        
        {diff && (
          <div className="flex flex-col gap-6">
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Row Counts */}
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-muted-foreground">Row Count Diff</CardTitle>
                </CardHeader>
                <CardContent className="flex justify-between items-end">
                  <div>
                    <div className="text-xs text-muted-foreground">Dataset A</div>
                    <div className="text-2xl font-mono">{formatNumber(diff.rows_a)}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-muted-foreground">Dataset B</div>
                    <div className="text-2xl font-mono">{formatNumber(diff.rows_b)}</div>
                  </div>
                </CardContent>
              </Card>
              
              {/* Schema Diff */}
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-muted-foreground">Schema Diff</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col gap-2">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Only in A</span>
                      <div className="flex gap-1">
                        {diff.schema_diff.only_in_a.map((c: string) => <span key={c} className="bg-rose-500/10 text-rose-400 px-1.5 py-0.5 rounded text-xs">{c}</span>)}
                        {diff.schema_diff.only_in_a.length === 0 && <span className="text-muted-foreground">-</span>}
                      </div>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Only in B</span>
                      <div className="flex gap-1">
                        {diff.schema_diff.only_in_b.map((c: string) => <span key={c} className="bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded text-xs">{c}</span>)}
                        {diff.schema_diff.only_in_b.length === 0 && <span className="text-muted-foreground">-</span>}
                      </div>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Common Columns</span>
                      <span className="font-mono">{diff.schema_diff.common.length}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* KPI Diffs */}
            <h3 className="text-lg font-semibold mt-4">KPI Deltas</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {diff.kpi_diffs.map((kpi: any) => (
                <Card key={kpi.name} className="glass-card">
                  <CardContent className="p-4 flex flex-col gap-2">
                    <div className="text-xs font-medium text-muted-foreground uppercase">{kpi.name}</div>
                    <div className="flex justify-between items-end">
                      <div className="text-sm">
                        <span className="text-muted-foreground block text-[10px]">A</span>
                        {formatNumber(kpi.value_a)}
                      </div>
                      <div className="text-sm text-right">
                        <span className="text-muted-foreground block text-[10px]">B</span>
                        {formatNumber(kpi.value_b)}
                      </div>
                    </div>
                    <div className={`mt-2 text-xs font-mono px-2 py-1 rounded w-max ${kpi.delta > 0 ? "bg-emerald-500/10 text-emerald-400" : kpi.delta < 0 ? "bg-rose-500/10 text-rose-400" : "bg-white/5 text-muted-foreground"}`}>
                      {kpi.delta > 0 ? "+" : ""}{formatNumber(kpi.delta)} ({kpi.delta > 0 ? "+" : ""}{kpi.delta_pct.toFixed(2)}%)
                    </div>
                  </CardContent>
                </Card>
              ))}
              {diff.kpi_diffs.length === 0 && <div className="text-sm text-muted-foreground col-span-full">No matching KPIs found to compare.</div>}
            </div>

            {/* Numeric Diffs */}
            <h3 className="text-lg font-semibold mt-4">Numeric Mean Deltas</h3>
            <div className="rounded-xl border border-border/40 overflow-hidden bg-surface/30">
              <table className="w-full text-left text-[13px]">
                <thead className="bg-white/[0.02]">
                  <tr className="border-b border-border/40 text-muted-foreground font-medium">
                    <th className="py-2.5 px-4">Column</th>
                    <th className="py-2.5 px-4 text-right">Mean (A)</th>
                    <th className="py-2.5 px-4 text-right">Mean (B)</th>
                    <th className="py-2.5 px-4 text-right">Delta</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/20">
                  {diff.num_diffs.map((num: any) => (
                    <tr key={num.column} className="hover:bg-white/[0.02]">
                      <td className="py-2.5 px-4 font-medium">{num.column}</td>
                      <td className="py-2.5 px-4 text-right font-mono">{formatNumber(num.mean_a)}</td>
                      <td className="py-2.5 px-4 text-right font-mono">{formatNumber(num.mean_b)}</td>
                      <td className={`py-2.5 px-4 text-right font-mono ${num.delta > 0 ? "text-emerald-400" : num.delta < 0 ? "text-rose-400" : ""}`}>
                        {num.delta > 0 ? "+" : ""}{formatNumber(num.delta)}
                      </td>
                    </tr>
                  ))}
                  {diff.num_diffs.length === 0 && <tr><td colSpan={4} className="p-4 text-center text-muted-foreground">No common numeric columns found.</td></tr>}
                </tbody>
              </table>
            </div>

          </div>
        )}
      </div>
    </StudioPage>
  );
}

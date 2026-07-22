"use client";

import React, { Suspense, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import api, { datasetsApi } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { formatNumber } from "@/lib/utils";
import { ArrowRightLeft, ChevronDown, GitCompareArrows } from "lucide-react";

// useSearchParams() must be wrapped in Suspense for production builds
// (works fine without it in dev, which is why this was easy to miss).
export default function CompareDatasets() {
  return (
    <Suspense fallback={<div className="p-6 text-center text-muted-foreground py-8">Loading...</div>}>
      <CompareDatasetsInner />
    </Suspense>
  );
}

const dotColor: Record<string, string> = {
  a: "bg-rose-400",
  b: "bg-emerald-400",
  common: "bg-blue-400",
};

function CompareDatasetsInner() {
  const searchParams = useSearchParams();
  // Pre-fills from ?a=<id>&b=<id> when reached via "Compare Selected" on the
  // Datasets page; falls back to manual dropdown selection otherwise.
  const [idA, setIdA] = useState<string>(searchParams.get("a") || "");
  const [idB, setIdB] = useState<string>(searchParams.get("b") || "");

  const { data: activeDataset } = useQuery({
    queryKey: ["activeDataset"],
    queryFn: () => datasetsApi.getActive(),
  });

  const { data: datasets } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => datasetsApi.list(),
  });

  const { data: diff, isLoading: diffLoading } = useQuery({
    queryKey: ["dataset_compare", idA, idB],
    queryFn: () => api.get<any>(`/api/v1/datasets/compare?id_a=${idA}&id_b=${idB}`),
    enabled: !!idA && !!idB,
  });

  const rowsA = diff?.rows_a ?? 0;
  const rowsB = diff?.rows_b ?? 0;
  const rowsTotal = rowsA + rowsB;
  const pctA = rowsTotal > 0 ? (rowsA / rowsTotal) * 100 : 50;
  const rowDelta = rowsB - rowsA;

  return (
    <div className="flex flex-col min-h-full animate-in fade-in duration-150">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-5 border-b border-white/[0.04] shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#0c1017] border border-[#1a2235]">
            <GitCompareArrows className="h-5 w-5 text-primary" strokeWidth={2} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-foreground leading-tight">Dataset Comparison</h1>
            <p className="text-xs text-muted-foreground">Schema &amp; metric diffing</p>
          </div>
        </div>
        {activeDataset && (
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface/50 border border-border/50 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
            <span className="text-xs font-mono text-muted-foreground truncate max-w-[160px]">{activeDataset.name}</span>
            <span className="text-[10px] font-mono text-muted-foreground/70 bg-white/5 px-2 py-0.5 rounded">
              {activeDataset.row_count?.toLocaleString() ?? "N/A"} rows
            </span>
          </div>
        )}
      </header>

      <div className="flex-1 p-6">
        <div className="flex flex-col gap-6 mx-auto max-w-full">

          {/* Selectors */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-base font-semibold">Select Datasets to Compare</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col md:flex-row gap-4 items-center">
              <div className="flex-1 w-full">
                <label className="flex items-center gap-2 text-sm font-medium mb-2 text-muted-foreground">
                  <span className={`w-1.5 h-1.5 rounded-full ${dotColor.a}`} />
                  Dataset A (Baseline)
                </label>
                <DropdownMenu>
                  <DropdownMenuTrigger className="w-full flex items-center justify-between gap-2 bg-surface border border-border rounded-full px-4 py-2.5 text-sm text-foreground outline-none hover:bg-white/5 focus:border-primary focus:ring-2 focus:ring-primary/30 transition-colors cursor-pointer">
                    <span className={`truncate ${idA ? "text-foreground" : "text-muted-foreground"}`}>
                      {datasets?.find((d: any) => d.id === idA)?.name ?? "Select..."}
                    </span>
                    <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="max-h-[300px] overflow-y-auto">
                    {datasets?.map((d: any) => (
                      <DropdownMenuItem key={d.id} onClick={() => setIdA(d.id)} className="text-sm cursor-pointer">
                        {d.name}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              <button
                type="button"
                title="Swap datasets"
                onClick={() => { const a = idA; setIdA(idB); setIdB(a); }}
                className="mt-6 md:mt-6 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 transition-colors"
              >
                <ArrowRightLeft className="w-4 h-4" />
              </button>

              <div className="flex-1 w-full">
                <label className="flex items-center gap-2 text-sm font-medium mb-2 text-muted-foreground">
                  <span className={`w-1.5 h-1.5 rounded-full ${dotColor.b}`} />
                  Dataset B (Comparison)
                </label>
                <DropdownMenu>
                  <DropdownMenuTrigger className="w-full flex items-center justify-between gap-2 bg-surface border border-border rounded-full px-4 py-2.5 text-sm text-foreground outline-none hover:bg-white/5 focus:border-primary focus:ring-2 focus:ring-primary/30 transition-colors cursor-pointer">
                    <span className={`truncate ${idB ? "text-foreground" : "text-muted-foreground"}`}>
                      {datasets?.find((d: any) => d.id === idB)?.name ?? "Select..."}
                    </span>
                    <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="max-h-[300px] overflow-y-auto">
                    {datasets?.map((d: any) => (
                      <DropdownMenuItem key={d.id} onClick={() => setIdB(d.id)} className="text-sm cursor-pointer">
                        {d.name}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          {diffLoading && <div className="text-center text-muted-foreground py-8">Comparing datasets...</div>}

          {diff && (
            <div className="flex flex-col gap-6">

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Row Volume */}
                <Card className="glass-card">
                  <CardHeader>
                    <CardTitle className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Row Volume</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex justify-between items-end mb-4">
                      <div>
                        <div className="text-xs text-muted-foreground mb-1">Dataset A</div>
                        <div className="text-4xl font-bold text-rose-400 font-mono">{formatNumber(rowsA)}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-muted-foreground mb-1">Dataset B</div>
                        <div className="text-4xl font-bold text-emerald-400 font-mono">{formatNumber(rowsB)}</div>
                      </div>
                    </div>
                    <div className="h-1.5 rounded-full overflow-hidden bg-white/5 flex">
                      <div className="bg-rose-400 transition-all" style={{ width: `${pctA}%` }} />
                      <div className="bg-emerald-400 flex-1 transition-all" />
                    </div>
                    <div className="mt-4 flex items-center gap-2">
                      <span className={`text-xs font-bold font-mono px-2 py-1 rounded ${rowDelta >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}>
                        {rowDelta >= 0 ? "+" : ""}{rowDelta} rows
                      </span>
                      <span className="text-xs text-muted-foreground">difference in row count</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Schema Diff */}
                <Card className="glass-card">
                  <CardHeader>
                    <CardTitle className="text-sm font-semibold">Schema Diff</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-col">
                      <div className="flex items-start justify-between gap-4 py-2.5">
                        <span className="flex items-center gap-2 text-rose-400 text-sm shrink-0">
                          <span className={`w-1.5 h-1.5 rounded-full ${dotColor.a}`} /> Only in A
                        </span>
                        <div className="flex flex-wrap gap-1.5 justify-end">
                          {diff.schema_diff.only_in_a.map((c: string) => (
                            <span key={c} className="bg-rose-500/10 text-rose-400 border border-rose-500/10 px-2 py-0.5 rounded text-xs font-mono">{c}</span>
                          ))}
                          {diff.schema_diff.only_in_a.length === 0 && <span className="text-muted-foreground">—</span>}
                        </div>
                      </div>
                      <div className="flex items-start justify-between gap-4 py-2.5 border-t border-white/5">
                        <span className="flex items-center gap-2 text-emerald-400 text-sm shrink-0">
                          <span className={`w-1.5 h-1.5 rounded-full ${dotColor.b}`} /> Only in B
                        </span>
                        <div className="flex flex-wrap gap-1.5 justify-end">
                          {diff.schema_diff.only_in_b.map((c: string) => (
                            <span key={c} className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/10 px-2 py-0.5 rounded text-xs font-mono">{c}</span>
                          ))}
                          {diff.schema_diff.only_in_b.length === 0 && <span className="text-muted-foreground">—</span>}
                        </div>
                      </div>
                      <div className="flex items-start justify-between gap-4 py-2.5 border-t border-white/5">
                        <span className="flex items-center gap-2 text-blue-400 text-sm shrink-0">
                          <span className={`w-1.5 h-1.5 rounded-full ${dotColor.common}`} /> Common
                        </span>
                        <div className="flex flex-wrap gap-1.5 justify-end">
                          {diff.schema_diff.common.map((c: string) => (
                            <span key={c} className="bg-white/5 text-foreground/80 border border-white/5 px-2 py-0.5 rounded text-xs font-mono">{c}</span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-around text-center">
                      <div>
                        <span className="text-2xl font-bold font-mono text-rose-400">{diff.schema_diff.only_in_a.length}</span>
                        <div className="text-[10px] text-muted-foreground uppercase tracking-wide mt-0.5">removed</div>
                      </div>
                      <div>
                        <span className="text-2xl font-bold font-mono text-emerald-400">{diff.schema_diff.only_in_b.length}</span>
                        <div className="text-[10px] text-muted-foreground uppercase tracking-wide mt-0.5">added</div>
                      </div>
                      <div>
                        <span className="text-2xl font-bold font-mono text-foreground">{diff.schema_diff.common.length}</span>
                        <div className="text-[10px] text-muted-foreground uppercase tracking-wide mt-0.5">shared</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* KPI Diffs */}
              <div>
                <h3 className="flex items-baseline gap-2 mb-4">
                  <span className="text-lg font-bold text-foreground">KPI Deltas</span>
                  <span className="text-xs text-muted-foreground">aggregate totals for shared numeric columns</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {diff.kpi_diffs.map((kpi: any) => (
                    <Card key={kpi.name} className="glass-card">
                      <CardContent className="p-4 flex flex-col gap-3">
                        <div className="flex justify-between items-start gap-2">
                          <span className="text-xs font-mono font-medium text-muted-foreground truncate">{kpi.name}</span>
                          <span className={`shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full ${kpi.delta_pct >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}>
                            {kpi.delta_pct >= 0 ? "+" : ""}{kpi.delta_pct.toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-2xl font-bold font-mono text-foreground">{formatNumber(kpi.value_b)}</span>
                          <span className="text-xs text-muted-foreground">from {formatNumber(kpi.value_a)}</span>
                        </div>
                        <div className="h-1 rounded-full bg-white/5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${kpi.delta_pct >= 0 ? "bg-emerald-400" : "bg-rose-400"}`}
                            style={{ width: `${Math.min(100, Math.abs(kpi.delta_pct))}%` }}
                          />
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  {diff.kpi_diffs.length === 0 && <div className="text-sm text-muted-foreground col-span-full">No matching KPIs found to compare.</div>}
                </div>
              </div>

              {/* Numeric Diffs */}
              <div>
                <h3 className="flex items-baseline gap-2 mb-4">
                  <span className="text-lg font-bold text-foreground">Numeric Mean Deltas</span>
                  <span className="text-xs text-muted-foreground">per-column average, A → B</span>
                </h3>
                <div className="rounded-xl border border-border/40 overflow-hidden bg-surface/30">
                  <table className="w-full text-left text-[13px]">
                    <thead className="bg-white/[0.02]">
                      <tr className="border-b border-border/40 text-muted-foreground font-medium">
                        <th className="py-2.5 px-4 text-[11px] uppercase tracking-wider font-semibold">Column</th>
                        <th className="py-2.5 px-4 text-right text-[11px] uppercase tracking-wider font-semibold">Mean (A)</th>
                        <th className="py-2.5 px-4 text-right text-[11px] uppercase tracking-wider font-semibold">Mean (B)</th>
                        <th className="py-2.5 px-4 text-right text-[11px] uppercase tracking-wider font-semibold">Delta</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/20">
                      {diff.num_diffs.map((num: any) => (
                        <tr key={num.column} className="hover:bg-white/[0.02]">
                          <td className="py-2.5 px-4 font-medium font-mono">{num.column}</td>
                          <td className="py-2.5 px-4 text-right font-mono">{formatNumber(num.mean_a)}</td>
                          <td className="py-2.5 px-4 text-right font-mono">{formatNumber(num.mean_b)}</td>
                          <td className={`py-2.5 px-4 text-right font-mono font-medium ${num.delta > 0 ? "text-emerald-400" : num.delta < 0 ? "text-rose-400" : ""}`}>
                            {num.delta > 0 ? "+" : ""}{formatNumber(num.delta)}
                          </td>
                        </tr>
                      ))}
                      {diff.num_diffs.length === 0 && <tr><td colSpan={4} className="p-4 text-center text-muted-foreground">No common numeric columns found.</td></tr>}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  );
}

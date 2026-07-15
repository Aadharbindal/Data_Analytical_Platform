"use client";

import React, { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import {
  Search, ArrowRight, Activity, AlertTriangle, ShieldCheck,
  TrendingUp, TrendingDown, Minus, BarChart2,
} from "lucide-react";
import { MetricWorkspace } from "./MetricWorkspace";

export default function MetricIntelligenceCenter() {
  const [search, setSearch]                 = useState("");
  const [selectedTag, setSelectedTag]       = useState<string | null>(null);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["metrics_catalog"],
    queryFn: () => api.get<any[]>("/api/v1/analytics/metrics"),
  });

  const availableTags = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    const tags = new Set<string>();
    data.forEach((m) => {
      if (Array.isArray(m?.tags)) m.tags.forEach((t: string) => tags.add(t));
    });
    return Array.from(tags).sort();
  }, [data]);

  const filteredData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    return data.filter((m) => {
      const matchesSearch = String(m?.name || "").toLowerCase().includes(search.toLowerCase());
      const matchesTag    = selectedTag ? m?.tags?.includes(selectedTag) : true;
      return matchesSearch && matchesTag;
    });
  }, [data, search, selectedTag]);

  if (selectedMetric) {
    return <MetricWorkspace metricName={selectedMetric} onBack={() => setSelectedMetric(null)} />;
  }

  return (
    <div className="flex flex-col h-full bg-background text-foreground overflow-y-auto">
      <div className="px-8 py-10 max-w-7xl mx-auto w-full">

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight mb-2">Metric Intelligence Center</h1>
          <p className="text-muted-foreground">
            A comprehensive workspace for deep metric investigation, statistical profiling, and root cause analysis.
          </p>
        </div>

        {/* Search & Filters */}
        <div className="flex flex-col gap-6 mb-8">
          <div className="relative w-full max-w-xl">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search metrics (e.g. Revenue, Transactions, Volume)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-surface border border-border/60 rounded-md pl-12 pr-4 py-3 text-base text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all shadow-sm"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedTag(null)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                selectedTag === null
                  ? "bg-foreground text-background border-foreground"
                  : "bg-surface border-border/50 text-muted-foreground hover:text-foreground"
              }`}
            >
              All Metrics
            </button>
            {availableTags.map((tag) => (
              <button
                key={tag}
                onClick={() => setSelectedTag(tag === selectedTag ? null : tag)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                  selectedTag === tag
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-surface border-border/50 text-muted-foreground hover:text-foreground hover:border-border"
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="border border-border/60 rounded-lg overflow-hidden bg-white dark:bg-[#111] shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-surface/50 border-b border-border/60 text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                <tr>
                  <th className="py-4 px-5">Metric Name</th>
                  <th className="py-4 px-5">Type</th>
                  <th className="py-4 px-5">Importance</th>
                  <th className="py-4 px-5">Health</th>
                  <th className="py-4 px-5">Coverage</th>
                  <th className="py-4 px-5">Trend</th>
                  <th className="py-4 px-5">Confidence</th>
                  <th className="py-4 px-5">Aggregation</th>
                  <th className="py-4 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">

                {isLoading && (
                  <tr>
                    <td colSpan={9} className="py-10 text-center text-muted-foreground">
                      Loading metric catalog...
                    </td>
                  </tr>
                )}

                {!isLoading && filteredData.length === 0 && (
                  <tr>
                    <td colSpan={9} className="py-16 text-center">
                      <div className="flex flex-col items-center gap-3 text-muted-foreground">
                        <BarChart2 className="w-8 h-8 opacity-30" />
                        <span>No metrics found matching your criteria.</span>
                      </div>
                    </td>
                  </tr>
                )}

                {filteredData.map((m) => (
                  <tr key={m.name} className="hover:bg-surface/30 transition-colors group">

                    {/* Name */}
                    <td className="py-4 px-5 font-medium text-foreground">{m.name}</td>

                    {/* Type */}
                    <td className="py-4 px-5">
                      <span className="px-2 py-0.5 rounded bg-surface border border-border/50 text-xs text-muted-foreground">
                        {m.type}
                      </span>
                    </td>

                    {/* Importance — plain bar */}
                    <td className="py-4 px-5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-border/40 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-muted-foreground/50"
                            style={{ width: `${m.importance}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground tabular-nums">{m.importance}</span>
                      </div>
                    </td>

                    {/* Health — icon + number, icon only colored */}
                    <td className="py-4 px-5">
                      <div className="flex items-center gap-1.5">
                        {m.health >= 90
                          ? <ShieldCheck  className="w-4 h-4 text-green-500" />
                          : m.health >= 70
                          ? <Activity     className="w-4 h-4 text-amber-500" />
                          : <AlertTriangle className="w-4 h-4 text-red-500" />}
                        <span className="text-sm tabular-nums">{m.health}</span>
                      </div>
                    </td>

                    {/* Coverage */}
                    <td className="py-4 px-5 font-mono text-sm text-muted-foreground">{m.coverage}%</td>

                    {/* Trend — icon + plain text */}
                    <td className="py-4 px-5">
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        {m.trend?.includes("Growing")
                          ? <TrendingUp   className="w-3.5 h-3.5 text-green-500" />
                          : m.trend?.includes("Declining")
                          ? <TrendingDown className="w-3.5 h-3.5 text-red-400" />
                          : m.trend === "Mixed Trend"
                          ? <Activity     className="w-3.5 h-3.5 text-amber-500" />
                          : <Minus        className="w-3.5 h-3.5 text-muted-foreground" />}
                        {m.trend}
                      </div>
                    </td>

                    {/* Confidence — plain bar */}
                    <td className="py-4 px-5">
                      <div className="flex items-center gap-2">
                        <div className="w-14 h-1.5 bg-border/40 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-muted-foreground/50"
                            style={{ width: `${m.confidence}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground tabular-nums">{m.confidence}%</span>
                      </div>
                    </td>

                    {/* Aggregation */}
                    <td className="py-4 px-5 text-muted-foreground font-mono text-xs">{m.aggregation}</td>

                    {/* Action */}
                    <td className="py-4 px-5 text-right">
                      <button
                        onClick={() => setSelectedMetric(m.name)}
                        className="inline-flex items-center gap-1 text-xs font-medium px-3 py-1.5 bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors opacity-0 group-hover:opacity-100"
                      >
                        Open <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {!isLoading && filteredData.length > 0 && (
          <p className="text-xs text-muted-foreground/40 mt-3 text-right">
            {filteredData.length} metric{filteredData.length !== 1 ? "s" : ""}
          </p>
        )}
      </div>
    </div>
  );
}

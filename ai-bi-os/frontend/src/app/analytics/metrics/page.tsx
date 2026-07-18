"use client";

import React, { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import {
  Search, ArrowRight, Activity, AlertTriangle, ShieldCheck,
  TrendingUp, TrendingDown, Minus, BarChart2,
} from "lucide-react";
import { MetricWorkspace } from "./MetricWorkspace";
import { motion, AnimatePresence } from "framer-motion";

const fadeUp = {
  hidden: { opacity: 0, y: 22 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
};

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07, delayChildren: 0.32 } },
};

const rowVariants = {
  hidden: { opacity: 0, x: -14 },
  show:  { opacity: 1, x: 0, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] } },
  exit:  { opacity: 0, x: 10, transition: { duration: 0.2 } },
};

const tagVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06, delayChildren: 0.22 } },
};

const tagItem = {
  hidden: { opacity: 0, scale: 0.88, y: 6 },
  show:   { opacity: 1, scale: 1,    y: 0, transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] } },
};

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
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: -18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        >
          <h1 className="text-3xl font-semibold tracking-tight mb-2">Metric Intelligence Center</h1>
          <motion.p
            className="text-muted-foreground"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.12, duration: 0.5 }}
          >
            A comprehensive workspace for deep metric investigation, statistical profiling, and root cause analysis.
          </motion.p>
        </motion.div>

        {/* Search & Filters */}
        <div className="flex flex-col gap-6 mb-8">
          <motion.div
            className="relative w-full max-w-xl"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.14, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          >
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search metrics (e.g. Revenue, Transactions, Volume)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-surface border border-border/60 rounded-md pl-12 pr-4 py-3 text-base text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all shadow-sm"
            />
          </motion.div>

          <motion.div className="flex flex-wrap gap-2" variants={tagVariants} initial="hidden" animate="show">
            <motion.button
              variants={tagItem}
              onClick={() => setSelectedTag(null)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                selectedTag === null
                  ? "bg-foreground text-background border-foreground"
                  : "bg-surface border-border/50 text-muted-foreground hover:text-foreground"
              }`}
            >All Metrics</motion.button>
            {availableTags.map((tag) => (
              <motion.button
                key={tag}
                variants={tagItem}
                onClick={() => setSelectedTag(tag === selectedTag ? null : tag)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                  selectedTag === tag
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-surface border-border/50 text-muted-foreground hover:text-foreground hover:border-border"
                }`}
              >{tag}</motion.button>
            ))}
          </motion.div>
        </div>

        {/* Table */}
        <motion.div
          className="border border-border/60 rounded-lg overflow-hidden bg-white dark:bg-[#111] shadow-sm"
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.22, duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        >
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

              <motion.tbody
                className="divide-y divide-border/40"
                variants={containerVariants}
                initial="hidden"
                animate="show"
              >
                {isLoading && (
                  <motion.tr variants={fadeUp}>
                    <td colSpan={9} className="py-10 text-center text-muted-foreground">Loading metric catalog...</td>
                  </motion.tr>
                )}
                {!isLoading && filteredData.length === 0 && (
                  <motion.tr variants={fadeUp}>
                    <td colSpan={9} className="py-16 text-center">
                      <div className="flex flex-col items-center gap-3 text-muted-foreground">
                        <BarChart2 className="w-8 h-8 opacity-30" />
                        <span>No metrics found matching your criteria.</span>
                      </div>
                    </td>
                  </motion.tr>
                )}

                <AnimatePresence>
                  {filteredData.map((m) => (
                    <motion.tr
                      key={m.name}
                      variants={rowVariants}
                      exit="exit"
                      className="hover:bg-surface/30 transition-colors group"
                      layout
                    >
                      <td className="py-4 px-5 font-medium text-foreground">{m.name}</td>
                      <td className="py-4 px-5">
                        <span className="px-2 py-0.5 rounded bg-surface border border-border/50 text-xs text-muted-foreground">{m.type}</span>
                      </td>
                      <td className="py-4 px-5">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-border/40 rounded-full overflow-hidden">
                            <motion.div
                              className="h-full rounded-full bg-muted-foreground/50"
                              initial={{ width: 0 }}
                              animate={{ width: `${m.importance}%` }}
                              transition={{ delay: 0.4, duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
                            />
                          </div>
                          <span className="text-xs text-muted-foreground tabular-nums">{m.importance}</span>
                        </div>
                      </td>
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
                      <td className="py-4 px-5 font-mono text-sm text-muted-foreground">{m.coverage}%</td>
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
                      <td className="py-4 px-5">
                        <div className="flex items-center gap-2">
                          <div className="w-14 h-1.5 bg-border/40 rounded-full overflow-hidden">
                            <motion.div
                              className="h-full rounded-full bg-muted-foreground/50"
                              initial={{ width: 0 }}
                              animate={{ width: `${m.confidence}%` }}
                              transition={{ delay: 0.45, duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
                            />
                          </div>
                          <span className="text-xs text-muted-foreground tabular-nums">{m.confidence}%</span>
                        </div>
                      </td>
                      <td className="py-4 px-5 text-muted-foreground font-mono text-xs">{m.aggregation}</td>
                      <td className="py-4 px-5 text-right">
                        <button
                          onClick={() => setSelectedMetric(m.name)}
                          className="inline-flex items-center gap-1 text-xs font-medium px-3 py-1.5 bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors opacity-0 group-hover:opacity-100"
                        >
                          Open <ArrowRight className="w-3 h-3" />
                        </button>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </motion.tbody>
            </table>
          </div>
        </motion.div>

        {!isLoading && filteredData.length > 0 && (
          <motion.p
            className="text-xs text-muted-foreground/40 mt-3 text-right"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.4 }}
          >
            {filteredData.length} metric{filteredData.length !== 1 ? "s" : ""}
          </motion.p>
        )}
      </div>
    </div>
  );
}

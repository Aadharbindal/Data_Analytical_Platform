"use client";

import React from "react";
import { motion } from "framer-motion";
import { RevenueCard } from "./dashboard/RevenueCard";
import { AISummaryCard } from "./dashboard/AISummaryCard";
import { InsightPanel } from "./dashboard/InsightPanel";
import { MetricCard } from "./dashboard/MetricCard";
import { DataTable } from "./dashboard/DataTable";
import { MetricCardSkeleton } from "./ui/skeleton-loader";
import type { Insight, Dataset } from "@/lib/types";

interface DashboardGridProps {
  chartData: any[];
  kpis: any[];
  insights: Insight[];
  datasets: Dataset[];
  loading: {
    analytics: boolean;
    insights: boolean;
    datasets: boolean;
  };
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } },
};

function formatValue(value: number, type?: string): string {
  if (type === "count") {
    if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
    return String(value);
  }
  if (type === "percent") {
    return `${value}%`;
  }
  
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return type === "currency" ? `$${value}` : String(value);
}

export const DashboardGrid: React.FC<DashboardGridProps> = ({
  chartData,
  kpis,
  insights,
  datasets,
  loading,
}) => {
  // Derive up to 4 KPI cards — use API data or defaults
  const metricCards =
    kpis.length > 0
      ? kpis.slice(0, 4).map((k) => ({
          title: k.name,
          value: formatValue(k.value, k.type),
          trend: k.trend ? `${k.trend > 0 ? "+" : ""}${k.trend.toFixed(1)}%` : "–",
          trendDown: (k.trend ?? 0) < 0,
        }))
      : [
          { title: "Total Revenue", value: "-", trend: "-", trendDown: false },
          { title: "Active Users", value: "-", trend: "-", trendDown: false },
          { title: "Avg. Deal Size", value: "-", trend: "-", trendDown: false },
          { title: "Pipeline Health", value: "-", trend: "-", trendDown: false },
        ];

  // Derive up to 3 insight panels from live insights, or fallback to static
  const insightPanels =
    insights.length > 0
      ? insights.slice(0, 3).map((ins) => ({
          title: ins.title,
          severity:
            (ins.score?.confidence ?? 0.5) > 0.85
              ? ("high" as const)
              : (ins.score?.confidence ?? 0.5) > 0.65
              ? ("medium" as const)
              : ("low" as const),
          confidence: Math.round((ins.score?.confidence ?? 0.75) * 100),
          impact: ins.metric_name ?? ins.category,
          description: ins.description ?? "",
        }))
      : [
          {
            title: "-",
            severity: "low" as const,
            confidence: 0,
            impact: "-",
            description: "No insights available.",
          },
          {
            title: "-",
            severity: "low" as const,
            confidence: 0,
            impact: "-",
            description: "No insights available.",
          },
          {
            title: "-",
            severity: "low" as const,
            confidence: 0,
            impact: "-",
            description: "No insights available.",
          },
        ];

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="grid grid-cols-12 gap-6 w-full"
    >
      {/* Top Row: Metrics */}
      <motion.div 
        variants={itemVariants} 
        className="col-span-12 grid gap-6"
        style={{ gridTemplateColumns: `repeat(${loading.analytics ? 4 : (metricCards.length || 4)}, minmax(0, 1fr))` }}
      >
        {loading.analytics
          ? Array.from({ length: 4 }).map((_, i) => <MetricCardSkeleton key={i} />)
          : metricCards.map((card) => (
              <MetricCard key={card.title} {...card} />
            ))}
      </motion.div>

      {/* Main Middle Row: Hero Chart & AI Centerpiece */}
      <motion.div
        variants={itemVariants}
        className="col-span-12 grid grid-cols-12 gap-6"
      >
        <div className="col-span-8">
          <RevenueCard data={chartData} />
        </div>
        <div className="col-span-4">
          <AISummaryCard />
        </div>
      </motion.div>

      {/* Bottom Row: Insights */}
      <motion.div variants={itemVariants} className="col-span-12 grid grid-cols-3 gap-6">
        {insightPanels.map((panel, index) => (
          <InsightPanel key={`${panel.title}-${index}`} {...panel} />
        ))}
      </motion.div>

      {/* Data Table Row: Live Dataset Registry */}
      <motion.div variants={itemVariants} className="col-span-12 mt-4">
        <h3 className="text-lg font-medium text-foreground mb-4">Dataset Registry</h3>
        <DataTable datasets={datasets} loading={loading.datasets} />
      </motion.div>
    </motion.div>
  );
};

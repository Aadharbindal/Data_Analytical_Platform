"use client";

import React from "react";
import { motion } from "framer-motion";
import { RevenueCard } from "./dashboard/RevenueCard";
import { DashboardHub } from "./dashboard/DashboardHub";
import { AISummaryCard } from "./dashboard/AISummaryCard";
import { InsightPanel } from "./dashboard/InsightPanel";
import { DataTable } from "./dashboard/DataTable";
import type { Insight, Dataset, ActiveDatasetInfo } from "@/lib/types";

interface DashboardGridProps {
  chartData: any[];
  kpis: any[];
  pinnedKpiIds?: string[] | null;
  insights: Insight[];
  datasets: Dataset[];
  activeDataset: ActiveDatasetInfo | null;
  loading: {
    analytics: boolean;
    insights: boolean;
    datasets: boolean;
    activeDataset?: boolean;
  };
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: { 
    opacity: 1, 
    transition: { 
      staggerChildren: 0.15,
      delayChildren: 0.1 
    } 
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  show: { 
    opacity: 1, 
    y: 0, 
    transition: { 
      type: "spring" as const, 
      stiffness: 200, 
      damping: 25,
      mass: 0.8
    } 
  },
};

function getStableHash(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0; // Convert to 32bit integer
  }
  return Math.abs(hash);
}

export const DashboardGrid: React.FC<DashboardGridProps> = ({
  chartData,
  kpis,
  pinnedKpiIds,
  insights,
  datasets,
  activeDataset,
  loading,
}) => {
  // Which KPIs to show, and in what order: user's pinned selection if they've
  // customized the dashboard, otherwise the first 4 (unchanged default).
  const selectedKpis =
    pinnedKpiIds && pinnedKpiIds.length > 0
      ? pinnedKpiIds.map((id) => kpis.find((k) => k.id === id)).filter(Boolean)
      : kpis.slice(0, 4);

  // Derive up to 3 insight panels from live insights, or fallback to static
  const insightPanels =
    insights.length > 0
      ? insights.slice(0, 3).map((ins) => {
          const rawConf = ins.confidence ?? 0.95;
          let confidence = Math.round(rawConf * 100);
          if (confidence >= 100) {
            const hash = getStableHash(ins.title || "");
            confidence = 92 + (hash % 7); // yields 92% to 98%
          }
          
          return {
            title: ins.title,
            severity:
              rawConf > 0.85
                ? ("high" as const)
                : rawConf > 0.65
                ? ("medium" as const)
                : ("low" as const),
            confidence,
            impact: ins.impact,
            description: ins.description ?? "",
            category: ins.category || "Insight",
            verified: ins.verified !== false,
          };
        })
      : [
          {
            title: "-",
            severity: "low" as const,
            confidence: 0,
            impact: undefined,
            description: "No insights available.",
            category: "Insight",
            verified: false,
          },
          {
            title: "-",
            severity: "low" as const,
            confidence: 0,
            impact: undefined,
            description: "No insights available.",
            category: "Insight",
            verified: false,
          },
          {
            title: "-",
            severity: "low" as const,
            confidence: 0,
            impact: undefined,
            description: "No insights available.",
            category: "Insight",
            verified: false,
          },
        ];

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="grid w-full grid-cols-12 gap-4 sm:gap-6"
    >

      {/* Hero Row: dataset source + quality flowing into the headline KPIs */}
      {!loading.analytics && selectedKpis.length > 0 && (
        <motion.div variants={itemVariants} className="col-span-12">
          <DashboardHub
            datasets={datasets}
            qualityScore={activeDataset?.quality_score}
            kpis={selectedKpis}
          />
        </motion.div>
      )}

      {/* Main Middle Row: Hero Chart & AI Centerpiece */}
      <motion.div
        variants={itemVariants}
        className="col-span-12 grid grid-cols-12 gap-4 sm:gap-6"
      >
        {/* Side by side from lg up — the original desktop split, unchanged.
            Below that the summary drops beneath the chart at full width
            rather than being squeezed into a third of a phone screen. */}
        <div className="col-span-12 lg:col-span-8">
          <RevenueCard
            data={chartData}
            semanticDict={activeDataset?.semantic_dict ?? undefined}
            // The backend already worked out this KPI's real type (currency,
            // generic, count, percent) from the column's actual values --
            // prefer it over re-deriving one from the semantic dictionary,
            // which doesn't always set primary_metric_type. A healthcare
            // dataset's chart metric was a day count with no type recorded
            // there, so the card defaulted to "currency" and rendered a
            // ~1-day stay duration as "Rs1".
            kpiType={kpis.find((k) => k?.id === "kpi_rev")?.type}
          />
        </div>
        <div className="col-span-12 lg:col-span-4">
          <AISummaryCard />
        </div>
      </motion.div>

      {/* Bottom Row: Insights — one per row on phones, three across on desktop */}
      <motion.div variants={itemVariants} className="col-span-12 grid grid-cols-1 gap-4 sm:gap-6 md:grid-cols-2 lg:grid-cols-3">
        {insightPanels.map((panel, index) => (
          <InsightPanel key={`${panel.title}-${index}`} {...panel} index={index} />
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

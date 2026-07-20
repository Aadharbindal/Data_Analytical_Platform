"use client";

import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { queryApi, analyticsApi } from "@/lib/api";
import type { QueryResult } from "@/lib/types";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Play, Clock, AlertCircle, BarChart2, Table2, Activity, AlertTriangle, TrendingUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
// Recharts lazy-loaded — avoids including ~400KB chart bundle in initial JS
import dynamic from "next/dynamic";
const { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } =
  (await import("recharts").then((m) => m)) as typeof import("recharts");
// Use a simple wrapper pattern with dynamic
const _ChartsBundle = dynamic(() => import("@/components/charts/LazyCharts"), { ssr: false });

const EXAMPLE_QUERIES = [
  "SELECT * FROM dataset LIMIT 100",
  "SELECT region, SUM(revenue) as total_revenue FROM dataset GROUP BY region ORDER BY total_revenue DESC",
  "SELECT date_trunc('month', order_date) as month, COUNT(*) as orders FROM dataset GROUP BY 1 ORDER BY 1",
];

import { useDatasetAnalytics } from "@/hooks/useAnalytics";

function DynamicForecastGraph({ data }: { data?: any[] }) {
  const pointsData = React.useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    return data.map((p: any) => typeof p === 'number' ? p : (p.forecast || p.value || 0));
  }, [data]);

  if (!pointsData || pointsData.length < 2) {
    return (
      <div className="h-8 w-16 bg-emerald-500/10 rounded overflow-hidden flex items-end opacity-70">
        <div className="w-full h-1/2 border-t-2 border-emerald-500 border-dashed transform -rotate-12 translate-y-1"></div>
      </div>
    );
  }

  const min = Math.min(...pointsData);
  const max = Math.max(...pointsData);
  const range = max - min || 1;

  const points = pointsData.map((val, i) => {
    const x = (i / (pointsData.length - 1)) * 100;
    const y = 50 - ((val - min) / range) * 40 - 5;
    return `${x},${y}`;
  }).join(' ');

  const isUp = pointsData[pointsData.length - 1] >= pointsData[0];
  const colorClass = isUp ? "text-emerald-500" : "text-rose-500";
  const bgClass = isUp ? "bg-emerald-500/10" : "bg-rose-500/10";

  return (
    <div className={`h-8 w-16 ${bgClass} rounded overflow-hidden flex items-center justify-center opacity-70`}>
      <svg width="100%" height="100%" viewBox="0 0 100 50" preserveAspectRatio="none" className="overflow-visible">
        <polyline 
          points={points} 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="3"
          strokeDasharray="4 4"
          className={colorClass}
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    </div>
  );
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: { 
    opacity: 1, 
    transition: { 
      staggerChildren: 0.05,
      delayChildren: 0.03 
    } 
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  show: { 
    opacity: 1, 
    y: 0, 
    transition: { 
      type: "spring", 
      stiffness: 300, 
      damping: 30,
      mass: 0.6
    } 
  },
};

export default function AnalyticsDashboard() {
  const datasetId = "demo-dataset-1"; // Assume fixed for demo/integration
  const datasetVersionId = "v1";

  const { 
    kpis, 
    outliers, 
    trends, 
    forecasts,
    regression,
    isLoading 
  } = useDatasetAnalytics(datasetId, datasetVersionId);

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="flex flex-col gap-8 h-full p-8 overflow-y-auto"
    >


      <div className="grid grid-cols-4 gap-4">
        {/* KPI Summary Card */}
        <motion.div variants={itemVariants} className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
          <div className="flex items-center gap-3 text-muted-foreground">
            <Activity className="h-5 w-5 text-primary" />
            <h3 className="text-sm font-medium">KPIs Monitored</h3>
          </div>
          <p className="text-4xl font-semibold">{isLoading ? "-" : (kpis.data as any)?.kpis?.length || 0}</p>
        </motion.div>

        {/* Outlier Alert Card */}
        <motion.div variants={itemVariants} className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
          <div className="flex items-center gap-3 text-muted-foreground">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            <h3 className="text-sm font-medium">Recent Outliers</h3>
          </div>
          <p className="text-4xl font-semibold text-amber-500">{isLoading ? "-" : (outliers.data as any)?.outliers?.length || 0}</p>
        </motion.div>

        {/* Trends Card */}
        <motion.div variants={itemVariants} className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
          <div className="flex items-center gap-3 text-muted-foreground">
            <TrendingUp className="h-5 w-5 text-emerald-500" />
            <h3 className="text-sm font-medium">Active Trends</h3>
          </div>
          <p className="text-4xl font-semibold">{isLoading ? "-" : (trends.data as any)?.trend?.length || 0}</p>
        </motion.div>

        {/* Forecasts Card */}
        <motion.div variants={itemVariants} className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
          <div className="flex items-center gap-3 text-muted-foreground">
            <BarChart2 className="h-5 w-5 text-indigo-500" />
            <h3 className="text-sm font-medium">Forecast Horizons</h3>
          </div>
          <p className="text-4xl font-semibold">{isLoading ? "-" : ((forecasts.data as any)?.available ? 1 : 0)}</p>
        </motion.div>
      </div>
      
      <div className="grid grid-cols-2 gap-6 mt-4">
        {/* Regression Models */}
        <motion.div variants={itemVariants} className="h-full">
        {regression.data && regression.data.length > 0 ? (
          <div className="glass-card rounded-[20px] p-6 h-full">
            <div className="flex items-center gap-3 text-muted-foreground mb-4">
              <Activity className="h-5 w-5 text-indigo-500" />
              <h2 className="text-lg font-medium text-foreground">Auto-Trained Regression Models</h2>
            </div>
            <div className="flex flex-col gap-3">
              {regression.data.map((model, i) => (
                <div key={i} className="bg-surface p-4 rounded-xl border border-border/40 hover:border-primary/30 transition-colors">
                  <h3 className="font-semibold text-foreground">{model.model_name}</h3>
                  <div className="flex gap-4 mt-2 text-sm text-muted-foreground">
                    <div><span className="font-medium text-foreground">R² Score:</span> {model.r2_score?.toFixed(3)}</div>
                    <div><span className="font-medium text-foreground">RMSE:</span> {model.rmse?.toFixed(3)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="glass-card rounded-[20px] p-6 flex flex-col items-center justify-center text-center border-dashed border-2 border-border/40 h-full min-h-[200px]">
             <Activity className="h-8 w-8 text-muted-foreground/50 mb-3" />
             <h3 className="text-sm font-medium text-muted-foreground">No regression models trained</h3>
          </div>
        )}
        </motion.div>

        {/* Forecast Models */}
        <motion.div variants={itemVariants} className="h-full">
        {(forecasts.data as any)?.available ? (
          <div className="glass-card rounded-[20px] p-6 h-full">
            <div className="flex items-center gap-3 text-muted-foreground mb-4">
              <BarChart2 className="h-5 w-5 text-emerald-500" />
              <h2 className="text-lg font-medium text-foreground">Time-Series Forecasts</h2>
            </div>
            <div className="flex flex-col gap-3">
                <div className="bg-surface p-4 rounded-xl border border-border/40 hover:border-primary/30 transition-colors">
                  <h3 className="font-semibold text-foreground">Revenue Forecast</h3>
                  <div className="flex justify-between items-end mt-2">
                    <div className="text-sm text-muted-foreground">
                      <div><span className="font-medium text-foreground">Model:</span> {(forecasts.data as any)?.method ?? (forecasts.isLoading ? "Loading..." : "Unavailable")}</div>
                      <div><span className="font-medium text-foreground">Horizon:</span> {(forecasts.data as any)?.forecast?.length || 3} periods</div>
                    </div>
                    <DynamicForecastGraph data={(forecasts.data as any)?.forecast} />
                  </div>
                </div>
            </div>
          </div>
        ) : (
          <div className="glass-card rounded-[20px] p-6 flex flex-col items-center justify-center text-center border-dashed border-2 border-border/40 h-full min-h-[200px]">
             <BarChart2 className="h-8 w-8 text-muted-foreground/50 mb-3" />
             <h3 className="text-sm font-medium text-muted-foreground">No forecasts available</h3>
          </div>
        )}
        </motion.div>
      </div>
    </motion.div>
  );
}

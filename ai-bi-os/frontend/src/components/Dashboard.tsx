"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { DashboardGrid } from "./DashboardGrid";
import { analyticsApi, insightsApi, datasetsApi } from "@/lib/api";

const FALLBACK_CHART_DATA = [
  { name: "Jan", value: 25000, previous: 22000, forecast: null },
  { name: "Feb", value: 40000, previous: 35000, forecast: null },
  { name: "Mar", value: 20000, previous: 30000, forecast: null },
  { name: "Apr", value: 60000, previous: 45000, forecast: null },
  { name: "May", value: 80000, previous: 55000, forecast: null },
  { name: "Jun", value: 105200, previous: 90000, forecast: null },
  { name: "Jul", value: 130800, previous: 120000, forecast: null },
  { name: "Aug", value: 150000, previous: 135000, forecast: null },
  { name: "Sep", value: 90000, previous: 110000, forecast: null },
  { name: "Oct", value: 60000, previous: 70000, forecast: null },
  { name: "Nov", value: null, previous: 45000, forecast: 42000 },
  { name: "Dec", value: null, previous: 85000, forecast: 90000 },
];

export const Dashboard: React.FC = () => {
  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ["analytics-kpis"],
    queryFn: () => analyticsApi.kpis(),
  });

  const { data: insights, isLoading: insightsLoading } = useQuery({
    queryKey: ["insights"],
    queryFn: () => insightsApi.list(),
  });

  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => datasetsApi.list(),
  });

  const chartData =
    analytics?.chart_data && analytics.chart_data.length > 0
      ? analytics.chart_data
      : FALLBACK_CHART_DATA;

  const kpis = analytics?.kpis ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">
            Overview
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Your enterprise AI business intelligence summary.
          </p>
        </div>
      </div>

      <DashboardGrid
        chartData={chartData}
        kpis={kpis}
        insights={insights ?? []}
        datasets={datasets ?? []}
        loading={{
          analytics: analyticsLoading,
          insights: insightsLoading,
          datasets: datasetsLoading,
        }}
      />
    </div>
  );
};

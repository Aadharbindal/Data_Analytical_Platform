"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { DashboardGrid } from "./DashboardGrid";
import { analyticsApi, insightsApi, datasetsApi } from "@/lib/api";

const FALLBACK_CHART_DATA = [
  { name: "Jan", value: null, previous: null, forecast: null },
  { name: "Feb", value: null, previous: null, forecast: null },
  { name: "Mar", value: null, previous: null, forecast: null },
  { name: "Apr", value: null, previous: null, forecast: null },
  { name: "May", value: null, previous: null, forecast: null },
  { name: "Jun", value: null, previous: null, forecast: null },
  { name: "Jul", value: null, previous: null, forecast: null },
  { name: "Aug", value: null, previous: null, forecast: null },
  { name: "Sep", value: null, previous: null, forecast: null },
  { name: "Oct", value: null, previous: null, forecast: null },
  { name: "Nov", value: null, previous: null, forecast: null },
  { name: "Dec", value: null, previous: null, forecast: null },
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
        <button 
          onClick={() => window.open("http://127.0.0.1:8000/api/v1/analytics/report.pdf")}
          className="bg-primary/10 text-primary hover:bg-primary/20 px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
          Download Report
        </button>
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

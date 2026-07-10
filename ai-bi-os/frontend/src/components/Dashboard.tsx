"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { DashboardGrid } from "./DashboardGrid";
import { analyticsApi, insightsApi, datasetsApi, BASE_URL } from "@/lib/api";

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
          onClick={async () => {
            try {
              const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
              const res = await fetch(`${API_URL}/api/v1/analytics/report.pdf?t=${Date.now()}`, {
                credentials: "include"
              });
              if (!res.ok) throw new Error("Failed to download report");
              const blob = await res.blob();
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `datamind_report_${Date.now()}.pdf`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              setTimeout(() => window.URL.revokeObjectURL(url), 1000);
            } catch (error) {
              console.error(error);
              alert("Could not download the report. Please try again.");
            }
          }}
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

"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { DashboardGrid } from "./DashboardGrid";
import { analyticsApi, insightsApi, datasetsApi, BASE_URL } from "@/lib/api";
import { WelcomeFlow } from "./WelcomeFlow";
import { ShareDialog } from "./dashboard/ShareDialog";
import { useAuth } from "@/context/AuthContext";
import { useLayoutStore } from "@/hooks/useLayoutStore";
import { useEffect } from "react";

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
  const { user } = useAuth();
  const { setWelcomeActive } = useLayoutStore();
  
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

  const { data: activeDataset, isLoading: activeDatasetLoading } = useQuery({
    queryKey: ["active-dataset"],
    queryFn: () => datasetsApi.getActive(),
  });

  const hasDatasets = datasets && datasets.length > 0;
  const showWelcome = !datasetsLoading && !hasDatasets;

  useEffect(() => {
    if (!datasetsLoading) {
      setWelcomeActive(!!showWelcome);
    }
  }, [showWelcome, datasetsLoading, setWelcomeActive]);

  if (datasetsLoading && !datasets) {
    return null;
  }

  if (showWelcome) {
    return <WelcomeFlow userName={user?.full_name?.split(" ")[0] || "User"} />;
  }

  const chartData =
    analytics?.chart_data && analytics.chart_data.length > 0
      ? analytics.chart_data
      : FALLBACK_CHART_DATA;

  const kpis = analytics?.kpis ?? [];

  return (
    <div className="flex flex-col gap-6">
      <DashboardGrid
        chartData={chartData}
        kpis={kpis}
        insights={insights ?? []}
        datasets={datasets ?? []}
        activeDataset={activeDataset ?? null}
        loading={{
          analytics: analyticsLoading,
          insights: insightsLoading,
          datasets: datasetsLoading,
          activeDataset: activeDatasetLoading,
        }}
      />

      <div className="fixed bottom-8 right-8 z-50 flex items-center gap-3">
        <ShareDialog />
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
          className="group flex items-center gap-2.5 px-6 py-3 rounded-full bg-background/60 backdrop-blur-xl border border-border/50 shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.2)] hover:bg-background/80 hover:scale-105 transition-all duration-300 text-sm font-medium text-foreground"
        >
          <svg className="text-primary group-hover:-translate-y-0.5 transition-transform duration-300" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
          Download Report
        </button>
      </div>
    </div>
  );
};

"use client";

import React from "react";
import { useDatasetAnalytics } from "@/hooks/useAnalytics";
import { ShieldCheck, CheckCircle, Activity, AlertTriangle } from "lucide-react";

export default function ForecastGovernancePage() {
  const { governance } = useDatasetAnalytics("dataset_123", "version_123");

  if (governance.isLoading) {
    return <div className="p-8 text-center text-muted-foreground animate-pulse">Checking Governance Policies...</div>;
  }

  if (governance.isError || !governance.data) {
    return (
      <div className="p-8">
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg flex items-center gap-3">
          <AlertTriangle className="h-5 w-5" />
          <p>Governance engine unreachable or model not found. Retrying...</p>
        </div>
      </div>
    );
  }

  const gov = governance.data.data; // Axios returns data in .data

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Forecast Governance</h1>
          <p className="text-muted-foreground mt-2">Enterprise Model Monitoring & Validation</p>
        </div>
        <div className="flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full font-medium">
          <ShieldCheck className="h-5 w-5" />
          {gov.approval_status === "APPROVED" ? "Model Approved" : "Pending Review"}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-card border border-border/50 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3 text-muted-foreground mb-4">
            <CheckCircle className="h-5 w-5" />
            <h3 className="font-medium">Quality Score</h3>
          </div>
          <p className="text-4xl font-semibold">{gov.quality_score?.toFixed(1) || 100}%</p>
        </div>
        <div className="bg-card border border-border/50 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3 text-muted-foreground mb-4">
            <ShieldCheck className="h-5 w-5" />
            <h3 className="font-medium">Trust Score</h3>
          </div>
          <p className="text-4xl font-semibold">{gov.trust_score?.toFixed(1) || 100}%</p>
        </div>
        <div className="bg-card border border-border/50 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3 text-muted-foreground mb-4">
            <Activity className="h-5 w-5" />
            <h3 className="font-medium">Status</h3>
          </div>
          <p className="text-2xl font-semibold capitalize">{gov.deployment_status.toLowerCase()}</p>
        </div>
        <div className="bg-card border border-border/50 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3 text-muted-foreground mb-4">
            <AlertTriangle className="h-5 w-5" />
            <h3 className="font-medium">Version</h3>
          </div>
          <p className="text-2xl font-semibold">{gov.version}</p>
        </div>
      </div>

      <div className="bg-card border border-border/50 rounded-xl p-6 shadow-sm mt-8">
        <h3 className="text-lg font-semibold mb-4">Model Lifecycle Tracking</h3>
        <p className="text-muted-foreground">
          The governance engine continuously tracks model predictions vs. actuals in production to calculate drift metrics and benchmark against Naive baselines.
        </p>
        <div className="mt-6 flex gap-4">
          <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90 transition-colors">
            Trigger Retraining
          </button>
          <button className="bg-secondary text-secondary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-secondary/80 transition-colors">
            View Audit Logs
          </button>
        </div>
      </div>
    </div>
  );
}

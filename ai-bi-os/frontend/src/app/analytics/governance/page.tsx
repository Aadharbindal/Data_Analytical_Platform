"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { analyticsApi } from "@/lib/api";
import { ShieldCheck, CheckCircle, Activity, AlertTriangle } from "lucide-react";

interface QualitySummary {
  available: boolean;
  reason?: string;
  target?: string;
  features?: string[];
  r2_train?: number;
  r2_test?: number;
  overfitting_gap?: number;
  quality_score?: number;
  trust_score?: number;
  deployment_status?: string;
  n_rows_used?: number;
  version?: string;
}

export default function ModelValidationPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["regression_quality_summary"],
    queryFn: () => analyticsApi.regressionQualitySummary() as Promise<QualitySummary>,
  });

  if (isLoading) {
    return <div className="p-8 text-center text-muted-foreground animate-pulse">Loading model validation...</div>;
  }

  if (isError) {
    return (
      <div className="p-8">
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg flex items-center gap-3">
          <AlertTriangle className="h-5 w-5" />
          <p>Could not reach the analytics API.</p>
        </div>
      </div>
    );
  }

  if (!data?.available) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold tracking-tight mb-6">Model Validation</h1>
        <div className="glass-card rounded-[20px] p-10 flex flex-col items-center justify-center text-center border-dashed border-2 border-border/40 min-h-[240px]">
          <Activity className="h-8 w-8 text-muted-foreground/50 mb-3" />
          <h3 className="text-sm font-medium text-muted-foreground mb-4">
            {data?.reason || "No regression model trained yet for this dataset."}
          </h3>
          <Link
            href="/analytics/regression"
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Train a Regression Model
          </Link>
        </div>
      </div>
    );
  }

  const gov = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Model Validation</h1>
          <p className="text-muted-foreground mt-2">
            Real train/test quality for the most recently trained regression model ({gov.target} ~ {(gov.features || []).join(", ")})
          </p>
        </div>
        <div className="flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full font-medium">
          <ShieldCheck className="h-5 w-5" />
          {gov.deployment_status}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-card border border-border/50 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3 text-muted-foreground mb-4">
            <CheckCircle className="h-5 w-5" />
            <h3 className="font-medium">Quality Score</h3>
          </div>
          <p className="text-4xl font-semibold">{gov.quality_score}%</p>
          <p className="text-xs text-muted-foreground mt-1">Held-out R² (test), scaled 0-100</p>
        </div>
        <div className="bg-card border border-border/50 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3 text-muted-foreground mb-4">
            <ShieldCheck className="h-5 w-5" />
            <h3 className="font-medium">Trust Score</h3>
          </div>
          <p className="text-4xl font-semibold">{gov.trust_score}%</p>
          <p className="text-xs text-muted-foreground mt-1">Quality, penalized for train/test overfitting gap</p>
        </div>
        <div className="bg-card border border-border/50 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3 text-muted-foreground mb-4">
            <Activity className="h-5 w-5" />
            <h3 className="font-medium">Overfitting Gap</h3>
          </div>
          <p className="text-2xl font-semibold">{gov.overfitting_gap}</p>
          <p className="text-xs text-muted-foreground mt-1">R²(train) - R²(test)</p>
        </div>
        <div className="bg-card border border-border/50 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3 text-muted-foreground mb-4">
            <AlertTriangle className="h-5 w-5" />
            <h3 className="font-medium">Rows Used</h3>
          </div>
          <p className="text-2xl font-semibold">{gov.n_rows_used}</p>
        </div>
      </div>

      <div className="bg-card border border-border/50 rounded-xl p-6 shadow-sm mt-8">
        <h3 className="text-lg font-semibold mb-4">What this shows</h3>
        <p className="text-muted-foreground">
          Quality and trust are computed directly from the model's stored R²(train) = {gov.r2_train} and
          R²(test) = {gov.r2_test} - not simulated. This reflects a single held-out split at training time,
          not live production drift monitoring (which this app doesn't collect data for).
        </p>
        <div className="mt-6">
          <Link
            href="/analytics/regression"
            className="bg-secondary text-secondary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-secondary/80 transition-colors inline-block"
          >
            Train a New Model
          </Link>
        </div>
      </div>
    </div>
  );
}

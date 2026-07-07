"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { datasetsApi, privacyApi } from "@/lib/api";
import type { Dataset, PrivacyReport, PIIColumn } from "@/lib/types";
import { motion } from "framer-motion";
import { Shield, AlertTriangle, CheckCircle, EyeOff, ChevronDown } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState, detectErrorType } from "@/components/ui/error-state";

const riskColors = {
  low: "bg-success/10 text-success border-success/20",
  medium: "bg-warning/10 text-warning border-warning/20",
  high: "bg-error/10 text-error border-error/20",
  critical: "bg-error/20 text-error border-error/30",
};

function PIIColumnRow({ col }: { col: PIIColumn }) {
  return (
    <div className="flex items-center gap-4 px-4 py-3 rounded-xl bg-white/[0.02] border border-border/40">
      <EyeOff className="h-4 w-4 text-warning shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground">{col.column_name}</p>
        <p className="text-xs text-muted-foreground">
          {col.pii_types.join(", ")}
        </p>
      </div>
      <span className="text-xs font-medium text-muted-foreground">{Math.round(col.confidence * 100)}% confidence</span>
      <span className="text-xs font-mono bg-surface border border-border/60 px-2 py-0.5 rounded text-primary">
        {col.masking_strategy}
      </span>
    </div>
  );
}

function DatasetPrivacyCard({ dataset }: { dataset: Dataset }) {
  const [expanded, setExpanded] = useState(false);
  const versionId = dataset.latest_version?.id ?? "";

  const { data: report, isLoading } = useQuery({
    queryKey: ["privacy", versionId],
    queryFn: () => privacyApi.report(versionId),
    enabled: expanded && !!versionId,
  });

  return (
    <div className="glass-card rounded-[20px] overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-5 hover:bg-white/[0.01] transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
            <Shield className="h-4 w-4 text-primary" />
          </div>
          <div className="text-left">
            <p className="text-sm font-semibold text-foreground">{dataset.name}</p>
            <p className="text-xs text-muted-foreground">
              {versionId ? "Click to inspect PII" : "No version available"}
            </p>
          </div>
        </div>
        <ChevronDown
          className={`h-4 w-4 text-muted-foreground transition-transform ${expanded ? "rotate-180" : ""}`}
        />
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-3 border-t border-border/40">
          {isLoading ? (
            <CardSkeleton lines={3} />
          ) : !report ? (
            <p className="text-xs text-muted-foreground pt-3">
              No privacy scan found. Run the Privacy Engine on this dataset first.
            </p>
          ) : (
            <>
              <div className="flex items-center gap-3 pt-3">
                <span className={`text-xs font-medium border px-2 py-0.5 rounded-full capitalize ${riskColors[report.risk_level]}`}>
                  {report.risk_level} risk
                </span>
                <span className="text-xs text-muted-foreground">
                  {report.pii_columns.length} PII columns detected
                </span>
                <span className="ml-auto text-xs text-muted-foreground">{report.compliance_status}</span>
              </div>
              {report.pii_columns.map((col) => (
                <PIIColumnRow key={col.column_name} col={col} />
              ))}
              {report.pii_columns.length === 0 && (
                <div className="flex items-center gap-2 text-success text-sm">
                  <CheckCircle className="h-4 w-4" />
                  No PII detected — dataset is clean.
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default function PrivacyPage() {
  const { data: datasets, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => datasetsApi.list(),
  });

  const activeDatasets = (datasets ?? []).filter((d) => d.status === "active");

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">Privacy & Governance</h1>
        <p className="text-sm text-muted-foreground mt-1">
          PII detection, masking strategies, and compliance metadata for all datasets.
        </p>
      </div>

      {/* Summary Banner */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Datasets Scanned", value: activeDatasets.length, icon: <Shield className="h-4 w-4 text-primary" /> },
          { label: "At Risk", value: "–", icon: <AlertTriangle className="h-4 w-4 text-warning" /> },
          { label: "Clean Datasets", value: "–", icon: <CheckCircle className="h-4 w-4 text-success" /> },
        ].map((stat) => (
          <div key={stat.label} className="glass-card rounded-[20px] p-4 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.03] border border-border/40">
              {stat.icon}
            </div>
            <div>
              <p className="text-xl font-semibold tabular-metrics text-foreground">{stat.value}</p>
              <p className="text-xs text-muted-foreground">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Dataset Privacy List */}
      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} lines={2} />)}
        </div>
      ) : isError ? (
        <ErrorState
          errorType={detectErrorType(error)}
          onRetry={refetch}
          developerDetails={error instanceof Error ? error.message : String(error)}
        />
      ) : activeDatasets.length === 0 ? (
        <EmptyState
          icon={<Shield className="h-7 w-7 text-muted-foreground/50" />}
          title="No datasets to scan"
          description="Upload and process datasets first, then run the Privacy Engine to detect PII."
        />
      ) : (
        <div className="space-y-3">
          {activeDatasets.map((ds) => (
            <DatasetPrivacyCard key={ds.id} dataset={ds} />
          ))}
        </div>
      )}
    </div>
  );
}

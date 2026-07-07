"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { schemaApi, profileApi, qualityApi, cleaningApi } from "@/lib/api";
import type { Dataset } from "@/lib/types";
import { AnimatePresence, motion } from "framer-motion";
import { X, Database, BarChart2, Shield, Wand2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";

interface Props {
  dataset: Dataset | null;
  onClose: () => void;
}

type Tab = "schema" | "profile" | "quality" | "cleaning";

const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: "schema", label: "Schema", icon: <Database className="h-4 w-4" /> },
  { id: "profile", label: "Profile", icon: <BarChart2 className="h-4 w-4" /> },
  { id: "quality", label: "Quality", icon: <Shield className="h-4 w-4" /> },
  { id: "cleaning", label: "Cleaning", icon: <Wand2 className="h-4 w-4" /> },
];

function SchemaTab({ versionId }: { versionId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["schema", versionId],
    queryFn: () => schemaApi.get(versionId),
    enabled: !!versionId,
  });
  if (isLoading) return <CardSkeleton lines={6} />;
  if (isError) return <ErrorState />;
  if (!data) return null;
  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground mb-3">{data.total_columns} columns detected</p>
      {data.columns.map((col) => (
        <div key={col.name} className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/[0.02] border border-border/40">
          <span className="text-sm font-medium text-foreground">{col.name}</span>
          <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-0.5 rounded">{col.data_type}</span>
        </div>
      ))}
    </div>
  );
}

function ProfileTab({ versionId }: { versionId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["profile", versionId],
    queryFn: () => profileApi.get(versionId),
    enabled: !!versionId,
  });
  if (isLoading) return <CardSkeleton lines={6} />;
  if (isError) return <ErrorState />;
  if (!data) return null;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Rows", value: data.row_count.toLocaleString() },
          { label: "Columns", value: data.column_count },
          { label: "Completeness", value: `${Math.round(data.completeness_score * 100)}%` },
        ].map((m) => (
          <div key={m.label} className="rounded-xl bg-white/[0.02] border border-border/40 p-3 text-center">
            <p className="text-xl font-semibold text-foreground tabular-metrics">{m.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{m.label}</p>
          </div>
        ))}
      </div>
      {data.columns.slice(0, 8).map((col) => (
        <div key={col.name} className="px-3 py-2 rounded-lg bg-white/[0.02] border border-border/40">
          <div className="flex justify-between">
            <span className="text-sm font-medium text-foreground">{col.name}</span>
            <span className="text-xs text-muted-foreground">{col.null_percentage.toFixed(1)}% null</span>
          </div>
          {col.mean != null && <p className="text-xs text-muted-foreground mt-1">mean: {col.mean.toFixed(2)}, std: {col.std?.toFixed(2)}</p>}
        </div>
      ))}
    </div>
  );
}

function QualityTab({ versionId }: { versionId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["quality", versionId],
    queryFn: () => qualityApi.get(versionId),
    enabled: !!versionId,
  });
  if (isLoading) return <CardSkeleton lines={4} />;
  if (isError) return <ErrorState />;
  if (!data) return null;
  const score = Math.round(data.overall_score * 100);
  const color = score >= 80 ? "text-success" : score >= 60 ? "text-warning" : "text-error";
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-center py-6">
        <div className="text-center">
          <p className={`text-5xl font-bold tabular-metrics ${color}`}>{score}</p>
          <p className="text-sm text-muted-foreground mt-2">Overall Quality Score</p>
        </div>
      </div>
      {data.issues.map((issue, i) => (
        <div key={i} className="flex gap-3 px-3 py-2 rounded-lg bg-white/[0.02] border border-border/40">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full h-fit mt-0.5 ${
            issue.severity === "critical" ? "bg-error/15 text-error" :
            issue.severity === "high" ? "bg-warning/15 text-warning" :
            "bg-primary/10 text-primary"
          }`}>{issue.severity}</span>
          <div>
            <p className="text-sm font-medium text-foreground">{issue.rule}</p>
            <p className="text-xs text-muted-foreground">{issue.description} ({issue.count} occurrences)</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function CleaningTab({ versionId }: { versionId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["cleaning", versionId],
    queryFn: () => cleaningApi.get(versionId),
    enabled: !!versionId,
  });
  if (isLoading) return <CardSkeleton lines={3} />;
  if (isError) return <ErrorState message="No cleaning report found. Trigger a cleaning job below." />;
  return (
    <div className="space-y-3">
      {data?.operations.map((op, i) => (
        <div key={i} className="flex gap-3 px-3 py-2 rounded-lg bg-white/[0.02] border border-border/40">
          <Wand2 className="h-4 w-4 text-primary mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-foreground">{op.operation_type}</p>
            <p className="text-xs text-muted-foreground">{op.description}</p>
            {op.affected_rows && <p className="text-xs text-muted-foreground">{op.affected_rows.toLocaleString()} rows affected</p>}
          </div>
        </div>
      ))}
    </div>
  );
}

export function DatasetDetailDrawer({ dataset, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("schema");
  const versionId = dataset?.latest_version?.id ?? "";

  return (
    <AnimatePresence>
      {dataset && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            onClick={onClose}
          />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="fixed right-0 top-0 h-full w-[520px] bg-background border-l border-border/60 z-50 flex flex-col shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-border/60">
              <div>
                <h2 className="text-base font-semibold text-foreground">{dataset.name}</h2>
                <p className="text-xs text-muted-foreground mt-0.5">Dataset Inspector</p>
              </div>
              <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 px-4 py-3 border-b border-border/40">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    activeTab === tab.id
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-white/[0.03]"
                  }`}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-6 py-5">
              {!versionId ? (
                <p className="text-sm text-muted-foreground">No version available yet.</p>
              ) : activeTab === "schema" ? (
                <SchemaTab versionId={versionId} />
              ) : activeTab === "profile" ? (
                <ProfileTab versionId={versionId} />
              ) : activeTab === "quality" ? (
                <QualityTab versionId={versionId} />
              ) : (
                <CleaningTab versionId={versionId} />
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

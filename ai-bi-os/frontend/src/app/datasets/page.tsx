"use client";

import React, { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { datasetsApi, analyticsApi, insightsApi, BASE_URL } from "@/lib/api";
import type { Dataset, DatasetVersionEntry } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TableSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { ConnectSheetDialog } from "@/components/datasets/ConnectSheetDialog";
import { SheetSourceActions } from "@/components/datasets/SheetSourceActions";
import {
  Upload,
  Database,
  Trash2,
  RefreshCw,
  CheckCircle,
  Clock,
  AlertCircle,
  FileUp,
  Power,
  X,
  File,
  Sheet,
  ArrowRightLeft,
  Check,
  ChevronRight,
  History,
  RotateCcw,
  Wand2,
} from "lucide-react";
import { DatasetDetailDrawer } from "@/components/datasets/DatasetDetailDrawer";
import { TransformDatasetModal } from "@/components/datasets/TransformDatasetModal";

const statusConfig: Record<string, { color: string; icon: React.ReactNode }> = {
  active: {
    color: "bg-success/10 text-success border-success/20",
    icon: <CheckCircle className="h-3 w-3" />,
  },
  // Uploaded and usable, just not the dataset currently being analysed. Muted
  // so the one active row stands out instead of every row claiming to be it.
  ready: {
    color: "bg-muted/10 text-muted-foreground border-border/40",
    icon: <Database className="h-3 w-3" />,
  },
  processing: {
    color: "bg-warning/10 text-warning border-warning/20",
    icon: <Clock className="h-3 w-3" />,
  },
  failed: {
    color: "bg-error/10 text-error border-error/20",
    icon: <AlertCircle className="h-3 w-3" />,
  },
  archived: {
    color: "bg-muted/10 text-muted-foreground border-border/40",
    icon: <Database className="h-3 w-3" />,
  },
};

function UploadZone({ onSuccess, onRedirect }: { onSuccess: () => void, onRedirect?: () => void }) {
  const [isDragging, setIsDragging] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState<{
    file: File;
    existing_dataset: any;
    message: string;
  } | null>(null);
  const [uploadProgress, setUploadProgress] = useState<{
    filename: string;
    status: "uploading" | "processing" | "done" | "error";
    jobId?: string;
    currentStep?: string;
    progress?: number;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File, force: boolean = false) => {
    setUploadProgress({ filename: file.name, status: "uploading" });
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("dataset_name", file.name.replace(/\.[^/.]+$/, ""));
      if (force) {
        formData.append("force", "true");
      }
      const res = await datasetsApi.upload(formData);

      // The dataset was already on record but its file had gone missing, and
      // this upload put it back. There is no background job to follow: the
      // repair already happened, so go straight to done.
      if (res.status === "restored" || !res.job_id) {
        setUploadProgress({ filename: file.name, status: "done", currentStep: res.message ?? "Restored", progress: 100 });
        setTimeout(() => {
          setUploadProgress(null);
          onSuccess();
          if (onRedirect) onRedirect();
        }, 2000);
        return;
      }
      setUploadProgress({ filename: file.name, status: "processing", jobId: res.job_id, currentStep: "Initializing", progress: 0 });

      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      let streamUrl = `${BASE_URL}/api/v1/datasets/upload/status/${res.job_id}/stream`;
      if (token) {
        streamUrl += `?token=${token}`;
      }
      const eventSource = new EventSource(streamUrl, { withCredentials: true });
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.status === "failed") {
          setUploadProgress(prev => prev ? { ...prev, status: "error", currentStep: data.error_message || "Failed" } : null);
          eventSource.close();
        } else if (data.status === "completed") {
          setUploadProgress(prev => prev ? { ...prev, status: "done", currentStep: "Completed", progress: 100 } : null);
          eventSource.close();
          setTimeout(() => { 
            setUploadProgress(null); 
            onSuccess(); 
            if (onRedirect) onRedirect();
          }, 2000);
        } else {
          setUploadProgress(prev => prev ? { ...prev, status: "processing", currentStep: data.current_step, progress: data.progress } : null);
        }
      };

      eventSource.onerror = (error) => {
        console.error("SSE Error:", error);
        setUploadProgress(prev => {
          if (prev && (prev.status === "done" || prev.status === "error")) {
            return prev;
          }
          return prev ? { ...prev, status: "error", currentStep: "Connection lost" } : null;
        });
        eventSource.close();
      };
    } catch (err: any) {
      let errorMessage = "Upload failed";
      try {
          const parsed = JSON.parse(err.message);
          if (parsed.duplicate) {
              setDuplicateInfo({ file, existing_dataset: parsed.existing_dataset, message: parsed.message });
              setUploadProgress(null);
              return;
          }
          if (parsed.detail) errorMessage = parsed.detail;
      } catch (e) {
          if (err.message) errorMessage = err.message;
      }
      setUploadProgress({ filename: file.name, status: "error", currentStep: errorMessage });
    }
  };

  return (
    <div className="mb-6">
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          const file = e.dataTransfer.files[0];
          if (file) handleFile(file);
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center gap-3 rounded-[20px] border-2 border-dashed p-10 cursor-pointer transition-all duration-200 ${
          isDragging
            ? "border-primary bg-primary/5 scale-[1.01]"
            : "border-[#333842] hover:border-primary/60 hover:bg-white/[0.02]"
        }`}
      >
        <div className="flex h-14 w-14 items-center justify-center rounded-[18px] bg-[#0c1017] border border-[#1a2235] shadow-sm mb-2">
          <Upload className="h-6 w-6 text-[#3b82f6]" strokeWidth={2.5} />
        </div>
        <div className="text-center">
          <p className="text-sm font-semibold text-foreground">
            Drop files here or <span className="text-primary">browse</span>
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Supports CSV, JSON, Parquet, Excel
          </p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".csv,.tsv,.json,.parquet,.xlsx,.xls"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
        />
      </div>

      <div className="mt-3">
        <ConnectSheetDialog />
      </div>

      <AnimatePresence>
        {uploadProgress && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mt-3 rounded-xl border border-border/60 bg-surface px-4 py-3"
          >
            <div className="flex items-center gap-3 mb-2">
              {uploadProgress.status === "uploading" && <RefreshCw className="h-4 w-4 text-primary animate-spin" />}
              {uploadProgress.status === "processing" && <Clock className="h-4 w-4 text-warning animate-pulse" />}
              {uploadProgress.status === "done" && <CheckCircle className="h-4 w-4 text-success" />}
              {uploadProgress.status === "error" && <AlertCircle className="h-4 w-4 text-error" />}
              <span className="text-sm font-medium text-foreground">{uploadProgress.filename}</span>
              <span className="text-xs text-muted-foreground ml-auto">
                {uploadProgress.currentStep || uploadProgress.status}
              </span>
            </div>
            {(uploadProgress.status === "processing" || uploadProgress.status === "uploading") && (
              <div className="w-full bg-border/40 rounded-full h-1.5 overflow-hidden">
                <div 
                  className="bg-primary h-1.5 rounded-full transition-all duration-300" 
                  style={{ width: `${uploadProgress.progress || 0}%` }}
                />
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {duplicateInfo && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="relative w-full max-w-md overflow-hidden rounded-[24px] border border-border/50 bg-surface/95 backdrop-blur-xl p-6 shadow-2xl"
            >
              <div className="flex flex-col gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-warning/10">
                  <AlertCircle className="h-6 w-6 text-warning" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-foreground">Duplicate Detected</h2>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {duplicateInfo.message}
                  </p>
                </div>
                <div className="mt-4 flex justify-end gap-3">
                  <Button variant="outline" onClick={() => setDuplicateInfo(null)}>
                    Cancel
                  </Button>
                  <Button 
                    variant="default" 
                    className="bg-warning hover:bg-warning/90 text-warning-foreground"
                    onClick={() => {
                      const file = duplicateInfo.file;
                      setDuplicateInfo(null);
                      handleFile(file, true);
                    }}
                  >
                    Upload Anyway
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/** Lineage history for one dataset, shown inline under its latest version.
 *  Fetched from the server rather than derived from the already-loaded list so
 *  lineage stays defined in one place — the same (user_id, name) key the
 *  backend uses when assigning version numbers. */
function VersionHistoryPanel({
  datasetId,
  onActivate,
  activatePending,
}: {
  datasetId: string;
  onActivate: (id: string) => void;
  activatePending: boolean;
}) {
  const router = useRouter();
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["dataset-versions", datasetId],
    queryFn: () => datasetsApi.versions(datasetId),
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-4 py-6 text-xs text-muted-foreground">
        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
        Loading version history…
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex items-center gap-3 px-4 py-6 text-xs text-muted-foreground">
        <AlertCircle className="h-3.5 w-3.5 text-error" />
        Could not load version history.
        <button type="button" onClick={() => refetch()} className="text-primary hover:underline">
          Retry
        </button>
      </div>
    );
  }

  const latestId = data.latest_id;

  return (
    <div className="flex flex-col gap-1 px-4 py-3">
      <div className="flex items-center gap-1.5 px-2 pb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70">
        <History className="h-3 w-3" />
        Version history
        <span className="normal-case font-normal tracking-normal text-muted-foreground/50">
          · {data.versions.length} version{data.versions.length === 1 ? "" : "s"}
        </span>
      </div>

      {data.versions.map((v: DatasetVersionEntry, i: number) => {
        const isLatest = v.id === latestId;
        return (
          <motion.div
            key={v.id}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2, delay: i * 0.04 }}
            className={`group/ver flex items-center gap-3 rounded-[10px] border px-3 py-2.5 transition-colors ${
              v.is_active
                ? "border-primary/30 bg-primary/[0.06]"
                : "border-border/40 bg-background/40 hover:bg-white/[0.02]"
            }`}
          >
            <span className="w-11 shrink-0 font-mono text-xs text-foreground">v{v.version}</span>

            <span className="w-16 shrink-0 text-xs">
              {isLatest ? (
                <span className="rounded-full border border-primary/20 bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                  Latest
                </span>
              ) : null}
            </span>

            <span className="tabular-metrics w-20 shrink-0 text-xs text-muted-foreground">
              {v.row_count?.toLocaleString() ?? "–"} rows
            </span>

            <span className="tabular-metrics w-20 shrink-0 text-xs text-muted-foreground">
              {v.file_size_bytes ? `${(v.file_size_bytes / 1024).toFixed(1)} KB` : "–"}
            </span>

            <span className="tabular-metrics w-16 shrink-0 text-xs text-muted-foreground">
              {v.column_count} cols
            </span>

            <span className="w-24 shrink-0 text-xs text-muted-foreground">
              {v.quality_score ? `${Math.round(v.quality_score)}% quality` : "–"}
            </span>

            <span className="flex-1 truncate text-xs text-muted-foreground/70">
              {new Date(v.created_at).toLocaleString()}
            </span>

            <div className="flex shrink-0 items-center gap-1">
              {!isLatest && latestId && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-[11px] text-muted-foreground hover:text-primary"
                  onClick={() => router.push(`/datasets/compare?a=${v.id}&b=${latestId}`)}
                  title={`Compare v${v.version} against the latest version`}
                >
                  <ArrowRightLeft className="mr-1 h-3 w-3" />
                  Compare
                </Button>
              )}

              {v.is_active ? (
                <Badge
                  variant="outline"
                  className="border-primary/20 bg-primary/10 text-[10px] text-primary"
                >
                  Active
                </Badge>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-[11px] text-muted-foreground hover:text-primary"
                  onClick={() => onActivate(v.id)}
                  disabled={activatePending}
                  title={isLatest ? "Make this version active" : `Roll back to v${v.version}`}
                >
                  <RotateCcw className="mr-1 h-3 w-3" />
                  {isLatest ? "Set Active" : "Roll back"}
                </Button>
              )}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

export default function DatasetsPage() {
  const qc = useQueryClient();
  const router = useRouter();
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [compareSelection, setCompareSelection] = useState<string[]>([]);
  const [expandedLineage, setExpandedLineage] = useState<string | null>(null);
  const [transformTarget, setTransformTarget] = useState<Dataset | null>(null);
  const [hoveredRowId, setHoveredRowId] = useState<string | null>(null);

  const toggleCompareSelection = (id: string) => {
    setCompareSelection((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      // Cap at 2 - selecting a 3rd replaces the oldest pick instead of
      // silently doing nothing or erroring.
      const next = [...prev, id];
      return next.length > 2 ? next.slice(1) : next;
    });
  };

  const { data: datasets, isLoading, isError, refetch } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => datasetsApi.list(),
    retry: 3,
    retryDelay: 1000,
  });

  const { data: activeDataset } = useQuery({
    queryKey: ["activeDataset"],
    queryFn: () => datasetsApi.getActive(),
  });

  // Re-uploading a file under the same name creates a new version rather than a
  // separate dataset, so collapse each name into one row headed by its newest
  // version — matching the (user_id, name) lineage the backend versions against.
  const lineages = React.useMemo(() => {
    if (!datasets) return [];
    const byName = new Map<string, Dataset[]>();
    for (const ds of datasets) {
      const group = byName.get(ds.name);
      if (group) group.push(ds);
      else byName.set(ds.name, [ds]);
    }
    return Array.from(byName.values()).map((group) =>
      [...group].sort((a, b) => (b.version ?? 1) - (a.version ?? 1))
    );
  }, [datasets]);

  // Memoized so the object identity only changes when transformTarget itself
  // does — an inline `{...}` literal here would be a fresh reference on every
  // render, and TransformDatasetModal's reset-on-open effect keys off that
  // reference, so it would wipe the "saved as vN" success message the moment
  // any unrelated re-render happened (e.g. right after the mutation's own
  // query invalidation).
  const transformDataset = React.useMemo(
    () => (transformTarget ? { id: transformTarget.id, name: transformTarget.name, columns: transformTarget.columns ?? [] } : null),
    [transformTarget]
  );

  const activateMutation = useMutation({
    mutationFn: (id: string) => datasetsApi.activate(id),
    onSuccess: () => {
      qc.invalidateQueries();
    },
  });

  // Surfaced in the confirm dialog. Without this a failed delete just left the
  // dialog sitting there doing nothing, with no indication anything went wrong.
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const deleteMutation = useMutation({
    mutationFn: (id: string) => datasetsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries();
      setDeleteConfirmId(null);
      setDeleteError(null);
    },
    onError: (err: unknown) => {
      setDeleteError(err instanceof Error ? err.message : "Could not delete this dataset. Please try again.");
    },
  });

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="flex flex-col gap-6"
    >
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1, ease: "easeOut" }}
        className="flex items-center justify-between gap-3 flex-wrap"
      >
        {compareSelection.length > 0 && (
          <motion.div
            key={compareSelection.length === 2 ? "pair" : "single"}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.25 }}
            className="flex items-center gap-2 text-xs text-muted-foreground"
          >
            {compareSelection.length === 2 ? (
              <span className="flex items-center gap-1.5 truncate max-w-[420px]">
                <span className="text-foreground font-medium truncate">
                  {datasets?.find((d) => d.id === compareSelection[0])?.name}
                </span>
                <ArrowRightLeft className="h-3 w-3 shrink-0 text-primary" />
                <span className="text-foreground font-medium truncate">
                  {datasets?.find((d) => d.id === compareSelection[1])?.name}
                </span>
              </span>
            ) : (
              <span>{datasets?.find((d) => d.id === compareSelection[0])?.name} selected — pick 1 more to compare</span>
            )}
          </motion.div>
        )}
        <div className="flex items-center gap-3 ml-auto">
          {compareSelection.length === 2 && (
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.25 }}>
              <Button
                size="sm"
                className="rounded-full gap-1.5 shadow-[0_0_16px_rgba(59,130,246,0.35)]"
                onClick={() =>
                  router.push(
                    `/datasets/compare?a=${compareSelection[0]}&b=${compareSelection[1]}`
                  )
                }
              >
                <ArrowRightLeft className="h-3.5 w-3.5" />
                Compare Selected
              </Button>
            </motion.div>
          )}
          <Badge variant="outline" className="flex items-center gap-2 rounded-full border-[#1a2235] bg-[#0c1017] px-3 py-1 text-muted-foreground">
            <div className="h-1.5 w-1.5 rounded-full bg-[#3b82f6] shadow-[0_0_8px_rgba(59,130,246,0.9)]"></div>
            <span>
              {lineages.length} dataset{lineages.length === 1 ? "" : "s"}
              {datasets && datasets.length > lineages.length && (
                <span className="text-muted-foreground/50"> · {datasets.length} versions</span>
              )}
            </span>
          </Badge>
        </div>
      </motion.div>

      {/* Upload Zone */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2, ease: "easeOut" }}
      >
        <UploadZone
        onSuccess={() => {
          // A fresh upload becomes the active dataset, so every page's
          // cached analytics (statistics, trend, distribution, KPIs, ...)
          // is now describing the wrong dataset. Invalidating only
          // "datasets"/"activeDataset" left all of that stale — the same
          // gap that made switching datasets show old numbers until a
          // refresh. Match the activate-mutation's behavior: invalidate
          // everything.
          qc.invalidateQueries();

          // Then pull the dashboard's two slowest queries now, while the user
          // is still looking at this page. Invalidating only marks them stale;
          // nothing fetches until the dashboard mounts, so without this the
          // click onto the dashboard is where the whole wait happens. These
          // two are the ones worth the head start -- the KPI computation and
          // the AI summary. If either fails it is ignored: this is a head
          // start, and the dashboard will ask again for itself.
          qc.prefetchQuery({ queryKey: ["analytics-kpis"], queryFn: () => analyticsApi.kpis() });
          qc.prefetchQuery({ queryKey: ["executiveSummary"], queryFn: () => insightsApi.executiveSummary() });
        }}
        onRedirect={() => router.push("/analytics")}
      />
      </motion.div>

      {/* Dataset Table */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.3, ease: "easeOut" }}
      >
        {isLoading ? (
        <TableSkeleton rows={6} />
      ) : isError ? (
        <ErrorState onRetry={refetch} />
      ) : !datasets || datasets.length === 0 ? (
        <EmptyState
          icon={<Database className="h-7 w-7 text-muted-foreground/50" />}
          title="No datasets yet"
          description="Upload your first CSV, JSON, or Parquet file above to get started."
        />
      ) : (
        <div className="rounded-[20px] border border-border bg-surface overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1080px] text-sm table-fixed">
              <colgroup>
                <col />
                <col className="w-[130px]" />
                <col className="w-[130px]" />
                <col className="w-[100px]" />
                <col className="w-[110px]" />
                <col className="w-[120px]" />
                <col className="w-[220px]" />
              </colgroup>
            <thead className="bg-background/80 border-b border-border/50">
              <tr>
                {["Name", "Version", "Status", "Rows", "Size", "Created", ""].map((h) => (
                  <th
                    key={h}
                    className="px-3 md:px-6 py-4 text-left text-xs font-semibold text-muted-foreground/80 uppercase tracking-wider truncate"
                  >
                    {h === "Name" ? (
                      <span className="flex items-center gap-1.5">
                        {h}
                        <span className="normal-case font-normal text-muted-foreground/50 tracking-normal">· select 2 to compare</span>
                      </span>
                    ) : h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {lineages.map((lineage) => {
                const ds = lineage[0];
                const olderCount = lineage.length - 1;
                const isExpanded = expandedLineage === ds.name;
                const isSelected = compareSelection.includes(ds.id);
                // After a roll back the active version is an older one, so look
                // across the whole lineage rather than just the newest row.
                const activeInLineage = lineage.find((v) => v.id === activeDataset?.id);
                // The stored status is "active" for every dataset that uploaded
                // cleanly, so printing it marked the whole table Active. Only
                // the lineage actually being analysed gets that badge; the rest
                // are uploaded and ready to be selected.
                const statusText = activeInLineage
                  ? "active"
                  : ds.status === "active"
                    ? "ready"
                    : ds.status;
                const sc = statusConfig[statusText] ?? statusConfig.archived;
                return (
                  <React.Fragment key={ds.name}>
                  <motion.tr
                    onMouseEnter={() => setHoveredRowId(ds.id)}
                    onMouseLeave={() => setHoveredRowId(null)}
                    animate={{
                      backgroundColor: isSelected
                        ? "rgba(59,130,246,0.04)"
                        : hoveredRowId === ds.id
                        ? "rgba(255,255,255,0.025)"
                        : isExpanded
                        ? "rgba(255,255,255,0.015)"
                        : "rgba(255,255,255,0)",
                    }}
                    transition={{ duration: 0.2 }}
                    className="relative border-b border-border/40 group"
                  >
                    <td className="relative px-3 md:px-6 py-5 font-medium text-foreground truncate" title={ds.name}>
                      <motion.span
                        aria-hidden
                        initial={false}
                        animate={{
                          opacity: hoveredRowId === ds.id || isSelected ? 1 : 0,
                          scaleY: hoveredRowId === ds.id || isSelected ? 1 : 0.3,
                        }}
                        transition={{ duration: 0.2 }}
                        className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r-full bg-primary"
                      />
                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => toggleCompareSelection(ds.id)}
                          title={isSelected ? "Selected for comparison — click to deselect" : "Select to compare with another dataset"}
                          className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-[6px] border transition-all hover:scale-110 active:scale-95 ${
                            isSelected
                              ? "bg-primary border-primary shadow-[0_0_8px_rgba(59,130,246,0.6)]"
                              : "bg-[#0c1017] border-[#1a2235] hover:border-primary/50"
                          }`}
                        >
                          {isSelected && <Check className="h-3 w-3 text-white" strokeWidth={3} />}
                        </button>
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[8px] bg-[#0c1017] border border-[#1a2235] shadow-sm transition-transform group-hover:scale-105">
                          {ds.source_type === "google_sheet" ? (
                            <Sheet className="h-4 w-4 text-[#34a853]" strokeWidth={2} />
                          ) : (
                            <File className="h-4 w-4 text-[#3b82f6]" strokeWidth={2} />
                          )}
                        </div>
                        <span className="truncate">{ds.name}</span>
                        {ds.source_type === "google_sheet" && (
                          <SheetSourceActions dataset={ds} />
                        )}
                      </div>
                    </td>
                    <td className="px-3 md:px-6 py-5 text-muted-foreground text-sm font-mono truncate">
                      {olderCount > 0 ? (
                        <button
                          type="button"
                          onClick={() => setExpandedLineage(isExpanded ? null : ds.name)}
                          title={isExpanded ? "Hide version history" : `Show all ${lineage.length} versions`}
                          className="-ml-1.5 flex items-center gap-1 rounded-md px-1.5 py-1 transition-colors hover:bg-white/[0.04] hover:text-primary"
                        >
                          <motion.span
                            animate={{ rotate: isExpanded ? 90 : 0 }}
                            transition={{ duration: 0.18 }}
                            className="flex"
                          >
                            <ChevronRight className="h-3.5 w-3.5" />
                          </motion.span>
                          v{ds.version || 1}
                          <span className="ml-0.5 rounded-full bg-primary/10 px-1.5 text-[10px] text-primary">
                            +{olderCount}
                          </span>
                        </button>
                      ) : (
                        <span className="pl-[22px]">v{ds.version || 1}</span>
                      )}
                    </td>
                    <td className="px-3 md:px-6 py-5">
                      <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium border ${sc.color}`}>
                        {sc.icon}{statusText}
                      </span>
                    </td>
                    <td className="px-3 md:px-6 py-5 tabular-metrics text-muted-foreground truncate">
                      {ds.latest_version?.row_count?.toLocaleString() ?? "–"}
                    </td>
                    <td className="px-3 md:px-6 py-5 tabular-metrics text-muted-foreground truncate">
                      {ds.latest_version?.file_size_bytes
                        ? `${(ds.latest_version.file_size_bytes / 1024).toFixed(1)} KB`
                        : "–"}
                    </td>
                    <td className="px-3 md:px-6 py-5 text-muted-foreground text-xs truncate">
                      {new Date(ds.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-3 md:px-6 py-5">
                      <div className="flex items-center justify-end h-8">
                        <AnimatePresence mode="wait" initial={false}>
                          {hoveredRowId === ds.id ? (
                            <motion.div
                              key="actions"
                              initial={{ opacity: 0, x: 6 }}
                              animate={{ opacity: 1, x: 0 }}
                              exit={{ opacity: 0, x: 6 }}
                              transition={{ duration: 0.15, ease: "easeOut" }}
                              className="flex items-center gap-1"
                            >
                              {activeDataset?.id !== ds.id && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/10 shrink-0 transition-all hover:scale-105 active:scale-95"
                                  onClick={() => activateMutation.mutate(ds.id)}
                                  disabled={activateMutation.isPending}
                                  title="Set as active dataset"
                                >
                                  <Power className="h-4 w-4" />
                                </Button>
                              )}

                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/10 shrink-0 transition-all hover:scale-105 active:scale-95"
                                onClick={() => setTransformTarget(ds)}
                                title="Rename columns, add a formula column, or merge with another dataset"
                              >
                                <Wand2 className="h-4 w-4" />
                              </Button>

                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-muted-foreground hover:text-error hover:bg-error/10 shrink-0 transition-all hover:scale-105 active:scale-95"
                                onClick={() => { setDeleteConfirmId(ds.id); setDeleteError(null); }}
                                title="Delete dataset"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </motion.div>
                          ) : (
                            <motion.div
                              key="status"
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              exit={{ opacity: 0 }}
                              transition={{ duration: 0.15 }}
                            >
                              {activeInLineage && activeInLineage.id !== ds.id ? (
                                <Badge
                                  variant="outline"
                                  className="bg-primary/10 text-primary border-primary/20 text-[10px] shrink-0"
                                  title={`Rolled back — v${activeInLineage.version ?? 1} is currently active`}
                                >
                                  v{activeInLineage.version ?? 1} active
                                </Badge>
                              ) : activeDataset?.id === ds.id ? (
                                <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 shrink-0">
                                  <CheckCircle className="h-3 w-3" />
                                  Active
                                </Badge>
                              ) : null}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </td>
                  </motion.tr>
                  <AnimatePresence initial={false}>
                    {isExpanded && (
                      <tr>
                        <td colSpan={7} className="border-b border-border/40 bg-background/30 p-0">
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.25, ease: "easeOut" }}
                            className="overflow-hidden"
                          >
                            <VersionHistoryPanel
                              datasetId={ds.id}
                              onActivate={(id) => activateMutation.mutate(id)}
                              activatePending={activateMutation.isPending}
                            />
                          </motion.div>
                        </td>
                      </tr>
                    )}
                  </AnimatePresence>
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
          </div>
        </div>
      )}
      </motion.div>

      {/* Detail Drawer */}
      <DatasetDetailDrawer
        dataset={selectedDataset}
        onClose={() => setSelectedDataset(null)}
      />

      {/* Transform Panel */}
      <TransformDatasetModal
        dataset={transformDataset}
        datasets={lineages.map((l) => l[0])}
        onClose={() => setTransformTarget(null)}
      />

      {/* Delete Confirmation Modal — deliberately NOT wrapped in
          AnimatePresence. Closing has to track React state directly: gating
          the unmount on an exit animation completing has repeatedly left
          stale overlays on screen here (see ChatUI.tsx, RuleHistoryPanel),
          which for this dialog looks exactly like "delete isn't working"
          even when the delete succeeded. The open transition still plays. */}
      {deleteConfirmId && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0, y: 15 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              transition={{ type: "spring", damping: 25, stiffness: 350 }}
              className="relative w-full max-w-[420px] overflow-hidden rounded-[24px] border border-[#1f2937] bg-[#111520] p-7 shadow-2xl"
            >
              <div className="flex flex-col">
                <div className="relative mb-5 h-11 w-11">
                  <motion.div
                    animate={{ scale: [1, 2.2], opacity: [0.5, 0] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
                    className="absolute inset-0 rounded-full bg-[#ef4444]/20"
                  />
                  <motion.div
                    animate={{ scale: [1, 1.6], opacity: [0.8, 0] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeOut", delay: 0.4 }}
                    className="absolute inset-0 rounded-full bg-[#ef4444]/30"
                  />
                  <motion.div 
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.1, type: "spring", damping: 12, stiffness: 300 }}
                    className="relative flex h-11 w-11 items-center justify-center rounded-full bg-[#35191d]"
                  >
                    <AlertCircle className="h-5 w-5 text-[#ef4444]" strokeWidth={2.5} />
                  </motion.div>
                </div>
                
                <motion.h2 
                  initial={{ opacity: 0, x: -10 }} 
                  animate={{ opacity: 1, x: 0 }} 
                  transition={{ delay: 0.15 }}
                  className="text-xl font-semibold text-white tracking-tight"
                >
                  Delete Dataset
                </motion.h2>
                <motion.p 
                  initial={{ opacity: 0, x: -10 }} 
                  animate={{ opacity: 1, x: 0 }} 
                  transition={{ delay: 0.2 }}
                  className="mt-3 text-sm text-[#94a3b8] leading-relaxed"
                >
                  Are you sure you want to delete this dataset? This action cannot be undone and will remove the file and all its associated metadata.
                </motion.p>

                {deleteError && (
                  <motion.p
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 rounded-xl border border-[#ef4444]/25 bg-[#ef4444]/10 px-3.5 py-2.5 text-[13px] leading-relaxed text-[#fca5a5]"
                  >
                    {deleteError}
                  </motion.p>
                )}

                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.25 }}
                  className="mt-8 flex justify-end gap-3"
                >
                  <Button
                    variant="ghost"
                    className="rounded-full bg-white/5 border border-white/10 hover:bg-white/10 text-white px-6 hover:text-white transition-all hover:scale-105 active:scale-95"
                    onClick={() => { setDeleteConfirmId(null); setDeleteError(null); }}
                  >
                    Cancel
                  </Button>
                  <Button 
                    variant="default" 
                    className="rounded-full bg-[#ef4444] hover:bg-[#dc2626] text-white px-6 border-0 shadow-lg shadow-red-500/20 transition-all hover:scale-105 active:scale-95"
                    onClick={() => deleteConfirmId && deleteMutation.mutate(deleteConfirmId)}
                    disabled={deleteMutation.isPending}
                  >
                    {deleteMutation.isPending ? "Deleting..." : "Delete"}
                  </Button>
                </motion.div>
              </div>
            </motion.div>
          </motion.div>
        )}
    </motion.div>
  );
}

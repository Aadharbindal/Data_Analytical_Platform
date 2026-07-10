"use client";

import React, { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { datasetsApi, BASE_URL } from "@/lib/api";
import type { Dataset } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TableSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import {
  Upload,
  Database,
  Trash2,
  RefreshCw,
  CheckCircle,
  Clock,
  AlertCircle,
  FileUp,
  Eye,
  Power,
  X,
} from "lucide-react";
import { DatasetDetailDrawer } from "@/components/datasets/DatasetDetailDrawer";

const statusConfig: Record<string, { color: string; icon: React.ReactNode }> = {
  active: {
    color: "bg-success/10 text-success border-success/20",
    icon: <CheckCircle className="h-3 w-3" />,
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
  const [uploadProgress, setUploadProgress] = useState<{
    filename: string;
    status: "uploading" | "processing" | "done" | "error";
    jobId?: string;
    currentStep?: string;
    progress?: number;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setUploadProgress({ filename: file.name, status: "uploading" });
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("dataset_name", file.name.replace(/\.[^/.]+$/, ""));
      const res = await datasetsApi.upload(formData);
      setUploadProgress({ filename: file.name, status: "processing", jobId: res.job_id, currentStep: "Initializing", progress: 0 });

      const eventSource = new EventSource(`${BASE_URL}/api/v1/datasets/upload/status/${res.job_id}/stream`, { withCredentials: true });
      
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
            : "border-border/60 hover:border-primary/40 hover:bg-white/[0.01]"
        }`}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
          <FileUp className="h-5 w-5 text-primary" />
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
    </div>
  );
}

export default function DatasetsPage() {
  const qc = useQueryClient();
  const router = useRouter();
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

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

  const activateMutation = useMutation({
    mutationFn: (id: string) => datasetsApi.activate(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["datasets"] });
      qc.invalidateQueries({ queryKey: ["activeDataset"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => datasetsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["datasets"] });
      qc.invalidateQueries({ queryKey: ["activeDataset"] });
      setDeleteConfirmId(null);
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">Datasets</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Upload, inspect, profile, and clean your data assets.
          </p>
        </div>
        <Badge variant="outline" className="text-muted-foreground">
          {datasets?.length ?? 0} datasets
        </Badge>
      </div>

      {/* Upload Zone */}
      <UploadZone 
        onSuccess={() => {
          qc.invalidateQueries({ queryKey: ["datasets"] });
          qc.invalidateQueries({ queryKey: ["activeDataset"] });
        }} 
        onRedirect={() => router.push("/analytics")}
      />

      {/* Dataset Table */}
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
          <table className="w-full text-sm">
            <thead className="bg-background/80 border-b border-border/50">
              <tr>
                {["Name", "Version", "Status", "Rows", "Size", "Created", ""].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground/80 uppercase tracking-wider"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {datasets.map((ds) => {
                const sc = statusConfig[ds.status] ?? statusConfig.archived;
                return (
                  <tr
                    key={ds.id}
                    className="border-b border-border/40 hover:bg-white/[0.02] transition-colors group"
                  >
                    <td className="px-4 py-4 font-medium text-foreground">
                      {ds.name}
                    </td>
                    <td className="px-4 py-4 text-muted-foreground text-sm font-mono">
                      v{ds.version || 1}
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium border ${sc.color}`}>
                        {sc.icon}{ds.status}
                      </span>
                    </td>
                    <td className="px-4 py-4 tabular-metrics text-muted-foreground">
                      {ds.latest_version?.row_count?.toLocaleString() ?? "–"}
                    </td>
                    <td className="px-4 py-4 tabular-metrics text-muted-foreground">
                      {ds.latest_version?.file_size_bytes
                        ? `${(ds.latest_version.file_size_bytes / 1024).toFixed(1)} KB`
                        : "–"}
                    </td>
                    <td className="px-4 py-4 text-muted-foreground text-xs">
                      {new Date(ds.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                        {activeDataset?.id === ds.id ? (
                          <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 mr-2">
                            Active Version
                          </Badge>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs mr-2 text-muted-foreground hover:text-primary"
                            onClick={() => activateMutation.mutate(ds.id)}
                            disabled={activateMutation.isPending}
                          >
                            <Power className="h-3 w-3 mr-1" />
                            Set Active
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-foreground"
                          onClick={() => setSelectedDataset(ds)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-error"
                          onClick={() => setDeleteConfirmId(ds.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail Drawer */}
      <DatasetDetailDrawer
        dataset={selectedDataset}
        onClose={() => setSelectedDataset(null)}
      />

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {deleteConfirmId && (
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
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-error/10">
                  <AlertCircle className="h-6 w-6 text-error" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-foreground">Delete Dataset</h2>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Are you sure you want to delete this dataset? This action cannot be undone and will remove the file and all its associated metadata.
                  </p>
                </div>
                <div className="mt-4 flex justify-end gap-3">
                  <Button variant="outline" onClick={() => setDeleteConfirmId(null)}>
                    Cancel
                  </Button>
                  <Button 
                    variant="default" 
                    className="bg-error hover:bg-error/90 text-error-foreground"
                    onClick={() => deleteConfirmId && deleteMutation.mutate(deleteConfirmId)}
                    disabled={deleteMutation.isPending}
                  >
                    {deleteMutation.isPending ? "Deleting..." : "Delete"}
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

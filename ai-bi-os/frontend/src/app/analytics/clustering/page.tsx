"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { StudioPage } from "@/components/analytics/StudioPage";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, LineChart, Line, BarChart, Bar, Cell, ReferenceLine,
} from "recharts";
import { Boxes, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

const CLUSTER_COLORS = [
  "#2f6bff", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
  "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#6366f1",
];

export default function ClusteringModels() {
  const queryClient = useQueryClient();
  const [features, setFeatures] = useState<string[]>([]);
  const [autoK, setAutoK] = useState(true);
  const [manualK, setManualK] = useState<number>(3);
  const [trainError, setTrainError] = useState<string | null>(null);
  const [activeModel, setActiveModel] = useState<any>(null);

  const { data: colsData } = useQuery({
    queryKey: ["clustering_columns"],
    queryFn: () => api.get<any>("/api/v1/analytics/clustering/columns"),
  });

  const { data: models, isLoading: isModelsLoading } = useQuery({
    queryKey: ["clustering_models"],
    queryFn: () => api.get<any[]>("/api/v1/analytics/clustering/models"),
  });

  const trainMutation = useMutation({
    mutationFn: (data: { features: string[]; n_clusters: number | null }) =>
      api.post("/api/v1/analytics/clustering/train", data),
    onSuccess: (res: any) => {
      queryClient.invalidateQueries({ queryKey: ["clustering_models"] });
      setTrainError(null);
      setActiveModel({ ...res });
    },
    onError: (err: any) => {
      let msg = "Failed to train model";
      try {
        const parsed = JSON.parse(err.message);
        if (parsed.detail) msg = parsed.detail;
      } catch (e) {
        msg = err.message || msg;
      }
      setTrainError(msg);
    },
  });

  const handleTrain = () => {
    if (features.length < 2) {
      setTrainError("Please select at least 2 numeric features");
      return;
    }
    setTrainError(null);
    trainMutation.mutate({ features, n_clusters: autoK ? null : manualK });
  };

  const handleFeatureToggle = (col: string) => {
    if (features.includes(col)) {
      setFeatures(features.filter((f) => f !== col));
    } else {
      setFeatures([...features, col]);
    }
  };

  const allCols = colsData?.features || [];

  const pointsByCluster: Record<number, any[]> = {};
  if (activeModel?.pca_points) {
    for (const p of activeModel.pca_points) {
      if (!pointsByCluster[p.cluster]) pointsByCluster[p.cluster] = [];
      pointsByCluster[p.cluster].push(p);
    }
  }

  return (
    <StudioPage title="Clustering">
      <motion.div
        initial={{ opacity: 0, filter: "blur(4px)" }}
        animate={{ opacity: 1, filter: "blur(0px)" }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="flex flex-col gap-6"
      >
        {/* Training Form */}
        <motion.div
          initial={{ opacity: 0, y: 15, x: -10 }}
          animate={{ opacity: 1, y: 0, x: 0 }}
          transition={{ duration: 0.4, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
        >
          <Card className="glass-card overflow-visible">
            <CardHeader>
              <CardTitle className="text-base font-semibold">Train New Model</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 overflow-visible">
              <div>
                <label className="block text-sm font-medium mb-2 text-muted-foreground">Features (numeric only, choose 2+)</label>
                <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 border border-border rounded-md bg-surface">
                  {allCols.map((col: string) => (
                    <button
                      key={col}
                      onClick={() => handleFeatureToggle(col)}
                      className={`px-2 py-1 text-xs rounded-md border ${
                        features.includes(col)
                          ? "bg-primary/20 border-primary text-primary-foreground"
                          : "bg-background border-border text-muted-foreground"
                      }`}
                    >
                      {col}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
                <div>
                  <label className="block text-sm font-medium mb-2 text-muted-foreground">Number of Clusters</label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setAutoK(true)}
                      className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2.5 text-sm rounded-[8px] border transition-colors ${
                        autoK
                          ? "bg-primary/15 border-primary text-primary"
                          : "bg-[#0b1220]/60 border-white/[0.08] text-muted-foreground hover:border-primary/40"
                      }`}
                    >
                      <Sparkles className="w-3.5 h-3.5" /> Auto-detect (best silhouette)
                    </button>
                    <button
                      onClick={() => setAutoK(false)}
                      className={`px-3 py-2.5 text-sm rounded-[8px] border transition-colors ${
                        !autoK
                          ? "bg-primary/15 border-primary text-primary"
                          : "bg-[#0b1220]/60 border-white/[0.08] text-muted-foreground hover:border-primary/40"
                      }`}
                    >
                      Manual
                    </button>
                  </div>
                </div>
                {!autoK && (
                  <div>
                    <input
                      type="number"
                      min={2}
                      max={10}
                      value={manualK}
                      onChange={(e) => setManualK(Math.max(2, Math.min(10, Number(e.target.value) || 2)))}
                      className="w-full bg-[#0b1220]/60 border border-white/[0.08] rounded-[8px] px-3 py-2.5 text-sm text-foreground"
                    />
                  </div>
                )}
              </div>

              {trainError && <div className="text-red-400 text-sm mt-2">{trainError}</div>}

              <div className="mt-2">
                <button
                  onClick={handleTrain}
                  disabled={trainMutation.isPending || features.length < 2}
                  className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 hover:bg-primary/90 transition-opacity"
                >
                  {trainMutation.isPending ? "Clustering..." : "Run Clustering"}
                </button>
                {features.length < 2 && (
                  <span className="text-xs text-muted-foreground ml-3">Select at least 2 numeric features.</span>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Active Model Results */}
        {activeModel && (
          <motion.div
            initial={{ opacity: 0, y: 15, x: -10 }}
            animate={{ opacity: 1, y: 0, x: 0 }}
            transition={{ duration: 0.4, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
          >
            <Card className="glass-card border-primary/30">
              <CardHeader className="border-b border-border/40 pb-4">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <Boxes className="w-5 h-5 text-primary" />
                    <CardTitle className="text-base font-semibold text-primary">
                      Active Model Results
                    </CardTitle>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {activeModel.n_rows_used} rows used
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-6 flex flex-col gap-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-surface border border-border p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground">Clusters (k)</div>
                    <div className="text-xl font-mono font-medium text-foreground">
                      {activeModel.n_clusters}
                      {activeModel.auto_selected && <span className="text-[10px] text-primary ml-1.5 align-middle">auto</span>}
                    </div>
                  </div>
                  <div className="bg-surface border border-border p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground">Silhouette Score</div>
                    <div className="text-xl font-mono font-medium text-emerald-500">{activeModel.silhouette_score?.toFixed(3)}</div>
                  </div>
                  <div className="bg-surface border border-border p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground">Inertia (WCSS)</div>
                    <div className="text-xl font-mono font-medium text-foreground">{activeModel.inertia?.toFixed(1)}</div>
                  </div>
                  <div className="bg-surface border border-border p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground">PCA Variance Explained</div>
                    <div className="text-xl font-mono font-medium text-foreground">
                      {activeModel.pca_explained_variance ? `${((activeModel.pca_explained_variance[0] + activeModel.pca_explained_variance[1]) * 100).toFixed(0)}%` : "—"}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium mb-3 text-muted-foreground">Clusters (2D PCA Projection)</h4>
                    <div className="h-72 bg-surface/30 rounded-lg p-2 border border-border/40">
                      <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                          <XAxis type="number" dataKey="x" name="PC1" tick={{ fill: "#666", fontSize: 11 }} domain={["auto", "auto"]} />
                          <YAxis type="number" dataKey="y" name="PC2" tick={{ fill: "#666", fontSize: 11 }} domain={["auto", "auto"]} />
                          <RechartsTooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ backgroundColor: "#1a1a1a", borderColor: "#333" }} />
                          {Object.keys(pointsByCluster).map((clusterKey) => {
                            const idx = Number(clusterKey);
                            return (
                              <Scatter
                                key={clusterKey}
                                name={`Cluster ${idx}`}
                                data={pointsByCluster[idx]}
                                fill={CLUSTER_COLORS[idx % CLUSTER_COLORS.length]}
                              />
                            );
                          })}
                        </ScatterChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium mb-3 text-muted-foreground">Cluster Sizes</h4>
                    <div className="h-72 bg-surface/30 rounded-lg p-2 border border-border/40">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={activeModel.cluster_sizes} margin={{ top: 10, right: 20, bottom: 5, left: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" vertical={false} />
                          <XAxis dataKey="cluster" tick={{ fill: "#666", fontSize: 11 }} tickFormatter={(v) => `Cluster ${v}`} />
                          <YAxis tick={{ fill: "#666", fontSize: 11 }} />
                          <RechartsTooltip contentStyle={{ backgroundColor: "#1a1a1a", borderColor: "#333" }} />
                          <Bar dataKey="count">
                            {activeModel.cluster_sizes.map((entry: any) => (
                              <Cell key={`cell-${entry.cluster}`} fill={CLUSTER_COLORS[entry.cluster % CLUSTER_COLORS.length]} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium mb-3 text-muted-foreground">Elbow Curve (Inertia by k)</h4>
                  <div className="h-56 bg-surface/30 rounded-lg p-2 border border-border/40">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={activeModel.elbow_data} margin={{ top: 10, right: 20, bottom: 5, left: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" vertical={false} />
                        <XAxis dataKey="k" tick={{ fill: "#666", fontSize: 11 }} />
                        <YAxis tick={{ fill: "#666", fontSize: 11 }} />
                        <RechartsTooltip contentStyle={{ backgroundColor: "#1a1a1a", borderColor: "#333" }} />
                        <ReferenceLine x={activeModel.n_clusters} stroke="#2f6bff" strokeDasharray="4 4" label={{ value: "chosen k", fill: "#2f6bff", fontSize: 10, position: "top" }} />
                        <Line type="monotone" dataKey="inertia" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium mb-3 text-muted-foreground">Cluster Centers (Feature Averages)</h4>
                  <div className="overflow-x-auto border border-border/40 rounded-lg">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-border/40 bg-surface/30">
                          <th className="text-left px-3 py-2 font-medium text-muted-foreground">Cluster</th>
                          {activeModel.features.map((f: string) => (
                            <th key={f} className="text-right px-3 py-2 font-medium text-muted-foreground">{f}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {activeModel.cluster_centers.map((c: any) => (
                          <tr key={c.cluster} className="border-b border-border/20 last:border-0">
                            <td className="px-3 py-2 flex items-center gap-2">
                              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CLUSTER_COLORS[c.cluster % CLUSTER_COLORS.length] }} />
                              Cluster {c.cluster}
                            </td>
                            {activeModel.features.map((f: string) => (
                              <td key={f} className="text-right px-3 py-2 font-mono text-foreground">{c.center[f]?.toFixed(2)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Model History List */}
        <motion.div
          initial={{ opacity: 0, y: 15, x: -10 }}
          animate={{ opacity: 1, y: 0, x: 0 }}
          transition={{ duration: 0.4, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
        >
          <h3 className="text-lg font-semibold mb-4">Model History</h3>
          {isModelsLoading ? (
            <div className="text-muted-foreground text-sm">Loading history...</div>
          ) : models?.length === 0 ? (
            <div className="text-muted-foreground text-sm">No models trained yet.</div>
          ) : (
            <div className="flex flex-col gap-4">
              {models?.map((model: any, i: number) => (
                <motion.div
                  key={model.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.05 + 0.25, ease: "easeOut" }}
                >
                  <Card
                    className="glass-card cursor-pointer hover:border-primary/50 transition-colors"
                    onClick={() => setActiveModel({ ...model, pca_points: null, pca_explained_variance: null })}
                  >
                    <CardHeader className="py-4">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <Boxes className="w-4 h-4 text-muted-foreground" />
                          <CardTitle className="text-sm font-semibold">
                            {model.features.join(" + ")} · k={model.n_clusters}
                          </CardTitle>
                        </div>
                        <div className="flex gap-4 items-center">
                          <div className="text-xs text-muted-foreground">Silhouette: <span className="font-mono text-emerald-400">{model.silhouette_score?.toFixed(3)}</span></div>
                          <div className="text-xs text-muted-foreground">{new Date(model.timestamp).toLocaleDateString()}</div>
                        </div>
                      </div>
                    </CardHeader>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </motion.div>
    </StudioPage>
  );
}

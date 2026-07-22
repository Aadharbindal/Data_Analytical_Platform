"use client";

import React, { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { StudioPage } from "@/components/analytics/StudioPage";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ResponsiveContainer, BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip } from "recharts";
import { GitBranch, ChevronDown, CheckCircle2, XCircle } from "lucide-react";
import { motion } from "framer-motion";

const ALGORITHMS = [
  { value: "logistic", label: "Logistic Regression" },
  { value: "decision_tree", label: "Decision Tree" },
];

export default function ClassificationModels() {
  const queryClient = useQueryClient();
  const [target, setTarget] = useState<string>("");
  const [features, setFeatures] = useState<string[]>([]);
  const [algorithm, setAlgorithm] = useState<string>("logistic");
  const [trainError, setTrainError] = useState<string | null>(null);
  const [activeModel, setActiveModel] = useState<any>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (features.includes(target)) {
      setFeatures((prev) => prev.filter((f) => f !== target));
    }
  }, [target]);

  const { data: colsData } = useQuery({
    queryKey: ["classification_columns"],
    queryFn: () => api.get<any>("/api/v1/analytics/classification/columns"),
  });

  const { data: models, isLoading: isModelsLoading } = useQuery({
    queryKey: ["classification_models"],
    queryFn: () => api.get<any[]>("/api/v1/analytics/classification/models"),
  });

  const trainMutation = useMutation({
    mutationFn: (data: { target: string; features: string[]; algorithm: string }) =>
      api.post("/api/v1/analytics/classification/train", data),
    onSuccess: (res: any) => {
      queryClient.invalidateQueries({ queryKey: ["classification_models"] });
      setTrainError(null);
      setActiveModel({ target, features, ...res });
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
    if (!target) {
      setTrainError("Please select a target column");
      return;
    }
    if (features.length === 0) {
      setTrainError("Please select at least one feature");
      return;
    }
    setTrainError(null);
    trainMutation.mutate({ target, features, algorithm });
  };

  const handleFeatureToggle = (col: string) => {
    if (features.includes(col)) {
      setFeatures(features.filter((f) => f !== col));
    } else {
      setFeatures([...features, col]);
    }
  };

  const targetCols = colsData?.targets || [];
  const allCols = colsData?.features || [];
  const availableFeatures = allCols.filter((c: string) => c !== target);

  const lift = activeModel
    ? ((activeModel.accuracy_test - activeModel.baseline_accuracy) * 100)
    : 0;

  const maxCm = activeModel?.confusion_matrix
    ? Math.max(...activeModel.confusion_matrix.flat())
    : 1;

  return (
    <StudioPage title="Classification Models">
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
          className="relative z-50"
        >
          <Card className="glass-card overflow-visible">
            <CardHeader>
              <CardTitle className="text-base font-semibold">Train New Model</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 overflow-visible">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium mb-2 text-muted-foreground">Target (Class Label)</label>
                  <div className="relative" ref={dropdownRef}>
                    <div
                      className="w-full bg-[#0b1220]/60 border border-white/[0.08] hover:border-primary/50 transition-colors rounded-[8px] px-3 py-2.5 text-sm text-foreground cursor-pointer flex justify-between items-center shadow-[inset_0_1px_1px_rgba(255,255,255,0.02)]"
                      onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                    >
                      <span className={target ? "text-white" : "text-muted-foreground"}>{target || "Select Target..."}</span>
                      <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform duration-200 ${isDropdownOpen ? "rotate-180" : ""}`} />
                    </div>

                    {isDropdownOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="absolute top-full left-0 right-0 mt-2 bg-[#131b2c] border border-white/[0.08] rounded-[8px] shadow-2xl z-50 py-1 overflow-hidden backdrop-blur-xl max-h-64 overflow-y-auto"
                      >
                        <div
                          className="px-3 py-2 text-sm text-muted-foreground hover:bg-white/[0.04] cursor-pointer transition-colors"
                          onClick={() => { setTarget(""); setIsDropdownOpen(false); }}
                        >
                          Select Target...
                        </div>
                        {targetCols.map((col: string) => (
                          <div
                            key={col}
                            className="px-3 py-2 text-sm text-white hover:bg-[#2f6bff]/20 hover:text-[#eef2fa] cursor-pointer transition-colors"
                            onClick={() => { setTarget(col); setIsDropdownOpen(false); }}
                          >
                            {col}
                          </div>
                        ))}
                      </motion.div>
                    )}
                  </div>
                  <p className="text-[11px] text-muted-foreground/70 mt-1.5">Only columns with 2–20 distinct values can be class labels.</p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-muted-foreground">Algorithm</label>
                  <div className="flex gap-2">
                    {ALGORITHMS.map((a) => (
                      <button
                        key={a.value}
                        onClick={() => setAlgorithm(a.value)}
                        className={`flex-1 px-3 py-2.5 text-sm rounded-[8px] border transition-colors ${
                          algorithm === a.value
                            ? "bg-primary/15 border-primary text-primary"
                            : "bg-[#0b1220]/60 border-white/[0.08] text-muted-foreground hover:border-primary/40"
                        }`}
                      >
                        {a.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-muted-foreground">Features</label>
                <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 border border-border rounded-md bg-surface">
                  {availableFeatures.map((col: string) => (
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

              {trainError && <div className="text-red-400 text-sm mt-2">{trainError}</div>}

              <div className="mt-2">
                <button
                  onClick={handleTrain}
                  disabled={trainMutation.isPending || !target || features.length === 0}
                  className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 hover:bg-primary/90 transition-opacity"
                >
                  {trainMutation.isPending ? "Training..." : "Train Model"}
                </button>
                {(!target || features.length === 0) && (
                  <span className="text-xs text-muted-foreground ml-3">Select a target and at least one feature to train.</span>
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
                    <GitBranch className="w-5 h-5 text-primary" />
                    <CardTitle className="text-base font-semibold text-primary">
                      Active Model Results
                    </CardTitle>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {activeModel.n_rows_used} rows used · {ALGORITHMS.find((a) => a.value === activeModel.algorithm)?.label}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-6 flex flex-col gap-6">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="bg-surface border border-border p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground">Test Accuracy</div>
                    <div className="text-xl font-mono font-medium text-emerald-500">{(activeModel.accuracy_test * 100)?.toFixed(1)}%</div>
                  </div>
                  <div className="bg-surface border border-border p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground">Precision</div>
                    <div className="text-xl font-mono font-medium text-foreground">{(activeModel.precision_test * 100)?.toFixed(1)}%</div>
                  </div>
                  <div className="bg-surface border border-border p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground">Recall</div>
                    <div className="text-xl font-mono font-medium text-foreground">{(activeModel.recall_test * 100)?.toFixed(1)}%</div>
                  </div>
                  <div className="bg-surface border border-border p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground">F1 Score</div>
                    <div className="text-xl font-mono font-medium text-foreground">{(activeModel.f1_test * 100)?.toFixed(1)}%</div>
                  </div>
                  <div className="bg-surface border border-border p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground">
                      {activeModel.roc_auc !== null && activeModel.roc_auc !== undefined ? "ROC-AUC" : "vs Baseline"}
                    </div>
                    {activeModel.roc_auc !== null && activeModel.roc_auc !== undefined ? (
                      <div className="text-xl font-mono font-medium text-foreground">{activeModel.roc_auc.toFixed(3)}</div>
                    ) : (
                      <div className={`text-xl font-mono font-medium ${lift > 0 ? "text-emerald-500" : "text-red-400"}`}>
                        {lift > 0 ? "+" : ""}{lift.toFixed(1)}pp
                      </div>
                    )}
                  </div>
                </div>

                <div className="text-xs text-muted-foreground">
                  Baseline (always guess the majority class): <span className="font-mono text-foreground">{(activeModel.baseline_accuracy * 100).toFixed(1)}%</span>
                  {" · "}Your model: <span className={`font-mono ${lift > 0 ? "text-emerald-400" : "text-red-400"}`}>{lift > 0 ? "+" : ""}{lift.toFixed(1)} points {lift > 0 ? "better" : "worse"}</span>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium mb-3 text-muted-foreground">Confusion Matrix (Test Set)</h4>
                    <div className="bg-surface/30 rounded-lg p-3 border border-border/40 overflow-x-auto">
                      <table className="border-collapse">
                        <thead>
                          <tr>
                            <th className="p-1"></th>
                            <th colSpan={activeModel.class_labels.length} className="text-[10px] text-muted-foreground font-normal pb-1">Predicted</th>
                          </tr>
                          <tr>
                            <th className="p-1"></th>
                            {activeModel.class_labels.map((label: string) => (
                              <th key={label} className="text-[10px] text-muted-foreground font-normal px-2 pb-1 max-w-[60px] truncate">{label}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {activeModel.confusion_matrix.map((row: number[], i: number) => (
                            <tr key={i}>
                              {i === 0 && (
                                <td rowSpan={activeModel.confusion_matrix.length} className="text-[10px] text-muted-foreground font-normal pr-2 [writing-mode:vertical-rl] rotate-180 text-center">Actual</td>
                              )}
                              <td className="text-[10px] text-muted-foreground pr-2 text-right whitespace-nowrap">{activeModel.class_labels[i]}</td>
                              {row.map((val: number, j: number) => {
                                const intensity = maxCm > 0 ? val / maxCm : 0;
                                const isDiag = i === j;
                                return (
                                  <td
                                    key={j}
                                    className="p-0"
                                  >
                                    <div
                                      className="w-11 h-11 flex items-center justify-center text-xs font-mono rounded-sm m-0.5"
                                      style={{
                                        backgroundColor: isDiag
                                          ? `rgba(16, 185, 129, ${0.15 + intensity * 0.65})`
                                          : `rgba(239, 68, 68, ${intensity * 0.5})`,
                                        color: intensity > 0.5 ? "#fff" : undefined,
                                      }}
                                    >
                                      {val}
                                    </div>
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium mb-3 text-muted-foreground">Feature Importance</h4>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={activeModel.feature_importance} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#2a2a2a" />
                          <XAxis type="number" tick={{ fill: "#666", fontSize: 11 }} />
                          <YAxis dataKey="feature" type="category" tick={{ fill: "#666", fontSize: 11 }} width={80} />
                          <RechartsTooltip contentStyle={{ backgroundColor: "#1a1a1a", borderColor: "#333" }} />
                          <Bar dataKey="value">
                            {activeModel.feature_importance.map((entry: any, index: number) => (
                              <Cell key={`cell-${index}`} fill={entry.value >= 0 ? "#10b981" : "#ef4444"} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {activeModel.predictions_sample && (
                  <div>
                    <h4 className="text-sm font-medium mb-3 text-muted-foreground">
                      Sample Predictions (Test Set, first {Math.min(20, activeModel.predictions_sample.length)})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {activeModel.predictions_sample.slice(0, 20).map((p: any, i: number) => (
                        <div
                          key={i}
                          className={`flex items-center gap-1.5 text-[11px] px-2 py-1 rounded-md border ${
                            p.correct ? "border-emerald-500/30 bg-emerald-500/[0.06] text-emerald-300" : "border-red-500/30 bg-red-500/[0.06] text-red-300"
                          }`}
                        >
                          {p.correct ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                          <span className="text-muted-foreground">actual:</span> {p.actual}
                          {!p.correct && <><span className="text-muted-foreground">pred:</span> {p.predicted}</>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeModel.cross_validation && (
                  <div className="text-xs text-muted-foreground">
                    {activeModel.cross_validation.folds}-fold CV accuracy: <span className="font-mono text-foreground">{(activeModel.cross_validation.accuracy_mean * 100).toFixed(1)}% ± {(activeModel.cross_validation.accuracy_std * 100).toFixed(1)}%</span>
                  </div>
                )}
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
                    onClick={() => setActiveModel(model)}
                  >
                    <CardHeader className="py-4">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <GitBranch className="w-4 h-4 text-muted-foreground" />
                          <CardTitle className="text-sm font-semibold">
                            {model.target} ~ {model.features.join(" + ")}
                          </CardTitle>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.06] text-muted-foreground">
                            {ALGORITHMS.find((a) => a.value === model.algorithm)?.label || model.algorithm}
                          </span>
                        </div>
                        <div className="flex gap-4 items-center">
                          <div className="text-xs text-muted-foreground">Accuracy: <span className="font-mono text-emerald-400">{(model.accuracy_test * 100)?.toFixed(1)}%</span></div>
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

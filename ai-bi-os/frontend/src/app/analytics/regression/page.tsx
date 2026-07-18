"use client";

import React, { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { StudioPage } from "@/components/analytics/StudioPage";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine, BarChart, Bar, Cell } from "recharts";
import { Calculator, ChevronDown } from "lucide-react";
import { motion } from "framer-motion";

export default function RegressionModels() {
  const queryClient = useQueryClient();
  const [target, setTarget] = useState<string>("");
  const [features, setFeatures] = useState<string[]>([]);
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
      setFeatures(prev => prev.filter(f => f !== target));
    }
  }, [target]);

  const { data: colsData, isLoading: isColsLoading } = useQuery({
    queryKey: ["regression_columns"],
    queryFn: () => api.get<any>("/api/v1/analytics/regression/columns"),
  });

  const { data: models, isLoading: isModelsLoading } = useQuery({
    queryKey: ["regression_models"],
    queryFn: () => api.get<any[]>("/api/v1/analytics/regression/models"),
  });

  const trainMutation = useMutation({
    mutationFn: (data: { target: string; features: string[] }) =>
      api.post("/api/v1/analytics/regression/train", data),
    onSuccess: (res: any) => {
      queryClient.invalidateQueries({ queryKey: ["regression_models"] });
      setTrainError(null);
      setActiveModel({
        target,
        features,
        ...res
      });
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
    trainMutation.mutate({ target, features });
  };

  const handleFeatureToggle = (col: string) => {
    if (features.includes(col)) {
      setFeatures(features.filter((f) => f !== col));
    } else {
      setFeatures([...features, col]);
    }
  };

  const numericCols = colsData?.targets || [];
  const allCols = colsData?.features || [];
  const availableFeatures = allCols.filter((c: string) => c !== target);

  return (
    <StudioPage title="Regression Models">
      <motion.div 
        initial={{ opacity: 0, filter: 'blur(4px)' }}
        animate={{ opacity: 1, filter: 'blur(0px)' }}
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
                <label className="block text-sm font-medium mb-2 text-muted-foreground">Target (Numeric)</label>
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
                      className="absolute top-full left-0 right-0 mt-2 bg-[#131b2c] border border-white/[0.08] rounded-[8px] shadow-2xl z-50 py-1 overflow-hidden backdrop-blur-xl"
                    >
                      <div 
                        className="px-3 py-2 text-sm text-muted-foreground hover:bg-white/[0.04] cursor-pointer transition-colors"
                        onClick={() => { setTarget(""); setIsDropdownOpen(false); }}
                      >
                        Select Target...
                      </div>
                      {numericCols.map((col: string) => (
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
                  <Calculator className="w-5 h-5 text-primary" />
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
              
              <div className="flex gap-4">
                <div className="bg-surface border border-border p-3 rounded-lg flex-1">
                  <div className="text-xs text-muted-foreground">Train R²</div>
                  <div className="text-xl font-mono font-medium text-emerald-500">{activeModel.r2_train?.toFixed(4)}</div>
                </div>
                <div className="bg-surface border border-border p-3 rounded-lg flex-1">
                  <div className="text-xs text-muted-foreground">Test R²</div>
                  <div className="text-xl font-mono font-medium text-emerald-500">{activeModel.r2_test?.toFixed(4)}</div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium mb-3 text-muted-foreground">Coefficients</h4>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={activeModel.coefficients} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#2a2a2a" />
                        <XAxis type="number" tick={{ fill: '#666', fontSize: 11 }} />
                        <YAxis dataKey="feature" type="category" tick={{ fill: '#666', fontSize: 11 }} width={80} />
                        <RechartsTooltip contentStyle={{ backgroundColor: '#1a1a1a', borderColor: '#333' }} />
                        <Bar dataKey="value">
                          {activeModel.coefficients.map((entry: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={entry.value > 0 ? "#10b981" : "#ef4444"} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {activeModel.predictions_sample && (
                  <div>
                    <h4 className="text-sm font-medium mb-3 text-muted-foreground">Actual vs Predicted (Test Sample)</h4>
                    <div className="h-64 bg-surface/30 rounded-lg p-2 border border-border/40">
                      <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                          <XAxis type="number" dataKey="actual" name="Actual" tick={{ fill: '#666', fontSize: 11 }} domain={['auto', 'auto']} />
                          <YAxis type="number" dataKey="predicted" name="Predicted" tick={{ fill: '#666', fontSize: 11 }} domain={['auto', 'auto']} />
                          <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#1a1a1a', borderColor: '#333' }} />
                          <Scatter name="Predictions" data={activeModel.predictions_sample} fill="#8b5cf6" />
                          {/* Approximate y=x line */}
                          <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1000000, y: 1000000 }]} stroke="#666" strokeOpacity={0.3} />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
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
                    onClick={() => setActiveModel(model)}
                  >
                    <CardHeader className="py-4">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <Calculator className="w-4 h-4 text-muted-foreground" />
                          <CardTitle className="text-sm font-semibold">
                            {model.target} ~ {model.features.join(" + ")}
                          </CardTitle>
                        </div>
                        <div className="flex gap-4 items-center">
                          <div className="text-xs text-muted-foreground">Test R²: <span className="font-mono text-emerald-400">{model.r2_test?.toFixed(4)}</span></div>
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

"use client";

import { useDatasetAnalytics } from "@/hooks/useAnalytics";
import { Calculator } from "lucide-react";

export default function RegressionModels() {
  const { regression, isLoading } = useDatasetAnalytics("demo", "v1");

  if (isLoading) return <div className="p-8">Loading Regression Models...</div>;

  const data = regression.data;
  if (!data) return <div className="p-8">No Regression data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Regression & Predictive Models</h1>
      
      <div className="flex flex-col gap-6">
        {data.map((model, i) => (
          <div key={i} className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-border/40 pb-4">
              <div className="flex items-center gap-2">
                <Calculator className="h-5 w-5 text-indigo-500" />
                <h3 className="font-semibold text-lg">{model.model_name}</h3>
              </div>
              <div className="flex gap-4">
                <div className="text-right">
                  <div className="text-xs text-muted-foreground">R² Score</div>
                  <div className="font-mono font-medium text-emerald-500">{model.r2_score.toFixed(4)}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-muted-foreground">RMSE</div>
                  <div className="font-mono font-medium">{model.rmse.toFixed(4)}</div>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-medium mb-3 text-muted-foreground">Coefficients</h4>
              <div className="grid grid-cols-4 gap-2">
                {Object.entries(model.coefficients).map(([feature, coef]) => (
                  <div key={feature} className="bg-surface/50 p-2 rounded-lg border border-border/40 flex justify-between">
                    <span className="text-xs text-muted-foreground truncate" title={feature}>{feature}</span>
                    <span className="text-xs font-mono font-medium">{coef.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

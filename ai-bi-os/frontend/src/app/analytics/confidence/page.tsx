"use client";

import { useDatasetAnalytics } from "@/hooks/useAnalytics";
import { CheckCircle, AlertTriangle } from "lucide-react";

export default function ConfidenceCenter() {
  const { validation, isLoading } = useDatasetAnalytics("demo", "v1");

  if (isLoading) return <div className="p-8">Loading Confidence Scores...</div>;

  const data = validation.data;
  if (!data) return <div className="p-8">No Validation data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Confidence & Validation Center</h1>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="glass-card rounded-[20px] p-8 flex flex-col items-center justify-center gap-4">
          <div className="text-sm text-muted-foreground uppercase tracking-widest font-medium">Overall Trust Score</div>
          <div className="relative flex items-center justify-center">
            <svg className="w-32 h-32 transform -rotate-90">
              <circle cx="64" cy="64" r="56" fill="transparent" stroke="rgba(255,255,255,0.05)" strokeWidth="12" />
              <circle 
                cx="64" cy="64" r="56" fill="transparent" 
                stroke={data.trust_score > 80 ? "#10b981" : "#f59e0b"} 
                strokeWidth="12" 
                strokeDasharray="351.8" 
                strokeDashoffset={351.8 - (351.8 * data.trust_score) / 100}
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute text-4xl font-bold">{data.trust_score}</div>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${data.trust_score > 80 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'}`}>
            {data.reliability}
          </div>
        </div>

        <div className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Validation Warnings
          </h3>
          <ul className="space-y-3">
            {data.warnings.length === 0 ? (
              <li className="flex items-center gap-2 text-emerald-500 text-sm">
                <CheckCircle className="h-4 w-4" />
                All checks passed successfully.
              </li>
            ) : (
              data.warnings.map((warn, i) => (
                <li key={i} className="bg-amber-500/10 border border-amber-500/20 text-amber-200/80 p-3 rounded-lg text-sm">
                  {warn}
                </li>
              ))
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}

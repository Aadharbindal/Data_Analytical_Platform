"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber } from "@/lib/utils";
import { DeepAnalysisDialog } from "./DeepAnalysisDialog";
import { motion } from "framer-motion";

export default function EDAPage() {
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null);
  
  const { data, isLoading, isError } = useQuery({
    queryKey: ['eda'],
    queryFn: () => analyticsApi.eda()
  });

  const { data: prefetchData } = useQuery({
    queryKey: ["analytics-prefetch"],
    queryFn: () => analyticsApi.prefetch(),
    staleTime: 5 * 60 * 1000,
  });
  
  const activeDataset = prefetchData?.active_dataset;

  return (
    <StudioPage title="Dataset Analysis (EDA)" isLoading={isLoading}>
      {isError ? (
        <ErrorState />
      ) : !data || !data.summary || data.summary.length === 0 ? (
        <div className="text-muted-foreground text-sm">No EDA data found. Upload a dataset first.</div>
      ) : (
        <div className="flex flex-col gap-5 pb-12 pt-2">
          {data.summary.map((c: any, index: number) => {
            const nullPct = data.rows ? (c.nulls / data.rows) : 0;
            const isNumeric = c.mean != null;
            const delay = index * 0.1;
            
            return (
              <motion.div 
                key={c.column} 
                onClick={() => setSelectedColumn(c.column)}
                initial={{ opacity: 0, y: 20, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                whileHover={{ 
                  scale: 1.01,
                  y: -4
                }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1], delay }}
                className="relative overflow-hidden cursor-pointer bg-white/[0.02] border border-white/[0.06] rounded-[20px] p-4 lg:px-6 lg:py-3.5 flex flex-col lg:flex-row lg:items-center gap-6 w-full group hover:bg-[#1a2333] hover:border-[#4d84ff]/50 transition-colors shadow-[inset_0_1px_2px_rgba(255,255,255,0.05),0_8px_24px_rgba(0,0,0,0.2)] backdrop-blur-xl"
              >
                {/* Glossy Top Line on Hover */}
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#4d84ff] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-20" />
                
                {/* Subtle Light Sweep Animation */}
                <motion.div 
                  initial={{ x: '-100%', opacity: 0 }}
                  animate={{ x: '100%', opacity: 0.05 }}
                  transition={{ duration: 1.5, ease: "linear", delay: delay + 0.3 }}
                  className="absolute inset-0 w-1/2 pointer-events-none -skew-x-12 z-10"
                  style={{ background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent)' }}
                />

                <div className="relative z-10 flex flex-col lg:flex-row lg:items-center gap-6 w-full">
                  
                  {/* Left Section: Identity & Health */}
                  <div className="flex flex-col gap-1 w-full lg:w-[220px] shrink-0 border-r-0 lg:border-r border-white/[0.08] pr-4">
                    <div className="flex items-center gap-3">
                      <span className="w-[6px] h-[6px] rounded-[2px] bg-gradient-to-b from-[#6aa4ff] to-[#2f6bff] shadow-[0_0_10px_rgba(47,107,255,0.6)] group-hover:shadow-[0_0_14px_rgba(47,107,255,1)] transition-shadow"></span>
                      <span className="text-[18px] font-bold tracking-tight text-white group-hover:text-[#eef2fa] transition-colors truncate">
                        {c.column}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-3 mt-1.5 pl-[18px]">
                      <span className="text-[9px] font-mono px-2 py-[2px] rounded-[5px] uppercase tracking-wider font-semibold border border-[#6aa4ff]/30 bg-[#2f6bff]/[0.08] text-[#6aa4ff]">
                        {c.type}
                      </span>
                      <div className="flex items-center gap-3 border-l border-white/[0.1] pl-3">
                        <span className="text-[10px] font-semibold text-[#8a99b8] leading-[1.2]">
                          {(nullPct * 100).toFixed(1)}%<br/>null
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Right Section: Stats */}
                  <div className="flex-1 flex flex-row items-center gap-6 lg:gap-10 w-full">
                    {isNumeric ? (
                      <>
                        <div className="flex flex-col gap-[2px] shrink-0">
                          <span className="text-[9px] uppercase tracking-wider font-bold text-[#69758c] group-hover:text-[#8a99b8] transition-colors">Mean</span>
                          <span className="text-[16px] font-bold tracking-tight font-mono text-white">
                            {formatNumber(c.mean)}
                          </span>
                        </div>
                        <div className="flex flex-col gap-[2px] shrink-0">
                          <span className="text-[9px] uppercase tracking-wider font-bold text-[#69758c] group-hover:text-[#8a99b8] transition-colors">Min</span>
                          <span className="text-[16px] font-bold tracking-tight font-mono text-white">
                            {formatNumber(c.min)}
                          </span>
                        </div>
                        <div className="flex flex-col gap-[2px] shrink-0">
                          <span className="text-[9px] uppercase tracking-wider font-bold text-[#69758c] group-hover:text-[#8a99b8] transition-colors">Max</span>
                          <span className="text-[16px] font-bold tracking-tight font-mono text-white">
                            {formatNumber(c.max)}
                          </span>
                        </div>
                        <div className="flex flex-col gap-[2px] shrink-0">
                          <span className="text-[9px] uppercase tracking-wider font-bold text-[#69758c] group-hover:text-[#8a99b8] transition-colors">Unique</span>
                          <span className="text-[16px] font-bold tracking-tight font-mono text-white/50">
                            N/A
                          </span>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="flex flex-col gap-[2px] shrink-0 min-w-[70px]">
                          <span className="text-[9px] uppercase tracking-wider font-bold text-[#69758c] group-hover:text-[#8a99b8] transition-colors">Unique</span>
                          <span className="text-[16px] font-bold tracking-tight font-mono text-white">
                            {formatNumber(c.unique)}
                          </span>
                        </div>
                        
                        <div className="flex flex-col gap-[6px] flex-1 w-full overflow-hidden">
                          <span className="text-[9px] uppercase tracking-wider font-bold text-[#69758c] group-hover:text-[#8a99b8] transition-colors">Top Values</span>
                          <div className="flex flex-wrap gap-2">
                            {c.top_values && Object.keys(c.top_values).length > 0 ? (
                              Object.entries(c.top_values).slice(0, 4).map(([k,v]) => (
                                <span key={k} className="text-[12px] flex items-center gap-1.5 px-2 py-1 rounded-[8px] transition-colors border border-white/[0.08] bg-[#0b1220]/60 group-hover:bg-[#131b2c] group-hover:border-[#4d84ff]/30 text-white shadow-[inset_0_1px_1px_rgba(255,255,255,0.02)]">
                                  <span className="truncate max-w-[130px] font-medium text-[#eef2fa]">{k}</span>
                                  <span className="text-[8px] font-mono text-[#8a99b8] bg-black/40 px-1.5 py-[1px] rounded-[4px]">{v as React.ReactNode}</span>
                                </span>
                              ))
                            ) : (
                              <span className="text-[12px] text-[#8a99b8]/50 italic">N/A</span>
                            )}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                  
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
      <DeepAnalysisDialog column={selectedColumn} onClose={() => setSelectedColumn(null)} />
    </StudioPage>
  );
}

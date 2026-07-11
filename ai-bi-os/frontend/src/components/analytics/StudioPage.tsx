"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";

interface StudioPageProps {
  title: string;
  toolbar?: React.ReactNode;
  children: React.ReactNode;
  isLoading?: boolean;
}

export function StudioPage({ title, toolbar, children, isLoading }: StudioPageProps) {
  const { data: activeDataset } = useQuery({
    queryKey: ["activeDataset"],
    queryFn: () => api.get<any>("/datasets/active"),
  });

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-150 relative">
      {/* Sticky Header */}
      <header className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 bg-background/80 backdrop-blur-md border-b border-white/[0.04] shrink-0 h-14">
        <h1 className="text-sm font-semibold tracking-wide text-foreground/90">
          {title}
        </h1>
        
        <div className="flex items-center gap-4">
          {toolbar && <div className="flex items-center gap-2">{toolbar}</div>}
          
          {activeDataset && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-surface/50 border border-border/50 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-green-500/80 animate-pulse" />
              <span className="text-[11px] font-medium text-muted-foreground truncate max-w-[120px]">
                {activeDataset.name}
              </span>
              <span className="text-[10px] text-muted-foreground/60 bg-white/5 px-1.5 py-0.5 rounded ml-1">
                {activeDataset.row_count?.toLocaleString() || "N/A"} rows
              </span>
            </div>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6 transition-all duration-150">
        <div className="mx-auto max-w-full">
          {isLoading ? (
            <div className="flex items-center justify-center h-48 opacity-50">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            children
          )}
        </div>
      </div>
    </div>
  );
}

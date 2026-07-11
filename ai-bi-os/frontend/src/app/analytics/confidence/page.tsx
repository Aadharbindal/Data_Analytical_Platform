"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { CheckCircle, AlertTriangle, Database, Lightbulb, Zap, ShieldCheck } from "lucide-react";
import { ErrorState, detectErrorType } from "@/components/ui/error-state";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";

function ExpandableAuditRow({ row }: { row: any }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr 
        onClick={() => setExpanded(!expanded)}
        className="hover:bg-white/[0.03] transition-colors cursor-pointer group"
      >
        <td className="px-5 py-4 font-medium text-foreground max-w-[280px] align-top" title={row.title}>
          <div className="flex flex-col gap-1.5">
            <span className={`leading-snug ${expanded ? 'line-clamp-none' : 'line-clamp-2'}`}>{row.title}</span>
            <span className="text-[10px] text-primary/70 font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity uppercase tracking-wider">
              {expanded ? 'Click to collapse' : 'Click to expand'}
            </span>
          </div>
        </td>
        <td className="px-5 py-4 align-top whitespace-nowrap">
          {Math.round(row.confidence * 100)}%
        </td>
        <td className="px-5 py-4 align-top whitespace-nowrap">
          {row.verified ? (
            <span className="flex items-center gap-1.5 text-success bg-success/10 px-2.5 py-1 rounded-full w-fit text-[11px] font-semibold border border-success/20">
              <CheckCircle className="h-3 w-3" />
              Verified
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-error bg-error/10 px-2.5 py-1 rounded-full w-fit text-[11px] font-semibold border border-error/20">
              <AlertTriangle className="h-3 w-3" />
              Unverified
            </span>
          )}
        </td>
        <td className="px-5 py-4 align-top">
          <div className={`max-w-md ${expanded ? '' : 'line-clamp-3 relative'}`}>
            <code className="text-[10px] font-mono text-muted-foreground bg-black/20 p-2.5 rounded-lg block break-words whitespace-pre-wrap border border-white/[0.03]">
              {row.audit_sql}
            </code>
            {!expanded && (
              <div className="absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-[#0e0f12] to-transparent pointer-events-none rounded-b-lg" />
            )}
          </div>
        </td>
      </tr>
      <AnimatePresence>
        {expanded && (
          <motion.tr
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-black/20"
          >
            <td colSpan={4} className="px-5 pb-5 pt-1 border-t-0">
              <motion.div 
                initial={{ y: -10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="p-4 bg-white/[0.02] border border-white/[0.05] rounded-xl text-[13px] text-muted-foreground/90 leading-relaxed"
              >
                <strong className="text-foreground/80 block mb-1">Detailed Description</strong>
                {row.description || "No additional description provided."}
              </motion.div>
            </td>
          </motion.tr>
        )}
      </AnimatePresence>
    </>
  );
}

function StatCard({ title, verified, unverified, icon }: { title: string; verified: number; unverified: number; icon: React.ReactNode }) {
  const total = verified + unverified;
  const pct = total === 0 ? 0 : Math.round((verified / total) * 100);

  return (
    <div className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg flex items-center gap-2">
          {icon}
          {title}
        </h3>
        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${pct > 80 ? 'bg-success/10 text-success border-success/20' : 'bg-warning/10 text-warning border-warning/20'}`}>
          {pct}% Verified
        </span>
      </div>
      <div className="grid grid-cols-2 gap-4 mt-2">
        <div className="p-4 bg-success/5 border border-success/10 rounded-xl flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-success">{verified}</span>
          <span className="text-xs text-muted-foreground uppercase tracking-wider mt-1">Verified</span>
        </div>
        <div className="p-4 bg-error/5 border border-error/10 rounded-xl flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-error">{unverified}</span>
          <span className="text-xs text-muted-foreground uppercase tracking-wider mt-1">Unverified</span>
        </div>
      </div>
    </div>
  );
}

export default function ConfidenceCenter() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["confidence"],
    queryFn: () => analyticsApi.confidence(),
  });

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="grid grid-cols-2 gap-6">
          <CardSkeleton lines={4} />
          <CardSkeleton lines={4} />
        </div>
        <CardSkeleton lines={10} />
      </div>
    );
  }

  if (isError) {
    return <ErrorState onRetry={refetch} errorType={detectErrorType(error)} />;
  }

  if (!data) return null;

  return (
    <div className="flex flex-col gap-8 h-full p-8 overflow-hidden">

      
      <div className="grid grid-cols-2 gap-6">
        <StatCard 
          title="Insights" 
          verified={data.insights.verified} 
          unverified={data.insights.unverified} 
          icon={<Lightbulb className="h-5 w-5 text-primary" />} 
        />
        <StatCard 
          title="Recommendations" 
          verified={data.recommendations.verified} 
          unverified={data.recommendations.unverified} 
          icon={<Zap className="h-5 w-5 text-primary" />} 
        />
      </div>

      <div className="glass-card rounded-[20px] overflow-hidden flex flex-col flex-1 min-h-0">
        <div className="p-5 border-b border-border/40 shrink-0">
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <Database className="h-5 w-5 text-muted-foreground" />
            Insights Audit Trail
          </h3>
          <p className="text-xs text-muted-foreground mt-1">
            Recent insights and their underlying SQL queries used for deterministic verification.
          </p>
        </div>
        
        <div className="overflow-auto flex-1 min-h-0 relative max-h-[500px]">
          <table className="w-full text-left text-sm relative">
            <thead className="bg-[#111] border-b border-border/40 text-xs text-muted-foreground uppercase tracking-wider sticky top-0 z-20">
              <tr>
                <th className="px-5 py-4 font-medium">Insight Title</th>
                <th className="px-5 py-4 font-medium">Confidence</th>
                <th className="px-5 py-4 font-medium">Status</th>
                <th className="px-5 py-4 font-medium">SQL Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/20">
              {data.audit_trail.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-5 py-8 text-center text-muted-foreground">
                    No insights generated yet.
                  </td>
                </tr>
              ) : (
                data.audit_trail.map((row: any) => (
                  <ExpandableAuditRow key={row.id} row={row} />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

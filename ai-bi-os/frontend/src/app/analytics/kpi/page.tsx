"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { ExecutiveKPICard } from "@/components/analytics/ExecutiveKPICard";
import { ExecutiveKPIReport } from "@/lib/types";
import { motion } from "framer-motion";

const containerVariants = {
  hidden: { opacity: 0 },
  show: { 
    opacity: 1, 
    transition: { 
      staggerChildren: 0.15,
      delayChildren: 0.1 
    } 
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  show: { 
    opacity: 1, 
    y: 0, 
    transition: { 
      type: "spring", 
      stiffness: 200, 
      damping: 25,
      mass: 0.8
    } 
  },
};

export default function KPICenter() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['kpiCenter'],
    queryFn: () => analyticsApi.kpiCenter()
  });

  return (
    <StudioPage title="KPI Intelligence" isLoading={isLoading}>
      {isError ? (
        <ErrorState />
      ) : !data ? (
        <div className="text-muted-foreground text-sm">No KPI data found.</div>
      ) : (
        <motion.div 
          className="flex flex-col gap-8"
          variants={containerVariants}
          initial="hidden"
          animate="show"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {data.available_kpis?.map((kpi: ExecutiveKPIReport, index: number) => (
              <motion.div key={kpi.query_id || kpi.name} variants={itemVariants}>
                <ExecutiveKPICard kpi={kpi} index={index} />
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </StudioPage>
  );
}

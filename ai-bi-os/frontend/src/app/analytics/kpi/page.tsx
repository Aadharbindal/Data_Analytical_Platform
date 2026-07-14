"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { ExecutiveKPICard } from "@/components/analytics/ExecutiveKPICard";
import { ExecutiveKPIReport } from "@/lib/types";

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
        <div className="flex flex-col gap-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {data.available_kpis?.map((kpi: ExecutiveKPIReport) => (
              <ExecutiveKPICard key={kpi.query_id || kpi.name} kpi={kpi} />
            ))}
          </div>
        </div>
      )}
    </StudioPage>
  );
}

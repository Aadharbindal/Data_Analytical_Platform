"use client";

import { useDatasetAnalytics } from "@/hooks/useAnalytics";
import { Activity } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function KPICenter() {
  const { kpis, isLoading } = useDatasetAnalytics("demo", "v1");

  if (isLoading) return <div className="p-8">Loading KPIs...</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">KPI Center</h1>
      <div className="grid grid-cols-3 gap-4">
        {kpis.data?.map(kpi => (
          <div key={kpi.id} className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-primary" />
                <span className="font-medium">{kpi.name}</span>
              </div>
              <span className={`text-sm ${kpi.trend === "UP" ? "text-emerald-500" : kpi.trend === "DOWN" ? "text-rose-500" : "text-muted-foreground"}`}>
                {kpi.growth_percentage}%
              </span>
            </div>
            <div className="text-3xl font-semibold">{kpi.current_value.toLocaleString()}</div>
            <div className="h-24 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={kpi.history}>
                  <XAxis dataKey="date" hide />
                  <Tooltip contentStyle={{ background: "#131722", border: "1px solid rgba(255,255,255,0.1)" }} />
                  <Line type="monotone" dataKey="value" stroke="#0070F3" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

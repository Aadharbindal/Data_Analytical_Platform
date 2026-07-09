"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { Clock } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function TimeSeriesPage() {
  const { data: statsData } = useQuery({
    queryKey: ['statistics'],
    queryFn: () => analyticsApi.statistics()
  });

  const [metric, setMetric] = useState<string>("");

  useEffect(() => {
    if (statsData?.stats?.length > 0 && !metric) {
      setMetric(statsData.stats[0].column);
    }
  }, [statsData, metric]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['timeseries', metric],
    queryFn: () => analyticsApi.timeseries(metric),
    enabled: !!metric
  });

  if (isLoading && !data) return <div className="p-8"><CardSkeleton lines={10} /></div>;
  if (isError) return <div className="p-8"><ErrorState /></div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Time Series Intelligence</h1>
        {statsData?.stats && (
          <select 
            className="bg-surface border border-border/40 rounded-lg px-3 py-1.5 text-sm"
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
          >
            {statsData.stats.map((s: any) => (
              <option key={s.column} value={s.column}>{s.column}</option>
            ))}
          </select>
        )}
      </div>
      
      {!data || !data.timeseries || data.timeseries.length === 0 ? (
        <div className="p-8 glass-card rounded-[20px]">No Time Series data found for the selected metric. Make sure your dataset has a date column.</div>
      ) : (
        <div className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
          <div className="flex items-center gap-2 border-b border-border/40 pb-4">
            <Clock className="h-5 w-5 text-indigo-400" />
            <h3 className="font-semibold text-lg">{metric} over Time</h3>
          </div>
          
          <div className="h-[400px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.timeseries}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ background: "#131722", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px" }} 
                />
                <Line type="monotone" dataKey="value" stroke="#818cf8" strokeWidth={2} dot={{ r: 4, fill: "#818cf8", strokeWidth: 0 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { LineChart as LineChartIcon } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function ForecastCenter() {
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
    queryKey: ['forecast', metric],
    queryFn: () => analyticsApi.forecast(metric),
    enabled: !!metric
  });

  if (isLoading && !data) return <div className="p-8"><CardSkeleton lines={10} /></div>;
  if (isError) return <div className="p-8"><ErrorState /></div>;

  const chartData = [];
  if (data?.historical && data?.forecast) {
    // Combine historical and forecast data
    const historical = data.historical.map((d: any) => ({
      date: d.date,
      value: d.value
    }));
    const forecast = data.forecast.map((d: any) => ({
      date: d.date,
      forecast: d.forecast,
      lower: d.lower,
      upper: d.upper
    }));
    
    // To connect the lines, we can add the forecast point to the last historical point if they are continuous,
    // or just let them be adjacent. We will just concatenate them.
    chartData.push(...historical);
    chartData.push(...forecast);
  }

  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Forecast Center</h1>
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
      
      {!data || data.available === false ? (
        <div className="p-8 glass-card rounded-[20px]">
          {data?.reason || "No Forecast data found. Make sure your dataset has a date column."}
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="glass-card rounded-[20px] p-6 flex flex-col gap-4 border-t-4 border-t-indigo-500">
            <div className="flex justify-between items-center border-b border-border/40 pb-4">
              <div className="flex items-center gap-2">
                <LineChartIcon className="h-5 w-5 text-indigo-400" />
                <h3 className="font-semibold text-lg">{metric} Forecast</h3>
              </div>
            </div>
            
            <div className="h-[400px] w-full mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ background: "#131722", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px" }} 
                  />
                  
                  {/* Confidence Interval */}
                  <Area type="monotone" dataKey="upper" stroke="none" fill="#6366f1" fillOpacity={0.1} />
                  <Area type="monotone" dataKey="lower" stroke="none" fill="#131722" fillOpacity={1} />
                  
                  {/* Actual vs Forecast lines */}
                  <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} name="Actual" />
                  <Line type="monotone" dataKey="forecast" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Forecast" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

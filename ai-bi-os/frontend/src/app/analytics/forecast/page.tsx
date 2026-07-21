"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { ChevronDown } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { ResponsiveContainer, ComposedChart, CartesianGrid, XAxis, YAxis, Tooltip, Area, Line } from "recharts";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber } from "@/lib/utils";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";

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

  const chartData = [];
  if (data?.historical && data?.forecast) {
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
    
    chartData.push(...historical);
    // Connect lines by assigning forecast value to the last historical point
    if (historical.length > 0 && forecast.length > 0) {
      historical[historical.length - 1].forecast = historical[historical.length - 1].value;
    }
    chartData.push(...forecast);
  }

  const toolbar = statsData?.stats && statsData.stats.length > 0 && (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-1.5 bg-surface border border-border text-xs font-medium text-foreground rounded-lg px-3 py-1.5 outline-none hover:bg-white/5 transition-colors focus:ring-2 focus:ring-primary/30 shadow-sm cursor-pointer">
        {metric || "Select Metric"}
        <ChevronDown className="h-3 w-3 text-muted-foreground ml-1 shrink-0" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48 max-h-[300px] overflow-y-auto">
        {statsData.stats.map((s: any) => (
          <DropdownMenuItem 
            key={s.column} 
            onClick={() => setMetric(s.column)}
            className="text-xs cursor-pointer"
          >
            {s.column}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );

  return (
    <StudioPage title="Forecast Center" isLoading={isLoading && !data} toolbar={toolbar}>
      {isError ? (
        <ErrorState />
      ) : !data || data.available === false ? (
        <div className="text-muted-foreground text-sm">
          {data?.reason || "No Forecast data found. Make sure your dataset has a date column."}
        </div>
      ) : (
        <div className="flex flex-col gap-6 h-full">
          <div className="glass-card rounded-xl p-6 flex flex-col gap-4 border border-white/[0.05] bg-surface/30 h-[400px]">
            <div className="flex items-center gap-2 pb-2">
              <span className="text-[14px] font-semibold text-foreground">{metric} Forecast Projection</span>
            </div>
            
            <div className="flex-1 w-full mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 10, fill: "#80848E", fontWeight: 500 }} 
                    axisLine={false} 
                    tickLine={false} 
                    dy={15} 
                  />
                  <YAxis 
                    tick={{ fontSize: 11, fill: "#80848E", fontWeight: 500 }} 
                    tickFormatter={(value) => formatNumber(value)}
                    axisLine={false} 
                    tickLine={false} 
                    dx={-10}
                  />
                  <Tooltip 
                    cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1, strokeDasharray: '4 4' }}
                    contentStyle={{ 
                      backgroundColor: 'rgba(19, 23, 34, 0.85)', 
                      backdropFilter: 'blur(12px)',
                      border: '1px solid rgba(255,255,255,0.08)', 
                      borderRadius: '12px',
                      boxShadow: '0 8px 32px -8px rgba(0,0,0,0.5)',
                      color: '#fff',
                      fontSize: '12px',
                      fontWeight: 500,
                      padding: '8px 12px'
                    }}
                    itemStyle={{ color: '#fff', fontWeight: 600, fontSize: '13px' }}
                    formatter={(value: number, name: string) => [formatNumber(value), name]}
                  />
                  
                  {/* Confidence Interval */}
                  <Area type="monotone" dataKey="upper" stroke="none" fill="#6366f1" fillOpacity={0.05} activeDot={false} />
                  <Area type="monotone" dataKey="lower" stroke="none" fill="#131722" fillOpacity={1} activeDot={false} />
                  
                  {/* Actual vs Forecast lines */}
                  <Line type="monotone" dataKey="value" stroke="#0070F3" strokeWidth={2.5} dot={false} name="Actual" activeDot={{ r: 5, fill: '#0B0D12', stroke: '#0070F3', strokeWidth: 2 }} />
                  <Line type="monotone" dataKey="forecast" stroke="#8b5cf6" strokeWidth={2.5} strokeDasharray="5 5" dot={false} name="Forecast" activeDot={{ r: 5, fill: '#0B0D12', stroke: '#8b5cf6', strokeWidth: 2 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </StudioPage>
  );
}

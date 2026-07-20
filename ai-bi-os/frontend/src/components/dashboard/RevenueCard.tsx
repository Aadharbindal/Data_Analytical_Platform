"use client";

import React, { useState, useMemo } from "react";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";
import dynamic from "next/dynamic";
const LazyCharts = dynamic(() => import("@/components/charts/LazyCharts"), { ssr: false });


import { SemanticDict } from "@/lib/types";
import { formatIndianCurrency, formatIndianNumber } from "@/lib/utils";

interface RevenueCardProps {
  data: any[];
  semanticDict?: SemanticDict;
}

export function RevenueCard({ data, semanticDict }: RevenueCardProps) {
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [range, setRange] = useState<'12m' | 'ytd' | 'all'>('12m');

  const chartTitle = semanticDict?.business_terminology?.chart_title || "Monthly Transaction Performance";
  const primaryLabel = semanticDict?.business_terminology?.primary_metric_label || "Volume";
  const primaryMetric = semanticDict?.business_terminology?.primary_metric || "";
  const metricType = semanticDict?.business_terminology?.primary_metric_type || "currency";

  // Data processing logic (Math)
  const processed = useMemo(() => {
    if (!data || data.length === 0) return { filteredData: [], total: 0, trend: 0, forecastStartIndex: -1 };

    let lastHistoryIdx = -1;
    for (let i = data.length - 1; i >= 0; i--) {
      if (data[i].value !== undefined && data[i].value !== null) {
        lastHistoryIdx = i;
        break;
      }
    }

    const historyData = lastHistoryIdx === -1 ? [] : data.slice(0, lastHistoryIdx + 1);
    const forecastData = lastHistoryIdx === -1 ? data : data.slice(lastHistoryIdx + 1);

    let filteredHistory = historyData;

    if (range === '12m') {
      filteredHistory = historyData.slice(-12);
    } else if (range === 'ytd') {
      const getYear = (name: string) => {
        const m = name.match(/\b(20\d{2})\b/);
        if (m) return m[1];
        const d = new Date(name);
        if (!isNaN(d.getTime())) return d.getFullYear().toString();
        return null;
      };
      const lastPoint = historyData[historyData.length - 1];
      const lastYear = lastPoint ? getYear(lastPoint.name) : null;
      if (lastYear) {
        filteredHistory = historyData.filter(d => getYear(d.name) === lastYear);
      }
    } else {
      // all
      const half = Math.floor(historyData.length / 2);
      filteredHistory = historyData.slice(half);
    }

    // Merge history and forecast (forecast is appended)
    let combinedData = [...filteredHistory];
    
    let forecastStartIndex = -1;
    if (forecastData.length > 0 && combinedData.length > 0) {
       const boundaryPoint = { ...combinedData[combinedData.length - 1] };
       boundaryPoint.forecast = boundaryPoint.value; // Start forecast from last actual point
       combinedData[combinedData.length - 1] = boundaryPoint;
       
       forecastStartIndex = combinedData.length - 1;
       combinedData = [...combinedData, ...forecastData];
    } else if (forecastData.length > 0) {
       combinedData = [...forecastData];
       forecastStartIndex = 0;
    }

    // KPI Calculation: Current month vs Previous month
    const currentTotal = filteredHistory.length > 0 ? (filteredHistory[filteredHistory.length - 1].value || 0) : 0;
    const prevTotal = filteredHistory.length > 1 ? (filteredHistory[filteredHistory.length - 2].value || 0) : 0;
    
    let trend = 0;
    if (prevTotal > 0) {
      trend = ((currentTotal - prevTotal) / prevTotal) * 100;
    } else if (currentTotal > 0) {
      trend = 100;
    }

    return { filteredData: combinedData, total: currentTotal, trend, forecastStartIndex };
  }, [data, range]);

  const { filteredData, total, trend, forecastStartIndex } = processed;
  const hasHistoricalData = filteredData.some((d: any) => d.value !== undefined && d.value !== null);

  // Format Total Value dynamically
  const formatBigNumber = (val: number) => {
    if (metricType === "currency") return formatIndianCurrency(val);
    if (metricType === "percent") return `${val.toFixed(1)}%`;
    return formatIndianNumber(val);
  };

  const { data: breakdownData, isLoading } = useQuery({
    queryKey: ["breakdown", selectedMonth, primaryMetric],
    queryFn: async () => {
      let revCol = primaryMetric;
      if (!revCol || revCol === "records") {
        const eda = await api.get<any>("/api/v1/analytics/eda");
        const cols = eda.summary.map((s: any) => s.column);
        revCol = cols.find((c: string) => /rev|sale|total|amount|price/i.test(c)) || cols[0];
      }
      return api.get<any[]>(`/api/v1/analytics/breakdown?metric=${revCol}&period=${selectedMonth}`);
    },
    enabled: !!selectedMonth,
  });

  const handleChartClick = (state: any) => {
    if (state && state.activeLabel) {
      setSelectedMonth(state.activeLabel);
    }
  };

  const forecastStartName = forecastStartIndex >= 0 && filteredData[forecastStartIndex] 
    ? filteredData[forecastStartIndex].name 
    : undefined;
  const forecastEndName = filteredData.length > 0 
    ? filteredData[filteredData.length - 1].name 
    : undefined;

  return (
    <>
      <div className="h-full flex flex-col p-6 rounded-2xl border border-[#1f2229] bg-[#0f1117] text-white">
        {/* Header */}
        <div className="flex flex-row justify-between items-start mb-6">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">{chartTitle}</h2>
            <p className="text-[#848a97] text-sm mt-1 mb-4">Total processed volume, with next-month projection</p>
            
            <div className="flex items-end gap-4">
              <span className="text-4xl font-extrabold tracking-tight">
                {formatBigNumber(total)}
              </span>
              <div className="flex items-center gap-2 mb-1.5">
                <span className={`flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-full ${trend >= 0 ? 'bg-[#062d1b] text-[#10b981]' : 'bg-[#3b1219] text-[#ef4444]'}`}>
                  {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}%
                </span>
                <span className="text-[#646a77] text-xs font-medium">vs. previous period</span>
              </div>
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center gap-2 bg-[#171a22] border border-[#2a2d35] text-xs font-medium text-[#a0a5b1] rounded-md px-3 py-1.5 outline-none hover:bg-[#1f222a] transition-colors shadow-sm cursor-pointer">
              {range === '12m' ? 'Last 12 Months' : range === 'ytd' ? 'Year to Date' : 'All Time'}
              <svg className="h-3.5 w-3.5 text-[#646a77]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-36 bg-[#171a22] border-[#2a2d35] text-[#a0a5b1]">
              <DropdownMenuItem className="focus:bg-[#20242e] focus:text-white cursor-pointer" onClick={() => setRange('12m')}>Last 12 Months</DropdownMenuItem>
              <DropdownMenuItem className="focus:bg-[#20242e] focus:text-white cursor-pointer" onClick={() => setRange('ytd')}>Year to Date</DropdownMenuItem>
              <DropdownMenuItem className="focus:bg-[#20242e] focus:text-white cursor-pointer" onClick={() => setRange('all')}>All Time</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Chart */}
        <div className="flex-1 min-h-[300px] w-full relative">
          {!hasHistoricalData ? (
            <div className="w-full h-full flex items-center justify-center text-[#646a77] text-sm font-medium">
              No data for this period
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={filteredData} margin={{ top: 10, right: 0, left: -20, bottom: 30 }} onClick={handleChartClick}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#0070F3" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#0070F3" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1f2229" />
                  
                  <XAxis 
                    dataKey="name" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#646a77', fontSize: 11, fontWeight: 500 }} 
                    dy={20}
                    minTickGap={30}
                  />
                  
                  <YAxis 
                    width={80}
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#646a77', fontSize: 11, fontWeight: 500 }}
                    tickFormatter={(value) => {
                      if (metricType === "currency") return formatIndianCurrency(value);
                      if (metricType === "percent") return `${value}%`;
                      return formatIndianNumber(value);
                    }}
                    dx={-10}
                  />
                  
                  <Tooltip
                    contentStyle={{ 
                      backgroundColor: '#171a22',
                      borderColor: '#2a2d35',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)'
                    }}
                    itemStyle={{ color: '#fff', fontWeight: 600 }}
                    formatter={(value: number) => {
                      const formatted = metricType === "currency"
                        ? formatIndianCurrency(value)
                        : metricType === "percent"
                        ? `${value.toFixed(1)}%`
                        : formatIndianNumber(value);
                      return [formatted, primaryLabel];
                    }}
                    cursor={{ stroke: '#2a2d35', strokeWidth: 1, strokeDasharray: '4 4' }}
                  />

                  {forecastStartName && forecastEndName && (
                    <ReferenceArea 
                      x1={forecastStartName} 
                      x2={forecastEndName} 
                      fill="#1e222d" 
                      fillOpacity={0.6} 
                    />
                  )}

                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#0070F3"
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#colorValue)"
                    activeDot={{ r: 5, fill: '#0070F3', stroke: '#fff', strokeWidth: 2 }}
                    dot={{ r: 3, fill: '#0070F3', stroke: '#0f1117', strokeWidth: 2 }}
                  />
                  
                  <Area
                    type="monotone"
                    dataKey="forecast"
                    stroke="#9ca3af"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    fill="none"
                    activeDot={{ r: 5, fill: '#9ca3af', stroke: '#15171e', strokeWidth: 2 }}
                    dot={{ r: 3, fill: '#9ca3af', stroke: '#15171e', strokeWidth: 1.5 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </>
          )}
        </div>
      </div>

      <Dialog open={!!selectedMonth} onOpenChange={(open) => !open && setSelectedMonth(null)}>
        <DialogContent className="sm:max-w-[700px] bg-[#0f1117] border-[#1f2229] text-white">
          <DialogHeader>
            <DialogTitle>Drill-down: {selectedMonth}</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-6 py-4">
            {isLoading ? (
              <div className="text-center text-[#646a77] py-12">Loading breakdowns...</div>
            ) : !breakdownData || breakdownData.length === 0 ? (
              <div className="text-center text-[#646a77] py-12">No categorical dimensions found for drill-down.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-h-[60vh] overflow-y-auto pr-2">
                {breakdownData.map((br: any) => (
                  <div key={br.dimension} className="bg-[#171a22] border border-[#1f2229] p-4 rounded-xl flex flex-col gap-2">
                    <h4 className="text-sm font-semibold capitalize text-[#a0a5b1]">{br.dimension}</h4>
                    <div className="h-48">
                      <BResponsiveContainer width="100%" height="100%">
                        <BarChart data={br.data} layout="vertical" margin={{ top: 5, right: 10, left: 20, bottom: 5 }}>
                          <BCartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#1f2229" />
                          <BXAxis type="number" tick={{ fill: '#646a77', fontSize: 10 }} />
                          <BYAxis dataKey="label" type="category" tick={{ fill: '#646a77', fontSize: 10 }} width={60} />
                          <BTooltip contentStyle={{ backgroundColor: '#0f1117', borderColor: '#1f2229', color: '#fff' }} itemStyle={{ color: '#fff' }} />
                          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                            {br.data.map((entry: any, index: number) => (
                              <Cell key={`cell-${index}`} fill="#0070F3" />
                            ))}
                          </Bar>
                        </BarChart>
                      </BResponsiveContainer>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

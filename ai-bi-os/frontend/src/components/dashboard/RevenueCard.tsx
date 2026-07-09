"use client";

import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { BarChart, Bar, CartesianGrid as BCartesianGrid, XAxis as BXAxis, YAxis as BYAxis, Tooltip as BTooltip, ResponsiveContainer as BResponsiveContainer, Cell } from "recharts";

interface RevenueCardProps {
  data: any[];
}

export function RevenueCard({ data }: RevenueCardProps) {
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);

  // Note: hardcoding "Revenue" or "Sales" could fail if the column is named differently.
  // The drill-down modal will try to fetch breakdown for the main revenue metric.
  // In a real app we'd pass the exact column name, but for this exercise we will try to fetch for common revenue columns if needed,
  // or assume the backend uses the main column.
  
  const { data: breakdownData, isLoading } = useQuery({
    queryKey: ["breakdown", selectedMonth],
    // The backend breakdown endpoint takes the column name. We'll use the metric from the chart data if possible,
    // otherwise fallback to Revenue. The EDA page shows the column names. We'll try Revenue for now.
    queryFn: async () => {
      // First find numeric columns to guess revenue metric
      const eda = await api.get<any>("/api/v1/analytics/eda");
      const cols = eda.summary.map((s: any) => s.column);
      const revCol = cols.find((c: string) => /rev|sale|total|amount|price/i.test(c)) || cols[0];
      return api.get<any[]>(`/api/v1/analytics/breakdown?metric=${revCol}&period=${selectedMonth}`);
    },
    enabled: !!selectedMonth,
  });

  const handleChartClick = (state: any) => {
    if (state && state.activeLabel) {
      setSelectedMonth(state.activeLabel);
    }
  };

  return (
    <>
      <Card className="glass-card h-full flex flex-col p-1">
        <CardHeader className="pb-2 pt-4 px-5 flex flex-row items-center justify-between border-b border-border/40 mb-4">
          <CardTitle className="text-base font-semibold tracking-tight text-foreground/90">Revenue Forecast (Click to drill down)</CardTitle>
          <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center gap-1.5 bg-surface border border-border text-xs font-medium text-foreground rounded-lg px-3 py-1.5 outline-none hover:bg-white/5 transition-colors focus:ring-2 focus:ring-primary/30 shadow-sm cursor-pointer">
              Last 12 Months
              <svg className="h-3 w-3 text-muted-foreground ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-36">
              <DropdownMenuItem>Last 12 Months</DropdownMenuItem>
              <DropdownMenuItem>Year to Date</DropdownMenuItem>
              <DropdownMenuItem>All Time</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </CardHeader>
        <CardContent className="flex-1 min-h-[300px] px-2 pb-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 30, left: 10, bottom: 20 }} onClick={handleChartClick}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0070F3" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#0070F3" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#A0A4AE" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#A0A4AE" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
              <XAxis 
                dataKey="name" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#80848E', fontSize: 11, fontWeight: 500 }} 
                dy={15}
              />
              <YAxis 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#80848E', fontSize: 11, fontWeight: 500 }}
                tickFormatter={(value) => `$${value / 1000}k`}
                dx={-10}
              />
              <Tooltip
                contentStyle={{ 
                  backgroundColor: 'rgba(19, 23, 34, 0.85)',
                  backdropFilter: 'blur(12px)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '12px',
                  boxShadow: '0 8px 32px -8px rgba(0,0,0,0.5)',
                  color: '#fff',
                  fontSize: '12px',
                  fontWeight: 500,
                  padding: '8px 12px'
                }}
                itemStyle={{ color: '#fff', fontWeight: 600, fontSize: '13px' }}
                formatter={(value: number) => [`$${value.toLocaleString()}`, 'Revenue']}
                cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1, strokeDasharray: '4 4' }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#0070F3"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#colorValue)"
                activeDot={{ r: 5, fill: '#0B0D12', stroke: '#0070F3', strokeWidth: 2, cursor: 'pointer' }}
              />
              <Area
                type="monotone"
                dataKey="forecast"
                stroke="#A0A4AE"
                strokeWidth={2}
                strokeDasharray="4 4"
                fillOpacity={1}
                fill="url(#colorForecast)"
                activeDot={{ r: 4, fill: '#0B0D12', stroke: '#A0A4AE', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Dialog open={!!selectedMonth} onOpenChange={(open) => !open && setSelectedMonth(null)}>
        <DialogContent className="sm:max-w-[700px] bg-background border-border text-foreground">
          <DialogHeader>
            <DialogTitle>Drill-down: {selectedMonth}</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-6 py-4">
            {isLoading ? (
              <div className="text-center text-muted-foreground py-12">Loading breakdowns...</div>
            ) : !breakdownData || breakdownData.length === 0 ? (
              <div className="text-center text-muted-foreground py-12">No categorical dimensions found for drill-down.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-h-[60vh] overflow-y-auto pr-2">
                {breakdownData.map((br: any) => (
                  <div key={br.dimension} className="glass-card p-4 rounded-xl flex flex-col gap-2">
                    <h4 className="text-sm font-semibold capitalize text-muted-foreground">{br.dimension}</h4>
                    <div className="h-48">
                      <BResponsiveContainer width="100%" height="100%">
                        <BarChart data={br.data} layout="vertical" margin={{ top: 5, right: 10, left: 20, bottom: 5 }}>
                          <BCartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#2a2a2a" />
                          <BXAxis type="number" tick={{ fill: '#666', fontSize: 10 }} />
                          <BYAxis dataKey="label" type="category" tick={{ fill: '#666', fontSize: 10 }} width={60} />
                          <BTooltip contentStyle={{ backgroundColor: '#1a1a1a', borderColor: '#333' }} />
                          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                            {br.data.map((entry: any, index: number) => (
                              <Cell key={`cell-${index}`} fill="#8b5cf6" />
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

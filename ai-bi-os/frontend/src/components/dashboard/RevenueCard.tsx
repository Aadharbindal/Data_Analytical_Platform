"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";

interface RevenueCardProps {
  data: any[];
}

export function RevenueCard({ data }: RevenueCardProps) {
  return (
    <Card className="glass-card h-full flex flex-col p-1">
      <CardHeader className="pb-2 pt-4 px-5 flex flex-row items-center justify-between border-b border-border/40 mb-4">
        <CardTitle className="text-base font-semibold tracking-tight text-foreground/90">Revenue Forecast</CardTitle>
        <div className="relative">
          <select className="appearance-none bg-surface border border-border text-xs font-medium text-foreground rounded-lg px-3 py-1.5 pr-7 outline-none hover:bg-white/5 transition-colors focus:ring-2 focus:ring-primary/30 shadow-sm cursor-pointer">
            <option>Last 12 Months</option>
            <option>Year to Date</option>
            <option>All Time</option>
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-muted-foreground">
            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 min-h-[300px] px-2 pb-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0070F3" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#0070F3" stopOpacity={0} />
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
              activeDot={{ r: 5, fill: '#0B0D12', stroke: '#0070F3', strokeWidth: 2 }}
            />
            <Area
              type="monotone"
              dataKey="forecast"
              stroke="#A0A4AE"
              strokeWidth={2}
              strokeDasharray="4 4"
              fillOpacity={0}
              activeDot={{ r: 4, fill: '#0B0D12', stroke: '#A0A4AE', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

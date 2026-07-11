"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { AlignEndVertical, ChevronDown } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber } from "@/lib/utils";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";

export default function DistributionExplorer() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['distribution'],
    queryFn: () => analyticsApi.distribution()
  });

  const [selectedColumn, setSelectedColumn] = useState<string | null>(null);

  useEffect(() => {
    if (data && data.length > 0 && !selectedColumn) {
      setSelectedColumn(data[0].column_name);
    }
  }, [data, selectedColumn]);

  const activeDist = data?.find((d: any) => d.column_name === selectedColumn) || data?.[0];

  const toolbar = data && data.length > 0 && (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-1.5 bg-surface border border-border text-xs font-medium text-foreground rounded-lg px-3 py-1.5 outline-none hover:bg-white/5 transition-colors focus:ring-2 focus:ring-primary/30 shadow-sm cursor-pointer">
        {selectedColumn || "Select Column"}
        <ChevronDown className="h-3 w-3 text-muted-foreground ml-1 shrink-0" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48 max-h-[300px] overflow-y-auto">
        {data.map((dist: any) => (
          <DropdownMenuItem 
            key={dist.column_name} 
            onClick={() => setSelectedColumn(dist.column_name)}
            className="text-xs cursor-pointer"
          >
            {dist.column_name}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );

  return (
    <StudioPage title="Distribution Explorer" isLoading={isLoading} toolbar={toolbar}>
      {isError ? (
        <ErrorState />
      ) : !data || data.length === 0 ? (
        <div className="text-muted-foreground text-sm">No Distribution data found.</div>
      ) : (
        <div className="flex flex-col gap-6 h-full">
          {activeDist && (
            <div className="glass-card rounded-xl p-6 flex flex-col gap-4 border border-white/[0.05] bg-surface/30 h-[400px]">
              <div className="flex justify-between items-center pb-2">
                <div className="flex items-center gap-2">
                  <span className="text-[14px] font-semibold text-foreground">{activeDist.column_name}</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 bg-primary/10 border border-primary/20 text-primary rounded shrink-0">
                  {activeDist.distribution_type}
                </span>
              </div>
              
              <div className="flex-1 w-full mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={activeDist.histogram} margin={{ top: 10, right: 10, left: -20, bottom: 70 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
                    <XAxis 
                      dataKey="bin" 
                      tick={{ fontSize: 10, fill: "#80848E", fontWeight: 500 }} 
                      axisLine={false} 
                      tickLine={false} 
                      dy={15} 
                      angle={-45} 
                      textAnchor="end"
                    />
                    <YAxis 
                      tick={{ fontSize: 11, fill: "#80848E", fontWeight: 500 }} 
                      tickFormatter={(value) => formatNumber(value)}
                      axisLine={false} 
                      tickLine={false} 
                      dx={-10}
                    />
                    <Tooltip 
                      cursor={{ fill: 'rgba(255,255,255,0.03)' }}
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
                      formatter={(value: number) => [formatNumber(value), 'Count']}
                    />
                    <Bar dataKey="count" fill="#0070F3" radius={[4, 4, 0, 0]} maxBarSize={60} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}
    </StudioPage>
  );
}

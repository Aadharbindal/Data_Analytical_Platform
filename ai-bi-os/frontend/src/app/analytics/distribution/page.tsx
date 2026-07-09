"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { AlignEndVertical } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";

export default function DistributionExplorer() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['distribution'],
    queryFn: () => analyticsApi.distribution()
  });

  if (isLoading) return <div className="p-8"><CardSkeleton lines={10} /></div>;
  if (isError) return <div className="p-8"><ErrorState /></div>;
  if (!data || data.length === 0) return <div className="p-8">No Distribution data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Distribution Explorer</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {data.map((dist: any, i: number) => (
          <div key={i} className="glass-card rounded-[20px] p-6 flex flex-col gap-4">
            <div className="flex justify-between items-center border-b border-border/40 pb-4">
              <div className="flex items-center gap-2">
                <AlignEndVertical className="h-5 w-5 text-sky-500" />
                <h3 className="font-semibold text-lg">{dist.column_name}</h3>
              </div>
              <span className="text-xs px-2 py-1 bg-sky-500/10 text-sky-500 rounded-md font-medium">
                {dist.distribution_type}
              </span>
            </div>
            
            <div className="h-48 w-full mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dist.histogram}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="bin" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
                  <Tooltip 
                    cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                    contentStyle={{ background: "#131722", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px" }} 
                  />
                  <Bar dataKey="count" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

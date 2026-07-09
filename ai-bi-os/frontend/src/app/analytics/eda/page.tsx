"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";

export default function EDAPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['eda'],
    queryFn: () => analyticsApi.eda()
  });

  if (isLoading) return <div className="p-8"><CardSkeleton lines={10} /></div>;
  if (isError) return <div className="p-8"><ErrorState /></div>;
  if (!data || !data.summary || data.summary.length === 0) return <div className="p-8">No EDA data found. Upload a dataset first.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Dataset Analysis (EDA)</h1>
      
      <div className="grid grid-cols-4 gap-4">
        <div className="glass-card rounded-[20px] p-6">
          <div className="text-sm text-muted-foreground">Rows</div>
          <div className="text-2xl font-semibold">{data.rows.toLocaleString()}</div>
        </div>
        <div className="glass-card rounded-[20px] p-6">
          <div className="text-sm text-muted-foreground">Columns</div>
          <div className="text-2xl font-semibold">{data.columns.length}</div>
        </div>
      </div>

      <div className="glass-card rounded-[20px] p-6 overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead>
            <tr className="border-b border-border/40 text-muted-foreground">
              <th className="py-3 px-4">Column Name</th>
              <th className="py-3 px-4">Type</th>
              <th className="py-3 px-4">Nulls</th>
              <th className="py-3 px-4">Mean</th>
              <th className="py-3 px-4">Min/Max</th>
              <th className="py-3 px-4">Unique / Top Vals</th>
            </tr>
          </thead>
          <tbody>
            {data.summary.map((c: any) => (
              <tr key={c.column} className="border-b border-border/20">
                <td className="py-3 px-4 font-medium">{c.column}</td>
                <td className="py-3 px-4 text-muted-foreground">{c.type}</td>
                <td className="py-3 px-4">{c.nulls}</td>
                <td className="py-3 px-4">{c.mean?.toFixed(2) ?? '-'}</td>
                <td className="py-3 px-4">{c.min != null ? `${c.min} / ${c.max}` : '-'}</td>
                <td className="py-3 px-4">
                  {c.unique != null ? `${c.unique} unique` : '-'}
                  {c.top_values && (
                    <div className="text-xs text-muted-foreground truncate max-w-[200px]">
                      {Object.entries(c.top_values).map(([k,v]) => `${k}:${v}`).join(', ')}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

"use client";

import { useDatasetAnalytics } from "@/hooks/useAnalytics";

export default function EDAPage() {
  const { eda, isLoading } = useDatasetAnalytics("demo", "v1");

  if (isLoading) return <div className="p-8">Loading EDA Profile...</div>;

  const data = eda.data;
  if (!data) return <div className="p-8">No EDA data found.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h1 className="text-2xl font-semibold">Dataset Analysis (EDA)</h1>
      
      <div className="grid grid-cols-4 gap-4">
        <div className="glass-card rounded-[20px] p-6">
          <div className="text-sm text-muted-foreground">Rows</div>
          <div className="text-2xl font-semibold">{data.row_count.toLocaleString()}</div>
        </div>
        <div className="glass-card rounded-[20px] p-6">
          <div className="text-sm text-muted-foreground">Columns</div>
          <div className="text-2xl font-semibold">{data.column_count}</div>
        </div>
        <div className="glass-card rounded-[20px] p-6">
          <div className="text-sm text-muted-foreground">Missing Cells</div>
          <div className="text-2xl font-semibold text-amber-500">{data.missing_cells.toLocaleString()}</div>
        </div>
        <div className="glass-card rounded-[20px] p-6">
          <div className="text-sm text-muted-foreground">Duplicate Rows</div>
          <div className="text-2xl font-semibold text-rose-500">{data.duplicate_rows.toLocaleString()}</div>
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
            </tr>
          </thead>
          <tbody>
            {data.columns.map(c => (
              <tr key={c.name} className="border-b border-border/20">
                <td className="py-3 px-4 font-medium">{c.name}</td>
                <td className="py-3 px-4 text-muted-foreground">{c.type}</td>
                <td className="py-3 px-4">{c.null_count}</td>
                <td className="py-3 px-4">{c.mean?.toFixed(2) ?? '-'}</td>
                <td className="py-3 px-4">{c.min ?? '-'} / {c.max ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

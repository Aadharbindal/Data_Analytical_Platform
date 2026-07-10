"use client";

import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { TableSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import type { Dataset } from "@/lib/types";
import { Database } from "lucide-react";

interface DataTableProps {
  datasets: Dataset[];
  loading: boolean;
}

const statusColors: Record<string, string> = {
  active: "bg-success/10 text-success border-success/20",
  processing: "bg-warning/10 text-warning border-warning/20",
  failed: "bg-error/10 text-error border-error/20",
  archived: "bg-muted/10 text-muted-foreground border-border/40",
};

export function DataTable({ datasets, loading }: DataTableProps) {
  if (loading) return <TableSkeleton rows={5} />;

  if (datasets.length === 0) {
    return (
      <div className="rounded-[20px] border border-border bg-surface overflow-hidden">
        <EmptyState
          icon={<Database className="h-7 w-7 text-muted-foreground/50" />}
          title="No datasets yet"
          description="Upload your first dataset to get started with analytics."
        />
      </div>
    );
  }

  return (
    <div className="rounded-[20px] border border-border bg-surface overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <Table className="w-full text-sm">
          <TableHeader className="bg-background/80 backdrop-blur-md sticky top-0 z-10 border-b border-border/50">
            <TableRow className="hover:bg-transparent">
              <TableHead className="font-semibold text-muted-foreground/80 h-14 px-6">Name</TableHead>
              <TableHead className="font-semibold text-muted-foreground/80 h-14 px-6">Status</TableHead>
              <TableHead className="font-semibold text-muted-foreground/80 h-14 px-6">Rows</TableHead>
              <TableHead className="font-semibold text-muted-foreground/80 h-14 px-6">Size</TableHead>
              <TableHead className="text-right font-semibold text-muted-foreground/80 h-14 px-6">Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {datasets.slice(0, 8).map((ds) => (
              <TableRow
                key={ds.id}
                className="border-border/40 hover:bg-white/[0.02] transition-colors h-16 group"
              >
                <TableCell className="font-medium text-foreground px-6 py-4">{ds.name}</TableCell>
                <TableCell className="px-6 py-4">
                  <Badge
                    variant="outline"
                    className={`rounded-full px-2.5 py-0.5 capitalize ${statusColors[ds.status] ?? statusColors.archived}`}
                  >
                    {ds.status}
                  </Badge>
                </TableCell>
                <TableCell className="tabular-metrics text-muted-foreground px-6 py-4">
                  {ds.latest_version?.row_count?.toLocaleString() ?? "–"}
                </TableCell>
                <TableCell className="tabular-metrics text-muted-foreground px-6 py-4">
                  {ds.latest_version?.file_size_bytes
                    ? `${(ds.latest_version.file_size_bytes / 1024).toFixed(1)} KB`
                    : "–"}
                </TableCell>
                <TableCell className="text-right text-muted-foreground text-[13px] px-6 py-4">
                  {new Date(ds.created_at).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

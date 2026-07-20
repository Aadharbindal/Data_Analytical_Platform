import { TableSkeleton } from "@/components/ui/skeleton-loader";

export default function DataCatalogLoading() {
  return (
    <div className="flex flex-col gap-6 animate-pulse">
      <div className="h-5 w-40 rounded-lg bg-white/[0.04]" />
      <TableSkeleton rows={6} />
    </div>
  );
}

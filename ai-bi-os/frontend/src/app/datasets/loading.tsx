// Next.js route-level loading UI — shown instantly during page navigation
import { TableSkeleton } from "@/components/ui/skeleton-loader";

export default function DatasetsLoading() {
  return (
    <div className="flex flex-col gap-6">
      {/* Badge placeholder */}
      <div className="flex items-center justify-end">
        <div className="h-6 w-24 rounded-full bg-white/[0.04] animate-pulse" />
      </div>
      {/* Upload zone placeholder */}
      <div className="rounded-[20px] border-2 border-dashed border-[#333842] p-10 animate-pulse flex items-center justify-center h-[160px]">
        <div className="h-5 w-48 rounded-lg bg-white/[0.04]" />
      </div>
      {/* Table placeholder */}
      <TableSkeleton rows={6} />
    </div>
  );
}

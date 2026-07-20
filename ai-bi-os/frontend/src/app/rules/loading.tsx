import { TableSkeleton } from "@/components/ui/skeleton-loader";

export default function RulesLoading() {
  return (
    <div className="flex flex-col gap-6 animate-pulse">
      <div className="h-5 w-36 rounded-lg bg-white/[0.04]" />
      <TableSkeleton rows={5} />
    </div>
  );
}

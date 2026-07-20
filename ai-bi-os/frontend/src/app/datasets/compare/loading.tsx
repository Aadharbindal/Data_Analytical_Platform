import { TableSkeleton } from "@/components/ui/skeleton-loader";

export default function DatasetsCompareLoading() {
  return (
    <div className="flex flex-col gap-6 animate-pulse">
      <div className="h-5 w-48 rounded-lg bg-white/[0.04]" />
      <div className="grid grid-cols-2 gap-4">
        <div className="glass-card rounded-[20px] h-[300px] bg-white/[0.02]" />
        <div className="glass-card rounded-[20px] h-[300px] bg-white/[0.02]" />
      </div>
    </div>
  );
}

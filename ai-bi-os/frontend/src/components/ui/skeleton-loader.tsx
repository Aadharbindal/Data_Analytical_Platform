import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-xl bg-white/[0.04]",
        className
      )}
    />
  );
}

export function MetricCardSkeleton() {
  return (
    <div className="glass-card rounded-[20px] p-5 md:p-6">
      <Skeleton className="h-4 w-32 mb-4" />
      <Skeleton className="h-9 w-28" />
    </div>
  );
}

export function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="glass-card rounded-[20px] p-6 space-y-3">
      <Skeleton className="h-5 w-48" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={`h-4 ${i === lines - 1 ? "w-2/3" : "w-full"}`} />
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="rounded-[20px] border border-border bg-surface overflow-hidden">
      <div className="p-4 border-b border-border/50">
        <Skeleton className="h-4 w-full" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="p-4 border-b border-border/40 flex gap-4">
          <Skeleton className="h-4 w-1/5" />
          <Skeleton className="h-4 w-2/5" />
          <Skeleton className="h-4 w-1/5" />
          <Skeleton className="h-4 w-1/5" />
        </div>
      ))}
    </div>
  );
}

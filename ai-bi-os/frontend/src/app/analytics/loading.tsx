// Next.js route-level loading UI — shown instantly during page navigation
// Uses existing skeleton components — no logic change
import { CardSkeleton } from "@/components/ui/skeleton-loader";

export default function AnalyticsLoading() {
  return (
    <div className="flex flex-col gap-8 h-full p-8 overflow-y-auto">
      {/* KPI row */}
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="glass-card rounded-[20px] p-6 animate-pulse space-y-4">
            <div className="h-4 w-32 rounded-lg bg-white/[0.04]" />
            <div className="h-9 w-20 rounded-lg bg-white/[0.04]" />
          </div>
        ))}
      </div>
      {/* Cards row */}
      <div className="grid grid-cols-2 gap-6 mt-4">
        <CardSkeleton lines={4} />
        <CardSkeleton lines={4} />
      </div>
    </div>
  );
}

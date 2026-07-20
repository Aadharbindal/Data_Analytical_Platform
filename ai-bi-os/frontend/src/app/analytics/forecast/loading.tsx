// Next.js route-level loading UI for forecast page
import { CardSkeleton } from "@/components/ui/skeleton-loader";

export default function ForecastLoading() {
  return (
    <div className="flex flex-col gap-6 h-full p-6">
      {/* Chart area skeleton */}
      <div className="glass-card rounded-xl p-6 h-[400px] animate-pulse">
        <div className="h-5 w-48 rounded-lg bg-white/[0.04] mb-6" />
        <div className="h-full w-full rounded-lg bg-white/[0.02]" />
      </div>
    </div>
  );
}

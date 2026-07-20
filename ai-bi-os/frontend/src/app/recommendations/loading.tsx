import { CardSkeleton } from "@/components/ui/skeleton-loader";

export default function RecommendationsLoading() {
  return (
    <div className="flex flex-col gap-6 animate-pulse">
      <div className="h-5 w-44 rounded-lg bg-white/[0.04]" />
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <CardSkeleton key={i} lines={2} />
        ))}
      </div>
    </div>
  );
}

import { CardSkeleton } from "@/components/ui/skeleton-loader";

export default function KnowledgeConsoleLoading() {
  return (
    <div className="flex flex-col gap-6 animate-pulse">
      <div className="h-5 w-48 rounded-lg bg-white/[0.04]" />
      <CardSkeleton lines={5} />
    </div>
  );
}

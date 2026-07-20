import { TableSkeleton } from "@/components/ui/skeleton-loader";

export default function ChatLoading() {
  return (
    <div className="flex flex-col h-full animate-pulse">
      <div className="flex-1 p-6 space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className={`flex ${i % 2 === 0 ? "justify-end" : "justify-start"}`}>
            <div className={`h-12 rounded-2xl bg-white/[0.04] ${i % 2 === 0 ? "w-2/5" : "w-3/5"}`} />
          </div>
        ))}
      </div>
      <div className="p-4 border-t border-border/40">
        <div className="h-12 rounded-xl bg-white/[0.04]" />
      </div>
    </div>
  );
}

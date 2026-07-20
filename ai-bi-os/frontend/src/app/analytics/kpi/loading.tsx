export default function KpiLoading() {
  return (
    <div className="flex flex-col gap-6 h-full p-6 animate-pulse">
      <div className="grid grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="glass-card rounded-[20px] p-6 space-y-4">
            <div className="h-4 w-28 rounded-lg bg-white/[0.04]" />
            <div className="h-9 w-20 rounded-lg bg-white/[0.04]" />
          </div>
        ))}
      </div>
    </div>
  );
}

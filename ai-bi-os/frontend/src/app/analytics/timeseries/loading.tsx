// Next.js route-level loading UI for timeseries page
export default function TimeseriesLoading() {
  return (
    <div className="flex flex-col gap-6 h-full p-6">
      <div className="glass-card rounded-xl h-[400px] animate-pulse bg-white/[0.02] p-6">
        <div className="h-5 w-44 rounded-lg bg-white/[0.04] mb-4" />
        <div className="h-full w-full rounded-lg bg-white/[0.02]" />
      </div>
    </div>
  );
}

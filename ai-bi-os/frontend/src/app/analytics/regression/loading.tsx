// Next.js route-level loading UI for regression page
export default function RegressionLoading() {
  return (
    <div className="flex flex-col gap-6 h-full p-6">
      <div className="glass-card rounded-xl p-6 animate-pulse space-y-4">
        <div className="h-5 w-52 rounded-lg bg-white/[0.04]" />
        <div className="grid grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 rounded-xl bg-white/[0.04]" />
          ))}
        </div>
      </div>
      <div className="glass-card rounded-xl h-[300px] animate-pulse bg-white/[0.02]" />
    </div>
  );
}

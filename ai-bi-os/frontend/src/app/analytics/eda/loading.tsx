export default function EdaLoading() {
  return (
    <div className="flex flex-col gap-6 h-full p-6 animate-pulse">
      <div className="glass-card rounded-xl p-6 space-y-4">
        <div className="h-5 w-56 rounded-lg bg-white/[0.04]" />
        <div className="grid grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-white/[0.04]" />
          ))}
        </div>
      </div>
    </div>
  );
}

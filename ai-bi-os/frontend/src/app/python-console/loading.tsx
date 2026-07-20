export default function PythonConsoleLoading() {
  return (
    <div className="flex flex-col h-full animate-pulse">
      <div className="flex-1 p-6">
        <div className="h-full rounded-xl bg-white/[0.04] border border-border/40" />
      </div>
      <div className="p-4 border-t border-border/40">
        <div className="h-10 rounded-lg bg-white/[0.04]" />
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { datasetsApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Dataset, DatasetColumn } from "@/lib/types";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Wand2, Sigma, GitMerge, AlertCircle, CheckCircle2, Loader2, ArrowRight } from "lucide-react";

// Hides native scrollbars on the element while keeping it scrollable —
// applied directly (not relying only on the global rule) since this list
// lives inside a portaled Dialog.
const scrollbarHideClass = "[scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden";

// Keyed off each column's position so a column keeps its colour as you scroll.
const ACCENTS = [
  "bg-emerald-400",
  "bg-blue-400",
  "bg-violet-400",
  "bg-orange-400",
  "bg-amber-300",
  "bg-pink-400",
  "bg-cyan-400",
  "bg-rose-400",
];

type Tab = "rename" | "formula" | "merge";

const TABS: { id: Tab; label: string; icon: typeof Wand2 }[] = [
  { id: "rename", label: "Rename columns", icon: Wand2 },
  { id: "formula", label: "Formula column", icon: Sigma },
  { id: "merge", label: "Merge datasets", icon: GitMerge },
];

const selectClass =
  "h-10 w-full rounded-xl border border-input bg-background/60 px-3 text-sm outline-none transition-colors hover:border-border focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50";

const fieldLabelClass = "mb-1.5 block text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground/70";

const primaryActionClass =
  "w-full rounded-full shadow-[0_6px_20px_rgba(59,130,246,0.4)] transition-transform hover:scale-[1.02] active:scale-[0.98]";

interface TransformDatasetModalProps {
  /** The dataset row (latest version of its lineage) the transform starts from. */
  dataset: { id: string; name: string; columns: DatasetColumn[] } | null;
  /** Every lineage's latest version, for the merge tab's "other dataset" picker. */
  datasets: Dataset[];
  onClose: () => void;
}

export function TransformDatasetModal({ dataset, datasets, onClose }: TransformDatasetModalProps) {
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("rename");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Rename tab state
  const [renameValues, setRenameValues] = useState<Record<string, string>>({});

  // Formula tab state
  const [formulaName, setFormulaName] = useState("");
  const [formulaExpr, setFormulaExpr] = useState("");

  // Merge tab state
  const [otherId, setOtherId] = useState("");
  const [leftOn, setLeftOn] = useState("");
  const [rightOn, setRightOn] = useState("");
  const [how, setHow] = useState("left");
  const [mergeName, setMergeName] = useState("");

  useEffect(() => {
    if (!dataset) return;
    // Resetting the form when a new dataset is opened for transforming is the
    // same "synchronize local state with a changed prop" case React's own
    // docs treat as a legitimate effect.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTab("rename");
    setError(null);
    setSuccess(null);
    setRenameValues(Object.fromEntries(dataset.columns.map((c) => [c.name, c.name])));
    setFormulaName("");
    setFormulaExpr("");
    setLeftOn(dataset.columns[0]?.name ?? "");
    setOtherId("");
    setRightOn("");
    setHow("left");
    setMergeName("");
  }, [dataset]);

  if (!dataset) return null;

  const otherOptions = datasets.filter((d) => d.name !== dataset.name);
  const otherDataset = otherOptions.find((d) => d.id === otherId);
  const changedCount = dataset.columns.filter(
    (c) => (renameValues[c.name] ?? c.name).trim() && (renameValues[c.name] ?? c.name).trim() !== c.name
  ).length;

  const afterSuccess = async (message: string) => {
    setSuccess(message);
    await Promise.all([
      qc.invalidateQueries({ queryKey: ["datasets"] }),
      qc.invalidateQueries({ queryKey: ["activeDataset"] }),
      qc.invalidateQueries({ queryKey: ["active-dataset"] }),
      qc.invalidateQueries({ queryKey: ["dataset-versions"] }),
    ]);
  };

  const submitRename = async () => {
    const renames = Object.fromEntries(
      Object.entries(renameValues).filter(([oldName, newName]) => newName.trim() && newName.trim() !== oldName)
    );
    if (Object.keys(renames).length === 0) {
      setError("Change at least one column name first");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await datasetsApi.transformRename(dataset.id, renames);
      await afterSuccess(`Saved as v${res.dataset.version} — ${Object.keys(renames).length} column(s) renamed`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rename failed");
    } finally {
      setBusy(false);
    }
  };

  const submitFormula = async () => {
    if (!formulaName.trim() || !formulaExpr.trim()) {
      setError("Give the new column a name and an expression");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await datasetsApi.transformFormula(dataset.id, formulaName.trim(), formulaExpr.trim());
      await afterSuccess(`Saved as v${res.dataset.version} — added '${formulaName.trim()}'`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Formula failed");
    } finally {
      setBusy(false);
    }
  };

  const submitMerge = async () => {
    if (!otherId || !leftOn || !rightOn) {
      setError("Pick a dataset and a join column on both sides");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await datasetsApi.transformMerge(dataset.id, {
        other_dataset_id: otherId,
        left_on: leftOn,
        right_on: rightOn,
        how,
        new_name: mergeName.trim() || undefined,
      });
      await afterSuccess(`Created '${res.dataset.name}' (${res.dataset.latest_version?.row_count ?? "?"} rows)`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Merge failed");
    } finally {
      setBusy(false);
    }
  };

  const activeTab = TABS.find((t) => t.id === tab)!;

  return (
    <Dialog open={!!dataset} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg gap-5 rounded-[24px] p-6">
        <DialogHeader className="gap-3">
          <div className="flex items-center gap-3.5">
            <motion.div
              key={tab}
              initial={{ scale: 0.5, opacity: 0, rotate: -12 }}
              animate={{ scale: 1, opacity: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 380, damping: 18 }}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#3b82f6] to-[#2563eb] shadow-[0_6px_20px_rgba(59,130,246,0.45)]"
            >
              <activeTab.icon className="h-5 w-5 text-white" strokeWidth={2.5} />
            </motion.div>
            <DialogTitle className="min-w-0 text-lg font-semibold tracking-tight">
              Transform <span className="text-primary">&quot;{dataset.name}&quot;</span>
            </DialogTitle>
          </div>
          <DialogDescription className="leading-relaxed">
            Every change is saved as a new version — nothing here overwrites the original, and you can roll back anytime
            from the version history.
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-1 rounded-2xl border border-border/50 bg-background/40 p-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => {
                setTab(t.id);
                setError(null);
                setSuccess(null);
              }}
              className={cn(
                "relative flex flex-1 items-center justify-center gap-1.5 whitespace-nowrap rounded-xl px-2 py-2 text-xs font-medium transition-colors",
                tab === t.id ? "text-primary" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {tab === t.id && (
                <motion.span
                  layoutId="transform-tab-pill"
                  transition={{ type: "spring", stiffness: 500, damping: 35 }}
                  className="absolute inset-0 rounded-xl border border-primary/25 bg-primary/10"
                />
              )}
              <t.icon className="relative h-3.5 w-3.5 shrink-0" />
              <span className="relative">{t.label}</span>
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {success ? (
            <motion.div
              key="success"
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="flex items-start gap-2.5 rounded-2xl border border-success/25 bg-success/10 p-4 text-sm text-success"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.1, type: "spring", stiffness: 400, damping: 15 }}
              >
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              </motion.div>
              <div>
                <div className="font-medium">{success}</div>
                <button
                  type="button"
                  onClick={onClose}
                  className="mt-1 text-xs underline underline-offset-2 hover:no-underline"
                >
                  Close
                </button>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key={tab}
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
            >
              {tab === "rename" && (
                <div className="flex flex-col gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground/70">
                      Columns
                    </span>
                    <span className="rounded-md bg-white/[0.06] px-1.5 py-0.5 text-[11px] font-semibold tabular-nums text-muted-foreground">
                      {dataset.columns.length}
                    </span>
                    <AnimatePresence>
                      {changedCount > 0 && (
                        <motion.span
                          initial={{ scale: 0.5, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          exit={{ scale: 0.5, opacity: 0 }}
                          transition={{ type: "spring", stiffness: 500, damping: 22 }}
                          className="ml-auto rounded-md bg-primary/15 px-2 py-0.5 text-[11px] font-semibold text-primary"
                        >
                          {changedCount} changed
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Fade at the bottom edge so a long list reads as "scrolls on"
                      rather than looking abruptly clipped mid-row. */}
                  <div className="relative">
                    <div className={cn("flex max-h-[280px] flex-col gap-2.5 overflow-y-auto pb-2", scrollbarHideClass)}>
                      {dataset.columns.map((col, i) => {
                        const value = renameValues[col.name] ?? col.name;
                        const changed = value.trim() !== col.name && value.trim() !== "";
                        return (
                          <motion.div
                            key={col.name}
                            initial={{ opacity: 0, y: -6 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.18, delay: Math.min(i * 0.03, 0.3) }}
                            className={cn(
                              "flex items-center gap-3 rounded-2xl border px-3.5 py-2.5 transition-colors",
                              changed
                                ? "border-primary/30 bg-primary/[0.06]"
                                : "border-border/50 bg-surface/60 hover:border-border hover:bg-surface"
                            )}
                          >
                            <span
                              className={cn("h-2 w-2 shrink-0 rounded-[3px]", ACCENTS[i % ACCENTS.length])}
                            />
                            <span
                              className="w-[34%] shrink-0 truncate text-sm text-muted-foreground"
                              title={col.name}
                            >
                              {col.name}
                            </span>
                            <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground/40" />
                            <Input
                              value={value}
                              onChange={(e) =>
                                setRenameValues((prev) => ({ ...prev, [col.name]: e.target.value }))
                              }
                              className="h-9 flex-1 rounded-xl"
                            />
                          </motion.div>
                        );
                      })}
                    </div>
                    <div className="pointer-events-none absolute inset-x-0 bottom-0 h-8 bg-gradient-to-t from-popover to-transparent" />
                  </div>

                  <Button onClick={submitRename} disabled={busy} className={primaryActionClass}>
                    {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save renamed columns"}
                  </Button>
                </div>
              )}

              {tab === "formula" && (
                <div className="flex flex-col gap-4">
                  <div>
                    <label className={fieldLabelClass}>New column name</label>
                    <Input
                      value={formulaName}
                      onChange={(e) => setFormulaName(e.target.value)}
                      placeholder="e.g. profit_margin"
                      className="h-10 rounded-xl"
                    />
                  </div>
                  <div>
                    <label className={fieldLabelClass}>Expression</label>
                    <Input
                      value={formulaExpr}
                      onChange={(e) => setFormulaExpr(e.target.value)}
                      placeholder="e.g. (revenue - cost) / revenue"
                      className="h-10 rounded-xl font-mono"
                    />
                  </div>
                  <div>
                    <label className={fieldLabelClass}>Insert a column</label>
                    <div className={cn("flex max-h-24 flex-wrap gap-1.5 overflow-y-auto", scrollbarHideClass)}>
                      {dataset.columns.map((c, i) => (
                        <motion.button
                          key={c.name}
                          type="button"
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ duration: 0.15, delay: Math.min(i * 0.02, 0.2) }}
                          whileHover={{ scale: 1.06 }}
                          whileTap={{ scale: 0.94 }}
                          onClick={() => setFormulaExpr((prev) => (prev ? `${prev} ${c.name}` : c.name))}
                          className="flex items-center gap-1.5 rounded-full border border-border/60 bg-surface/60 px-2.5 py-1 font-mono text-[11px] text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary"
                        >
                          <span className={cn("h-1.5 w-1.5 rounded-full", ACCENTS[i % ACCENTS.length])} />
                          {c.name}
                        </motion.button>
                      ))}
                    </div>
                  </div>
                  <p className="rounded-xl border border-border/40 bg-background/40 p-3 text-[11px] leading-relaxed text-muted-foreground">
                    Supports + − × ÷ () and abs, round, sqrt, log, log10, exp, min, max. No other functions run — kept
                    deliberately narrow so a formula can&apos;t reach outside your data.
                  </p>
                  <Button onClick={submitFormula} disabled={busy} className={primaryActionClass}>
                    {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Add column"}
                  </Button>
                </div>
              )}

              {tab === "merge" && (
                <div className="flex flex-col gap-4">
                  <div>
                    <label className={fieldLabelClass}>Merge with</label>
                    <select
                      className={selectClass}
                      value={otherId}
                      onChange={(e) => {
                        setOtherId(e.target.value);
                        setRightOn("");
                      }}
                    >
                      <option value="">Select a dataset…</option>
                      {otherOptions.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className={fieldLabelClass}>This dataset&apos;s key</label>
                      <select className={selectClass} value={leftOn} onChange={(e) => setLeftOn(e.target.value)}>
                        {dataset.columns.map((c) => (
                          <option key={c.name} value={c.name}>
                            {c.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className={fieldLabelClass}>Other dataset&apos;s key</label>
                      <select
                        className={selectClass}
                        value={rightOn}
                        onChange={(e) => setRightOn(e.target.value)}
                        disabled={!otherDataset}
                      >
                        <option value="">—</option>
                        {(otherDataset?.columns ?? []).map((c) => (
                          <option key={c.name} value={c.name}>
                            {c.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className={fieldLabelClass}>Join type</label>
                    <select className={selectClass} value={how} onChange={(e) => setHow(e.target.value)}>
                      <option value="left">Left — keep every row from this dataset</option>
                      <option value="inner">Inner — only rows that match in both</option>
                      <option value="right">Right — keep every row from the other dataset</option>
                      <option value="outer">Outer — keep every row from either</option>
                    </select>
                  </div>
                  <div>
                    <label className={fieldLabelClass}>New dataset name (optional)</label>
                    <Input
                      value={mergeName}
                      onChange={(e) => setMergeName(e.target.value)}
                      placeholder={`${dataset.name} + ${otherDataset?.name ?? "..."} (merged).csv`}
                      className="h-10 rounded-xl"
                    />
                  </div>
                  <Button onClick={submitMerge} disabled={busy || !otherId} className={primaryActionClass}>
                    {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Merge into a new dataset"}
                  </Button>
                </div>
              )}

              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, height: 0, marginTop: 0 }}
                    animate={{ opacity: 1, height: "auto", marginTop: 14 }}
                    exit={{ opacity: 0, height: 0, marginTop: 0 }}
                    transition={{ duration: 0.18 }}
                    className="flex items-start gap-2 overflow-hidden rounded-xl border border-error/25 bg-error/10 p-3 text-xs text-error"
                  >
                    <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    <span>{error}</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
}

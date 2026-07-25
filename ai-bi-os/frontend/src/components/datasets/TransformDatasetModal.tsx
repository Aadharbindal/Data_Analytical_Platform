"use client";

import { useState, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { datasetsApi } from "@/lib/api";
import type { Dataset, DatasetColumn } from "@/lib/types";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Wand2, Sigma, GitMerge, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

type Tab = "rename" | "formula" | "merge";

const TABS: { id: Tab; label: string; icon: typeof Wand2 }[] = [
  { id: "rename", label: "Rename columns", icon: Wand2 },
  { id: "formula", label: "Formula column", icon: Sigma },
  { id: "merge", label: "Merge datasets", icon: GitMerge },
];

const selectClass =
  "h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50";

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

  return (
    <Dialog open={!!dataset} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Transform &quot;{dataset.name}&quot;</DialogTitle>
          <DialogDescription>
            Every change is saved as a new version — nothing here overwrites the original, and you can roll back anytime from the version history.
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-1 rounded-lg border border-border bg-surface/50 p-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => {
                setTab(t.id);
                setError(null);
                setSuccess(null);
              }}
              className={`flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 text-xs font-medium transition-colors ${
                tab === t.id ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <t.icon className="h-3.5 w-3.5" />
              {t.label}
            </button>
          ))}
        </div>

        {success ? (
          <div className="flex items-start gap-2.5 rounded-lg border border-success/25 bg-success/10 p-3 text-sm text-success">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <div className="font-medium">{success}</div>
              <button type="button" onClick={onClose} className="mt-1 text-xs underline underline-offset-2 hover:no-underline">
                Close
              </button>
            </div>
          </div>
        ) : (
          <>
            {tab === "rename" && (
              <div className="flex flex-col gap-3">
                <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
                  {dataset.columns.map((col) => (
                    <div key={col.name} className="flex items-center gap-2">
                      <span className="w-1/2 truncate text-xs text-muted-foreground" title={col.name}>
                        {col.name}
                      </span>
                      <span className="text-muted-foreground/50">→</span>
                      <Input
                        value={renameValues[col.name] ?? col.name}
                        onChange={(e) => setRenameValues((prev) => ({ ...prev, [col.name]: e.target.value }))}
                        className="flex-1"
                      />
                    </div>
                  ))}
                </div>
                <Button onClick={submitRename} disabled={busy} className="w-full">
                  {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save renamed columns"}
                </Button>
              </div>
            )}

            {tab === "formula" && (
              <div className="flex flex-col gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-muted-foreground">New column name</label>
                  <Input value={formulaName} onChange={(e) => setFormulaName(e.target.value)} placeholder="e.g. profit_margin" />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-muted-foreground">Expression</label>
                  <Input
                    value={formulaExpr}
                    onChange={(e) => setFormulaExpr(e.target.value)}
                    placeholder="e.g. (revenue - cost) / revenue"
                    className="font-mono"
                  />
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {dataset.columns.map((c) => (
                    <button
                      key={c.name}
                      type="button"
                      onClick={() => setFormulaExpr((prev) => (prev ? `${prev} ${c.name}` : c.name))}
                      className="rounded-full border border-border bg-surface px-2 py-0.5 font-mono text-[11px] text-muted-foreground hover:text-foreground"
                    >
                      {c.name}
                    </button>
                  ))}
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Supports + − × ÷ () and abs, round, sqrt, log, log10, exp, min, max. No other functions run — kept
                  deliberately narrow so a formula can&apos;t reach outside your data.
                </p>
                <Button onClick={submitFormula} disabled={busy} className="w-full">
                  {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Add column"}
                </Button>
              </div>
            )}

            {tab === "merge" && (
              <div className="flex flex-col gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-muted-foreground">Merge with</label>
                  <select className={selectClass} value={otherId} onChange={(e) => { setOtherId(e.target.value); setRightOn(""); }}>
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
                    <label className="mb-1 block text-xs font-medium text-muted-foreground">This dataset&apos;s key</label>
                    <select className={selectClass} value={leftOn} onChange={(e) => setLeftOn(e.target.value)}>
                      {dataset.columns.map((c) => (
                        <option key={c.name} value={c.name}>
                          {c.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium text-muted-foreground">Other dataset&apos;s key</label>
                    <select className={selectClass} value={rightOn} onChange={(e) => setRightOn(e.target.value)} disabled={!otherDataset}>
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
                  <label className="mb-1 block text-xs font-medium text-muted-foreground">Join type</label>
                  <select className={selectClass} value={how} onChange={(e) => setHow(e.target.value)}>
                    <option value="left">Left — keep every row from this dataset</option>
                    <option value="inner">Inner — only rows that match in both</option>
                    <option value="right">Right — keep every row from the other dataset</option>
                    <option value="outer">Outer — keep every row from either</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-muted-foreground">New dataset name (optional)</label>
                  <Input value={mergeName} onChange={(e) => setMergeName(e.target.value)} placeholder={`${dataset.name} + ${otherDataset?.name ?? "..."} (merged).csv`} />
                </div>
                <Button onClick={submitMerge} disabled={busy || !otherId} className="w-full">
                  {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Merge into a new dataset"}
                </Button>
              </div>
            )}

            {error && (
              <div className="flex items-start gap-2 rounded-lg border border-error/25 bg-error/10 p-2.5 text-xs text-error">
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

"use client";

import React, { useState } from "react";
import { motion, AnimatePresence, Reorder } from "framer-motion";
import { GripVertical, Pin, PinOff, Loader2, LayoutGrid, AlertCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { dashboardApi } from "@/lib/api";
import { cn, formatKpiValue } from "@/lib/utils";
import { useQueryClient } from "@tanstack/react-query";
import type { KpiItem } from "@/lib/types";

const DEFAULT_PINNED_COUNT = 4;

// Hides native scrollbars on the element while keeping it scrollable —
// applied directly (not relying only on the global rule) since this list
// lives inside a portaled Dialog.
const scrollbarHideClass = "[scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden";

// Keyed off each KPI's position in the full list (not the pinned list) so a
// metric keeps its colour while being pinned, unpinned, and reordered.
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

interface CustomizeDashboardModalProps {
  kpis: KpiItem[];
  pinnedIds: string[] | null;
}

export function CustomizeDashboardModal({ kpis, pinnedIds }: CustomizeDashboardModalProps) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const defaultPinned = kpis.slice(0, DEFAULT_PINNED_COUNT).map((k) => k.id);
  const effectivePinned = pinnedIds && pinnedIds.length > 0 ? pinnedIds : defaultPinned;

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (next) {
      setError(null);
      // Only keep ids that still exist among the current dataset's KPIs.
      setDraft(effectivePinned.filter((id) => kpis.some((k) => k.id === id)));
    }
  };

  const kpiById = (id: string) => kpis.find((k) => k.id === id);
  const accentFor = (id: string) => ACCENTS[Math.max(0, kpis.findIndex((k) => k.id === id)) % ACCENTS.length];
  const availableKpis = kpis.filter((k) => !draft.includes(k.id));

  const pin = (id: string) => setDraft((prev) => [...prev, id]);
  const unpin = (id: string) => setDraft((prev) => prev.filter((x) => x !== id));

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await dashboardApi.saveLayout(draft);
      await queryClient.invalidateQueries({ queryKey: ["dashboard-layout"] });
      setOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save your dashboard layout.");
    } finally {
      setSaving(false);
    }
  };

  const handleResetToDefault = () => setDraft(defaultPinned);

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <button
        onClick={() => handleOpenChange(true)}
        className="group flex items-center gap-2.5 px-6 py-3 rounded-full bg-background/60 backdrop-blur-xl border border-border/50 shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.2)] hover:bg-background/80 hover:scale-105 transition-all duration-300 text-sm font-medium text-foreground"
      >
        <LayoutGrid className="h-4 w-4 text-primary group-hover:-translate-y-0.5 transition-transform duration-300" />
        Customize
      </button>

      <DialogContent className="sm:max-w-lg gap-5 rounded-[24px] p-6">
        <DialogHeader className="gap-3">
          <div className="flex items-center gap-3.5">
            <motion.div
              initial={{ scale: 0.5, opacity: 0, rotate: -12 }}
              animate={{ scale: 1, opacity: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 380, damping: 18 }}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#3b82f6] to-[#2563eb] shadow-[0_6px_20px_rgba(59,130,246,0.45)]"
            >
              <LayoutGrid className="h-5 w-5 text-white" strokeWidth={2.5} />
            </motion.div>
            <DialogTitle className="text-lg font-semibold tracking-tight">Customize your dashboard</DialogTitle>
          </div>
          <DialogDescription className="leading-relaxed">
            Pin the KPIs you care about and drag to reorder them. Unpinned metrics stay available below.
          </DialogDescription>
        </DialogHeader>

        {kpis.length === 0 ? (
          <div className="py-6 text-center text-sm text-muted-foreground">
            No KPIs available yet — upload a dataset first.
          </div>
        ) : (
          <div className={cn("flex flex-col gap-5 max-h-[52vh] overflow-y-auto", scrollbarHideClass)}>
            <section>
              <div className="mb-2.5 flex items-center gap-2">
                <span className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground/70">
                  Pinned
                </span>
                <motion.span
                  key={draft.length}
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: "spring", stiffness: 500, damping: 22 }}
                  className="rounded-md bg-primary/15 px-1.5 py-0.5 text-[11px] font-semibold tabular-nums text-primary"
                >
                  {draft.length}
                </motion.span>
              </div>

              {draft.length === 0 ? (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="rounded-2xl border border-dashed border-border/50 px-4 py-6 text-center text-sm italic text-muted-foreground"
                >
                  Nothing pinned — the dashboard will show its default metrics.
                </motion.p>
              ) : (
                <Reorder.Group axis="y" values={draft} onReorder={setDraft} className="flex flex-col gap-2.5">
                  {draft.map((id) => {
                    const kpi = kpiById(id);
                    if (!kpi) return null;
                    return (
                      <Reorder.Item
                        key={id}
                        value={id}
                        layout
                        initial={{ opacity: 0, y: -6 }}
                        animate={{ opacity: 1, y: 0 }}
                        whileDrag={{
                          scale: 1.02,
                          boxShadow: "0 12px 32px rgba(0,0,0,0.35)",
                          cursor: "grabbing",
                        }}
                        transition={{ type: "spring", stiffness: 450, damping: 34 }}
                        className="group flex cursor-grab items-center gap-3 rounded-2xl border border-border/50 bg-surface/60 px-3.5 py-3 transition-colors hover:border-primary/30 hover:bg-surface active:cursor-grabbing"
                      >
                        <GripVertical className="h-4 w-4 shrink-0 text-muted-foreground/40 transition-colors group-hover:text-muted-foreground/80" />
                        <span className={cn("h-2 w-2 shrink-0 rounded-[3px]", accentFor(id))} />
                        <span className="flex-1 truncate text-sm font-medium text-foreground">{kpi.name}</span>
                        <span className="shrink-0 text-sm tabular-nums text-muted-foreground">
                          {formatKpiValue(kpi.value, kpi.type)}
                        </span>
                        <motion.button
                          type="button"
                          onClick={() => unpin(id)}
                          title="Unpin from dashboard"
                          whileHover={{ scale: 1.08 }}
                          whileTap={{ scale: 0.9 }}
                          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-primary/30 bg-primary/10 text-primary transition-colors hover:bg-primary/20"
                        >
                          <PinOff className="h-3.5 w-3.5" />
                        </motion.button>
                      </Reorder.Item>
                    );
                  })}
                </Reorder.Group>
              )}
            </section>

            <AnimatePresence initial={false}>
              {availableKpis.length > 0 && (
                <motion.section
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                >
                  <div className="mb-2.5 text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground/70">
                    Available
                  </div>
                  <div className="flex flex-col gap-2.5">
                    <AnimatePresence initial={false}>
                      {availableKpis.map((kpi, i) => (
                        <motion.div
                          key={kpi.id}
                          layout
                          initial={{ opacity: 0, y: -6 }}
                          animate={{ opacity: 1, y: 0, transition: { delay: Math.min(i * 0.025, 0.15) } }}
                          exit={{ opacity: 0, scale: 0.97, transition: { duration: 0.12 } }}
                          transition={{ type: "spring", stiffness: 450, damping: 34 }}
                          className="flex items-center gap-3 rounded-2xl border border-border/30 bg-background/40 px-3.5 py-3 transition-colors hover:border-border/60 hover:bg-surface/40"
                        >
                          <span className={cn("ml-7 h-2 w-2 shrink-0 rounded-[3px] opacity-70", accentFor(kpi.id))} />
                          <span className="flex-1 truncate text-sm text-foreground/80">{kpi.name}</span>
                          <span className="shrink-0 text-sm tabular-nums text-muted-foreground/70">
                            {formatKpiValue(kpi.value, kpi.type)}
                          </span>
                          <motion.button
                            type="button"
                            onClick={() => pin(kpi.id)}
                            title="Pin to dashboard"
                            whileHover={{ scale: 1.08 }}
                            whileTap={{ scale: 0.9 }}
                            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-border/60 text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary"
                          >
                            <Pin className="h-3.5 w-3.5" />
                          </motion.button>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                </motion.section>
              )}
            </AnimatePresence>
          </div>
        )}

        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.18 }}
              className="flex items-start gap-2 overflow-hidden rounded-xl border border-error/25 bg-error/10 p-2.5 text-xs text-error"
            >
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}
        </AnimatePresence>

        <DialogFooter className="-mx-6 -mb-6 items-center gap-3 rounded-b-[24px] border-t border-border/40 bg-transparent px-6 py-4">
          <Button
            type="button"
            variant="ghost"
            onClick={handleResetToDefault}
            disabled={saving}
            className="text-muted-foreground transition-transform hover:text-foreground hover:scale-[1.03] active:scale-[0.97]"
          >
            Reset to default
          </Button>
          <Button
            type="button"
            onClick={handleSave}
            disabled={saving || kpis.length === 0}
            className="rounded-full px-7 shadow-[0_6px_20px_rgba(59,130,246,0.4)] transition-transform hover:scale-[1.03] active:scale-[0.97]"
          >
            {saving ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : null}
            {saving ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

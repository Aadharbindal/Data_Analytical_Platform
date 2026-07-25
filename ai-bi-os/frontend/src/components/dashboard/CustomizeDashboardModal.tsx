"use client";

import React, { useState } from "react";
import { Reorder } from "framer-motion";
import { GripVertical, Pin, PinOff, Loader2, LayoutGrid } from "lucide-react";
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
import { useQueryClient } from "@tanstack/react-query";
import type { KpiItem } from "@/lib/types";

const DEFAULT_PINNED_COUNT = 4;

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
    } catch (e: any) {
      setError(e.message || "Could not save your dashboard layout.");
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

      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Customize your dashboard</DialogTitle>
          <DialogDescription>
            Pin the KPIs you care about and drag to reorder them. Unpinned metrics stay available below.
          </DialogDescription>
        </DialogHeader>

        {kpis.length === 0 ? (
          <div className="text-sm text-muted-foreground py-4">
            No KPIs available yet — upload a dataset first.
          </div>
        ) : (
          <div className="flex flex-col gap-4 max-h-[55vh] overflow-y-auto pr-1">
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
                Pinned ({draft.length})
              </p>
              {draft.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">
                  Nothing pinned — the dashboard will show its default metrics.
                </p>
              ) : (
                <Reorder.Group axis="y" values={draft} onReorder={setDraft} className="flex flex-col gap-2">
                  {draft.map((id) => {
                    const kpi = kpiById(id);
                    if (!kpi) return null;
                    return (
                      <Reorder.Item
                        key={id}
                        value={id}
                        className="flex items-center gap-2 rounded-lg border border-border/50 bg-surface/40 px-3 py-2 cursor-grab active:cursor-grabbing"
                      >
                        <GripVertical className="h-4 w-4 text-muted-foreground shrink-0" />
                        <span className="text-sm text-foreground flex-1 truncate">{kpi.name}</span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => unpin(id)}
                          title="Unpin"
                        >
                          <PinOff className="h-3.5 w-3.5 text-muted-foreground" />
                        </Button>
                      </Reorder.Item>
                    );
                  })}
                </Reorder.Group>
              )}
            </div>

            {availableKpis.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
                  Available
                </p>
                <div className="flex flex-col gap-2">
                  {availableKpis.map((kpi) => (
                    <div
                      key={kpi.id}
                      className="flex items-center gap-2 rounded-lg border border-border/30 px-3 py-2"
                    >
                      <span className="text-sm text-foreground/80 flex-1 truncate">{kpi.name}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => pin(kpi.id)}
                        title="Pin"
                      >
                        <Pin className="h-3.5 w-3.5 text-muted-foreground" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {error && <p className="text-sm text-red-400">{error}</p>}

        <DialogFooter>
          <Button type="button" variant="ghost" onClick={handleResetToDefault} disabled={saving}>
            Reset to default
          </Button>
          <Button type="button" onClick={handleSave} disabled={saving || kpis.length === 0}>
            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : null}
            {saving ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

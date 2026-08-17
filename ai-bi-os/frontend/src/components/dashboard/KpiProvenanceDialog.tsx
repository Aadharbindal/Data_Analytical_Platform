"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { CheckCircle2, AlertTriangle, Loader2, Sigma, Table2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { analyticsApi } from "@/lib/api";
import { formatKpiValue } from "@/lib/utils";
import type { KpiProvenance } from "@/lib/types";

interface Props {
  kpiId: string | null;
  kpiName: string;
  /** The figure currently on the card, so the drilldown can be checked against it. */
  cardValue?: number;
  kpiType?: string;
  onClose: () => void;
  /** How to fetch the drilldown. Defaults to the signed-in endpoint; the public
   *  shared dashboard passes its own, which goes through the share token and
   *  its password instead. One dialog either way — a second implementation for
   *  the public view is how the two would end up explaining the same figure
   *  differently. */
  fetcher?: (kpiId: string) => Promise<KpiProvenance>;
  /** Distinguishes the two callers' caches, so a public drilldown and a private
   *  one for the same kpi id are never served from each other's entry. */
  cacheKey?: string;
}

function cell(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(2);
  return String(v);
}

export function KpiProvenanceDialog({
  kpiId,
  kpiName,
  cardValue,
  kpiType,
  onClose,
  fetcher,
  cacheKey = "private",
}: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["kpi-provenance", cacheKey, kpiId],
    queryFn: () => (fetcher ?? analyticsApi.kpiProvenance)(kpiId as string),
    enabled: !!kpiId,
    staleTime: 5 * 60 * 1000,
  });

  // The card and the drilldown are computed by the same resolver, so these
  // should always agree. Checking anyway — and saying so on screen — is the
  // whole point: a claim the reader can verify beats one they have to trust.
  const agrees =
    data?.recomputed_value != null &&
    cardValue != null &&
    Math.abs(data.recomputed_value - cardValue) < 0.011;

  return (
    <Dialog open={!!kpiId} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-3xl gap-4 rounded-[24px] p-0">
        <DialogHeader className="gap-2 border-b border-border/40 px-6 pt-6 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#3b82f6] to-[#2563eb] shadow-[0_6px_18px_-6px_rgba(59,130,246,0.7)]">
              <Sigma className="h-5 w-5 text-white" strokeWidth={2.4} />
            </div>
            <div className="min-w-0">
              <DialogTitle className="truncate text-base font-semibold">{kpiName}</DialogTitle>
              <DialogDescription className="text-xs">
                Where this number came from
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="max-h-[70vh] overflow-y-auto px-6 pb-6">
          {isLoading && (
            <div className="flex items-center justify-center gap-2 py-14 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Tracing the calculation…
            </div>
          )}

          {isError && (
            <div className="py-14 text-center text-sm text-muted-foreground">
              Couldn&apos;t trace this metric on the current dataset.
            </div>
          )}

          {data && (
            <div className="flex flex-col gap-5 pt-5">
              {/* The calculation itself */}
              <section>
                <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground/70">
                  Calculation
                </p>
                <code className="block overflow-x-auto rounded-xl border border-border/50 bg-background/60 px-4 py-3 font-mono text-[13px] text-foreground">
                  {data.formula}
                </code>
                {data.note && (
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{data.note}</p>
                )}
              </section>

              {/* Verification + honest coverage, side by side */}
              <section className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div
                  className={`rounded-xl border px-4 py-3 ${
                    agrees ? "border-success/25 bg-success/[0.07]" : "border-border/50 bg-background/40"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {agrees ? (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-success" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 shrink-0 text-warning" />
                    )}
                    <span className="text-xs font-medium text-foreground">
                      {agrees ? "Recomputed from these rows" : "Recomputed value"}
                    </span>
                  </div>
                  <p className="mt-1.5 text-lg font-semibold tabular-metrics text-foreground">
                    {data.recomputed_value != null
                      ? formatKpiValue(data.recomputed_value, kpiType)
                      : "—"}
                  </p>
                  {agrees && (
                    <p className="mt-0.5 text-[11px] text-success/90">Matches the figure on the card</p>
                  )}
                </div>

                <div className="rounded-xl border border-border/50 bg-background/40 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Table2 className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <span className="text-xs font-medium text-foreground">Rows used</span>
                  </div>
                  <p className="mt-1.5 text-lg font-semibold tabular-metrics text-foreground">
                    {data.rows_used.toLocaleString("en-IN")}
                    <span className="text-sm font-normal text-muted-foreground">
                      {" "}
                      of {data.rows_total.toLocaleString("en-IN")}
                    </span>
                  </p>
                  {/* Stated plainly rather than hidden. A figure drawn from
                      part of the data is still useful — silently presenting it
                      as if drawn from all of it is not. */}
                  <p className="mt-0.5 text-[11px] text-muted-foreground">
                    {data.excluded_reason ?? "Every row contributed"}
                  </p>
                </div>
              </section>

              {/* The actual rows */}
              <section>
                <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground/70">
                  Contributing rows
                  {data.rows.length < data.rows_used && (
                    <span className="ml-1.5 normal-case tracking-normal text-muted-foreground/60">
                      (first {data.rows.length})
                    </span>
                  )}
                </p>
                <div className="overflow-x-auto rounded-xl border border-border/50">
                  <table className="w-full min-w-max text-left text-[12px]">
                    <thead className="bg-surface/60">
                      <tr>
                        {data.columns.map((c) => (
                          <th
                            key={c}
                            className={`whitespace-nowrap px-3 py-2 font-medium ${
                              c === data.column ? "text-primary" : "text-muted-foreground"
                            }`}
                          >
                            {c}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data.rows.map((row, i) => (
                        <motion.tr
                          key={i}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ duration: 0.18, delay: Math.min(i * 0.012, 0.25) }}
                          className="border-t border-border/30"
                        >
                          {data.columns.map((c) => (
                            <td
                              key={c}
                              className={`whitespace-nowrap px-3 py-2 ${
                                c === data.column
                                  ? "font-semibold text-foreground"
                                  : "text-muted-foreground"
                              }`}
                            >
                              {cell(row[c])}
                            </td>
                          ))}
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

"use client";

import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { RefreshCw, Check } from "lucide-react";
import { datasetsApi } from "@/lib/api";
import type { Dataset } from "@/lib/types";

/** Badge plus a refresh control for a dataset backed by a Google Sheet. */
export function SheetSourceActions({ dataset }: { dataset: Dataset }) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<null | "updated" | "current" | "error">(null);
  const [message, setMessage] = useState<string | null>(null);
  const qc = useQueryClient();

  const refresh = async (e: React.MouseEvent) => {
    // The row itself is clickable; refreshing shouldn't also open the dataset.
    e.stopPropagation();
    e.preventDefault();
    setBusy(true);
    setResult(null);
    try {
      const res = await datasetsApi.refreshFromSource(dataset.id);
      // Distinguishing these two matters: "nothing changed" is a successful
      // sync, not a failed one, and saying "updated" when no new rows arrived
      // would be a small lie the user could catch.
      setResult(res?.unchanged ? "current" : "updated");
      await qc.invalidateQueries();
    } catch (err) {
      setResult("error");
      setMessage(err instanceof Error ? err.message : "Refresh failed");
    } finally {
      setBusy(false);
      setTimeout(() => setResult(null), 3200);
    }
  };

  return (
    <span className="ml-2 flex shrink-0 items-center gap-1.5">
      <span className="rounded-full border border-[#34a853]/30 bg-[#34a853]/10 px-2 py-0.5 text-[10px] font-medium text-[#34a853]">
        Sheet
      </span>

      <button
        onClick={refresh}
        disabled={busy}
        title={busy ? "Pulling the latest rows…" : "Pull the latest rows from the sheet"}
        className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-white/[0.06] hover:text-foreground disabled:opacity-60"
      >
        <RefreshCw className={`h-3.5 w-3.5 ${busy ? "animate-spin" : ""}`} />
      </button>

      {result === "updated" && (
        <span className="flex items-center gap-1 text-[10px] font-medium text-success">
          <Check className="h-3 w-3" /> Updated
        </span>
      )}
      {result === "current" && (
        <span className="text-[10px] text-muted-foreground">Already up to date</span>
      )}
      {result === "error" && (
        <span className="max-w-[190px] truncate text-[10px] text-error" title={message ?? ""}>
          {message}
        </span>
      )}
    </span>
  );
}

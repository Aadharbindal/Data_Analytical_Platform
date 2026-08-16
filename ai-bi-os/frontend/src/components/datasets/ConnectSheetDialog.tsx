"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useQueryClient } from "@tanstack/react-query";
import { AlertCircle, Loader2, Sheet, ArrowRight, Info } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { datasetsApi } from "@/lib/api";

export function ConnectSheetDialog() {
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const qc = useQueryClient();
  const router = useRouter();

  const submit = async () => {
    if (!url.trim()) return;
    setBusy(true);
    setError(null);
    try {
      // The backend already makes a newly ingested dataset the active one, so
      // there is nothing to switch to by hand — landing on the analysis view
      // is what makes connecting feel finished. Matches what an upload does.
      await datasetsApi.connectSheet(url.trim());
      await qc.invalidateQueries();
      setOpen(false);
      setUrl("");
      router.push("/analytics");
    } catch (e) {
      // The backend's messages here are written for the user (how to share the
      // sheet, what to paste), so they're shown as-is rather than replaced
      // with a generic failure.
      setError(e instanceof Error ? e.message : "Couldn't connect that sheet.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (!o) setError(null);
      }}
    >
      <button
        onClick={() => setOpen(true)}
        className="group flex w-full items-center justify-center gap-2.5 rounded-[20px] border border-border/60 bg-surface/40 px-5 py-3.5 text-sm font-medium text-foreground transition-colors hover:border-primary/50 hover:bg-white/[0.03]"
      >
        <Sheet className="h-4 w-4 text-[#34a853]" strokeWidth={2.3} />
        Connect a Google Sheet
        <span className="text-xs text-muted-foreground">— stays up to date</span>
      </button>

      <DialogContent className="sm:max-w-lg gap-5 rounded-[24px] p-6">
        <DialogHeader className="gap-3">
          <div className="flex items-center gap-3.5">
            <motion.div
              initial={{ scale: 0.5, opacity: 0, rotate: -12 }}
              animate={{ scale: 1, opacity: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 380, damping: 18 }}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#34a853] to-[#188038] shadow-[0_6px_20px_rgba(52,168,83,0.4)]"
            >
              <Sheet className="h-5 w-5 text-white" strokeWidth={2.5} />
            </motion.div>
            <DialogTitle className="text-lg font-semibold tracking-tight">
              Connect a Google Sheet
            </DialogTitle>
          </div>
          <DialogDescription className="leading-relaxed">
            Work from the sheet you already keep updated. Refresh any time to pull the
            latest rows — no re-uploading.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          <div>
            <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground/70">
              Sheet link
            </label>
            <input
              autoFocus
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !busy && submit()}
              placeholder="https://docs.google.com/spreadsheets/d/…"
              className="h-11 w-full rounded-xl border border-border/60 bg-background/60 px-4 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>

          <div className="rounded-xl border border-border/50 bg-background/40 p-4">
            <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-foreground">
              <Info className="h-3.5 w-3.5 text-primary" /> First, make the sheet readable
            </p>
            <ol className="ml-4 list-decimal space-y-1 text-xs leading-relaxed text-muted-foreground">
              <li>Open your sheet and click <strong className="text-foreground/80">Share</strong></li>
              <li>
                Under <strong className="text-foreground/80">General access</strong>, choose{" "}
                <strong className="text-foreground/80">Anyone with the link</strong>
              </li>
              <li>Leave the role as <strong className="text-foreground/80">Viewer</strong>, then copy the link</li>
            </ol>
            {/* Said plainly rather than left for the user to discover: this
                setting is what makes the import work, and it is also a real
                change to who can read their data. */}
            <p className="mt-3 border-t border-border/40 pt-2.5 text-[11px] leading-relaxed text-muted-foreground/80">
              Note that &ldquo;Anyone with the link&rdquo; means exactly that — anyone holding the
              URL can read the sheet. Use a sheet you&apos;re comfortable sharing that way.
            </p>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.18 }}
                className="flex items-start gap-2 overflow-hidden rounded-xl border border-error/25 bg-error/10 p-3 text-xs leading-relaxed text-error"
              >
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>{error}</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <DialogFooter className="items-center gap-3">
          <Button variant="ghost" onClick={() => setOpen(false)} disabled={busy}>
            Cancel
          </Button>
          <Button
            onClick={submit}
            disabled={busy || !url.trim()}
            className="rounded-full px-6 shadow-[0_6px_20px_rgba(59,130,246,0.35)]"
          >
            {busy ? (
              <>
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> Reading sheet…
              </>
            ) : (
              <>
                Connect <ArrowRight className="ml-1 h-4 w-4" />
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

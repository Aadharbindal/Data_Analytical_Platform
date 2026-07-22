"use client";

import React, { useState } from "react";
import { Share2, Copy, Check, Loader2, Trash2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { shareApi } from "@/lib/api";

export function ShareDialog() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [revoking, setRevoking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [viewCount, setViewCount] = useState(0);
  const [copied, setCopied] = useState(false);

  const shareUrl = token && typeof window !== "undefined" ? `${window.location.origin}/shared/${token}` : "";

  const handleOpenChange = async (next: boolean) => {
    setOpen(next);
    if (next && !token) {
      setLoading(true);
      setError(null);
      try {
        const res = await shareApi.create();
        setToken(res.token);
        setViewCount(res.view_count ?? 0);
      } catch (e: any) {
        setError(e.message || "Could not create a share link.");
      } finally {
        setLoading(false);
      }
    }
  };

  const handleCopy = async () => {
    if (!shareUrl) return;
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRevoke = async () => {
    if (!token) return;
    setRevoking(true);
    try {
      await shareApi.revoke(token);
      setToken(null);
      setViewCount(0);
      setOpen(false);
    } catch (e: any) {
      setError(e.message || "Could not revoke the link.");
    } finally {
      setRevoking(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <button
        onClick={() => handleOpenChange(true)}
        className="group flex items-center gap-2.5 px-6 py-3 rounded-full bg-background/60 backdrop-blur-xl border border-border/50 shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.2)] hover:bg-background/80 hover:scale-105 transition-all duration-300 text-sm font-medium text-foreground"
      >
        <Share2 className="h-4 w-4 text-primary group-hover:-translate-y-0.5 transition-transform duration-300" />
        Share
      </button>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Share this dashboard</DialogTitle>
          <DialogDescription>
            Anyone with this link can view a read-only snapshot of your KPIs and verified insights — no login required. They can&apos;t see raw data, other datasets, or make any changes.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-6">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="text-sm text-red-400">{error}</div>
        ) : (
          <>
            <div className="flex items-center gap-2">
              <Input readOnly value={shareUrl} className="font-mono text-xs" onFocus={(e) => e.currentTarget.select()} />
              <Button type="button" variant="outline" size="icon-sm" onClick={handleCopy}>
                {copied ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
            {viewCount > 0 && (
              <p className="text-xs text-muted-foreground">Viewed {viewCount} time{viewCount === 1 ? "" : "s"} so far.</p>
            )}
          </>
        )}

        <DialogFooter>
          <Button type="button" variant="ghost" onClick={handleRevoke} disabled={!token || revoking} className="text-red-400 hover:text-red-400">
            <Trash2 className="h-3.5 w-3.5 mr-1.5" />
            {revoking ? "Revoking..." : "Revoke link"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

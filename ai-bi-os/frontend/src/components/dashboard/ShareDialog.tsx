"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Share2, Copy, Check, Loader2, Trash2, AlertCircle, Link2, Lock, Clock, ShieldCheck, Save } from "lucide-react";
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
import { cn } from "@/lib/utils";

const EXPIRY_OPTIONS = [
  { value: 24, label: "24 hours" },
  { value: 24 * 7, label: "7 days" },
  { value: 24 * 30, label: "30 days" },
];

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative h-5 w-9 shrink-0 rounded-full transition-colors focus:outline-none ${checked ? "bg-primary" : "bg-muted-foreground/30"}`}
    >
      <span className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${checked ? "translate-x-4" : "translate-x-0"}`} />
    </button>
  );
}

export function ShareDialog() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [revoking, setRevoking] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [viewCount, setViewCount] = useState(0);
  const [copied, setCopied] = useState(false);

  // Server-confirmed protection state (what the live link actually enforces).
  const [hasPassword, setHasPassword] = useState(false);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);

  // Local draft state for the protection form — separate from the confirmed
  // state above so the "Update protection" button only appears once the
  // draft actually differs from what's live, instead of on every keystroke.
  const [passwordEnabled, setPasswordEnabled] = useState(false);
  const [password, setPassword] = useState("");
  const [expiryEnabled, setExpiryEnabled] = useState(false);
  const [expiryHours, setExpiryHours] = useState(24);

  const shareUrl = token && typeof window !== "undefined" ? `${window.location.origin}/shared/${token}` : "";

  const isDirty =
    passwordEnabled !== hasPassword ||
    (passwordEnabled && password.length > 0) ||
    expiryEnabled !== !!expiresAt ||
    (expiryEnabled && !expiresAt);

  const handleOpenChange = async (next: boolean) => {
    setOpen(next);
    if (next && !token) {
      setLoading(true);
      setError(null);
      try {
        const res = await shareApi.create();
        setToken(res.token);
        setViewCount(res.view_count ?? 0);
        setHasPassword(res.has_password);
        setExpiresAt(res.expires_at);
        setPasswordEnabled(res.has_password);
        setExpiryEnabled(!!res.expires_at);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not create a share link.");
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

  const handleSaveSettings = async () => {
    setSavingSettings(true);
    setSettingsError(null);
    try {
      const res = await shareApi.create({
        password: passwordEnabled ? password || null : null,
        expiresInHours: expiryEnabled ? expiryHours : null,
      });
      setHasPassword(res.has_password);
      setExpiresAt(res.expires_at);
      setPassword("");
    } catch (e) {
      setSettingsError(e instanceof Error ? e.message : "Could not update protection settings.");
    } finally {
      setSavingSettings(false);
    }
  };

  const handleRevoke = async () => {
    if (!token) return;
    setRevoking(true);
    try {
      await shareApi.revoke(token);
      setToken(null);
      setViewCount(0);
      setHasPassword(false);
      setExpiresAt(null);
      setPasswordEnabled(false);
      setExpiryEnabled(false);
      setPassword("");
      setOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not revoke the link.");
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

      <DialogContent className="gap-5 rounded-[24px] p-6">
        <DialogHeader className="gap-3">
          <div className="flex items-center gap-3.5">
            <motion.div
              initial={{ scale: 0.5, opacity: 0, rotate: -12 }}
              animate={{ scale: 1, opacity: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 380, damping: 18 }}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#3b82f6] to-[#2563eb] shadow-[0_6px_20px_rgba(59,130,246,0.45)]"
            >
              <Share2 className="h-5 w-5 text-white" strokeWidth={2.5} />
            </motion.div>
            <DialogTitle className="text-lg font-semibold tracking-tight">Share this dashboard</DialogTitle>
          </div>
          <DialogDescription className="leading-relaxed">
            Anyone with this link can view a read-only snapshot of your KPIs and verified insights — no login required.
            They can&apos;t see raw data, other datasets, or make any changes.
          </DialogDescription>
        </DialogHeader>

        <>
          {loading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center justify-center py-8"
            >
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </motion.div>
          ) : error ? (
            <motion.div
              key="error"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              transition={{ duration: 0.18 }}
              className="flex items-start gap-2 overflow-hidden rounded-xl border border-error/25 bg-error/10 p-3 text-sm text-error"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </motion.div>
          ) : (
            <motion.div
              key="link"
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col gap-4"
            >
              <div>
                <div className="flex items-center gap-2 rounded-2xl border border-border/50 bg-surface/60 py-1.5 pl-4 pr-1.5">
                  <Link2 className="h-3.5 w-3.5 shrink-0 text-muted-foreground/60" />
                  <Input
                    readOnly
                    value={shareUrl}
                    className="h-9 flex-1 border-0 bg-transparent px-0 font-mono text-xs shadow-none focus-visible:ring-0"
                    onFocus={(e) => e.currentTarget.select()}
                  />
                  <motion.button
                    type="button"
                    onClick={handleCopy}
                    whileHover={{ scale: 1.06 }}
                    whileTap={{ scale: 0.92 }}
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-border/60 text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary"
                  >
                    {copied ? (
                      <motion.span
                        key="check"
                        initial={{ scale: 0.5, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ duration: 0.15 }}
                      >
                        <Check className="h-4 w-4 text-emerald-400" />
                      </motion.span>
                    ) : (
                      <motion.span
                        key="copy"
                        initial={{ scale: 0.5, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ duration: 0.15 }}
                      >
                        <Copy className="h-4 w-4" />
                      </motion.span>
                    )}
                  </motion.button>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  {viewCount > 0 && (
                    <p className="pl-1 text-xs text-muted-foreground">
                      Viewed {viewCount} time{viewCount === 1 ? "" : "s"} so far.
                    </p>
                  )}
                  {hasPassword && (
                    <span className="inline-flex items-center gap-1 rounded-full border border-primary/25 bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary">
                      <Lock className="h-2.5 w-2.5" /> Password protected
                    </span>
                  )}
                  {expiresAt && (
                    <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/25 bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-500">
                      <Clock className="h-2.5 w-2.5" /> Expires {new Date(expiresAt).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex flex-col gap-3 rounded-2xl border border-border/50 bg-surface/40 p-4">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  <ShieldCheck className="h-3.5 w-3.5" /> Access control
                </div>

                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground">Require a password</p>
                    <p className="text-xs text-muted-foreground">Visitors must enter it before they see anything.</p>
                  </div>
                  <Toggle checked={passwordEnabled} onChange={setPasswordEnabled} />
                </div>
                {passwordEnabled && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    transition={{ duration: 0.18 }}
                    className="overflow-hidden"
                  >
                    <Input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={hasPassword ? "Enter a new password to change it" : "Set a password"}
                      className="h-9 rounded-xl bg-surface/60 text-sm"
                    />
                  </motion.div>
                )}

                <div className="h-px bg-border/40" />

                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground">Set an expiry</p>
                    <p className="text-xs text-muted-foreground">Link stops working automatically after this.</p>
                  </div>
                  <Toggle checked={expiryEnabled} onChange={setExpiryEnabled} />
                </div>
                {expiryEnabled && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    transition={{ duration: 0.18 }}
                    className="overflow-hidden"
                  >
                    <div className="flex gap-2">
                      {EXPIRY_OPTIONS.map((opt) => (
                        <button
                          key={opt.value}
                          type="button"
                          onClick={() => setExpiryHours(opt.value)}
                          className={cn(
                            "flex-1 rounded-xl border py-1.5 text-xs font-medium transition-colors",
                            expiryHours === opt.value
                              ? "border-primary/50 bg-primary/10 text-primary"
                              : "border-border/60 text-muted-foreground hover:text-foreground"
                          )}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </motion.div>
                )}

                {settingsError && (
                  <p className="flex items-center gap-1.5 text-xs text-error">
                    <AlertCircle className="h-3 w-3 shrink-0" /> {settingsError}
                  </p>
                )}

                {isDirty && (
                  <motion.div
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.15 }}
                  >
                    <Button
                      type="button"
                      onClick={handleSaveSettings}
                      disabled={savingSettings}
                      className="w-full gap-2 rounded-xl"
                    >
                      {savingSettings ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                      {savingSettings ? "Updating..." : "Update protection"}
                    </Button>
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </>

        <DialogFooter className="-mx-6 -mb-6 items-center gap-3 rounded-b-[24px] border-t border-border/40 bg-transparent px-6 py-4 sm:justify-between">
          <span className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary/60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
            </span>
            Link is live
          </span>
          <Button
            type="button"
            variant="ghost"
            onClick={handleRevoke}
            disabled={!token || revoking}
            className="rounded-full border border-error/25 text-error transition-transform hover:scale-[1.03] hover:bg-error/10 hover:text-error active:scale-[0.97]"
          >
            {revoking ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <Trash2 className="mr-1.5 h-3.5 w-3.5" />}
            {revoking ? "Revoking..." : "Revoke link"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

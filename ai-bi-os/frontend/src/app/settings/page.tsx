"use client";

import React, { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTheme } from "next-themes";
import { authApi, type SessionInfo } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { motion } from "framer-motion";
import {
  User,
  KeyRound,
  AlertTriangle,
  Check,
  Loader2,
  Sun,
  Moon,
  Monitor,
  Smartphone,
  ShieldCheck,
  Download,
  LogOut,
} from "lucide-react";

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function formatMemberSince(iso?: string) {
  if (!iso) return null;
  const d = new Date(iso);
  if (isNaN(d.getTime())) return null;
  return d.toLocaleDateString("en-IN", { month: "long", year: "numeric" });
}

export default function SettingsPage() {
  const qc = useQueryClient();

  const { data: user, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: () => authApi.me(),
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="flex flex-col gap-6 max-w-2xl"
    >
      {isLoading || !user ? (
        <div className="flex items-center justify-center py-24 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      ) : (
        <>
          <ProfileCard user={user} onSaved={() => qc.invalidateQueries({ queryKey: ["me"] })} />
          <AppearanceCard />
          <SecurityCard />
          <SessionsCard />
          <PrivacyDataCard />
          <DangerZoneCard email={user.email} />
        </>
      )}
    </motion.div>
  );
}

function ProfileCard({
  user,
  onSaved,
}: {
  user: { id: string; email: string; full_name: string; created_at?: string };
  onSaved: () => void;
}) {
  const [fullName, setFullName] = useState(user.full_name);
  const [saved, setSaved] = useState(false);

  useEffect(() => setFullName(user.full_name), [user.full_name]);

  const mutation = useMutation({
    mutationFn: (name: string) => authApi.updateProfile(name),
    onSuccess: () => {
      onSaved();
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  const memberSince = formatMemberSince(user.created_at);
  const dirty = fullName.trim() !== user.full_name && fullName.trim().length > 0;

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold">
          <User className="h-4 w-4 text-primary" /> Profile
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary text-lg font-semibold border border-primary/20">
            {initials(user.full_name)}
          </div>
          <div className="min-w-0">
            <div className="text-sm font-medium text-foreground truncate">{user.email}</div>
            {memberSince && (
              <div className="text-xs text-muted-foreground mt-0.5">Member since {memberSince}</div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Full name</label>
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Your name" />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Email</label>
            <Input value={user.email} disabled className="opacity-60" />
          </div>
        </div>

        {mutation.isError && (
          <p className="text-xs text-destructive">{(mutation.error as Error).message}</p>
        )}

        <div className="flex items-center gap-3">
          <Button
            size="sm"
            disabled={!dirty || mutation.isPending}
            onClick={() => mutation.mutate(fullName.trim())}
          >
            {mutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Save changes"}
          </Button>
          {saved && (
            <span className="flex items-center gap-1 text-xs text-emerald-500">
              <Check className="h-3.5 w-3.5" /> Saved
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function SecurityCard() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [success, setSuccess] = useState(false);

  const mismatch = confirmPassword.length > 0 && newPassword !== confirmPassword;
  const canSubmit = currentPassword.length > 0 && newPassword.length >= 8 && newPassword === confirmPassword;

  const mutation = useMutation({
    mutationFn: () => authApi.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setSuccess(true);
      setTimeout(() => setSuccess(false), 2500);
    },
  });

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold">
          <KeyRound className="h-4 w-4 text-primary" /> Security
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Current password</label>
          <Input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="••••••••"
          />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1.5 block">New password</label>
            <Input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="At least 8 characters"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Confirm new password</label>
            <Input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Repeat new password"
              aria-invalid={mismatch}
            />
          </div>
        </div>

        {mismatch && <p className="text-xs text-destructive">Passwords don't match.</p>}
        {mutation.isError && (
          <p className="text-xs text-destructive">{(mutation.error as Error).message}</p>
        )}

        <div className="flex items-center gap-3">
          <Button size="sm" disabled={!canSubmit || mutation.isPending} onClick={() => mutation.mutate()}>
            {mutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Update password"}
          </Button>
          {success && (
            <span className="flex items-center gap-1 text-xs text-emerald-500">
              <Check className="h-3.5 w-3.5" /> Password updated
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function AppearanceCard() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const options: { id: string; label: string; icon: typeof Sun }[] = [
    { id: "light", label: "Light", icon: Sun },
    { id: "dark", label: "Dark", icon: Moon },
    { id: "system", label: "System", icon: Monitor },
  ];

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold">
          <Sun className="h-4 w-4 text-primary" /> Appearance
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3">
          {options.map((opt) => {
            const Icon = opt.icon;
            const active = mounted && theme === opt.id;
            return (
              <button
                key={opt.id}
                onClick={() => setTheme(opt.id)}
                className={`flex flex-col items-center gap-2 rounded-xl border py-4 text-sm font-medium transition-colors ${
                  active
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border/50 text-muted-foreground hover:bg-white/5 hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                {opt.label}
              </button>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function timeAgo(iso: string) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 2) return "Active now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" });
}

function SessionsCard() {
  const qc = useQueryClient();
  const [revokingId, setRevokingId] = useState<string | null>(null);

  const { data: sessions, isLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => authApi.listSessions(),
  });

  const revokeMutation = useMutation({
    mutationFn: (id: string) => authApi.revokeSession(id),
    onMutate: (id) => setRevokingId(id),
    onSettled: () => setRevokingId(null),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sessions"] }),
  });

  const revokeOthersMutation = useMutation({
    mutationFn: () => authApi.revokeOtherSessions(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sessions"] }),
  });

  const others = (sessions ?? []).filter((s: SessionInfo) => !s.is_current);

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold">
          <ShieldCheck className="h-4 w-4 text-primary" /> Active Sessions
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-1">
        {isLoading ? (
          <div className="flex justify-center py-6 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
          </div>
        ) : !sessions || sessions.length === 0 ? (
          <p className="text-xs text-muted-foreground py-2">No active sessions found.</p>
        ) : (
          <div className="flex flex-col divide-y divide-border/30">
            {sessions.map((s: SessionInfo) => (
              <div key={s.id} className="flex items-center justify-between gap-3 py-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/5 border border-border/40">
                    <Smartphone className="h-3.5 w-3.5 text-muted-foreground" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-foreground truncate">{s.device}</span>
                      {s.is_current && <Badge variant="secondary" className="text-[10px]">This device</Badge>}
                    </div>
                    <div className="text-xs text-muted-foreground truncate">
                      {s.ip_address} · {timeAgo(s.last_active_at)}
                    </div>
                  </div>
                </div>
                {!s.is_current && (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={revokingId === s.id}
                    onClick={() => revokeMutation.mutate(s.id)}
                  >
                    {revokingId === s.id ? <Loader2 className="h-3 w-3 animate-spin" /> : "Sign out"}
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}

        {others.length > 0 && (
          <div className="pt-3">
            <Button
              variant="destructive"
              size="sm"
              className="gap-1.5"
              disabled={revokeOthersMutation.isPending}
              onClick={() => revokeOthersMutation.mutate()}
            >
              <LogOut className="h-3.5 w-3.5" />
              {revokeOthersMutation.isPending ? "Signing out..." : `Sign out ${others.length} other device${others.length > 1 ? "s" : ""}`}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PrivacyDataCard() {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setDownloading(true);
    setError(null);
    try {
      const data = await authApi.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `datamind-data-export-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold">
          <Download className="h-4 w-4 text-primary" /> Privacy &amp; Data
        </CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <p className="text-sm font-medium text-foreground">Export your data</p>
          <p className="text-xs text-muted-foreground mt-0.5 max-w-md">
            Download a JSON copy of your insights, recommendations, rules and knowledge base entries.
          </p>
          {error && <p className="text-xs text-destructive mt-1">{error}</p>}
        </div>
        <Button size="sm" variant="outline" disabled={downloading} onClick={handleExport}>
          {downloading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Download"}
        </Button>
      </CardContent>
    </Card>
  );
}

function DangerZoneCard({ email }: { email: string }) {
  const [open, setOpen] = useState(false);
  const [confirmText, setConfirmText] = useState("");

  const mutation = useMutation({
    mutationFn: () => authApi.deleteAccount(),
    onSuccess: () => {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    },
  });

  return (
    <Card className="glass-card ring-1 ring-destructive/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-destructive">
          <AlertTriangle className="h-4 w-4" /> Danger Zone
        </CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <p className="text-sm font-medium text-foreground">Delete account</p>
          <p className="text-xs text-muted-foreground mt-0.5 max-w-md">
            Permanently deletes your profile, saved insights, recommendations, rules and knowledge base entries.
            Shared datasets are not affected. This can't be undone.
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <Button variant="destructive" size="sm" onClick={() => setOpen(true)}>
            Delete account
          </Button>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete your account?</DialogTitle>
              <DialogDescription>
                Type <span className="font-mono font-medium text-foreground">{email}</span> to confirm. This
                immediately and permanently deletes your account.
              </DialogDescription>
            </DialogHeader>
            <Input
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder={email}
              autoFocus
            />
            {mutation.isError && (
              <p className="text-xs text-destructive">{(mutation.error as Error).message}</p>
            )}
            <DialogFooter>
              <DialogClose render={<Button variant="outline" size="sm" />}>Cancel</DialogClose>
              <Button
                variant="destructive"
                size="sm"
                disabled={confirmText !== email || mutation.isPending}
                onClick={() => mutation.mutate()}
              >
                {mutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Delete permanently"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}

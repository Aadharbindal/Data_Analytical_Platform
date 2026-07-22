"use client";

import React, { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
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
import { User, KeyRound, AlertTriangle, Check, Loader2 } from "lucide-react";

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
          <SecurityCard />
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

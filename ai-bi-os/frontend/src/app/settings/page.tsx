"use client";

import React, { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTheme } from "next-themes";
import { authApi, avatarUrl, type SessionInfo } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ACCENT_STORAGE_KEY } from "@/components/ThemeProvider";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
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
  Fingerprint,
} from "lucide-react";

const SECTIONS = [
  { id: "profile", label: "Profile", icon: User, keywords: "profile name email avatar identity" },
  { id: "appearance", label: "Appearance", icon: Sun, keywords: "appearance theme dark light accent color" },
  { id: "security", label: "Security", icon: KeyRound, keywords: "security password two factor 2fa authentication totp authenticator" },
  { id: "sessions", label: "Sessions", icon: Smartphone, keywords: "sessions devices sign out logout" },
  { id: "privacy", label: "Privacy & Data", icon: Download, keywords: "privacy data export download" },
  { id: "danger", label: "Danger Zone", icon: AlertTriangle, keywords: "danger delete account remove" },
] as const;

type SectionId = (typeof SECTIONS)[number]["id"];

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

function SectionHeader({
  icon: Icon,
  title,
  subtitle,
  tone = "primary",
}: {
  icon: typeof User;
  title: string;
  subtitle: string;
  tone?: "primary" | "destructive";
}) {
  return (
    <div className="flex items-center gap-3.5">
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
          tone === "destructive" ? "bg-destructive/10 text-destructive" : "bg-primary/10 text-primary"
        }`}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <h2 className={`text-[18px] font-bold leading-tight ${tone === "destructive" ? "text-destructive" : "text-foreground"}`}>
          {title}
        </h2>
        <p className="text-[13px] text-muted-foreground mt-0.5">{subtitle}</p>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const qc = useQueryClient();
  const { refreshUser } = useAuth();
  const [activeSection, setActiveSection] = useState<SectionId>("profile");
  const sectionRefs = useRef<Partial<Record<SectionId, HTMLDivElement | null>>>({});

  const { data: user, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: () => authApi.me(),
  });

  const visibleSections = SECTIONS;

  // AppLayoutWrapper scrolls its own #main-layout container (overflow-y-auto),
  // not the window — window.scrollY/scrollTo are no-ops here since the
  // window itself never scrolls on this layout.
  const getScrollContainer = (): HTMLElement | (Window & typeof globalThis) =>
    (document.getElementById("main-layout") as HTMLElement | null) ?? window;

  useEffect(() => {
    const container = getScrollContainer();
    const onScroll = () => {
      const containerTop = container === window ? 0 : (container as HTMLElement).getBoundingClientRect().top;
      let current: SectionId | null = null;
      for (const s of visibleSections) {
        const el = sectionRefs.current[s.id];
        if (el && el.getBoundingClientRect().top - containerTop <= 160) current = s.id;
      }
      if (current && current !== activeSection) setActiveSection(current);
    };
    container.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => container.removeEventListener("scroll", onScroll);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visibleSections.map((s) => s.id).join(",")]);

  const scrollTo = (id: SectionId) => {
    const el = sectionRefs.current[id];
    const container = getScrollContainer();
    if (el) {
      if (container === window) {
        const top = el.getBoundingClientRect().top + window.scrollY - 88;
        window.scrollTo({ top, behavior: "smooth" });
      } else {
        const c = container as HTMLElement;
        const top = el.getBoundingClientRect().top - c.getBoundingClientRect().top + c.scrollTop - 24;
        c.scrollTo({ top, behavior: "smooth" });
      }
    }
    setActiveSection(id);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="flex flex-col gap-6"
    >
      {isLoading || !user ? (
        <div className="flex items-center justify-center py-24 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-[210px_minmax(0,1fr)] gap-8 items-start">
          <nav className="flex md:flex-col gap-1 overflow-x-auto md:overflow-visible md:sticky md:top-6 pb-1 md:pb-0">
            {visibleSections.map((s) => {
              const Icon = s.icon;
              const active = activeSection === s.id;
              return (
                <button
                  key={s.id}
                  onClick={() => scrollTo(s.id)}
                  className={`flex items-center gap-2.5 shrink-0 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left whitespace-nowrap ${
                    active
                      ? s.id === "danger"
                        ? "bg-destructive/10 text-destructive"
                        : "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                  }`}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {s.label}
                </button>
              );
            })}
          </nav>

          <div className="flex flex-col gap-6 min-w-0">
            {visibleSections.map((s) => (
              <div
                key={s.id}
                ref={(el) => {
                  sectionRefs.current[s.id] = el;
                }}
                className="scroll-mt-24 flex flex-col gap-6"
              >
                {s.id === "profile" && (
                  <ProfileCard
                    user={user}
                    onSaved={() => {
                      qc.invalidateQueries({ queryKey: ["me"] });
                      refreshUser();
                    }}
                  />
                )}
                {s.id === "appearance" && <AppearanceCard />}
                {s.id === "security" && (
                  <>
                    <SecurityCard />
                    <TwoFactorCard user={user} onChanged={() => qc.invalidateQueries({ queryKey: ["me"] })} />
                  </>
                )}
                {s.id === "sessions" && <SessionsCard />}
                {s.id === "privacy" && <PrivacyDataCard />}
                {s.id === "danger" && <DangerZoneCard email={user.email} />}
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}

function ProfileCard({
  user,
  onSaved,
}: {
  user: { id: string; email: string; full_name: string; created_at?: string; has_avatar?: boolean };
  onSaved: () => void;
}) {
  const [fullName, setFullName] = useState(user.full_name);
  const [saved, setSaved] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const [cacheBust, setCacheBust] = useState(() => Date.now());
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => setFullName(user.full_name), [user.full_name]);

  const mutation = useMutation({
    mutationFn: (name: string) => authApi.updateProfile(name),
    onSuccess: () => {
      onSaved();
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  const uploadAvatarMutation = useMutation({
    mutationFn: (file: File) => authApi.uploadAvatar(file),
    onSuccess: () => {
      onSaved();
      setCacheBust(Date.now());
      setAvatarError(null);
    },
    onError: (e) => setAvatarError((e as Error).message),
  });

  const removeAvatarMutation = useMutation({
    mutationFn: () => authApi.removeAvatar(),
    onSuccess: () => {
      onSaved();
      setAvatarError(null);
    },
    onError: (e) => setAvatarError((e as Error).message),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (!["image/jpeg", "image/png"].includes(file.type)) {
      setAvatarError("Only JPG or PNG images are allowed");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setAvatarError("Image must be under 2MB");
      return;
    }
    uploadAvatarMutation.mutate(file);
  };

  const avatarBusy = uploadAvatarMutation.isPending || removeAvatarMutation.isPending;
  const memberSince = formatMemberSince(user.created_at);
  const dirty = fullName.trim() !== user.full_name && fullName.trim().length > 0;

  return (
    <Card className="glass-card">
      <CardContent className="flex flex-col gap-5">
        <div className="flex items-center gap-4">
          <div className="relative h-16 w-16 shrink-0">
            {user.has_avatar ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={avatarUrl(user.id, cacheBust)}
                alt={user.full_name}
                className="h-16 w-16 rounded-full object-cover border border-primary/20"
              />
            ) : (
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/15 text-primary text-xl font-semibold border border-primary/20">
                {initials(user.full_name)}
              </div>
            )}
            {avatarBusy && (
              <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/50">
                <Loader2 className="h-5 w-5 animate-spin text-white" />
              </div>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-medium text-foreground truncate">{user.email}</div>
            {memberSince && (
              <div className="text-xs text-muted-foreground mt-0.5">Member since {memberSince}</div>
            )}
            <div className="flex items-center gap-3 mt-2">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png"
                className="hidden"
                onChange={handleFileChange}
              />
              <button
                type="button"
                disabled={avatarBusy}
                onClick={() => fileInputRef.current?.click()}
                className="text-xs font-medium text-primary hover:underline disabled:opacity-50"
              >
                {user.has_avatar ? "Change photo" : "Upload photo"}
              </button>
              {user.has_avatar && (
                <button
                  type="button"
                  disabled={avatarBusy}
                  onClick={() => removeAvatarMutation.mutate()}
                  className="text-xs font-medium text-muted-foreground hover:text-destructive disabled:opacity-50"
                >
                  Remove
                </button>
              )}
            </div>
            {avatarError ? (
              <p className="text-xs text-destructive mt-1">{avatarError}</p>
            ) : (
              <p className="text-xs text-muted-foreground/70 mt-1">JPG or PNG, max 2MB.</p>
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

const ACCENT_SWATCHES = ["#3b82f6", "#8b5cf6", "#ec4899", "#10b981", "#f59e0b", "#06b6d4"];

function AppearanceCard() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [accent, setAccent] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
    setAccent(localStorage.getItem(ACCENT_STORAGE_KEY));
  }, []);

  const applyAccent = (hex: string) => {
    setAccent(hex);
    localStorage.setItem(ACCENT_STORAGE_KEY, hex);
    document.documentElement.style.setProperty("--primary", hex);
    document.documentElement.style.setProperty("--ring", hex);
  };

  const resetAccent = () => {
    setAccent(null);
    localStorage.removeItem(ACCENT_STORAGE_KEY);
    document.documentElement.style.removeProperty("--primary");
    document.documentElement.style.removeProperty("--ring");
  };

  const options: { id: string; label: string; icon: typeof Sun }[] = [
    { id: "light", label: "Light", icon: Sun },
    { id: "dark", label: "Dark", icon: Moon },
    { id: "system", label: "System", icon: Monitor },
  ];

  return (
    <Card className="glass-card">
      <CardHeader>
        <SectionHeader icon={Sun} title="Appearance" subtitle="Personalize how the app looks — changes apply instantly." />
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        <div>
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2.5">Theme</div>
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
        </div>

        <div>
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2.5">Accent color</div>
          <div className="flex items-center gap-3 flex-wrap">
            {ACCENT_SWATCHES.map((hex) => (
              <button
                key={hex}
                onClick={() => applyAccent(hex)}
                aria-label={`Accent ${hex}`}
                style={{ background: hex }}
                className={`h-8 w-8 rounded-full transition-transform border-2 ${
                  mounted && accent === hex
                    ? "border-foreground scale-110"
                    : "border-transparent hover:scale-105"
                }`}
              />
            ))}
            {mounted && accent && (
              <button
                onClick={resetAccent}
                className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2"
              >
                Reset to default
              </button>
            )}
          </div>
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
        <SectionHeader icon={KeyRound} title="Password" subtitle="Change your account password." />
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

        {mismatch && <p className="text-xs text-destructive">Passwords don&apos;t match.</p>}
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

function TwoFactorCard({
  user,
  onChanged,
}: {
  user: { totp_enabled?: boolean };
  onChanged: () => void;
}) {
  const [step, setStep] = useState<"idle" | "setup" | "recovery">("idle");
  const [qr, setQr] = useState<string | null>(null);
  const [secret, setSecret] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null);
  const [disableOpen, setDisableOpen] = useState(false);
  const [disablePassword, setDisablePassword] = useState("");

  const setupMutation = useMutation({
    mutationFn: () => authApi.setup2FA(),
    onSuccess: (data) => {
      setQr(data.qr_code);
      setSecret(data.secret);
      setStep("setup");
    },
  });

  const enableMutation = useMutation({
    mutationFn: () => authApi.enable2FA(code),
    onSuccess: (data) => {
      setRecoveryCodes(data.recovery_codes);
      setStep("recovery");
      setCode("");
    },
  });

  const disableMutation = useMutation({
    mutationFn: () => authApi.disable2FA(disablePassword),
    onSuccess: () => {
      setDisableOpen(false);
      setDisablePassword("");
      onChanged();
    },
  });

  const finishSetup = () => {
    setStep("idle");
    setQr(null);
    setSecret(null);
    setRecoveryCodes(null);
    onChanged();
  };

  return (
    <Card className="glass-card">
      <CardHeader>
        <SectionHeader
          icon={Fingerprint}
          title="Two-Factor Authentication"
          subtitle="Require a 6-digit code from an authenticator app at sign-in."
        />
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {user.totp_enabled ? (
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-2 text-sm text-emerald-500 font-medium">
              <ShieldCheck className="h-4 w-4" /> Two-factor authentication is on
            </div>
            <Button variant="outline" size="sm" onClick={() => setDisableOpen(true)}>
              Disable
            </Button>
          </div>
        ) : step === "idle" ? (
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <p className="text-xs text-muted-foreground max-w-md">
              Use an app like Google Authenticator or Authy to generate login codes.
            </p>
            <Button size="sm" disabled={setupMutation.isPending} onClick={() => setupMutation.mutate()}>
              {setupMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Enable 2FA"}
            </Button>
          </div>
        ) : step === "setup" ? (
          <div className="flex flex-col sm:flex-row gap-5 items-start">
            {qr && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={qr} alt="2FA QR code" className="h-40 w-40 rounded-lg border border-border bg-white p-2 shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-xs text-muted-foreground mb-2">
                Scan with your authenticator app, or enter this key manually:
              </p>
              <code className="block text-xs font-mono bg-surface/50 border border-border rounded-lg px-3 py-2 break-all">
                {secret}
              </code>
              <label className="text-xs font-medium text-muted-foreground mt-4 mb-1.5 block">
                Enter the 6-digit code to confirm
              </label>
              <Input
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="000000"
                className="max-w-[160px] font-mono tracking-widest"
              />
              {enableMutation.isError && (
                <p className="text-xs text-destructive mt-1.5">{(enableMutation.error as Error).message}</p>
              )}
              <div className="flex gap-2 mt-3">
                <Button
                  size="sm"
                  disabled={code.length !== 6 || enableMutation.isPending}
                  onClick={() => enableMutation.mutate()}
                >
                  {enableMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Confirm & enable"}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setStep("idle");
                    setQr(null);
                    setSecret(null);
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <p className="text-sm font-medium text-emerald-500 flex items-center gap-2">
              <Check className="h-4 w-4" /> Two-factor authentication enabled
            </p>
            <p className="text-xs text-muted-foreground">
              Save these recovery codes somewhere safe — each one works once if you lose access to your authenticator.
            </p>
            <div className="grid grid-cols-2 gap-2 font-mono text-xs bg-surface/50 border border-border rounded-lg p-3">
              {recoveryCodes?.map((c) => (
                <span key={c}>{c}</span>
              ))}
            </div>
            <Button size="sm" className="self-start" onClick={finishSetup}>
              Done
            </Button>
          </div>
        )}
      </CardContent>

      <Dialog open={disableOpen} onOpenChange={setDisableOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Disable two-factor authentication?</DialogTitle>
            <DialogDescription>Enter your password to confirm.</DialogDescription>
          </DialogHeader>
          <Input
            type="password"
            value={disablePassword}
            onChange={(e) => setDisablePassword(e.target.value)}
            placeholder="Password"
            autoFocus
          />
          {disableMutation.isError && (
            <p className="text-xs text-destructive">{(disableMutation.error as Error).message}</p>
          )}
          <DialogFooter>
            <DialogClose render={<Button variant="outline" size="sm" />}>Cancel</DialogClose>
            <Button
              variant="destructive"
              size="sm"
              disabled={!disablePassword || disableMutation.isPending}
              onClick={() => disableMutation.mutate()}
            >
              {disableMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Disable"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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
        <SectionHeader icon={Smartphone} title="Active Sessions" subtitle="Devices currently signed in to your account." />
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
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/5 border border-border/40">
                    <Smartphone className="h-4 w-4 text-muted-foreground" />
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
              {revokeOthersMutation.isPending
                ? "Signing out..."
                : `Sign out ${others.length} other device${others.length > 1 ? "s" : ""}`}
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
        <SectionHeader icon={Download} title="Privacy & Data" subtitle="Control and export what you share." />
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
        <SectionHeader icon={AlertTriangle} title="Danger Zone" subtitle="Irreversible account actions." tone="destructive" />
      </CardHeader>
      <CardContent className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <p className="text-sm font-medium text-foreground">Delete account</p>
          <p className="text-xs text-muted-foreground mt-0.5 max-w-md">
            Permanently deletes your profile, saved insights, recommendations, rules and knowledge base entries.
            Shared datasets are not affected. This can&apos;t be undone.
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

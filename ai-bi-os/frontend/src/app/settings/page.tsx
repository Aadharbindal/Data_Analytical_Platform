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
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
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
  Settings,
  Shield,
  Lock,
} from "lucide-react";// ─────────────────────────────────────────────────────────────
// MOTION TOKENS — single source of truth
// ─────────────────────────────────────────────────────────────
const spring = { type: "spring", stiffness: 380, damping: 36, mass: 0.8 } as const;
const springSnappy = { type: "spring", stiffness: 500, damping: 40, mass: 0.6 } as const;
const easeOut = { duration: 0.22, ease: [0.0, 0.0, 0.2, 1.0] } as const;
const easeOutSlow = { duration: 0.32, ease: [0.0, 0.0, 0.2, 1.0] } as const;

// Staggered children container
const staggerContainer = {
  hidden: {},
  show: { transition: { staggerChildren: 0.035, delayChildren: 0 } },
};

// Each staggered child rises smoothly
const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 30, mass: 1 } },
};

// Section scroll-in
const sectionReveal = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: easeOutSlow },
};

// ─────────────────────────────────────────────────────────────
// DATA
// ─────────────────────────────────────────────────────────────
const SIDEBAR_GROUPS = [
  {
    label: "GENERAL",
    items: [
      { id: "profile", label: "Profile", icon: User },
      { id: "appearance", label: "Appearance", icon: Sun },
    ],
  },
  {
    label: "ACCOUNT",
    items: [
      { id: "security", label: "Security", icon: Shield },
      { id: "sessions", label: "Sessions", icon: Smartphone },
    ],
  },
  {
    label: "DATA & PRIVACY",
    items: [
      { id: "privacy", label: "Privacy & Data", icon: Lock },
    ],
  },
  {
    label: "SAFETY",
    items: [{ id: "danger", label: "Danger Zone", icon: AlertTriangle }],
  },
] as const;

const SECTIONS = SIDEBAR_GROUPS.flatMap((g) => g.items);
type SectionId = (typeof SECTIONS)[number]["id"];

// ─────────────────────────────────────────────────────────────
// UTILS
// ─────────────────────────────────────────────────────────────
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

// ─────────────────────────────────────────────────────────────
// SECTION HEADER — staggered title + subtitle
// ─────────────────────────────────────────────────────────────
function SectionHeader({ 
  title, 
  subtitle, 
  icon: Icon,
  variant = "default"
}: { 
  title: string; 
  subtitle: string; 
  icon?: React.ElementType;
  variant?: "default" | "danger"
}) {
  const isDanger = variant === "danger";
  const ringColor = isDanger ? "rgba(239,68,68,0.8)" : "rgba(0,112,243,0.8)";
  const glowColor = isDanger ? "rgba(239,68,68,0.3)" : "rgba(0,112,243,0.3)";
  const iconColorClass = isDanger ? "text-red-500" : "text-primary";
  
  return (
    <motion.div className="flex items-start gap-4 mb-8" variants={staggerContainer} initial="hidden" animate="show">
      {Icon && (
        <motion.div variants={fadeUp} className="relative h-12 w-12 shrink-0 mt-1">
          {/* Slow-pulse outer glow ring */}
          <motion.div
            className="absolute -inset-[2px] rounded-full opacity-[0.8]"
            style={{
              background: "transparent",
              boxShadow: `0 0 0 1px ${ringColor}, 0 0 12px 2px ${glowColor}`,
              borderRadius: "9999px",
            }}
          />
          <div className="flex h-full w-full items-center justify-center rounded-full bg-[#081226] relative z-10">
            <Icon className={`h-5 w-5 ${iconColorClass}`} strokeWidth={2.5} />
          </div>
        </motion.div>
      )}
      <div>
        <motion.h1
          className={`text-[26px] font-semibold tracking-tight leading-tight ${isDanger ? "text-red-500" : "text-white"}`}
          variants={fadeUp}
        >
          {title}
        </motion.h1>
        <motion.p
          className="text-[14px] text-muted-foreground mt-2 leading-snug"
          variants={fadeUp}
        >
          {subtitle}
        </motion.p>
      </div>
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────
// ANIMATED SIDEBAR NAV ITEM
// ─────────────────────────────────────────────────────────────
function SidebarItem({
  id,
  label,
  icon: Icon,
  active,
  onClick,
  delay,
}: {
  id: string;
  label: string;
  icon: React.ElementType;
  active: boolean;
  onClick: () => void;
  delay: number;
}) {
  return (
    <motion.button
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ ...easeOut, delay }}
      onClick={onClick}
      whileTap={{ scale: 0.98 }}
      className={`group relative flex items-center gap-3 ml-2 px-3 py-2.5 text-[13px] font-medium text-left rounded-md w-[calc(100%-8px)] outline-none focus-visible:ring-1 focus-visible:ring-primary/40 transition-colors duration-200 ${
        active
          ? "text-primary bg-primary/[0.08]"
          : "text-muted-foreground/90 hover:bg-white/[0.03] hover:text-foreground"
      }`}
    >
      {/* Left indicator pill — floats with gap from button background */}
      {active && (
        <motion.div
          layoutId="settings-active-pill"
          className="absolute left-[-16px] top-1/2 -translate-y-1/2 w-[3px] h-5 bg-primary rounded-r-full"
          transition={{ type: "spring", stiffness: 500, damping: 40 }}
        />
      )}

      <Icon
        className={`h-[15px] w-[15px] shrink-0 transition-colors ${
          active
            ? "text-primary drop-shadow-[0_0_8px_rgba(0,112,243,0.3)]"
            : "text-muted-foreground/70 group-hover:text-foreground/90"
        }`}
      />

      <span>{label}</span>
    </motion.button>
  );
}

// ─────────────────────────────────────────────────────────────
// ANIMATED SECTION WRAPPER — scroll-in on viewport enter
// ─────────────────────────────────────────────────────────────
function AnimatedSection({ children, id }: { children: React.ReactNode; id: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced) { setVisible(true); return; }
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true); },
      { threshold: 0.04, rootMargin: "0px 0px -32px 0px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [reduced]);

  return (
    <motion.div
      ref={ref}
      initial={reduced ? false : { opacity: 0, y: 16 }}
      animate={visible ? { opacity: 1, y: 0 } : {}}
      transition={easeOutSlow}
      id={id}
    >
      {children}
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────
// ANIMATED DIVIDER — draws left → right
// ─────────────────────────────────────────────────────────────
function AnimatedDivider() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced) { setVisible(true); return; }
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true); },
      { threshold: 0.5 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [reduced]);

  return (
    <div ref={ref} className="relative h-px overflow-hidden">
      <motion.div
        className="absolute inset-0 bg-white/[0.04]"
        initial={{ scaleX: 0, opacity: 0 }}
        animate={visible ? { scaleX: 1, opacity: 1 } : {}}
        transition={{ duration: 0.6, ease: [0.0, 0.0, 0.2, 1.0] }}
        style={{ transformOrigin: "left center" }}
      />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// SAVE BUTTON with spring + success morph
// ─────────────────────────────────────────────────────────────
function SaveButton({
  saved,
  pending,
  disabled,
  onClick,
  label = "Save changes",
}: {
  saved: boolean;
  pending: boolean;
  disabled: boolean;
  onClick: () => void;
  label?: string;
}) {
  return (
    <div className="flex items-center gap-4">
      <motion.div
        whileHover={disabled ? {} : { y: -2, boxShadow: "0 4px 20px rgba(0,112,243,0.25)" }}
        whileTap={disabled ? {} : { scale: 0.97 }}
        transition={springSnappy}
        style={{ borderRadius: 999 }}
      >
        <Button
          className="bg-primary hover:bg-primary/90 text-primary-foreground rounded-full px-5 h-9 font-medium text-[13.5px]"
          disabled={disabled || pending}
          onClick={onClick}
        >
          <AnimatePresence mode="wait" initial={false}>
            {pending ? (
              <motion.span
                key="loading"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={easeOut}
              >
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              </motion.span>
            ) : (
              <motion.span
                key="label"
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={easeOut}
              >
                {label}
              </motion.span>
            )}
          </AnimatePresence>
        </Button>
      </motion.div>

      <AnimatePresence>
        {saved && (
          <motion.span
            initial={{ opacity: 0, x: -8, filter: "blur(4px)" }}
            animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, x: 4, filter: "blur(4px)" }}
            transition={easeOut}
            className="flex items-center gap-1.5 text-[13px] text-emerald-500 font-medium"
          >
            <Check className="h-3.5 w-3.5" /> Saved
          </motion.span>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// PAGE
// ─────────────────────────────────────────────────────────────
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



  const scrollTo = (id: SectionId) => {
    const el = sectionRefs.current[id];
    const container = document.getElementById("settings-content");
    if (el && container) {
      const top = el.getBoundingClientRect().top - container.getBoundingClientRect().top + container.scrollTop - 24;
      container.scrollTo({ top, behavior: "smooth" });
    }
    setActiveSection(id);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="flex flex-col text-foreground w-full h-full overflow-hidden"
    >


      {isLoading || !user ? (
        <div className="flex items-center justify-center py-24 text-muted-foreground relative z-10">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[220px_minmax(0,1fr)] items-start w-full h-full">
          {/* Left sidebar — fixed width, sticky */}
          <motion.div
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ ...easeOut, delay: 0.05 }}
            className="flex flex-col gap-0 lg:sticky lg:top-0 lg:h-full border-r border-white/[0.04] px-5 py-8"
          >
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ ...easeOut, delay: 0.1 }}
              className="flex items-center gap-2.5 mb-8"
            >
              <Settings className="h-[18px] w-[18px] text-foreground/70" />
              <span className="text-[15px] font-medium text-foreground">Settings</span>
            </motion.div>

            <nav className="flex flex-col gap-5">
              {SIDEBAR_GROUPS.map((group, gi) => (
                <div key={group.label} className="flex flex-col gap-0.5">
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ ...easeOut, delay: 0.12 + gi * 0.04 }}
                    className="text-[10px] font-semibold text-muted-foreground/50 uppercase tracking-[0.12em] px-3 mb-2"
                  >
                    {group.label}
                  </motion.span>
                  <div className="flex flex-col gap-1">
                    {group.items.map((s, si) => {
                      const active = activeSection === s.id;
                      const delay = 0.15 + gi * 0.06 + si * 0.04;
                      return (
                        <SidebarItem
                          key={s.id}
                          id={s.id}
                          label={s.label}
                          icon={s.icon}
                          active={active}
                          onClick={() => scrollTo(s.id)}
                          delay={delay}
                        />
                      );
                    })}
                  </div>
                </div>
              ))}
            </nav>
          </motion.div>

          {/* Right content area */}
          <div id="settings-content" className="flex flex-col min-w-0 overflow-y-auto h-full pb-24 px-10 py-8">
            <div className="flex flex-col gap-0">
              {visibleSections.map((s, i) => (
                <div
                  key={s.id}
                  ref={(el) => { sectionRefs.current[s.id] = el; }}
                  className="scroll-mt-8 flex flex-col pb-6 last:pb-0 mb-6 last:mb-0"
                >
                  <AnimatedSection id={`section-${s.id}`}>
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
                  </AnimatedSection>

                  {/* Animated divider between sections */}
                  {i < visibleSections.length - 1 && <div className="mt-6"><AnimatedDivider /></div>}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────
// PROFILE CARD
// ─────────────────────────────────────────────────────────────
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
    <motion.div
      className="flex flex-col"
      variants={staggerContainer}
      initial="hidden"
      animate="show"
    >
      <SectionHeader title="Profile" subtitle="Manage your personal information and how others see you." icon={User} />

      {/* Avatar block */}
      <motion.div className="flex items-start gap-5 mb-8" variants={fadeUp}>
        {/* Avatar with permanent glowing blue ring */}
        <motion.div
          className="relative h-[80px] w-[80px] shrink-0 mt-0.5 cursor-pointer"
          whileHover={{ scale: 1.05 }}
          transition={spring}
          onClick={() => !avatarBusy && fileInputRef.current?.click()}
          title="Click to change photo"
        >
          {/* Slow-pulse outer glow ring */}
          <motion.div
            className="absolute -inset-[4px] rounded-full opacity-[0.8]"
            style={{
              background: "transparent",
              boxShadow: "0 0 0 1.5px rgba(0,112,243,0.9), 0 0 20px 4px rgba(0,112,243,0.35)",
              borderRadius: "9999px",
            }}
          />

          {user.has_avatar ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={avatarUrl(user.id, cacheBust)}
              alt={user.full_name}
              className="h-full w-full rounded-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center rounded-full bg-[#0d1a33] text-white text-2xl font-normal">
              {initials(user.full_name)}
            </div>
          )}

          {avatarBusy && (
            <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/50">
              <Loader2 className="h-5 w-5 animate-spin text-white" />
            </div>
          )}
        </motion.div>

        {/* Info block */}
        <div className="flex flex-col min-w-0 pt-1">
          <span className="text-[15px] font-medium text-white truncate leading-normal">{user.email}</span>
          {memberSince && (
            <span className="text-[12.5px] text-muted-foreground/70 mt-1.5">{memberSince}</span>
          )}
          <div className="flex items-center gap-4 mt-3">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png"
              className="hidden"
              onChange={handleFileChange}
            />
            <motion.button
              type="button"
              disabled={avatarBusy}
              onClick={() => fileInputRef.current?.click()}
              whileHover={{ opacity: 0.8 }}
              whileTap={{ scale: 0.97 }}
              transition={easeOut}
              className="text-[13px] font-medium text-primary disabled:opacity-40"
            >
              {user.has_avatar ? "Change photo" : "Upload photo"}
            </motion.button>
            {user.has_avatar && (
              <motion.button
                type="button"
                disabled={avatarBusy}
                onClick={() => removeAvatarMutation.mutate()}
                whileHover={{ opacity: 0.7 }}
                whileTap={{ scale: 0.97 }}
                transition={easeOut}
                className="text-[13px] font-medium text-muted-foreground/60 hover:text-destructive transition-colors disabled:opacity-40"
              >
                Remove
              </motion.button>
            )}
          </div>
          {avatarError ? (
            <motion.p
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={easeOut}
              className="text-[12px] text-destructive mt-2"
            >
              {avatarError}
            </motion.p>
          ) : (
            <p className="text-[11.5px] text-muted-foreground/40 mt-2">JPG or PNG, max 2MB.</p>
          )}
        </div>
      </motion.div>

      {/* Inputs */}
      <motion.div className="grid grid-cols-2 gap-5" variants={fadeUp}>
        <div className="flex flex-col gap-2">
          <label className="text-[12px] font-medium text-muted-foreground tracking-wide">Full name</label>
          <Input
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Your name"
            className="bg-background border-white/[0.07] text-white h-10 rounded-lg text-[14px] focus-visible:ring-1 focus-visible:ring-primary/40 focus-visible:border-primary/40 transition-all duration-200"
          />
        </div>
        <div className="flex flex-col gap-2">
          <label className="text-[12px] font-medium text-muted-foreground tracking-wide">Email</label>
          <Input
            value={user.email}
            disabled
            className="bg-background border-white/[0.07] text-muted-foreground opacity-50 h-10 rounded-lg text-[14px]"
          />
        </div>
      </motion.div>

      {mutation.isError && (
        <motion.p
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={easeOut}
          className="text-[12px] text-destructive mt-3"
        >
          {(mutation.error as Error).message}
        </motion.p>
      )}

      <motion.div className="mt-8" variants={fadeUp}>
        <SaveButton
          saved={saved}
          pending={mutation.isPending}
          disabled={!dirty}
          onClick={() => mutation.mutate(fullName.trim())}
        />
      </motion.div>
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────
// APPEARANCE CARD
// ─────────────────────────────────────────────────────────────
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
    <motion.div
      className="flex flex-col gap-8"
      variants={staggerContainer}
      initial="hidden"
      animate="show"
    >
      <SectionHeader title="Appearance" subtitle="Personalize how the app looks — changes apply instantly." icon={Sun} />
      <motion.div className="flex flex-col gap-10" variants={fadeUp}>
        <div className="flex flex-col gap-3">
          <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-widest">Theme</div>
          <div className="grid grid-cols-3 gap-0 border border-white/5 rounded-xl overflow-hidden bg-[#0a0f18] p-1">
            {options.map((opt) => {
              const Icon = opt.icon;
              const active = mounted && theme === opt.id;
              return (
                <motion.button
                  key={opt.id}
                  onClick={() => setTheme(opt.id)}
                  whileTap={{ scale: 0.97 }}
                  transition={springSnappy}
                  className={`relative flex items-center justify-center gap-2.5 py-2.5 text-[13px] font-medium rounded-lg ${
                    active ? "text-primary" : "text-muted-foreground hover:text-white"
                  }`}
                  style={{ transition: "color 180ms ease" }}
                >
                  {active && (
                    <motion.div
                      layoutId="theme-pill"
                      className="absolute inset-0 bg-[#111B33] rounded-lg"
                      transition={spring}
                    />
                  )}
                  <span className="relative z-10 flex items-center gap-2.5">
                    <Icon className="h-4 w-4" />
                    {opt.label}
                  </span>
                </motion.button>
              );
            })}
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-widest">Accent color</div>
          <div className="flex items-center gap-4 flex-wrap">
            {ACCENT_SWATCHES.map((hex) => {
              const isActive = mounted && accent === hex;
              return (
                <motion.button
                  key={hex}
                  onClick={() => applyAccent(hex)}
                  aria-label={`Accent ${hex}`}
                  style={{ background: hex }}
                  whileHover={{ scale: 1.12 }}
                  whileTap={{ scale: 0.94 }}
                  animate={{
                    scale: isActive ? 1.1 : 1,
                    boxShadow: isActive ? `0 0 16px ${hex}55` : "0 0 0px transparent",
                  }}
                  transition={spring}
                  className={`h-9 w-9 rounded-full border-2 ${isActive ? "border-white" : "border-transparent"}`}
                />
              );
            })}
            {mounted && accent && (
              <motion.button
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -8 }}
                onClick={resetAccent}
                whileHover={{ opacity: 0.8 }}
                transition={easeOut}
                className="text-[12px] text-muted-foreground ml-2"
              >
                Reset to default
              </motion.button>
            )}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────
// SECURITY CARD
// ─────────────────────────────────────────────────────────────
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
    <motion.div
      className="flex flex-col gap-8"
      variants={staggerContainer}
      initial="hidden"
      animate="show"
    >
      <SectionHeader title="Security" subtitle="Manage your password and authentication methods." icon={KeyRound} />
      <motion.div className="flex flex-col gap-5" variants={fadeUp}>
        <div className="flex items-center gap-2 mb-1">
          <div className="h-1.5 w-1.5 rounded-full bg-primary" />
          <h3 className="text-[15px] font-medium text-white">Password</h3>
        </div>
        <div>
          <label className="text-[13px] font-medium text-muted-foreground mb-1.5 block">Current password</label>
          <Input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="••••••••"
            className="bg-[#0a0f18] border-white/5 text-white h-11 rounded-lg focus-visible:ring-1 focus-visible:ring-primary/50 focus-visible:border-primary/50 transition-all duration-200"
          />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="text-[13px] font-medium text-muted-foreground mb-1.5 block">New password</label>
            <Input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="At least 8 characters"
              className="bg-[#0a0f18] border-white/5 text-white h-11 rounded-lg focus-visible:ring-1 focus-visible:ring-primary/50 focus-visible:border-primary/50 transition-all duration-200"
            />
          </div>
          <div>
            <label className="text-[13px] font-medium text-muted-foreground mb-1.5 block">Confirm new password</label>
            <Input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Repeat new password"
              aria-invalid={mismatch}
              className="bg-[#0a0f18] border-white/5 text-white h-11 rounded-lg focus-visible:ring-1 focus-visible:ring-primary/50 focus-visible:border-primary/50 transition-all duration-200"
            />
          </div>
        </div>

        <AnimatePresence>
          {mismatch && (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={easeOut}
              className="text-xs text-destructive"
            >
              Passwords don&apos;t match.
            </motion.p>
          )}
        </AnimatePresence>

        {mutation.isError && (
          <p className="text-xs text-destructive">{(mutation.error as Error).message}</p>
        )}

        <div className="mt-2">
          <SaveButton
            label="Update password"
            saved={success}
            pending={mutation.isPending}
            disabled={!canSubmit}
            onClick={() => mutation.mutate()}
          />
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────
// TWO FACTOR CARD
// ─────────────────────────────────────────────────────────────
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
    <div className="flex flex-col gap-5 mt-10 border-t border-white/5 pt-10">
      <SectionHeader 
        title="Two-Factor Authentication" 
        subtitle="Require a 6-digit code from an authenticator app at sign-in." 
        icon={Fingerprint} 
      />
      <div className="flex flex-col gap-4">
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
      </div>

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
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// SESSIONS CARD
// ─────────────────────────────────────────────────────────────
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
    <motion.div
      className="flex flex-col gap-8"
      variants={staggerContainer}
      initial="hidden"
      animate="show"
    >
      <SectionHeader title="Sessions" subtitle="View and manage your active sessions across devices." icon={Smartphone} />
      <motion.div className="flex flex-col gap-1" variants={fadeUp}>
        {isLoading ? (
          <div className="flex justify-center py-6 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
          </div>
        ) : !sessions || sessions.length === 0 ? (
          <p className="text-xs text-muted-foreground py-2">No active sessions found.</p>
        ) : (
          <motion.div
            className="flex flex-col divide-y divide-border/30"
            variants={staggerContainer}
            initial="hidden"
            animate="show"
          >
            {sessions.map((s: SessionInfo) => (
              <motion.div key={s.id} variants={fadeUp} className="flex items-center justify-between gap-3 py-3">
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
              </motion.div>
            ))}
          </motion.div>
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
      </motion.div>
    </motion.div>
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
      a.download = `numerate-data-export-${new Date().toISOString().slice(0, 10)}.json`;
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
    <motion.div
      className="flex flex-col gap-8"
      variants={staggerContainer}
      initial="hidden"
      animate="show"
    >
      <SectionHeader title="Privacy & Data" subtitle="Control and export what you share." icon={Lock} />
      <motion.div
        variants={fadeUp}
        className="flex items-center justify-between gap-4 flex-wrap border border-white/5 bg-[#0a0f18] p-6 rounded-xl"
      >
        <div>
          <p className="text-sm font-medium text-foreground">Export your data</p>
          <p className="text-xs text-muted-foreground mt-0.5 max-w-md">
            Download a JSON copy of your insights, recommendations, rules and knowledge base entries.
          </p>
          {error && <p className="text-xs text-destructive mt-1">{error}</p>}
        </div>
        <motion.div
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.97 }}
          transition={springSnappy}
        >
          <Button 
            size="sm" 
            className="rounded-md bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.08] text-foreground hover:text-white shadow-sm transition-all"
            disabled={downloading} 
            onClick={handleExport}
          >
            {downloading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Download"}
          </Button>
        </motion.div>
      </motion.div>
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────
// DANGER ZONE CARD
// ─────────────────────────────────────────────────────────────
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
    <motion.div
      className="flex flex-col gap-8"
      variants={staggerContainer}
      initial="hidden"
      animate="show"
    >
      <SectionHeader title="Danger Zone" subtitle="Irreversible and sensitive account actions." icon={AlertTriangle} variant="danger" />

      <motion.div
        variants={fadeUp}
        whileHover={{ boxShadow: "0 0 0 1px rgba(240,68,56,0.2)", transition: { duration: 0.2 } }}
        className="flex items-center justify-between gap-4 flex-wrap border border-destructive/20 bg-destructive/5 p-6 rounded-xl"
      >
        <div>
          <p className="text-sm font-medium text-foreground">Delete account</p>
          <p className="text-xs text-muted-foreground mt-0.5 max-w-md">
            Permanently deletes your profile, saved insights, recommendations, rules and knowledge base entries.
            Shared datasets are not affected. This can&apos;t be undone.
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <motion.div whileHover={{ y: -1 }} whileTap={{ scale: 0.97 }} transition={springSnappy}>
            <Button variant="destructive" size="sm" onClick={() => setOpen(true)}>
              Delete account
            </Button>
          </motion.div>
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
      </motion.div>
    </motion.div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import { avatarUrl } from "@/lib/api";
import { useLayoutStore } from "@/hooks/useLayoutStore";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  Database,
  MessageSquare,
  Lightbulb,
  Layers,
  Network,
  GitBranch,
  Settings,
  Shield,
  Zap,
  User,
  MoreVertical,
  BarChart3,
  LogOut,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react";
import { AnimatedLogo } from "@/components/ui/AnimatedLogo";

/** Survives reloads as well as navigation — the rail's width is a preference,
 *  and a preference that resets when you refresh is not one. */
const SIDEBAR_COLLAPSED_KEY = "numerate:sidebar-collapsed";

const mainNavItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Datasets", href: "/datasets", icon: Database },
  { name: "Data Catalog", href: "/data-catalog", icon: Network },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Insights", href: "/insights", icon: Lightbulb },
  { name: "Recommendations", href: "/recommendations", icon: Zap },
  { name: "Rules", href: "/rules", icon: GitBranch },
  { name: "Confidence Center", href: "/analytics/confidence", icon: Shield },
  { name: "AI Chat", href: "/chat", icon: MessageSquare },
];

const bottomNavItems = [
  { name: "Settings", href: "/settings", icon: Settings },
];

const sidebarVariants = {
  hidden: { opacity: 0, x: -16 },
  show: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.5,
      ease: [0.25, 1, 0.5, 1] as [number, number, number, number],
      staggerChildren: 0.05,
      delayChildren: 0.1,
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, x: -10 },
  show: { 
    opacity: 1, 
    x: 0,
    transition: {
      duration: 0.5,
      ease: [0.25, 1, 0.5, 1] as [number, number, number, number]
    }
  }
};

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout, avatarVersion } = useAuth();
  const { isMobileNavOpen, setMobileNavOpen } = useLayoutStore();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Desktop-only concept: the narrow icon rail. On mobile the sidebar is an
  // off-canvas drawer that is either fully open or fully hidden, so every
  // collapse style below is applied at `lg:` and the mobile drawer always
  // renders the full-width, labelled version.
  //
  // One piece of state, changed only by the toggle. This used to be two flags
  // picked between by route — collapsed by default on the welcome screen and
  // under /analytics, expanded everywhere else — which meant walking from the
  // welcome screen to any other page silently reopened a rail the user had
  // deliberately left shut. The rail is the user's setting, not the route's.
  const [isCollapsed, setIsCollapsed] = useState(true);

  // Restored after mount rather than in the initial state: the server renders
  // the default, and reading storage during the first render would make the
  // markup disagree with what was sent.
  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
      if (saved !== null) setIsCollapsed(saved === "1");
    } catch {
      // Private mode, or storage disabled. The default stands.
    }
    setMounted(true);
  }, []);

  // The collapsed icon rail keeps its original desktop classes untouched, and
  // mobile re-expands them via `max-lg:`. Overriding in that direction matters:
  // a `lg:`-prefixed override of an arbitrary base value (e.g. `lg:max-w-[0px]`
  // against `max-w-[200px]`) loses on source order in Tailwind v4, whereas
  // `max-lg:` utilities are emitted after the base ones and reliably win.
  const railLabel = isCollapsed
    ? "max-w-0 opacity-0 ml-0 max-lg:max-w-[200px] max-lg:opacity-100 max-lg:ml-3"
    : "max-w-[200px] opacity-100 ml-3";

  // The icon is centered in the rail by growing horizontal padding rather than
  // swapping to `justify-center h-10 w-10 mx-auto`. That swap resized the box
  // and reset its margin with nothing to tween, so every row jumped a frame
  // before the width animation had even begun. Padding animates, so the icon
  // glides to center instead. These rows sit inside a container that already
  // has 12px of its own padding, so the centering figure is measured against
  // that inner 40px box, not the full 64px rail: (40 - 18) / 2 = 11px.
  const railItem = isCollapsed
    ? "py-2.5 text-[13px] px-[11px] max-lg:px-3"
    : "py-2.5 text-[13px] px-3";

  // One curve, one duration for everything the toggle moves, so the rail
  // width, the labels and the padding land together. Labels then get a
  // direction-aware fade: collapsing, the text must clear out *before* the
  // rail narrows or it visibly squashes against the edge; expanding, the
  // space has to exist before text appears in it. Fading symmetrically in
  // both directions is what made this read as a jerk rather than a slide.
  const EASE = "cubic-bezier(0.4, 0, 0.2, 1)";
  const RAIL_MS = 380;

  // Silent until the stored width has been restored. The rail renders collapsed
  // first and only then learns it should be open, so leaving transitions on
  // would play a full expand on every single page load for anyone who keeps it
  // open — an animation for something the user never asked to change.
  const railMotion = mounted
    ? `width ${RAIL_MS}ms ${EASE}, padding ${RAIL_MS}ms ${EASE}`
    : "none";
  const labelMotion = !mounted
    ? "none"
    : isCollapsed
      ? `opacity 150ms ease-out, max-width ${RAIL_MS}ms ${EASE}, margin-left ${RAIL_MS}ms ${EASE}`
      : `opacity 220ms ease-in 190ms, max-width ${RAIL_MS}ms ${EASE}, margin-left ${RAIL_MS}ms ${EASE}`;

  const toggleSidebar = () => {
    setIsCollapsed((collapsed) => {
      const next = !collapsed;
      try {
        window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, next ? "1" : "0");
      } catch {
        // Storage unavailable — the choice still holds for this session.
      }
      return next;
    });
  };

  // Navigating always dismisses the drawer — otherwise tapping a link on a
  // phone leaves the overlay covering the page you just moved to.
  useEffect(() => {
    setMobileNavOpen(false);
  }, [pathname, setMobileNavOpen]);

  // Escape closes the drawer, and while it's open the page behind it must not
  // scroll — without this, scrolling the drawer drags the dashboard with it.
  useEffect(() => {
    if (!isMobileNavOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileNavOpen(false);
    };
    window.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [isMobileNavOpen, setMobileNavOpen]);

  return (
    <>
    {/* Backdrop — mobile only. Kept mounted and faded so opening/closing the
        drawer doesn't re-trigger a mount animation on every toggle. */}
    <div
      onClick={() => setMobileNavOpen(false)}
      aria-hidden="true"
      className={cn(
        "fixed inset-0 z-30 bg-background/70 backdrop-blur-sm transition-opacity duration-300 lg:hidden",
        isMobileNavOpen ? "opacity-100" : "pointer-events-none opacity-0"
      )}
    />

    <aside
      aria-label="Main navigation"
      style={{ transition: `${railMotion}, transform 300ms ${EASE}` }}
      className={cn(
      // Desktop: permanent in-flow rail, exactly as before.
      "relative z-20 flex h-screen shrink-0 flex-col border-r border-border/60 bg-surface/40 text-text-secondary",
      isCollapsed ? "w-[64px]" : "w-[260px]",
      // Mobile: lift out of flow into an off-canvas drawer, always full width.
      "max-lg:fixed max-lg:inset-y-0 max-lg:left-0 max-lg:z-40 max-lg:w-[280px] max-lg:max-w-[85vw] max-lg:bg-surface",
      isMobileNavOpen ? "max-lg:translate-x-0" : "max-lg:-translate-x-full"
    )}>
    <motion.div
      initial="hidden"
      animate="show"
      variants={sidebarVariants}
      className="flex h-full flex-col"
    >
      {/* Floating Toggle Button — the collapse rail is desktop-only */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-[24px] hidden h-6 w-6 items-center justify-center rounded-full bg-[#11131a] border border-border text-muted-foreground shadow-[0_0_10px_rgba(0,0,0,0.5)] hover:bg-white/[0.1] hover:text-foreground z-50 transition-all duration-200 lg:flex"
        title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
      >
        <ChevronLeft className={cn("h-3.5 w-3.5", isCollapsed && "rotate-180")} style={{ transition: `transform ${RAIL_MS}ms ${EASE}` }} strokeWidth={2.5} />
      </button>

      {/* Close button — mobile drawer only */}
      <button
        onClick={() => setMobileNavOpen(false)}
        aria-label="Close navigation"
        className="absolute right-3 top-[24px] flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-white/[0.06] hover:text-foreground lg:hidden"
      >
        <X className="h-4 w-4" strokeWidth={2.5} />
      </button>

      {/* Brand / Logo */}
      <motion.div variants={itemVariants} style={{ transition: railMotion }} className={cn("flex h-[72px] shrink-0 items-center border-b border-border/40 mb-2", isCollapsed ? "px-[16px] max-lg:px-6" : "px-6")}>
        <Link href="/" className="flex items-center text-foreground font-semibold text-[15px] tracking-wide" title="Numerate">
          <AnimatedLogo />
          <div className={cn(
            "overflow-hidden whitespace-nowrap flex items-center",
            isCollapsed
              ? "max-w-0 opacity-0 ml-0 max-lg:max-w-[120px] max-lg:opacity-100 max-lg:ml-3"
              : "max-w-[120px] opacity-100 ml-3"
          )} style={{ transition: labelMotion }}>
            <span>Numerate</span>
          </div>
        </Link>
      </motion.div>

      {/* Main Navigation */}
      <nav className="flex-1 space-y-0.5 px-3 py-2 overflow-y-auto overflow-x-hidden [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        {mainNavItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
          return (
            <motion.div key={item.name} variants={itemVariants}>
              <Link
                href={item.href}
                title={isCollapsed ? item.name : undefined}
                className={cn(
                  "group relative flex items-center rounded-xl font-medium transition-colors duration-200",
                  railItem,
                  isActive
                    ? "text-primary bg-primary/[0.08]"
                    : "text-muted-foreground/90 hover:bg-white/[0.03] hover:text-foreground"
                )}
              >
                {isActive && (
                  <div className="absolute left-[-12px] top-1/2 -translate-y-1/2 w-1 h-5 bg-primary rounded-r-full" />
                )}
                <item.icon
                  className={cn(
                    "h-[18px] w-[18px] shrink-0 transition-colors",
                    isActive ? "text-primary drop-shadow-[0_0_8px_rgba(0,112,243,0.3)]" : "text-muted-foreground/70 group-hover:text-foreground/90"
                  )}
                />
                <div className={cn("overflow-hidden whitespace-nowrap", railLabel)} style={{ transition: labelMotion }}>
                  {item.name}
                </div>
              </Link>
            </motion.div>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div style={{ transition: railMotion }} className="mt-auto border-t border-border/40 p-3 space-y-0.5">
        {bottomNavItems.map((item) => (
          <motion.div key={item.name} variants={itemVariants}>
            <Link
              href={item.href}
              title={isCollapsed ? item.name : undefined}
              className={cn(
                "group flex items-center rounded-xl font-medium text-muted-foreground/90 transition-colors duration-200 hover:bg-white/[0.03] hover:text-foreground",
                railItem
              )}
            >
              <item.icon className="h-[18px] w-[18px] shrink-0 text-muted-foreground/70 group-hover:text-foreground/90 transition-colors" />
              <div className={cn("overflow-hidden whitespace-nowrap", railLabel)} style={{ transition: labelMotion }}>
                {item.name}
              </div>
            </Link>
          </motion.div>
        ))}

        {/* User Profile */}
        <motion.div variants={itemVariants} className="pt-2 mt-2 border-t border-border/40 w-full">
          {/* Stays a single row in both states — the old collapsed variant
              switched to flex-col, which re-stacked the avatar and the logout
              button the instant you clicked, ahead of any width animation. */}
          <div
            style={{ transition: railMotion }}
            className={cn(
              "group flex items-center justify-between rounded-xl py-2.5 hover:bg-white/[0.03]",
              isCollapsed ? "px-[4px] max-lg:px-3" : "px-3"
            )}
          >
            <Link
              href="/settings"
              className="flex items-center min-w-0 cursor-pointer"
              title={isCollapsed ? (user?.full_name || "User") : undefined}
            >
              {user?.has_avatar ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={avatarUrl(user.id, avatarVersion)}
                  alt={user.full_name}
                  className="h-8 w-8 rounded-full object-cover border border-primary/30 shrink-0"
                />
              ) : (
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-primary border border-primary/30 shrink-0 font-semibold text-sm">
                  {user?.full_name ? user.full_name.charAt(0).toUpperCase() : <User className="h-4 w-4" />}
                </div>
              )}
              <div className={cn(
                "flex flex-col overflow-hidden justify-center",
                isCollapsed
                  ? "max-w-0 opacity-0 ml-0 max-lg:max-w-[150px] max-lg:opacity-100 max-lg:ml-3"
                  : "max-w-[150px] opacity-100 ml-3"
              )} style={{ transition: labelMotion }}>
                <span className="text-[13px] font-semibold text-foreground/90 group-hover:text-foreground transition-colors truncate">{user?.full_name || "Guest"}</span>
              </div>
            </Link>
            {/* Collapses to zero width alongside the labels. Left at its
                natural size it would sit beside the avatar in a 64px rail and,
                because a flex item's automatic minimum size is its content,
                hold the whole sidebar open at ~86px. */}
            <div
              className={cn(
                "overflow-hidden",
                isCollapsed
                  ? "max-w-0 opacity-0 max-lg:max-w-[32px] max-lg:opacity-100"
                  : "max-w-[32px] opacity-100"
              )}
              style={{ transition: labelMotion }}
            >
              <button
                onClick={() => setShowLogoutConfirm(true)}
                className="p-1 text-muted-foreground/70 transition-colors duration-200 hover:text-destructive group-hover:text-foreground/90"
                title="Logout"
                tabIndex={isCollapsed ? -1 : 0}
              >
                <LogOut className="h-4 w-4 shrink-0" />
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
    </aside>

    {/* Portalled to document.body: the sidebar root above animates with
        CSS transforms, which makes any position:fixed descendant position
        itself relative to that transformed ancestor instead of the
        viewport — this modal would otherwise render squeezed into the
        sidebar's own (much narrower) width instead of centered on screen. */}
    {mounted && createPortal(
      <AnimatePresence>
        {showLogoutConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm"
            onClick={() => setShowLogoutConfirm(false)}
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0, y: 15 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.8, opacity: 0, y: 15 }}
              transition={{ type: "spring", damping: 25, stiffness: 350 }}
              className="relative w-full max-w-[420px] overflow-hidden rounded-[24px] border border-[#1f2937] bg-[#111520] p-7 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex flex-col">
                <div className="relative mb-5 h-11 w-11">
                  <motion.div
                    animate={{ scale: [1, 2.2], opacity: [0.5, 0] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
                    className="absolute inset-0 rounded-full bg-primary/20"
                  />
                  <motion.div
                    animate={{ scale: [1, 1.6], opacity: [0.8, 0] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeOut", delay: 0.4 }}
                    className="absolute inset-0 rounded-full bg-primary/30"
                  />
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.1, type: "spring", damping: 12, stiffness: 300 }}
                    className="relative flex h-11 w-11 items-center justify-center rounded-full bg-primary/15"
                  >
                    <LogOut className="h-5 w-5 text-primary" strokeWidth={2.5} />
                  </motion.div>
                </div>

                <motion.h2
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.15 }}
                  className="text-xl font-semibold text-white tracking-tight"
                >
                  Log out
                </motion.h2>
                <motion.p
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                  className="mt-3 text-sm text-[#94a3b8] leading-relaxed"
                >
                  Are you sure you want to log out? You&apos;ll need to sign in again to access your workspace.
                </motion.p>

                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.25 }}
                  className="mt-8 flex justify-end gap-3"
                >
                  <Button
                    variant="ghost"
                    className="rounded-full bg-white/5 border border-white/10 hover:bg-white/10 text-white px-6 hover:text-white transition-all hover:scale-105 active:scale-95"
                    onClick={() => setShowLogoutConfirm(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="default"
                    className="rounded-full bg-primary hover:bg-primary/80 text-primary-foreground px-6 border-0 shadow-lg shadow-primary/20 transition-all hover:scale-105 active:scale-95"
                    onClick={logout}
                  >
                    Log out
                  </Button>
                </motion.div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>,
      document.body
    )}
    </>
  );
}


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
  const { isWelcomeActive, isMobileNavOpen, setMobileNavOpen } = useLayoutStore();
  const [isManualCollapsed, setIsManualCollapsed] = useState(false);
  const [isManualExpanded, setIsManualExpanded] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const isAnalyticsRoute = pathname?.startsWith("/analytics") ?? false;
  const isWelcomePage = pathname === "/" && isWelcomeActive;

  // Desktop-only concept: the narrow icon rail. On mobile the sidebar is an
  // off-canvas drawer that is either fully open or fully hidden, so every
  // collapse style below is applied at `lg:` and the mobile drawer always
  // renders the full-width, labelled version.
  const isCollapsed = (isAnalyticsRoute || isWelcomePage) ? !isManualExpanded : isManualCollapsed;

  // The collapsed icon rail keeps its original desktop classes untouched, and
  // mobile re-expands them via `max-lg:`. Overriding in that direction matters:
  // a `lg:`-prefixed override of an arbitrary base value (e.g. `lg:max-w-[0px]`
  // against `max-w-[200px]`) loses on source order in Tailwind v4, whereas
  // `max-lg:` utilities are emitted after the base ones and reliably win.
  const railLabel = isCollapsed
    ? "max-w-0 opacity-0 ml-0 max-lg:max-w-[200px] max-lg:opacity-100 max-lg:ml-3"
    : "max-w-[200px] opacity-100 ml-3";
  const railItem = isCollapsed
    ? "justify-center h-10 w-10 mx-auto max-lg:justify-start max-lg:h-auto max-lg:w-auto max-lg:mx-0 max-lg:px-3 max-lg:py-2.5 max-lg:text-[13px]"
    : "px-3 py-2.5 text-[13px]";

  const toggleSidebar = () => {
    if (isAnalyticsRoute || isWelcomePage) {
      setIsManualExpanded(!isManualExpanded);
    } else {
      setIsManualCollapsed(!isManualCollapsed);
    }
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
      style={{ transition: 'width 480ms cubic-bezier(0.65,0,0.35,1), transform 300ms cubic-bezier(0.4,0,0.2,1)' }}
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
        <ChevronLeft className={cn("h-3.5 w-3.5", isCollapsed && "rotate-180")} style={{ transition: 'transform 480ms cubic-bezier(0.65,0,0.35,1)' }} strokeWidth={2.5} />
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
      <motion.div variants={itemVariants} className={cn("flex h-[72px] shrink-0 items-center border-b border-border/40 mb-2 transition-all duration-400", isCollapsed ? "px-0 justify-center max-lg:px-6 max-lg:justify-start" : "px-6")}>
        <Link href="/" className="flex items-center text-foreground font-semibold text-[15px] tracking-wide" title="Numerate">
          <AnimatedLogo />
          <div className={cn(
            "overflow-hidden whitespace-nowrap flex items-center",
            isCollapsed
              ? "max-w-0 opacity-0 ml-0 max-lg:max-w-[120px] max-lg:opacity-100 max-lg:ml-3"
              : "max-w-[120px] opacity-100 ml-3"
          )} style={{ transition: 'max-width 420ms cubic-bezier(0.65,0,0.35,1), opacity 300ms ease, margin-left 420ms cubic-bezier(0.65,0,0.35,1)' }}>
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
                <div className={cn("overflow-hidden whitespace-nowrap", railLabel)} style={{ transition: 'max-width 420ms cubic-bezier(0.65,0,0.35,1), opacity 300ms ease, margin-left 420ms cubic-bezier(0.65,0,0.35,1)' }}>
                  {item.name}
                </div>
              </Link>
            </motion.div>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className={cn("mt-auto border-t border-border/40 p-3 space-y-0.5 transition-all duration-400", isCollapsed && "flex flex-col items-center p-2 max-lg:block max-lg:p-3")}>
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
              <div className={cn("overflow-hidden whitespace-nowrap", railLabel)} style={{ transition: 'max-width 420ms cubic-bezier(0.65,0,0.35,1), opacity 300ms ease, margin-left 420ms cubic-bezier(0.65,0,0.35,1)' }}>
                {item.name}
              </div>
            </Link>
          </motion.div>
        ))}

        {/* User Profile */}
        <motion.div variants={itemVariants} className="pt-2 mt-2 border-t border-border/40 w-full">
          <div className={cn(
            "flex items-center rounded-xl hover:bg-white/[0.03] transition-colors duration-200 group",
            isCollapsed
              ? "justify-center py-2 px-0 flex-col max-lg:justify-between max-lg:flex-row max-lg:px-3 max-lg:py-2.5"
              : "justify-between px-3 py-2.5"
          )}>
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
              )} style={{ transition: 'max-width 420ms cubic-bezier(0.65,0,0.35,1), opacity 300ms ease, margin-left 420ms cubic-bezier(0.65,0,0.35,1)' }}>
                <span className="text-[13px] font-semibold text-foreground/90 group-hover:text-foreground transition-colors truncate">{user?.full_name || "Guest"}</span>
              </div>
            </Link>
            <button onClick={() => setShowLogoutConfirm(true)} className={cn(
                "p-1 hover:text-destructive transition-colors duration-200 text-muted-foreground/70",
                isCollapsed ? "mt-2 max-lg:mt-0" : "group-hover:text-foreground/90"
              )} title="Logout">
              <LogOut className="h-4 w-4 shrink-0" />
            </button>
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


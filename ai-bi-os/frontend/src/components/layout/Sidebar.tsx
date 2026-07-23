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
  const { isWelcomeActive } = useLayoutStore();
  const [isManualCollapsed, setIsManualCollapsed] = useState(false);
  const [isManualExpanded, setIsManualExpanded] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const isAnalyticsRoute = pathname?.startsWith("/analytics") ?? false;
  const isWelcomePage = pathname === "/" && isWelcomeActive;
  
  const isCollapsed = (isAnalyticsRoute || isWelcomePage) ? !isManualExpanded : isManualCollapsed;

  const toggleSidebar = () => {
    if (isAnalyticsRoute || isWelcomePage) {
      setIsManualExpanded(!isManualExpanded);
    } else {
      setIsManualCollapsed(!isManualCollapsed);
    }
  };

  return (
    <>
    <motion.div
      initial="hidden"
      animate="show"
      variants={sidebarVariants}
      style={{ transition: 'width 480ms cubic-bezier(0.65,0,0.35,1)' }}
      className={cn(
      "relative flex h-screen flex-col border-r border-border/60 bg-surface/40 text-text-secondary shrink-0 z-20",
      isCollapsed ? "w-[64px]" : "w-[260px]"
    )}>
      {/* Floating Toggle Button */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-[24px] flex h-6 w-6 items-center justify-center rounded-full bg-[#11131a] border border-border text-muted-foreground shadow-[0_0_10px_rgba(0,0,0,0.5)] hover:bg-white/[0.1] hover:text-foreground z-50 transition-all duration-200"
        title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
      >
        <ChevronLeft className={cn("h-3.5 w-3.5", isCollapsed && "rotate-180")} style={{ transition: 'transform 480ms cubic-bezier(0.65,0,0.35,1)' }} strokeWidth={2.5} />
      </button>

      {/* Brand / Logo */}
      <motion.div variants={itemVariants} className={cn("flex h-[72px] shrink-0 items-center border-b border-border/40 mb-2 transition-all duration-400", isCollapsed ? "px-0 justify-center" : "px-6")}>
        <Link href="/" className="flex items-center text-foreground font-semibold text-[15px] tracking-wide" title="DataMind">
          <AnimatedLogo />
          <div className={cn(
            "overflow-hidden whitespace-nowrap flex items-center",
            isCollapsed ? "max-w-0 opacity-0 ml-0" : "max-w-[120px] opacity-100 ml-3"
          )} style={{ transition: 'max-width 420ms cubic-bezier(0.65,0,0.35,1), opacity 300ms ease, margin-left 420ms cubic-bezier(0.65,0,0.35,1)' }}>
            <span>DataMind</span>
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
                  isCollapsed ? "justify-center h-10 w-10 mx-auto" : "px-3 py-2.5 text-[13px]",
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
                <div className={cn(
                  "overflow-hidden whitespace-nowrap",
                  isCollapsed ? "max-w-0 opacity-0 ml-0" : "max-w-[200px] opacity-100 ml-3"
                )} style={{ transition: 'max-width 420ms cubic-bezier(0.65,0,0.35,1), opacity 300ms ease, margin-left 420ms cubic-bezier(0.65,0,0.35,1)' }}>
                  {item.name}
                </div>
              </Link>
            </motion.div>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className={cn("mt-auto border-t border-border/40 p-3 space-y-0.5 transition-all duration-400", isCollapsed && "flex flex-col items-center p-2")}>
        {bottomNavItems.map((item) => (
          <motion.div key={item.name} variants={itemVariants}>
            <Link
              href={item.href}
              title={isCollapsed ? item.name : undefined}
              className={cn(
                "group flex items-center rounded-xl font-medium text-muted-foreground/90 transition-colors duration-200 hover:bg-white/[0.03] hover:text-foreground",
                isCollapsed ? "justify-center h-10 w-10 mx-auto" : "px-3 py-2.5 text-[13px]"
              )}
            >
              <item.icon className="h-[18px] w-[18px] shrink-0 text-muted-foreground/70 group-hover:text-foreground/90 transition-colors" />
              <div className={cn(
                "overflow-hidden whitespace-nowrap",
                isCollapsed ? "max-w-0 opacity-0 ml-0" : "max-w-[200px] opacity-100 ml-3"
              )} style={{ transition: 'max-width 420ms cubic-bezier(0.65,0,0.35,1), opacity 300ms ease, margin-left 420ms cubic-bezier(0.65,0,0.35,1)' }}>
                {item.name}
              </div>
            </Link>
          </motion.div>
        ))}

        {/* User Profile */}
        <motion.div variants={itemVariants} className="pt-2 mt-2 border-t border-border/40 w-full">
          <div className={cn(
            "flex items-center rounded-xl hover:bg-white/[0.03] transition-colors duration-200 group",
            isCollapsed ? "justify-center py-2 px-0 flex-col" : "justify-between px-3 py-2.5"
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
                isCollapsed ? "max-w-0 opacity-0 ml-0" : "max-w-[150px] opacity-100 ml-3"
              )} style={{ transition: 'max-width 420ms cubic-bezier(0.65,0,0.35,1), opacity 300ms ease, margin-left 420ms cubic-bezier(0.65,0,0.35,1)' }}>
                <span className="text-[13px] font-semibold text-foreground/90 group-hover:text-foreground transition-colors truncate">{user?.full_name || "Guest"}</span>
              </div>
            </Link>
            <button onClick={() => setShowLogoutConfirm(true)} className={cn(
                "p-1 hover:text-destructive transition-colors duration-200 text-muted-foreground/70",
                isCollapsed ? "mt-2" : "group-hover:text-foreground/90"
              )} title="Logout">
              <LogOut className="h-4 w-4 shrink-0" />
            </button>
          </div>
        </motion.div>
      </div>
    </motion.div>

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


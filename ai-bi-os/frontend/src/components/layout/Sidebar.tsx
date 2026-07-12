"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import {
  LayoutDashboard,
  Database,
  MessageSquare,
  Lightbulb,
  Layers,
  Network,
  GitBranch,
  Settings,
  CreditCard,
  Shield,
  Zap,
  User,
  MoreVertical,
  BarChart3,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

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
  { name: "Billing", href: "/billing", icon: CreditCard },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [isManualCollapsed, setIsManualCollapsed] = useState(false);
  const isAnalyticsRoute = pathname?.startsWith("/analytics") ?? false;
  const isCollapsed = isAnalyticsRoute || isManualCollapsed;

  return (
    <div className={cn(
      "relative flex h-screen flex-col border-r border-border/60 bg-surface/40 text-text-secondary shrink-0 transition-all duration-300 z-20",
      isCollapsed ? "w-[64px]" : "w-[260px]"
    )}>
      {/* Floating Toggle Button */}
      {!isAnalyticsRoute && (
        <button
          onClick={() => setIsManualCollapsed(!isManualCollapsed)}
          className="absolute -right-3 top-[24px] flex h-6 w-6 items-center justify-center rounded-full bg-[#11131a] border border-border text-muted-foreground shadow-[0_0_10px_rgba(0,0,0,0.5)] hover:bg-white/[0.1] hover:text-foreground z-50 transition-all duration-200"
          title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {isCollapsed ? <ChevronRight className="h-3.5 w-3.5" strokeWidth={2.5} /> : <ChevronLeft className="h-3.5 w-3.5" strokeWidth={2.5} />}
        </button>
      )}

      {/* Brand / Logo */}
      <div className={cn("flex h-[72px] shrink-0 items-center border-b border-border/40 mb-2", isCollapsed ? "px-0 justify-center" : "px-6")}>
        <Link href="/" className="flex items-center gap-3 text-foreground font-semibold text-[15px] tracking-wide" title="DataMind">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#0c1e3e] border border-[#1a3b70] shadow-[0_0_15px_rgba(0,112,243,0.2)] shrink-0">
            <Layers className="h-4 w-4 text-[#3b82f6]" strokeWidth={2.5} />
          </div>
          {!isCollapsed && <span>DataMind</span>}
        </Link>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 space-y-0.5 px-3 py-2 overflow-y-auto overflow-x-hidden [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        {mainNavItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              title={isCollapsed ? item.name : undefined}
              className={cn(
                "group relative flex items-center rounded-xl font-medium transition-all duration-200",
                isCollapsed ? "justify-center h-10 w-10 mx-auto" : "gap-3 px-3 py-2.5 text-[13px]",
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
              {!isCollapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className={cn("mt-auto border-t border-border/40 p-3 space-y-0.5", isCollapsed && "flex flex-col items-center p-2")}>
        {bottomNavItems.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            title={isCollapsed ? item.name : undefined}
            className={cn(
              "group flex items-center rounded-xl font-medium text-muted-foreground/90 transition-all duration-200 hover:bg-white/[0.03] hover:text-foreground",
              isCollapsed ? "justify-center h-10 w-10 mx-auto" : "gap-3 px-3 py-2.5 text-[13px]"
            )}
          >
            <item.icon className="h-[18px] w-[18px] shrink-0 text-muted-foreground/70 group-hover:text-foreground/90 transition-colors" />
            {!isCollapsed && <span>{item.name}</span>}
          </Link>
        ))}

        {/* User Profile */}
        <div className="pt-2 mt-2 border-t border-border/40 w-full">
          <div className={cn(
            "flex items-center rounded-xl hover:bg-white/[0.03] cursor-pointer transition-colors duration-200 group",
            isCollapsed ? "justify-center py-2 px-0 flex-col" : "justify-between px-3 py-2.5"
          )} title={isCollapsed ? (user?.full_name || "User") : undefined}>
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-primary border border-primary/30 shrink-0">
                <User className="h-4 w-4" />
              </div>
              {!isCollapsed && (
                <div className="flex flex-col overflow-hidden">
                  <span className="text-[13px] font-semibold text-foreground/90 group-hover:text-foreground transition-colors truncate">{user?.full_name || "Guest"}</span>
                  <span className="text-[11px] text-muted-foreground tracking-wide font-medium truncate w-24">{user?.email || "guest@example.com"}</span>
                </div>
              )}
            </div>
            {!isCollapsed && (
              <button onClick={logout} className="p-1 hover:text-destructive transition-colors text-muted-foreground/70 group-hover:text-foreground/90" title="Logout">
                <LogOut className="h-4 w-4 shrink-0" />
              </button>
            )}
            {isCollapsed && (
              <button onClick={logout} className="p-1 hover:text-destructive transition-colors text-muted-foreground/70 mt-2" title="Logout">
                <LogOut className="h-4 w-4 shrink-0" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

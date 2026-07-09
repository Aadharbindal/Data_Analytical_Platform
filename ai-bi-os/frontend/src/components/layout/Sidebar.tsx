"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Database,
  MessageSquare,
  Lightbulb,
  Network,
  GitBranch,
  Settings,
  CreditCard,
  Shield,
  Zap,
  User,
  MoreVertical,
  BarChart3,
} from "lucide-react";

const mainNavItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Datasets", href: "/datasets", icon: Database },
  { name: "Data Catalog", href: "/data-catalog", icon: Network },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Insights", href: "/insights", icon: Lightbulb },
  { name: "Rules & Decisions", href: "/rules", icon: GitBranch },
  { name: "Recommendations", href: "/recommendations", icon: Zap },
  { name: "Privacy & Governance", href: "/privacy", icon: Shield },
  { name: "AI Chat", href: "/chat", icon: MessageSquare },
];

const bottomNavItems = [
  { name: "Settings", href: "/settings", icon: Settings },
  { name: "Billing", href: "/billing", icon: CreditCard },
];

export function Sidebar() {
  const pathname = usePathname();
  const isAnalytics = pathname?.startsWith("/analytics") ?? false;

  return (
    <div className={cn(
      "flex h-screen flex-col border-r border-border/60 bg-surface/40 text-text-secondary shrink-0 transition-all duration-300",
      isAnalytics ? "w-[64px]" : "w-[260px]"
    )}>
      {/* Brand / Logo */}
      <div className={cn("flex h-[72px] shrink-0 items-center border-b border-border/40 mb-2", isAnalytics ? "px-0 justify-center" : "px-6")}>
        <Link href="/" className="flex items-center gap-3 text-foreground font-semibold text-[15px] tracking-wide" title="DataMind OS">
          <div className="flex h-7 w-7 items-center justify-center rounded-[8px] bg-primary text-primary-foreground shadow-[0_0_12px_rgba(0,112,243,0.4)] shrink-0">
            <LayoutDashboard className="h-4 w-4" />
          </div>
          {!isAnalytics && <span>DataMind OS</span>}
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
              title={isAnalytics ? item.name : undefined}
              className={cn(
                "group relative flex items-center rounded-xl font-medium transition-all duration-200",
                isAnalytics ? "justify-center h-10 w-10 mx-auto" : "gap-3 px-3 py-2.5 text-[13px]",
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
              {!isAnalytics && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className={cn("mt-auto border-t border-border/40 p-3 space-y-0.5", isAnalytics && "flex flex-col items-center p-2")}>
        {bottomNavItems.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            title={isAnalytics ? item.name : undefined}
            className={cn(
              "group flex items-center rounded-xl font-medium text-muted-foreground/90 transition-all duration-200 hover:bg-white/[0.03] hover:text-foreground",
              isAnalytics ? "justify-center h-10 w-10 mx-auto" : "gap-3 px-3 py-2.5 text-[13px]"
            )}
          >
            <item.icon className="h-[18px] w-[18px] shrink-0 text-muted-foreground/70 group-hover:text-foreground/90 transition-colors" />
            {!isAnalytics && <span>{item.name}</span>}
          </Link>
        ))}

        {/* User Profile */}
        <div className="pt-2 mt-2 border-t border-border/40 w-full">
          <div className={cn(
            "flex items-center rounded-xl hover:bg-white/[0.03] cursor-pointer transition-colors duration-200 group",
            isAnalytics ? "justify-center py-2 px-0" : "justify-between px-3 py-2.5"
          )} title={isAnalytics ? "Wade Warren (Admin)" : undefined}>
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-primary border border-primary/30 shrink-0">
                <User className="h-4 w-4" />
              </div>
              {!isAnalytics && (
                <div className="flex flex-col overflow-hidden">
                  <span className="text-[13px] font-semibold text-foreground/90 group-hover:text-foreground transition-colors truncate">Wade Warren</span>
                  <span className="text-[11px] text-muted-foreground tracking-wide uppercase font-medium">Admin</span>
                </div>
              )}
            </div>
            {!isAnalytics && <MoreVertical className="h-4 w-4 shrink-0 text-muted-foreground/70 group-hover:text-foreground/90 transition-colors" />}
          </div>
        </div>
      </div>
    </div>
  );
}

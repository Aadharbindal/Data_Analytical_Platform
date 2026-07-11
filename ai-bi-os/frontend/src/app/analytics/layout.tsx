"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  BarChart, Activity, PieChart, Network, 
  Sigma, Calculator, CheckCircle, AlignEndVertical,
  AlertTriangle, Clock, TrendingUp, LineChart
} from "lucide-react";

const NAV_GROUPS = [
  {
    title: "Overview",
    items: [
      { name: "Dashboard", href: "/analytics", icon: BarChart },
      { name: "KPI Center", href: "/analytics/kpi", icon: Activity },
      { name: "Metrics Explorer", href: "/analytics/metrics", icon: PieChart },
    ]
  },
  {
    title: "Explore",
    items: [
      { name: "Dataset Analysis", href: "/analytics/eda", icon: AlignEndVertical },
      { name: "Distribution", href: "/analytics/distribution", icon: AlignEndVertical },
      { name: "Outliers", href: "/analytics/outliers", icon: AlertTriangle },
    ]
  },
  {
    title: "Statistical",
    items: [
      { name: "Statistics", href: "/analytics/statistics", icon: Sigma },
      { name: "Correlation", href: "/analytics/correlation", icon: Network },
      { name: "Regression", href: "/analytics/regression", icon: Calculator },
    ]
  },
  {
    title: "Advanced",
    items: [
      { name: "Time Series", href: "/analytics/timeseries", icon: Clock },
      { name: "Trend Analysis", href: "/analytics/trend", icon: TrendingUp },
      { name: "Forecast", href: "/analytics/forecast", icon: LineChart },
      { name: "Confidence Center", href: "/analytics/confidence", icon: CheckCircle },
    ]
  }
];

export default function AnalyticsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-[200px] border-r border-border/40 bg-surface/30 backdrop-blur-xl flex flex-col h-full z-10 shrink-0">
        <div className="p-4 border-b border-white/[0.02]">
          <h2 className="text-[13px] font-semibold tracking-tight text-foreground/90">Analytics Studio</h2>
        </div>
        
        <nav className="flex-1 overflow-y-auto py-3 space-y-4">
          {NAV_GROUPS.map((group) => (
            <div key={group.title} className="px-3">
              <h3 className="px-2 mb-1.5 text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase">
                {group.title}
              </h3>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = pathname === item.href;
                  const Icon = item.icon;
                  
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={`group flex items-center gap-2.5 px-2 py-1.5 rounded-md text-[12px] font-medium transition-all duration-200 relative ${
                        isActive 
                          ? "bg-primary/[0.08] text-primary" 
                          : "text-muted-foreground/80 hover:bg-white/[0.04] hover:text-foreground"
                      }`}
                    >
                      {isActive && (
                        <div className="absolute left-[-12px] top-1/2 -translate-y-1/2 w-0.5 h-4 bg-primary rounded-r-full" />
                      )}
                      <Icon className={`h-3.5 w-3.5 shrink-0 ${isActive ? "text-primary" : "text-muted-foreground/60 group-hover:text-foreground/80"}`} />
                      <span className="truncate">{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 h-full overflow-hidden bg-background">
        {children}
      </main>
    </div>
  );
}

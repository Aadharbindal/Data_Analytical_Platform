"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  BarChart, Activity, PieChart, Network, 
  Sigma, Calculator, CheckCircle, AlignEndVertical,
  AlertTriangle, Clock, TrendingUp, LineChart
} from "lucide-react";

const NAV_ITEMS = [
  { name: "Dashboard", href: "/analytics", icon: BarChart },
  { name: "KPI Center", href: "/analytics/kpi", icon: Activity },
  { name: "Metrics Explorer", href: "/analytics/metrics", icon: PieChart },
  { name: "Dataset Analysis (EDA)", href: "/analytics/eda", icon: AlignEndVertical },
  { name: "Correlation Studio", href: "/analytics/correlation", icon: Network },
  { name: "Statistical Analysis", href: "/analytics/statistics", icon: Sigma },
  { name: "Regression Models", href: "/analytics/regression", icon: Calculator },
  { name: "Confidence Center", href: "/analytics/confidence", icon: CheckCircle },
  { name: "Distribution Explorer", href: "/analytics/distribution", icon: AlignEndVertical },
  { name: "Outlier Explorer", href: "/analytics/outliers", icon: AlertTriangle },
  { name: "Time Series", href: "/analytics/timeseries", icon: Clock },
  { name: "Trend Analysis", href: "/analytics/trend", icon: TrendingUp },
  { name: "Forecast Center", href: "/analytics/forecast", icon: LineChart },
  { name: "Forecast Governance", href: "/analytics/governance", icon: CheckCircle },
];

export default function AnalyticsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-border/40 bg-surface/50 backdrop-blur-xl flex flex-col h-full z-10 shrink-0">
        <div className="p-6">
          <h2 className="text-lg font-semibold tracking-tight">Analytics Studio</h2>
          <p className="text-xs text-muted-foreground mt-1">Enterprise Intelligence</p>
        </div>
        
        <nav className="flex-1 overflow-y-auto px-4 pb-6 space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive 
                    ? "bg-primary/15 text-primary shadow-sm" 
                    : "text-muted-foreground hover:bg-white/[0.04] hover:text-foreground"
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? "text-primary" : "text-muted-foreground/70"}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 h-full overflow-y-auto">
        <div className="p-8 max-w-7xl mx-auto h-full">
          {children}
        </div>
      </main>
    </div>
  );
}

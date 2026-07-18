"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  BarChart, Activity, PieChart, Network, 
  Sigma, Calculator, CheckCircle, AlignEndVertical,
  AlertTriangle, Clock, TrendingUp, LineChart,
  ChevronLeft, ChevronRight
} from "lucide-react";
import { motion } from "framer-motion";

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
      { name: "Confidence Center", href: "/analytics/confidence", icon: CheckCircle },
    ]
  }
];

const sidebarVariants = {
  hidden: { opacity: 0, x: -16 },
  show: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.5,
      ease: [0.25, 1, 0.5, 1],
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
      ease: [0.25, 1, 0.5, 1]
    }
  }
};

export default function AnalyticsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = React.useState(false);

  return (
    <div className="flex h-full bg-background text-foreground overflow-hidden">
      {/* Sidebar Navigation */}
      <motion.aside 
        initial="hidden"
        animate="show"
        variants={sidebarVariants}
        className={`border-r border-border/40 bg-surface/30 backdrop-blur-xl flex flex-col h-full z-10 shrink-0 relative transition-all duration-300 ${isCollapsed ? 'w-[60px]' : 'w-[200px]'}`}
      >
        
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-3 top-6 z-20 flex h-6 w-6 items-center justify-center rounded-full border border-border/50 bg-background text-muted-foreground shadow-sm hover:text-foreground hover:bg-surface/80"
        >
          {isCollapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
        </button>

        <nav className="flex-1 overflow-y-auto py-3 space-y-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          {NAV_GROUPS.map((group) => (
            <div key={group.title} className="px-3">
              {!isCollapsed ? (
                <motion.h3 variants={itemVariants} className="px-2 mb-1.5 text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase">
                  {group.title}
                </motion.h3>
              ) : (
                <div className="h-4 mb-1.5" />
              )}
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = pathname === item.href;
                  const Icon = item.icon;
                  return (
                    <motion.div key={item.name} variants={itemVariants}>
                      <Link
                        href={item.href}
                        title={isCollapsed ? item.name : undefined}
                        className={`group flex items-center gap-2.5 px-2 py-1.5 rounded-md text-[12px] font-medium transition-all duration-200 relative ${
                          isActive 
                            ? "bg-primary/[0.08] text-primary" 
                            : "text-muted-foreground/80 hover:bg-white/[0.04] hover:text-foreground"
                        } ${isCollapsed ? 'justify-center px-0' : ''}`}
                      >
                        {isActive && (
                          <div className={`absolute left-[-12px] top-1/2 -translate-y-1/2 w-0.5 h-4 bg-primary rounded-r-full ${isCollapsed ? 'left-[-12px]' : ''}`} />
                        )}
                        <Icon className={`h-3.5 w-3.5 shrink-0 ${isActive ? "text-primary" : "text-muted-foreground/60 group-hover:text-foreground/80"}`} />
                        {!isCollapsed && <span className="truncate">{item.name}</span>}
                      </Link>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </motion.aside>

      {/* Main Content Area */}
      <main className="flex-1 h-full overflow-y-auto bg-background relative">
        {children}
      </main>
    </div>
  );
}

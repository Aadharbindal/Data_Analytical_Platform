"use client";

import React from "react";
import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, CreditCard, Users, AlertTriangle, Calendar, Store, Lightbulb, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface InsightPanelProps {
  title: string;
  severity: "high" | "medium" | "low";
  confidence: number;
  impact?: number | string;
  description: string;
  category: string;
  verified?: boolean;
  index?: number;
}

function formatImpact(val: number | string | undefined | null, title: string): string {
  if (val === undefined || val === null) return "N/A";
  if (typeof val === "string") {
    const trimmed = val.trim();
    if (trimmed === "" || trimmed.toLowerCase() === "n/a" || trimmed.toLowerCase() === "null") return "N/A";
    return trimmed;
  }
  if (isNaN(val as number)) return "N/A";

  const isCount = /count|transactions|volume|number of/i.test(title);
  const isAverage = /average|avg/i.test(title);
  const isRate = /rate|percentage/i.test(title);

  if (isRate) {
    return `${val.toFixed(1)}%`;
  }

  if (isCount) {
    if (val >= 10_000_000) return `${(val / 10_000_000).toFixed(1)}Cr`;
    if (val >= 100_000) return `${(val / 100_000).toFixed(1)}L`;
    if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
    return `${val.toLocaleString('en-IN')}`;
  }

  const useDollar = title.includes('$');
  // Changed to always default to ₹ for INR datasets
  const symbol = useDollar ? '$' : '₹';

  let formatted = "";
  if (val >= 10_000_000) {
    formatted = `${symbol}${(val / 10_000_000).toFixed(1)}Cr`;
  } else if (val >= 100_000) {
    formatted = `${symbol}${(val / 100_000).toFixed(1)}L`;
  } else if (val >= 1_000) {
    formatted = `${symbol}${(val / 1_000).toFixed(1)}K`;
  } else {
    formatted = `${symbol}${val.toLocaleString('en-IN')}`;
  }

  if (isAverage) {
    return `${formatted} Avg`;
  }
  return formatted;
}

export function InsightPanel({ title, severity, confidence, impact, description, category, verified = true, index = 0 }: InsightPanelProps) {
  const delayMs = 150 + index * 110;

  const getCategoryIcon = () => {
    const cat = category?.toLowerCase();
    if (cat === "trend") return <TrendingUp className="h-full w-full" />;
    if (cat === "opportunity") return <CreditCard className="h-full w-full" />;
    if (cat === "anomaly" || cat === "risk") return <AlertTriangle className="h-full w-full" />;

    // Fallbacks based on title
    const text = title.toLowerCase();
    if (text.includes("trend") || text.includes("growth")) {
      return <TrendingUp className="h-full w-full" />;
    }
    if (text.includes("payment") || text.includes("transaction") || text.includes("spend") || text.includes("upi")) {
      return <CreditCard className="h-full w-full" />;
    }
    if (text.includes("customer") || text.includes("user") || text.includes("payer") || text.includes("payee")) {
      return <Users className="h-full w-full" />;
    }
    if (text.includes("risk") || text.includes("anomaly") || text.includes("fail") || text.includes("drop") || text.includes("loss")) {
      return <AlertTriangle className="h-full w-full" />;
    }
    if (text.includes("time") || text.includes("month") || text.includes("date")) {
      return <Calendar className="h-full w-full" />;
    }
    if (text.includes("merchant") || text.includes("store")) {
      return <Store className="h-full w-full" />;
    }

    // Defaults based on other possible category terms
    if (cat?.includes("user") || cat?.includes("customer")) return <Users className="h-full w-full" />;
    if (cat?.includes("time") || cat?.includes("date") || cat?.includes("calendar")) return <Calendar className="h-full w-full" />;
    if (cat?.includes("store") || cat?.includes("merchant")) return <Store className="h-full w-full" />;

    return <Lightbulb className="h-full w-full" />;
  };

  const getTheme = () => {
    const text = `${category} ${title}`.toLowerCase();
    if (text.includes("risk") || text.includes("anomaly") || text.includes("fail") || text.includes("drop")) {
      return {
        accent: "#f87171",
        glow: "rgba(248, 113, 113, 0.35)",
        border: "border-red-500/25 group-hover:border-red-500/45",
        iconBg: "bg-red-500/15",
        iconRing: "border-red-400/40",
        iconColor: "text-red-400",
        badge: "bg-red-500/15 text-red-300 border-red-500/25",
        bar: "from-red-500 to-red-600",
      };
    }
    if (category?.toLowerCase() === "opportunity") {
      return {
        accent: "#fbbf24",
        glow: "rgba(251, 191, 36, 0.35)",
        border: "border-amber-500/25 group-hover:border-amber-500/45",
        iconBg: "bg-amber-500/15",
        iconRing: "border-amber-400/40",
        iconColor: "text-amber-400",
        badge: "bg-amber-500/15 text-amber-300 border-amber-500/25",
        bar: "from-amber-500 to-amber-600",
      };
    }
    return {
      accent: "#60a5fa",
      glow: "rgba(96, 165, 250, 0.35)",
      border: "border-blue-500/25 group-hover:border-blue-500/45",
      iconBg: "bg-blue-500/15",
      iconRing: "border-blue-400/40",
      iconColor: "text-blue-400",
      badge: "bg-blue-500/15 text-blue-300 border-blue-500/25",
      bar: "from-blue-500 to-blue-600",
    };
  };
  const theme = getTheme();

  const renderDescription = () => {
    if (!description) return null;

    const lines = description.split("\n").map(l => l.trim()).filter(Boolean);

    if (lines.length > 1) {
      const stats: { label: string; value: string }[] = [];
      const findings: string[] = [];

      lines.forEach(line => {
        if (line.includes(":") && !line.toLowerCase().startsWith("finding:")) {
          const parts = line.split(":");
          const label = parts[0].trim();
          const value = parts.slice(1).join(":").trim();
          stats.push({ label, value });
        } else {
          const cleanLine = line.toLowerCase().startsWith("finding:")
            ? line.substring(8).trim()
            : line.replace(/^-\s*/, '').trim();
          findings.push(cleanLine);
        }
      });

      return (
        <div className="flex flex-col gap-3 w-full">
          {stats.length > 0 && (
            <div className="grid grid-cols-2 gap-3 bg-background/40 rounded-xl p-3 border border-border/30 shadow-sm">
              {stats.map((stat, idx) => (
                <div key={idx} className="flex flex-col">
                  <span className="text-[10px] text-muted-foreground uppercase font-medium tracking-wider">{stat.label}</span>
                  <span className="text-xs font-semibold text-foreground/90 mt-0.5">{stat.value}</span>
                </div>
              ))}
            </div>
          )}
          {findings.length > 0 && (
            <div className="flex flex-col gap-1 border-t border-border/20 pt-2">
              <span className="text-[9px] uppercase tracking-widest font-semibold text-muted-foreground/50 mb-1">Finding</span>
              <div className="bg-primary/5 border-l-2 border-primary rounded-r-xl p-3 text-[12px] text-foreground/90 leading-relaxed font-medium">
                {findings.join(" ")}
              </div>
            </div>
          )}
        </div>
      );
    }

    return (
      <p className="text-[13px] text-muted-foreground leading-relaxed">
        {description}
      </p>
    );
  };

  const confidencePct = Number(confidence) || 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 400, damping: 28, delay: delayMs / 1000 }}
      className="group h-full relative overflow-hidden rounded-[20px]"
    >
      <Card
        className={cn(
          "glass-card relative overflow-hidden hover:bg-surface/90 transition-colors duration-300 flex flex-col h-full rounded-[20px] border",
          theme.border
        )}
        style={{ boxShadow: `0 0 28px -16px ${theme.glow}` }}
      >
        {/* Glow Sweep */}
        <motion.div
          initial={{ x: "-120%" }}
          animate={{ x: "220%" }}
          transition={{ duration: 1.1, ease: "easeOut", delay: (delayMs + 250) / 1000 }}
          className="absolute top-0 bottom-0 w-[60%] pointer-events-none z-0"
          style={{ background: "linear-gradient(100deg, transparent, rgba(255,255,255,0.05), transparent)" }}
        />

        <CardHeader className="relative z-10 flex flex-row items-start space-y-0 pb-3 pt-5 px-5">
          <div className="flex items-center gap-3">
            <div className="relative flex h-12 w-12 shrink-0 items-center justify-center">
              <motion.span
                className={cn("absolute inset-0 rounded-full", theme.iconBg)}
                animate={{ scale: [1, 1.2, 1], opacity: [0.55, 0.15, 0.55] }}
                transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut", delay: delayMs / 1000 }}
              />
              <motion.div
                initial={{ scale: 0.5, opacity: 0, rotate: -10 }}
                animate={{ scale: 1, opacity: 1, rotate: 0 }}
                transition={{ type: "spring", stiffness: 380, damping: 18, delay: (delayMs + 120) / 1000 }}
                className={cn(
                  "relative flex h-10 w-10 items-center justify-center rounded-full border p-2.5",
                  theme.iconBg,
                  theme.iconRing,
                  theme.iconColor
                )}
              >
                {getCategoryIcon()}
              </motion.div>
            </div>
            <div className="flex flex-col gap-1.5 items-start">
              <Badge
                variant="outline"
                className={cn(
                  "uppercase font-bold text-[9px] tracking-wider py-0.5 px-2 rounded-full",
                  theme.badge
                )}
              >
                {category || "Insight"}
              </Badge>
              <CardTitle className="text-[14px] font-semibold text-foreground/95 tracking-tight leading-snug">{title}</CardTitle>
            </div>
          </div>
        </CardHeader>
        <CardContent className="relative z-10 flex-1 flex flex-col justify-between px-5 pb-5 pt-0">
          <div className="mb-4">
            {renderDescription()}
          </div>

          <div>
            <div className="flex items-center justify-between pt-3 border-t border-border/40 mt-auto">
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-widest font-semibold text-muted-foreground/50 mb-0.5">Business Impact</span>
                <span className="text-xs font-bold text-foreground tabular-metrics">
                  {formatImpact(impact, title)}
                </span>
              </div>

              <div className="flex flex-col items-end">
                <span className="text-[9px] uppercase tracking-widest font-semibold text-muted-foreground/50 mb-0.5">Confidence</span>
                <Badge variant="outline" className="mt-0.5 bg-background/50 tabular-metrics border-border/50 text-foreground/80 rounded-full px-2 py-0 text-[10px]">
                  {confidencePct}%
                </Badge>
              </div>
            </div>

            <div className="mt-2.5 h-2 w-full overflow-hidden rounded-full bg-white/[0.06] ring-1 ring-white/5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${confidencePct}%` }}
                transition={{ duration: 0.9, ease: "easeOut", delay: (delayMs + 350) / 1000 }}
                className={cn("relative h-full min-w-[6px] overflow-hidden rounded-full bg-gradient-to-r", theme.bar)}
                style={{ boxShadow: `0 0 10px -1px ${theme.glow}` }}
              >
                <span className="absolute inset-x-0 top-0 h-1/2 rounded-full bg-white/25" />
                <motion.span
                  className="absolute inset-y-0 w-10 -skew-x-12 bg-gradient-to-r from-transparent via-white/50 to-transparent"
                  initial={{ x: "-120%" }}
                  animate={{ x: "220%" }}
                  transition={{ duration: 1.3, ease: "easeOut", delay: (delayMs + 700) / 1000 }}
                />
              </motion.div>
            </div>
          </div>

          {verified && (
            <div className="flex items-center gap-1.5 pt-2.5 mt-2 border-t border-border/20">
              <CheckCircle className="h-3.5 w-3.5 text-success" />
              <span className="text-[11px] text-success font-medium">SQL Verified</span>
            </div>
          )}

        </CardContent>
      </Card>
    </motion.div>
  );
}

"use client";

import React from "react";
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
}

function formatImpact(val: number | string | undefined | null, title: string): string {
  if (val === undefined || val === null) return "N/A";
  if (typeof val === "string") {
    const trimmed = val.trim();
    if (trimmed === "" || trimmed.toLowerCase() === "n/a" || trimmed.toLowerCase() === "null") return "N/A";
    return trimmed;
  }
  if (isNaN(val as any)) return "N/A";
  
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

export function InsightPanel({ title, severity, confidence, impact, description, category, verified = true }: InsightPanelProps) {
  const getCategoryIcon = () => {
    const cat = category?.toLowerCase();
    if (cat === "trend") return <TrendingUp className="h-4 w-4" />;
    if (cat === "opportunity") return <CreditCard className="h-4 w-4" />;
    if (cat === "anomaly" || cat === "risk") return <AlertTriangle className="h-4 w-4" />;
    
    // Fallbacks based on title
    const text = title.toLowerCase();
    if (text.includes("trend") || text.includes("growth")) {
      return <TrendingUp className="h-4 w-4" />;
    }
    if (text.includes("payment") || text.includes("transaction") || text.includes("spend") || text.includes("upi")) {
      return <CreditCard className="h-4 w-4" />;
    }
    if (text.includes("customer") || text.includes("user") || text.includes("payer") || text.includes("payee")) {
      return <Users className="h-4 w-4" />;
    }
    if (text.includes("risk") || text.includes("anomaly") || text.includes("fail") || text.includes("drop") || text.includes("loss")) {
      return <AlertTriangle className="h-4 w-4" />;
    }
    if (text.includes("time") || text.includes("month") || text.includes("date")) {
      return <Calendar className="h-4 w-4" />;
    }
    if (text.includes("merchant") || text.includes("store")) {
      return <Store className="h-4 w-4" />;
    }
    
    // Defaults based on other possible category terms
    if (cat?.includes("user") || cat?.includes("customer")) return <Users className="h-4 w-4" />;
    if (cat?.includes("time") || cat?.includes("date") || cat?.includes("calendar")) return <Calendar className="h-4 w-4" />;
    if (cat?.includes("store") || cat?.includes("merchant")) return <Store className="h-4 w-4" />;

    return <Lightbulb className="h-4 w-4" />;
  };

  const getBorderColor = () => {
    const text = `${category} ${title}`.toLowerCase();
    if (text.includes("risk") || text.includes("anomaly") || text.includes("fail") || text.includes("drop")) {
      return "border-error/20 text-error";
    }
    if (category?.toLowerCase() === "opportunity") {
      return "border-warning/20 text-warning";
    }
    return "border-primary/20 text-primary";
  };

  const renderDescription = () => {
    if (!description) return null;

    const lines = description.split("\n").map(l => l.trim()).filter(Boolean);

    if (lines.length > 1) {
      const stats: { label: string; value: string }[] = [];
      let findings: string[] = [];

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

  return (
    <Card className="glass-card hover:bg-surface/90 transition-all duration-300 group flex flex-col h-full rounded-[20px]">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3 pt-5 px-5">
        <div className="flex items-center gap-3">
          <div className={cn(
            "flex h-9 w-9 items-center justify-center rounded-xl bg-background/60 border",
            getBorderColor()
          )}>
            {getCategoryIcon()}
          </div>
          <div className="flex flex-col gap-1.5 items-start">
            <Badge variant="outline" className="bg-background/50 border-border/30 text-muted-foreground uppercase font-bold text-[9px] tracking-wider py-0.5 px-2 rounded-full">
              {category || "Insight"}
            </Badge>
            <CardTitle className="text-[14px] font-semibold text-foreground/95 tracking-tight leading-snug">{title}</CardTitle>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-between px-5 pb-5 pt-0">
        <div className="mb-4">
          {renderDescription()}
        </div>
        
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
              {Number(confidence) ? `${Number(confidence)}%` : '0%'}
            </Badge>
          </div>
        </div>

        {verified && (
          <div className="flex items-center gap-1.5 pt-2.5 mt-2 border-t border-border/20">
            <CheckCircle className="h-3 w-3 text-success" />
            <span className="text-[11px] text-success font-medium">SQL Verified</span>
          </div>
        )}

      </CardContent>
    </Card>
  );
}


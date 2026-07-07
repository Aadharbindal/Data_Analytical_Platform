"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Zap, AlertTriangle, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";

interface InsightPanelProps {
  title: string;
  severity: "high" | "medium" | "low";
  confidence: number;
  impact: string;
  description: string;
}

export function InsightPanel({ title, severity, confidence, impact, description }: InsightPanelProps) {
  const getSeverityIcon = () => {
    switch (severity) {
      case "high": return <ShieldAlert className="h-4 w-4 text-error" />;
      case "medium": return <AlertTriangle className="h-4 w-4 text-warning" />;
      case "low": return <Zap className="h-4 w-4 text-primary" />;
    }
  };

  return (
    <Card className="glass-card hover:bg-surface/90 transition-all duration-300 group flex flex-col h-full rounded-[20px]">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3 pt-5 px-5">
        <div className="flex items-center gap-3">
          <div className={cn(
            "flex h-9 w-9 items-center justify-center rounded-xl bg-background/60 border",
            severity === "high" && "border-error/20 text-error",
            severity === "medium" && "border-warning/20 text-warning",
            severity === "low" && "border-primary/20 text-primary"
          )}>
            {getSeverityIcon()}
          </div>
          <CardTitle className="text-[15px] font-semibold text-foreground/90 tracking-tight">{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-between px-5 pb-5 pt-0">
        <p className="text-[13px] text-muted-foreground mb-5 leading-relaxed">
          {description}
        </p>
        
        <div className="flex items-center justify-between pt-4 border-t border-border/40 mt-auto">
          <div className="flex flex-col">
            <span className="text-[10px] uppercase tracking-widest font-medium text-muted-foreground/80 mb-1">Impact</span>
            <span className={cn(
              "text-sm font-semibold tabular-metrics",
              impact.startsWith("+") ? "text-success" : impact.startsWith("-") ? "text-error" : "text-foreground"
            )}>{impact}</span>
          </div>
          
          <div className="flex flex-col items-end">
            <span className="text-[10px] uppercase tracking-widest font-medium text-muted-foreground/80 mb-1">Confidence</span>
            <Badge variant="outline" className="mt-0.5 bg-background/50 tabular-metrics border-border/50 text-foreground/80 rounded-full px-2 py-0">
              {confidence}%
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

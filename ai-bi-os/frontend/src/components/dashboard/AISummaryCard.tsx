"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Sparkles, TrendingUp, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export function AISummaryCard() {
  return (
    <Card className="glass-card h-full flex flex-col relative overflow-hidden group">
      {/* Background Gradient Effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent opacity-50 transition-opacity duration-700 group-hover:opacity-100" />
      
      <CardHeader className="pb-0 pt-5 px-6 relative z-10">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <CardTitle className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">AI Executive Summary</CardTitle>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col relative z-10 px-6 pt-4 pb-6">
        <div className="flex-1 flex items-center justify-center">
          <p className="text-[15px] leading-relaxed text-muted-foreground text-center">
            No data available for analysis.
          </p>
        </div>

        <div className="mt-6 pt-5 border-t border-border/40">
          <Button variant="ghost" className="group/btn w-full justify-between text-primary hover:text-primary hover:bg-primary/10 rounded-lg h-10 px-4 text-sm font-medium transition-all">
            Ask Copilot for deep dive
            <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover/btn:translate-x-1" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

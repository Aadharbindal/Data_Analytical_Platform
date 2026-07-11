"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Sparkles, TrendingUp, ArrowRight, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { insightsApi } from "@/lib/api";
import { useRouter } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton-loader";

export function AISummaryCard() {
  const router = useRouter();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["executiveSummary"],
    queryFn: () => insightsApi.executiveSummary(),
  });

  return (
    <Card className="glass-card h-full flex flex-col relative overflow-hidden group">
      {/* Background Gradient Effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent opacity-50 transition-opacity duration-700 group-hover:opacity-100" />
      
      <CardHeader className="pb-0 pt-5 px-6 relative z-10">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <CardTitle className="flex-1 flex items-center text-sm font-semibold tracking-wide uppercase text-muted-foreground">
            AI Executive Summary
            {data && data.verified === false && (
              <span className="text-[10px] bg-muted/50 text-muted-foreground px-1.5 py-0.5 rounded-sm ml-auto uppercase tracking-wider flex items-center gap-1">
                <AlertCircle className="h-3 w-3" /> Unverified
              </span>
            )}
          </CardTitle>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col relative z-10 px-6 pt-4 pb-6">
        <div className="flex-1 flex flex-col justify-center">
          {isLoading ? (
            <div className="space-y-3 w-full">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-11/12" />
              <Skeleton className="h-4 w-4/5" />
            </div>
          ) : isError || !data || !data.summary ? (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-[15px] leading-relaxed text-muted-foreground text-center">
                No data available for analysis.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-[15px] leading-relaxed text-foreground">
                {data.summary}
              </p>
              {data.highlights && data.highlights.length > 0 && (
                <ul className="space-y-2 mt-2">
                  {data.highlights.map((highlight: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <TrendingUp className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                      <span>{highlight}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        <div className="mt-6 pt-5 border-t border-border/40">
          <Button 
            onClick={() => {
              let question = "Give me a deeper analysis of the current dataset.";
              if (data?.facts) {
                const { metric_name, percent_change } = data.facts;
                if (metric_name && percent_change !== undefined) {
                  const direction = percent_change > 0 ? "increased" : "decreased";
                  question = `Give me a deeper analysis of why ${metric_name} ${direction} by ${Math.abs(percent_change)}% this period, and what's driving it`;
                } else if (metric_name) {
                  question = `Give me a deeper analysis of the ${metric_name} metric.`;
                }
              }
              router.push(`/chat?q=${encodeURIComponent(question)}`);
            }}
            variant="ghost" 
            className="group/btn w-full justify-between text-primary hover:text-primary hover:bg-primary/10 rounded-lg h-10 px-4 text-sm font-medium transition-all"
          >
            Ask Copilot for deep dive
            <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover/btn:translate-x-1" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

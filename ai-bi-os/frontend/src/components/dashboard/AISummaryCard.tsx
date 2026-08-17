"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Sparkles, FileText, IndianRupee, TrendingUp, TrendingDown, ArrowRight, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { insightsApi } from "@/lib/api";
import { useRouter } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton-loader";
import { detectErrorType } from "@/components/ui/error-state";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

// No `g` flag: String.split() finds all matches regardless, and a global
// flag here would make the repeated `.test()` calls below stateful across
// iterations (lastIndex carries over), silently skipping every other match.
const NUMBER_PATTERN = /(₹-?[\d,]+\.?\d*|-?[\d,]+\.?\d*%|\$-?[\d,]+\.?\d*|\b-?\d{1,3}(?:,\d{3})+(?:\.\d+)?\b)/;

function highlightNumbers(text: string): React.ReactNode[] {
  const parts = text.split(NUMBER_PATTERN);
  return parts.map((part, idx) =>
    NUMBER_PATTERN.test(part) && part.length > 0 ? (
      <span key={idx} className="font-semibold text-primary">
        {part}
      </span>
    ) : (
      <React.Fragment key={idx}>{part}</React.Fragment>
    )
  );
}

function TypewriterText({ text }: { text: string }) {
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    if (!text) return;

    setDisplayedText("");
    const words = text.split(" ");
    let currentWordIndex = 0;
    // Must live outside the setTimeout callback: a cleanup function returned
    // from inside setTimeout is discarded (only the effect's own return value
    // is honored), so without this the interval below leaks past text
    // changes/unmount and keeps writing into the next run's state.
    let intervalId: ReturnType<typeof setInterval> | undefined;

    const startDelay = setTimeout(() => {
      intervalId = setInterval(() => {
        const nextWord = words[currentWordIndex];
        // Explicit undefined check (not just the index guard) so an
        // out-of-bounds read can never get string-concatenated into
        // displayedText as the literal text "undefined".
        if (nextWord !== undefined) {
          setDisplayedText((prev) => (prev ? prev + " " + nextWord : nextWord));
          currentWordIndex++;
        } else if (intervalId) {
          clearInterval(intervalId);
        }
      }, 50);
    }, 1200);

    return () => {
      clearTimeout(startDelay);
      if (intervalId) clearInterval(intervalId);
    };
  }, [text]);

  const isTyping = displayedText !== text && displayedText.length > 0;

  return (
    <p className="text-[15px] leading-relaxed text-foreground break-words">
      {highlightNumbers(displayedText)}
      {isTyping && (
        <motion.span
          animate={{ opacity: [1, 0, 1] }}
          transition={{ duration: 0.8, repeat: Infinity }}
          className="text-primary ml-1"
        >
          ▍
        </motion.span>
      )}
    </p>
  );
}

function StatTile({
  icon: Icon,
  label,
  value,
  subLabel,
  delaySeconds,
  bordered,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  subLabel: string;
  delaySeconds: number;
  bordered?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut", delay: delaySeconds }}
      className={cn("flex min-w-0 flex-col items-center gap-1.5 px-1 text-center", bordered && "border-l border-border/40")}
    >
      <div className="relative flex h-9 w-9 shrink-0 items-center justify-center">
        <motion.span
          className="absolute inset-0 rounded-full bg-primary/15"
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.15, 0.5] }}
          transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut", delay: delaySeconds }}
        />
        <div className="relative flex h-9 w-9 items-center justify-center rounded-full border border-primary/30 bg-primary/10">
          <Icon className="h-4 w-4 text-primary" />
        </div>
      </div>
      <span className="w-full truncate text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
      <span className="w-full break-words text-sm font-bold text-foreground tabular-metrics leading-tight sm:text-base">{value}</span>
      <span className="w-full truncate text-[10px] text-muted-foreground/70">{subLabel}</span>
    </motion.div>
  );
}

export function AISummaryCard() {
  const router = useRouter();
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["executiveSummary"],
    queryFn: () => insightsApi.executiveSummary(),
  });

  const fileIsMissing = detectErrorType(error) === "dataset_missing";
  const facts = data?.facts;
  const netPositive = (facts?.total_value ?? 0) >= 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 14, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 380, damping: 28, delay: 0.15 }}
      className="h-full"
    >
    <Card className="glass-card h-full flex flex-col relative overflow-hidden group">
      {/* Background Gradient Effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent opacity-50 transition-opacity duration-700 group-hover:opacity-100" />

      {/* Glow Sweep */}
      <motion.div
        initial={{ x: "-120%" }}
        animate={{ x: "220%" }}
        transition={{ duration: 1.2, ease: "easeOut", delay: 0.5 }}
        className="absolute top-0 bottom-0 w-[60%] pointer-events-none z-0"
        style={{ background: "linear-gradient(100deg, transparent, rgba(255,255,255,0.06), transparent)" }}
      />

      <CardHeader className="pb-0 pt-5 px-6 relative z-10">
        <div className="flex items-center gap-2.5">
          <motion.div
            initial={{ scale: 0.5, opacity: 0, rotate: -10 }}
            animate={{ scale: 1, opacity: 1, rotate: 0 }}
            transition={{ type: "spring", stiffness: 380, damping: 18 }}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-blue-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_14px_-4px_var(--primary)]"
          >
            <Sparkles className="h-4 w-4 text-white" strokeWidth={2.25} />
          </motion.div>
          <CardTitle className="flex-1 flex items-center text-xs font-bold tracking-widest uppercase text-primary">
            AI Executive Summary
            {data && data.verified === false && (
              <span className="text-[10px] bg-muted/50 text-muted-foreground px-1.5 py-0.5 rounded-sm ml-auto uppercase tracking-wider flex items-center gap-1 normal-case font-medium">
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
                {/* "No data available" is the right thing to say when there is
                    genuinely nothing to summarize. It is the wrong thing to say
                    when the dataset is right there in the picker and only its
                    file has gone missing — that reads as a fact about the data
                    rather than a fault, and leaves no hint that re-uploading is
                    what fixes it. */}
                {fileIsMissing
                  ? "This dataset's file is no longer on the server. Upload it again to restore this summary."
                  : "No data available for analysis."}
              </p>
            </div>
          ) : (
            <TypewriterText text={data.summary} />
          )}
        </div>

        {facts && facts.total_value !== undefined && (
          <div className="mt-5 pt-4 border-t border-border/40 grid grid-cols-3">
            <StatTile
              icon={FileText}
              label={facts.row_label === "transactions" ? "Transactions" : "Records"}
              value={facts.row_count.toLocaleString("en-IN")}
              subLabel="Total"
              delaySeconds={1.4}
            />
            <StatTile
              icon={IndianRupee}
              label="Total Value"
              value={facts.formatted_total ?? "-"}
              subLabel="Cumulative"
              delaySeconds={1.55}
              bordered
            />
            <StatTile
              icon={netPositive ? TrendingUp : TrendingDown}
              label="Net Value"
              value={netPositive ? "Positive" : "Negative"}
              subLabel="Result"
              delaySeconds={1.7}
              bordered
            />
          </div>
        )}

        <div className="mt-5 pt-4 border-t border-border/40">
          <Button
            onClick={() => {
              let question = "Give me a deeper analysis of the current dataset.";
              if (facts) {
                const { percent_change } = facts;
                if (percent_change !== undefined && percent_change !== null) {
                  const direction = percent_change > 0 ? "increased" : "decreased";
                  question = `Give me a deeper analysis of why the primary metric ${direction} by ${Math.abs(percent_change).toFixed(1)}% this period, and what's driving it.`;
                } else {
                  question = `Give me a deeper analysis of the primary metric.`;
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
    </motion.div>
  );
}

"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { cn } from "@/lib/utils";

import { motion } from "framer-motion";

interface MetricCardProps {
  title: string;
  value: string;
  trend: string;
  trendDown?: boolean;
}

export function MetricCard({ title, value, trend, trendDown = false }: MetricCardProps) {
  return (
    <motion.div
      whileHover={{ y: -2, scale: 1.01 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
    >
      <Card className="glass-card h-full transition-colors duration-300">
        <CardContent className="p-5 md:p-6">
          <h3 className="text-sm font-medium text-muted-foreground/80 tracking-wide">{title}</h3>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-semibold tabular-metrics tracking-tight text-foreground">{value}</span>
            <div
              className={cn(
                "flex items-center text-xs font-semibold px-2 py-0.5 rounded-full",
                trendDown ? "bg-error/10 text-error" : "bg-success/10 text-success"
              )}
            >
              {trendDown ? <ArrowDownRight className="mr-0.5 h-3.5 w-3.5" /> : <ArrowUpRight className="mr-0.5 h-3.5 w-3.5" />}
              {trend}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

"use client";

import React from "react";
import { Card } from "@/components/ui/card";
import { ArrowUpRight, ArrowDownRight, DollarSign, Users, CreditCard, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface MetricCardProps {
  title: string;
  value: string;
  trend: string;
  trendDown?: boolean;
  index?: number;
}

const THEMES = [
  {
    icon: DollarSign,
    bg: "bg-[#4c1d95]/20",
    text: "text-[#a78bfa]",
    stroke: "#a78bfa",
    stop1: "rgba(167, 139, 250, 0.4)",
    stop2: "rgba(167, 139, 250, 0)",
  },
  {
    icon: Users,
    bg: "bg-[#1e3a8a]/20",
    text: "text-[#60a5fa]",
    stroke: "#60a5fa",
    stop1: "rgba(96, 165, 250, 0.4)",
    stop2: "rgba(96, 165, 250, 0)",
  },
  {
    icon: CreditCard,
    bg: "bg-[#064e3b]/20",
    text: "text-[#34d399]",
    stroke: "#34d399",
    stop1: "rgba(52, 211, 153, 0.4)",
    stop2: "rgba(52, 211, 153, 0)",
  },
  {
    icon: Activity,
    bg: "bg-[#7c2d12]/20",
    text: "text-[#fb923c]",
    stroke: "#fb923c",
    stop1: "rgba(251, 146, 60, 0.4)",
    stop2: "rgba(251, 146, 60, 0)",
  },
];

export function MetricCard({ title, value, trend, trendDown = false, index = 0 }: MetricCardProps) {
  const theme = THEMES[index % THEMES.length];
  const Icon = theme.icon;

  return (
    <motion.div
      whileHover={{ y: -2, scale: 1.01 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className="h-full"
    >
      <Card className="glass-card relative overflow-hidden h-full flex flex-col transition-all hover:bg-surface/50 border border-border/50 rounded-[20px]">
        <div className="p-4 flex flex-col flex-1 relative z-10">
          <div className="flex items-center gap-3 mb-3">
            <div className={cn("flex items-center justify-center w-10 h-10 rounded-xl", theme.bg)}>
              <Icon className={cn("w-5 h-5", theme.text)} />
            </div>
            <span className="text-[15px] font-medium text-foreground/80">{title}</span>
          </div>
          
          <div className="mt-auto">
            <div className="text-3xl font-bold tracking-tight mb-2 text-foreground">
              {value}
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

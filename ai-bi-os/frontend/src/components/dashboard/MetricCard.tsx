"use client";

import React, { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { ArrowUpRight, ArrowDownRight, DollarSign, Users, CreditCard, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface MetricCardProps {
  title: string;
  value: string;
  trend: string;
  trendDown?: boolean;
  index?: number;
  type?: string;
}

const THEMES = [
  {
    icon: DollarSign,
    gradient: "from-[#a78bfa] to-[#7c3aed]",
    glow: "rgba(167, 139, 250, 0.6)",
    stroke: "#a78bfa",
    stop1: "rgba(167, 139, 250, 0.4)",
    stop2: "rgba(167, 139, 250, 0)",
  },
  {
    icon: Users,
    gradient: "from-[#60a5fa] to-[#2563eb]",
    glow: "rgba(96, 165, 250, 0.6)",
    stroke: "#60a5fa",
    stop1: "rgba(96, 165, 250, 0.4)",
    stop2: "rgba(96, 165, 250, 0)",
  },
  {
    icon: CreditCard,
    gradient: "from-[#34d399] to-[#059669]",
    glow: "rgba(52, 211, 153, 0.6)",
    stroke: "#34d399",
    stop1: "rgba(52, 211, 153, 0.4)",
    stop2: "rgba(52, 211, 153, 0)",
  },
  {
    icon: TrendingUp,
    gradient: "from-[#fb923c] to-[#ea580c]",
    glow: "rgba(251, 146, 60, 0.6)",
    stroke: "#fb923c",
    stop1: "rgba(251, 146, 60, 0.4)",
    stop2: "rgba(251, 146, 60, 0)",
  },
];

// Metric type -> theme index, so a currency figure always gets the $ badge
// and a percentage always gets the card/rate badge regardless of which KPI
// slot it lands in. Falls back to cycling by position when the type is
// missing or unrecognized, so older callers that don't pass `type` keep
// their existing (still-themed, just position-based) look.
const TYPE_THEME_INDEX: Record<string, number> = {
  currency: 0,
  count: 1,
  percent: 2,
  generic: 3,
  numeric: 3,
};

export function getMetricTheme(type: string | undefined, index: number) {
  const themeIndex = type && type in TYPE_THEME_INDEX ? TYPE_THEME_INDEX[type] : index % THEMES.length;
  return THEMES[themeIndex];
}

export function MetricCard({ title, value, trend, trendDown = false, index = 0, type }: MetricCardProps) {
  const theme = getMetricTheme(type, index);
  const Icon = theme.icon;
  const delayMs = 150 + index * 110;

  return (
    <motion.div
      whileHover={{ y: -2, scale: 1.01 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className="group h-full relative overflow-hidden rounded-[20px]"
    >
      <Card className="glass-card relative overflow-hidden h-full flex flex-col transition-all hover:bg-surface/50 border border-border/50 rounded-[20px]">
        {/* Glow Sweep */}
        <motion.div 
          initial={{ x: '-120%' }}
          animate={{ x: '220%' }}
          transition={{ duration: 1.1, ease: "easeOut", delay: (delayMs + 250) / 1000 }}
          className="absolute top-0 bottom-0 w-[60%] pointer-events-none z-0"
          style={{ background: 'linear-gradient(100deg, transparent, rgba(255,255,255,0.05), transparent)' }}
        />
        
        <div className="p-4 flex flex-col flex-1 relative z-10">
          <div className="flex items-center gap-3 mb-3">
            <motion.div
              initial={{ scale: 0.5, opacity: 0, rotate: -10 }}
              animate={{ scale: 1, opacity: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 380, damping: 18, delay: (delayMs + 120) / 1000 }}
              className={cn(
                "flex shrink-0 items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br transition-[filter] duration-300 group-hover:brightness-110",
                theme.gradient
              )}
              style={{ boxShadow: `inset 0 1px 0 rgba(255,255,255,0.35), 0 0 16px -4px ${theme.glow}` }}
            >
              <Icon className="w-5 h-5 text-white" strokeWidth={2.25} />
            </motion.div>
            <span className="text-[15px] font-medium text-foreground/80">{title}</span>
          </div>
          
          <div className="mt-auto">
            <div className="text-3xl font-bold tracking-tight mb-2 text-foreground font-variant-numeric-tabular">
              <CountUpValue valueString={value} delayMs={delayMs} />
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

function CountUpValue({ valueString, delayMs = 0 }: { valueString: string; delayMs?: number }) {
  const [display, setDisplay] = useState(() => {
    // Initial display is "0" with matching prefix/suffix
    const match = valueString.match(/^([^\d]*)([\d.,]+)([^\d]*)$/);
    if (!match) return valueString;
    const prefix = match[1];
    const numStr = match[2].replace(/,/g, '');
    const suffix = match[3];
    const target = parseFloat(numStr);
    if (isNaN(target)) return valueString;
    const decimalMatch = numStr.match(/\.(\d+)/);
    const decimals = decimalMatch ? decimalMatch[1].length : 0;
    return `${prefix}${(0).toFixed(decimals)}${suffix}`;
  });

  useEffect(() => {
    const match = valueString.match(/^([^\d]*)([\d.,]+)([^\d]*)$/);
    if (!match) {
      setDisplay(valueString);
      return;
    }
    
    const prefix = match[1];
    const numStr = match[2].replace(/,/g, '');
    const suffix = match[3];
    const target = parseFloat(numStr);
    
    if (isNaN(target)) {
      setDisplay(valueString);
      return;
    }
    
    const decimalMatch = numStr.match(/\.(\d+)/);
    const decimals = decimalMatch ? decimalMatch[1].length : 0;
    
    const duration = 900;
    let start = 0;
    let frameId: number;
    let timeoutId: any;
    
    const step = (timestamp: number) => {
      if (!start) start = timestamp;
      const progress = Math.min(1, (timestamp - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3); // cubic ease-out
      const current = target * eased;
      
      const formattedNum = current.toFixed(decimals);
      setDisplay(`${prefix}${formattedNum}${suffix}`);
      
      if (progress < 1) {
        frameId = requestAnimationFrame(step);
      } else {
        setDisplay(valueString); 
      }
    };
    
    timeoutId = setTimeout(() => {
      frameId = requestAnimationFrame(step);
    }, delayMs);

    // The count-up is decoration; the number itself is not. requestAnimationFrame
    // does not fire while a tab is backgrounded or throttled, and this component
    // starts from zero — so without a guaranteed settle the card can sit showing
    // "₹0.00Cr" for a real figure of ₹1.58Cr, which reads as a fact rather than
    // as a missing animation. Land on the true value regardless of whether a
    // single frame ever ran.
    const settleId = setTimeout(() => setDisplay(valueString), delayMs + duration + 250);

    return () => {
      clearTimeout(timeoutId);
      clearTimeout(settleId);
      if (frameId) cancelAnimationFrame(frameId);
    };
  }, [valueString, delayMs]);

  return <>{display}</>;
}

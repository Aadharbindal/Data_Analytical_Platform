"use client";

import React, { useEffect, useState } from "react";
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
  const delayMs = 150 + index * 110;

  return (
    <motion.div
      whileHover={{ y: -2, scale: 1.01 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className="h-full relative overflow-hidden rounded-[20px]"
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
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, ease: [0.34, 1.56, 0.64, 1], delay: (delayMs + 120) / 1000 }}
              className={cn("flex items-center justify-center w-10 h-10 rounded-xl", theme.bg)}
            >
              <Icon className={cn("w-5 h-5", theme.text)} />
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
    
    return () => {
      clearTimeout(timeoutId);
      if (frameId) cancelAnimationFrame(frameId);
    };
  }, [valueString, delayMs]);

  return <>{display}</>;
}

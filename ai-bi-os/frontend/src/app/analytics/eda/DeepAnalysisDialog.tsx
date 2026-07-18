"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { formatNumber } from "@/lib/utils";
import { Loader2 } from "lucide-react";
import { motion } from "framer-motion";

interface DeepAnalysisDialogProps {
  column: string | null;
  onClose: () => void;
}

function shortLabel(val: string) {
  if (!val) return "";
  if (val.match(/^\d{4}-\d{2}-\d{2}/)) {
    // Format date string to short format e.g. Sep 01
    const d = new Date(val);
    if (!isNaN(d.getTime())) {
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }
  }
  if (val.length > 15) return val.substring(0,13) + "...";
  return val;
}

export function DeepAnalysisDialog({ column, onClose }: DeepAnalysisDialogProps) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['edaColumn', column],
    queryFn: () => column ? analyticsApi.edaColumn(column) : null,
    enabled: !!column,
  });

  const [hover, setHover] = useState<number>(-1);

  // SVG Calculation logic
  let bars: any[] = [];
  let yTicks: any[] = [];
  let xTicks: any[] = [];
  let tip: any = null;
  let totalCount = 0;

  const PL = 64, PR = 24, top = 20, base = 450, W = 1600;
  const plotW = W - PL - PR, plotH = base - top;

  if (data) {
    const isNum = data.type === "numeric";
    const arr = isNum ? data.histogram : data.frequencies;
    const nv = arr.length;
    
    totalCount = arr.reduce((sum: number, b: any) => sum + b.count, 0);
    
    if (nv > 0) {
      const step = plotW / nv;
      const barW = Math.max(1, step * 0.7);
      let maxCount = 0;
      arr.forEach((d: any) => { if (d.count > maxCount) maxCount = d.count; });

      // Y Scale
      const niceMax = Math.ceil((maxCount || 1) / 5) * 5; 
      const yFor = (v: number) => base - (v / niceMax) * plotH;
      
      const yStep = Math.max(1, Math.ceil(niceMax / 4));
      for (let v = 0; v <= niceMax; v += yStep) {
        const y = yFor(v);
        yTicks.push({ y, ty: y + 4, label: formatNumber(v) });
      }

      // Bars
      bars = arr.map((b: any, vi: number) => {
        const hitX = PL + vi * step;
        const barX = hitX + (step - barW) / 2;
        const barY = b.count > 0 ? yFor(b.count) : base;
        const barH = Math.max(0, base - barY);
        const hot = hover === vi;
        return {
          idx: vi, hitX, colW: step, barX, barW, barY, barH, count: b.count,
          fill: hot ? "url(#barGradHot)" : "url(#barGrad)",
          opacity: 1,
          isHot: hot,
          label: isNum 
            ? (formatNumber(b.bin_start) + " - " + formatNumber(b.bin_end || b.bin_start + 1))
            : String(b.value),
          shortLbl: isNum ? formatNumber(b.bin_start) : shortLabel(String(b.value))
        };
      });

      // X Ticks
      const maxTicks = 12; // Prevent overlap
      const every = Math.max(1, Math.ceil(nv / maxTicks));
      arr.forEach((b: any, vi: number) => {
        if (vi % every === 0) {
          xTicks.push({ 
            x: PL + vi * step + step / 2, 
            label: bars[vi].shortLbl
          });
        }
      });

      // Tooltip
      if (hover >= 0) {
        const vb = bars[hover];
        if (vb) {
          const cx = vb.barX + vb.barW / 2;
          let bx = cx - 145; bx = Math.max(PL, Math.min(bx, W - PR - 290));
          let by = vb.barY - 120; if (by < top) by = vb.barY + 14;
          by = Math.min(by, base - 110);
          const tx = bx + 20;
          tip = {
            cx, barY: vb.barY, bx, by, tx,
            l1: by + 36, l2: by + 68, l3: by + 94,
            label: vb.label,
            count: vb.count.toLocaleString("en-US") + (vb.count === 1 ? " record" : " records"),
            pct: totalCount > 0 ? (vb.count / totalCount * 100).toFixed(1) + "% of total" : "0%"
          };
        }
      }
    }
  }

  return (
    <Dialog open={!!column} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-[95vw] sm:max-w-3xl md:max-w-4xl lg:max-w-5xl bg-[#080b12]/60 border border-white/[0.08] backdrop-blur-[40px] shadow-[0_40px_90px_-30px_rgba(0,0,0,0.9),inset_0_1px_0_rgba(255,255,255,0.06)] max-h-[90vh] overflow-y-auto p-0 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] rounded-[24px]">
        <style>{`
          @keyframes barrise { from { transform: scaleY(0); } to { transform: scaleY(1); } }
        `}</style>
        
        <motion.div 
          initial={{ opacity: 0, scale: 0.97, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          className="p-[30px_34px_40px] pb-12 relative overflow-hidden"
        >
          <motion.div 
            initial={{ x: '-100%', opacity: 0 }}
            animate={{ x: '200%', opacity: 0.15 }}
            transition={{ duration: 1.5, ease: "easeInOut", delay: 0.2 }}
            className="absolute top-0 bottom-0 w-1/2 bg-gradient-to-r from-transparent via-white to-transparent pointer-events-none -skew-x-12 z-0"
          />

          <DialogHeader className="flex flex-row items-center justify-between px-2 pt-2 relative z-10 mb-[14px]">
            <div className="flex items-center gap-4">
              <DialogTitle className="text-[28px] font-bold text-white tracking-tight">
                Column Analysis
              </DialogTitle>
              {column && (
                <span className="font-mono text-sm text-[#4d84ff] border border-[#4d84ff]/30 bg-[#4d84ff]/10 px-4 py-1.5 rounded-full font-medium shadow-[inset_0_1px_2px_rgba(255,255,255,0.05)]">
                  {column}
                </span>
              )}
            </div>
          </DialogHeader>

          {isLoading ? (
            <div className="flex items-center justify-center h-[400px]">
              <Loader2 className="w-10 h-10 animate-spin text-primary" />
            </div>
          ) : isError || !data ? (
            <div className="flex flex-col items-center justify-center h-[400px] text-red-400 gap-3 bg-red-500/10 rounded-xl border border-red-500/20">
              <span className="text-lg font-medium">Failed to load deep analysis.</span>
              {error && <span className="text-sm opacity-80 max-w-lg text-center overflow-auto max-h-32 font-mono bg-black/40 p-3 rounded-md">{(error as any).message || String(error)}</span>}
            </div>
          ) : (
            <div className="flex flex-col gap-6 relative z-10">
              {/* Chart Area */}
              <div className="w-full bg-[#0d121c]/40 rounded-[24px] p-[30px_40px_20px] border border-white/[0.04] shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] backdrop-blur-xl relative overflow-hidden flex flex-col items-center justify-center mt-2 mb-2">
                {/* Subtle background glow */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[70%] h-[70%] bg-[#4d84ff]/10 blur-[120px] pointer-events-none rounded-full" />
                
                {/* Top Text inside Chart box */}
                <div className="absolute top-6 left-8 right-8 flex justify-between items-center z-20 w-[calc(100%-64px)]">
                  <span className="text-[12px] uppercase tracking-[0.25em] font-mono text-[#8a99b8]/70 font-semibold">Distribution</span>
                </div>

                <div className="relative z-10 w-full max-w-[96%] mt-6">
                  <svg viewBox="0 0 1600 520" className="w-full block overflow-visible" onMouseLeave={() => setHover(-1)}>
                  <defs>
                    <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#eef2fa"></stop>
                      <stop offset="45%" stopColor="#a3b8cc"></stop>
                      <stop offset="100%" stopColor="#4a5d73"></stop>
                    </linearGradient>
                    <linearGradient id="barGradHot" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#d0fbff"></stop>
                      <stop offset="25%" stopColor="#00f0ff"></stop>
                      <stop offset="100%" stopColor="#00aacc"></stop>
                    </linearGradient>
                  </defs>

                  {/* Horizontal Grid lines */}
                  {yTicks.map((t, i) => (
                    <g key={`y-${i}`}>
                      <line x1="64" x2="1576" y1={t.y} y2={t.y} stroke="rgba(255,255,255,.055)" strokeDasharray="2 7"></line>
                      <text x="52" y={t.ty} textAnchor="end" style={{ fill: '#8a99b8', fontFamily: '"IBM Plex Mono", monospace', fontSize: '18px' }}>{t.label}</text>
                    </g>
                  ))}

                  <line x1="64" x2="1576" y1="450" y2="450" stroke="rgba(255,255,255,.14)"></line>

                  {/* Bars */}
                  {bars.map((b) => (
                    <g key={`b-${b.idx}`}>
                      <rect x={b.hitX} y="20" width={b.colW} height="430" fill="transparent" onMouseEnter={() => setHover(b.idx)}></rect>
                      <rect 
                        x={b.barX} y={b.barY} width={b.barW} height={b.barH} rx={Math.min(4, b.barW / 2)} 
                        fill={b.fill} opacity={b.opacity} 
                        style={{ 
                          pointerEvents: 'none', 
                          transformBox: 'fill-box', 
                          transformOrigin: 'bottom', 
                          animation: `barrise 0.8s cubic-bezier(0.22,1,0.36,1) ${b.idx * 0.012}s both`,
                          filter: b.isHot ? 'drop-shadow(0px 0px 10px rgba(0,240,255,0.7))' : 'none'
                        }}
                      ></rect>
                    </g>
                  ))}

                  {/* X Ticks */}
                  {xTicks.map((t, i) => (
                    <g key={`x-${i}`}>
                      <line x1={t.x} x2={t.x} y1="450" y2="456" stroke="rgba(255,255,255,.2)"></line>
                      <text x={t.x} y="478" textAnchor="middle" style={{ fill: '#8a99b8', fontFamily: '"IBM Plex Mono", monospace', fontSize: '18px' }}>{t.label}</text>
                    </g>
                  ))}
                  
                  {/* Tooltip rendering */}
                  {tip && (
                    <g style={{ pointerEvents: 'none' }}>
                      <line x1={tip.cx} x2={tip.cx} y1={tip.barY} y2="450" stroke="rgba(150,190,255,.5)" strokeDasharray="3 4"></line>
                      <rect x={tip.bx} y={tip.by} width="290" height="114" rx="12" fill="#0b1220" stroke="rgba(120,160,255,.35)"></rect>
                      <rect x={tip.bx} y={tip.by} width="5" height="114" rx="3" fill="#4d84ff"></rect>
                      <text x={tip.tx} y={tip.l1} style={{ fill: '#eef2fa', fontFamily: '"IBM Plex Mono", monospace', fontSize: '22px', fontWeight: 700 }}>
                        {tip.label.length > 20 ? tip.label.substring(0, 18) + '...' : tip.label}
                      </text>
                      <text x={tip.tx} y={tip.l2} style={{ fill: '#9fb2d4', fontFamily: '"IBM Plex Mono", monospace', fontSize: '18px' }}>{tip.count}</text>
                      <text x={tip.tx} y={tip.l3} style={{ fill: '#6aa4ff', fontFamily: '"IBM Plex Mono", monospace', fontSize: '18px' }}>{tip.pct}</text>
                    </g>
                  )}
                </svg>
              </div>
            </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mt-6 mb-6">
                {Object.entries(data.stats).map(([k, v]) => (
                  <div key={k} className="bg-[#0b121e] border border-[#2f3b54]/40 rounded-[14px] p-5 flex flex-col gap-3 transition-all duration-300 relative overflow-hidden shadow-[inset_0_4px_20px_-5px_rgba(77,132,255,0.4),inset_0_1px_1px_rgba(106,164,255,0.8),0_4px_12px_rgba(0,0,0,0.4)] backdrop-blur-md cursor-default">
                    <span className="text-[10px] text-[#5c7099] uppercase tracking-[0.25em] font-semibold relative z-10 font-mono">
                      {k}
                    </span>
                    <span className="font-mono text-[22px] text-white font-bold relative z-10 drop-shadow-md">
                      {typeof v === 'number' ? formatNumber(v) : (v as string)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </DialogContent>
    </Dialog>
  );
}


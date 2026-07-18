"use client";

import { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { ChevronDown } from "lucide-react";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber } from "@/lib/utils";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { motion } from "framer-motion";

function fmtShort(n: number) { 
  if(isNaN(n)) return "";
  return n >= 1000 ? Math.round(n / 1000) + "k" : "" + Math.round(n); 
}
function fmtMoney(n: number) { 
  if(isNaN(n)) return "";
  return Math.round(n).toLocaleString("en-US"); 
}

export default function DistributionExplorer() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['distribution'],
    queryFn: () => analyticsApi.distribution()
  });

  const [selectedColumn, setSelectedColumn] = useState<string | null>(null);
  const [logScale, setLogScale] = useState(false);
  const [focus, setFocus] = useState(false);
  const [hover, setHover] = useState<number>(-1);

  useEffect(() => {
    if (data && data.length > 0 && !selectedColumn) {
      setSelectedColumn(data[0].column_name);
    }
  }, [data, selectedColumn]);

  const activeDist = data?.find((d: any) => d.column_name === selectedColumn) || data?.[0];

  const toolbar = data && data.length > 0 && (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-1.5 bg-surface border border-border text-xs font-medium text-foreground rounded-lg px-3 py-1.5 outline-none hover:bg-white/5 transition-colors focus:ring-2 focus:ring-primary/30 shadow-sm cursor-pointer">
        {selectedColumn || "Select Column"}
        <ChevronDown className="h-3 w-3 text-muted-foreground ml-1 shrink-0" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48 max-h-[300px] overflow-y-auto">
        {data.map((dist: any) => (
          <DropdownMenuItem 
            key={dist.column_name} 
            onClick={() => { setSelectedColumn(dist.column_name); setHover(-1); }}
            className="text-xs cursor-pointer"
          >
            {dist.column_name}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );

  const { parsedData, totalCount, maxCount, cutoff, rangeLabel } = useMemo(() => {
    if (!activeDist || !activeDist.histogram) return { parsedData: [], totalCount: 0, maxCount: 0, cutoff: 0, rangeLabel: "" };
    
    let total = 0;
    let maxC = 0;
    const bins = activeDist.histogram.map((h: any, i: number) => {
      const parts = h.bin.split(' - ');
      let lo = 0, hi = 0;
      if(parts.length === 2) {
        lo = parseFloat(parts[0]);
        hi = parseFloat(parts[1]);
      }
      total += h.count;
      if (h.count > maxC) maxC = h.count;
      return { idx: i, lo, hi, count: h.count };
    });

    let cut = bins.length - 1;
    for (let i = bins.length - 1; i >= 0; i--) { 
      if (bins[i].count > maxC * 0.02) { cut = i; break; } 
    }
    const finalCut = Math.min(bins.length - 1, cut + 2);
    
    let rl = "";
    if (bins.length > 0) {
      rl = fmtShort(bins[0].lo) + "–" + fmtShort(bins[bins.length - 1].hi);
    }

    return { parsedData: bins, totalCount: total, maxCount: maxC, cutoff: finalCut, rangeLabel: rl };
  }, [activeDist]);

  // Derived state for SVG
  const PL = 64, PR = 24, top = 20, base = 450, W = 1600;
  const plotW = W - PL - PR, plotH = base - top;
  const visible = focus ? parsedData.slice(0, cutoff + 1) : parsedData;
  const nv = visible.length;
  const step = nv > 0 ? plotW / nv : plotW;
  const barW = Math.max(2, step * 0.62);

  // Y Scale
  let yFor: (v: number) => number;
  let yTicks: any[] = [];
  if (logScale && maxCount > 0) {
    const maxLog = Math.max(1, Math.ceil(Math.log10(maxCount)));
    yFor = (v: number) => v <= 0 ? base : base - (Math.log10(v) / maxLog) * plotH;
    for (let e = 0; e <= maxLog; e++) {
      const v = Math.pow(10, e);
      const y = yFor(v);
      yTicks.push({ y, ty: y + 5, label: v >= 1000 ? (v / 1000) + "k" : "" + v });
    }
  } else {
    const niceMax = Math.ceil((maxCount || 1) / 150) * 150;
    yFor = (v: number) => base - (v / niceMax) * plotH;
    for (let v = 0; v <= niceMax; v += niceMax / 4) {
      const y = yFor(v);
      yTicks.push({ y, ty: y + 5, label: "" + Math.round(v) });
    }
  }

  // Bars
  const bars = visible.map((b: any, vi: number) => {
    const hitX = PL + vi * step;
    const barX = hitX + (step - barW) / 2;
    const barY = b.count > 0 ? yFor(b.count) : base;
    const barH = Math.max(0, base - barY);
    const hot = hover === b.idx;
    return {
      idx: b.idx, hitX, colW: step, barX, barW, barY, barH,
      fill: hot ? "url(#barGradHot)" : "url(#barGrad)",
      opacity: hover === -1 ? 0.92 : (hot ? 1 : 0.42),
    };
  });

  // X Ticks
  const every = Math.max(1, Math.round(nv / 11));
  const xTicks: any[] = [];
  visible.forEach((b: any, vi: number) => {
    if (vi % every === 0) xTicks.push({ x: PL + vi * step + step / 2, label: fmtShort(b.lo) });
  });

  // Tooltip
  let tip: any = null;
  if (hover >= 0) {
    const vb = bars.find((x: any) => x.idx === hover);
    const d = parsedData[hover];
    if (vb && d) {
      const cx = vb.barX + vb.barW / 2;
      let bx = cx - 145; bx = Math.max(PL, Math.min(bx, W - PR - 290));
      let by = vb.barY - 120; if (by < top) by = vb.barY + 14;
      by = Math.min(by, base - 110);
      const tx = bx + 20;
      tip = {
        cx, barY: vb.barY, bx, by, tx,
        l1: by + 36, l2: by + 68, l3: by + 94,
        range: fmtMoney(d.lo) + " – " + fmtMoney(d.hi),
        count: d.count.toLocaleString("en-US") + (d.count === 1 ? " record" : " records"),
        pct: totalCount > 0 ? (d.count / totalCount * 100).toFixed(1) + "% of total" : "0%",
      };
    }
  }

  const scaleNote = (logScale ? " · log scale" : "") + (focus ? " · focused" : "");
  
  const btnBase = "font-mono text-[13px] font-medium cursor-pointer px-4 py-2 rounded-lg border transition-all duration-150 outline-none";
  const activeBtn = `${btnBase} border-[#4d84ff] bg-gradient-to-b from-[#3d74ff] to-[#2455d6] text-white shadow-sm`;
  const idleBtn = `${btnBase} border-white/[0.14] bg-white/[0.03] text-[#8a97b0] hover:bg-white/[0.08]`;

  return (
    <StudioPage title="Distribution Explorer" isLoading={isLoading} toolbar={toolbar}>
      <style>{`
        @keyframes barrise { from { transform: scaleY(0); } to { transform: scaleY(1); } }
      `}</style>
      
      {isError ? (
        <ErrorState />
      ) : !data || data.length === 0 ? (
        <div className="text-muted-foreground text-sm">No Distribution data found.</div>
      ) : (
        <div className="flex flex-col h-full w-full max-w-[1560px] mx-auto pb-8">
          {activeDist && (
            <motion.div 
              initial={{ opacity: 0, y: 20, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
              className="w-full bg-gradient-to-b from-[#0c111c] to-[#080b12] border border-white/[0.07] rounded-[22px] p-[30px_34px_26px] shadow-[0_40px_90px_-30px_rgba(0,0,0,0.8),inset_0_1px_0_rgba(255,255,255,0.04)] relative overflow-hidden"
            >
              <motion.div 
                initial={{ x: '-100%', opacity: 0 }}
                animate={{ x: '200%', opacity: 0.15 }}
                transition={{ duration: 1.5, ease: "easeInOut", delay: 0.2 }}
                className="absolute top-0 bottom-0 w-1/2 bg-gradient-to-r from-transparent via-white to-transparent pointer-events-none -skew-x-12 z-0"
              />
              
              <div className="relative z-10">
                {/* Header section */}
              <div className="flex items-start justify-between gap-6 flex-wrap">
                <div className="flex flex-col gap-[6px]">
                  <div className="flex items-center gap-[11px]">
                    <span className="w-[10px] h-[10px] rounded-[3px] bg-gradient-to-b from-[#6aa4ff] to-[#2f6bff] shadow-[0_0_14px_rgba(47,107,255,0.7)]"></span>
                    <h1 className="m-0 text-[28px] font-bold tracking-tight text-white">
                      {activeDist.column_name}
                    </h1>
                  </div>
                  <div className="font-mono text-sm text-[#8a99b8] pl-[24px]">
                    {totalCount.toLocaleString()} records · range {rangeLabel}
                  </div>
                </div>
                
                <div className="flex items-center gap-[10px]">
                  <button onClick={() => setFocus(!focus)} className={focus ? activeBtn : idleBtn}>Focus range</button>
                  <button onClick={() => setLogScale(!logScale)} className={logScale ? activeBtn : idleBtn}>Log scale</button>
                  <span className="font-mono text-xs text-[#6aa4ff] border border-[#6aa4ff]/40 bg-[#2f6bff]/[0.08] px-3 py-1.5 rounded-lg uppercase tracking-wider font-bold">
                    {activeDist.distribution_type}
                  </span>
                </div>
              </div>

              {/* Chart SVG section */}
              <div className="relative mt-[14px]">
                <svg viewBox="0 0 1600 560" className="w-full block overflow-visible" onMouseLeave={() => setHover(-1)}>
                  <defs>
                    <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#8fbcff"></stop>
                      <stop offset="45%" stopColor="#4d84ff"></stop>
                      <stop offset="100%" stopColor="#2455d6"></stop>
                    </linearGradient>
                    <linearGradient id="barGradHot" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#d6e6ff"></stop>
                      <stop offset="55%" stopColor="#7aa8ff"></stop>
                      <stop offset="100%" stopColor="#3d6dff"></stop>
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
                  {bars.map((b: any) => (
                    <g key={`b-${b.idx}`}>
                      <rect x={b.hitX} y="20" width={b.colW} height="430" fill="transparent" onMouseEnter={() => setHover(b.idx)}></rect>
                      <rect 
                        x={b.barX} y={b.barY} width={b.barW} height={b.barH} rx="2.5" 
                        fill={b.fill} opacity={b.opacity} 
                        style={{ pointerEvents: 'none', transformBox: 'fill-box', transformOrigin: 'bottom', animation: 'barrise .55s cubic-bezier(.22,1,.36,1) both' }}
                      ></rect>
                    </g>
                  ))}

                  {/* X Axis Labels */}
                  {xTicks.map((t, i) => (
                    <g key={`x-${i}`}>
                      <line x1={t.x} x2={t.x} y1="450" y2="456" stroke="rgba(255,255,255,.2)"></line>
                      <text x={t.x} y="478" textAnchor="middle" style={{ fill: '#8a99b8', fontFamily: '"IBM Plex Mono", monospace', fontSize: '18px' }}>{t.label}</text>
                    </g>
                  ))}
                  
                  {/* Axis Title */}
                  <text x="820" y="534" textAnchor="middle" style={{ fill: '#5a6b8c', fontFamily: '"IBM Plex Mono", monospace', fontSize: '20px', letterSpacing: '.5px', fontWeight: 600 }}>AMOUNT (VALUES)</text>

                  {/* Tooltip rendering */}
                  {tip && (
                    <g style={{ pointerEvents: 'none' }}>
                      <line x1={tip.cx} x2={tip.cx} y1={tip.barY} y2="450" stroke="rgba(150,190,255,.5)" strokeDasharray="3 4"></line>
                      <rect x={tip.bx} y={tip.by} width="290" height="114" rx="12" fill="#0b1220" stroke="rgba(120,160,255,.35)"></rect>
                      <rect x={tip.bx} y={tip.by} width="5" height="114" rx="3" fill="#4d84ff"></rect>
                      <text x={tip.tx} y={tip.l1} style={{ fill: '#eef2fa', fontFamily: '"IBM Plex Mono", monospace', fontSize: '22px', fontWeight: 700 }}>{tip.range}</text>
                      <text x={tip.tx} y={tip.l2} style={{ fill: '#9fb2d4', fontFamily: '"IBM Plex Mono", monospace', fontSize: '18px' }}>{tip.count}</text>
                      <text x={tip.tx} y={tip.l3} style={{ fill: '#6aa4ff', fontFamily: '"IBM Plex Mono", monospace', fontSize: '18px' }}>{tip.pct}</text>
                    </g>
                  )}
                </svg>
              </div>

              {/* Footer Note */}
              <div className="flex items-center gap-[8px] mt-[6px] pl-[2px] font-mono text-sm text-[#8a99b8]">
                <span className="w-[22px] h-[8px] rounded-[2px] bg-gradient-to-r from-[#8fbcff] to-[#2455d6] inline-block"></span>
                Count per bin · hover for details{scaleNote}
              </div>
              </div>
            </motion.div>
          )}
        </div>
      )}
    </StudioPage>
  );
}

"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { ErrorState } from "@/components/ui/error-state";
import { StudioPage } from "@/components/analytics/StudioPage";
import { formatNumber, formatPercent } from "@/lib/utils";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect } from "react";

function AnimatedNumber({ value, isPercent = false }: { value: number, isPercent?: boolean }) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) => 
    isPercent ? formatPercent(latest * 100) : formatNumber(latest)
  );

  useEffect(() => {
    const controls = animate(count, value, { duration: 1.5, ease: "easeOut" });
    return controls.stop;
  }, [count, value]);

  return <motion.span>{rounded}</motion.span>;
}

export default function TrendAnalysis() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['trend'],
    queryFn: () => analyticsApi.trend()
  });

  return (
    <StudioPage title="Trend & Change Detection" isLoading={isLoading}>
      {isError ? (
        <ErrorState />
      ) : !data || !data.trend || data.trend.length === 0 ? (
        <div className="text-muted-foreground text-sm">
          No Trend data found. Make sure your dataset has a date column.
        </div>
      ) : (
        <motion.div 
          initial={{ opacity: 0, filter: 'blur(4px)' }}
          animate={{ opacity: 1, filter: 'blur(0px)' }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="flex flex-col gap-4"
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {data.trend.map((trend: any, i: number) => {
              const isUp = trend.trend === 'UP';
              const isDown = trend.trend === 'DOWN';
              
              return (
                <motion.div 
                  key={i} 
                  initial={{ opacity: 0, y: 15, x: -10 }}
                  animate={{ opacity: 1, y: 0, x: 0 }}
                  transition={{ duration: 0.4, delay: i * 0.05 + 0.1, ease: [0.22, 1, 0.36, 1] }}
                  className="relative bg-[#0A0E17] rounded-[24px] overflow-hidden flex flex-col shadow-2xl border border-white/[0.03] max-w-[420px]"
                >
                  {/* Left edge glow fading inwards */}
                  <div 
                    className="absolute top-0 left-0 w-full h-full z-0 pointer-events-none" 
                    style={{ 
                      background: isUp ? 'linear-gradient(90deg, rgba(59,130,246,0.15) 0%, transparent 40%)' : 
                                  isDown ? 'linear-gradient(90deg, rgba(244,63,94,0.15) 0%, transparent 40%)' : 
                                  'linear-gradient(90deg, rgba(100,116,139,0.15) 0%, transparent 40%)'
                    }}
                  />
                  {/* Intense left edge line */}
                  <div 
                    className="absolute top-0 left-0 w-1 h-full z-20" 
                    style={{ 
                      backgroundColor: isUp ? '#3b82f6' : isDown ? '#f43f5e' : '#64748b',
                      boxShadow: `0 0 30px 4px ${isUp ? 'rgba(59,130,246,1)' : isDown ? 'rgba(244,63,94,1)' : 'rgba(100,116,139,1)'}`
                    }}
                  />
                  
                  {/* Top Header Section */}
                  <div className="p-5 pb-0 relative z-10 flex flex-col">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex flex-col gap-1.5 ml-2">
                        <span className="text-[9px] text-slate-400 font-bold uppercase tracking-[0.2em]">Trend Analysis</span>
                        <h3 className="text-[22px] font-extrabold text-white tracking-tight leading-none">{trend.column}</h3>
                      </div>
                      
                      <div 
                        className="px-3 py-1.5 rounded-full border border-white/5 bg-white/5 backdrop-blur-md flex items-center gap-2 mt-1"
                      >
                        <div 
                          className="w-2 h-2 rounded-full"
                          style={{ 
                            backgroundColor: isUp ? '#60a5fa' : isDown ? '#fb7185' : '#94a3b8',
                            boxShadow: `0 0 10px ${isUp ? '#60a5fa' : isDown ? '#fb7185' : '#94a3b8'}`
                          }}
                        />
                        <span 
                          className="text-[10px] font-bold tracking-[0.1em] uppercase"
                          style={{ color: isUp ? '#93c5fd' : isDown ? '#fda4af' : '#cbd5e1' }}
                        >
                          {isUp ? 'Increasing' : isDown ? 'Decreasing' : 'Stable'}
                        </span>
                      </div>
                    </div>
                    
                    {/* SVG Chart Area (Neon effect) */}
                    <div className="h-[100px] w-full relative mb-4 mt-2 ml-1 pr-1">
                      <svg width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 400 130" className="overflow-visible">
                        
                        {/* Dotted Trendline */}
                        <line 
                          x1="0" y1={isUp ? "100" : isDown ? "30" : "65"} 
                          x2="400" y2={isUp ? "30" : isDown ? "100" : "65"} 
                          stroke={isUp ? 'rgba(59,130,246,0.6)' : isDown ? 'rgba(244,63,94,0.6)' : 'rgba(100,116,139,0.6)'} 
                          strokeWidth="1.5" 
                          strokeDasharray="6 6" 
                        />
                        
                        {/* Glowing Wavy Path */}
                        {isUp && (
                          <>
                            <motion.path 
                              initial={{ pathLength: 0, opacity: 0 }}
                              animate={{ pathLength: 1, opacity: 1 }}
                              transition={{ duration: 1.5, ease: "easeInOut", delay: i * 0.1 }}
                              d="M 0,95 C 20,90 35,75 50,80 C 65,85 70,100 80,100 C 90,100 95,55 110,60 C 125,65 130,105 140,105 C 150,105 160,40 180,45 C 200,50 205,110 220,110 C 235,110 240,30 260,30 C 280,30 285,115 300,115 C 315,115 320,25 340,25 C 360,25 365,100 375,100 C 385,100 390,50 395,50" 
                              fill="none" 
                              stroke="#60a5fa" 
                              strokeWidth="3.5" 
                              strokeLinecap="round"
                              style={{ 
                                filter: "drop-shadow(0px 0px 10px rgba(59,130,246,1)) drop-shadow(0px 0px 25px rgba(59,130,246,0.7))"
                              }}
                            />
                            {/* End circle */}
                            <motion.circle 
                               initial={{ scale: 0, opacity: 0 }}
                               animate={{ scale: 1, opacity: 1 }}
                               transition={{ duration: 0.3, ease: "easeOut", delay: i * 0.1 + 1.5 }}
                               cx="395" cy="50" r="5" 
                               fill="#0A0E17" 
                               stroke="#60a5fa" 
                               strokeWidth="3" 
                               style={{ filter: "drop-shadow(0 0 12px rgba(59,130,246,1))" }}
                            />
                          </>
                        )}
                        {isDown && (
                          <>
                            <motion.path 
                              initial={{ pathLength: 0, opacity: 0 }}
                              animate={{ pathLength: 1, opacity: 1 }}
                              transition={{ duration: 1.5, ease: "easeInOut", delay: i * 0.1 }}
                              d="M 0,35 C 20,40 35,55 50,50 C 65,45 70,30 80,30 C 90,30 95,75 110,70 C 125,65 130,25 140,25 C 150,25 160,90 180,85 C 200,80 205,20 220,20 C 235,20 240,100 260,100 C 280,100 285,15 300,15 C 315,15 320,105 340,105 C 360,105 365,30 375,30 C 385,30 390,80 395,80" 
                              fill="none" 
                              stroke="#fb7185" 
                              strokeWidth="3.5" 
                              strokeLinecap="round"
                              style={{ 
                                filter: "drop-shadow(0px 0px 10px rgba(244,63,94,1)) drop-shadow(0px 0px 25px rgba(244,63,94,0.7))"
                              }}
                            />
                            <motion.circle 
                               initial={{ scale: 0, opacity: 0 }}
                               animate={{ scale: 1, opacity: 1 }}
                               transition={{ duration: 0.3, ease: "easeOut", delay: i * 0.1 + 1.5 }}
                               cx="395" cy="80" r="5" 
                               fill="#0A0E17" 
                               stroke="#fb7185" 
                               strokeWidth="3" 
                               style={{ filter: "drop-shadow(0 0 12px rgba(244,63,94,1))" }}
                            />
                          </>
                        )}
                        {!isUp && !isDown && (
                          <>
                            <motion.path 
                              initial={{ pathLength: 0, opacity: 0 }}
                              animate={{ pathLength: 1, opacity: 1 }}
                              transition={{ duration: 1.5, ease: "easeInOut", delay: i * 0.1 }}
                              d="M 0,65 C 20,55 35,75 50,65 C 65,55 70,75 80,65 C 90,55 95,75 110,65 C 125,55 130,75 140,65 C 150,55 160,75 180,65 C 200,55 205,75 220,65 C 235,55 240,75 260,65 C 280,55 285,75 300,65 C 315,55 320,75 340,65 C 360,55 365,75 375,65 C 385,55 390,65 395,65" 
                              fill="none" 
                              stroke="#94a3b8" 
                              strokeWidth="3.5" 
                              strokeLinecap="round"
                              style={{ 
                                filter: "drop-shadow(0px 0px 10px rgba(148,163,184,0.8)) drop-shadow(0px 0px 25px rgba(148,163,184,0.4))"
                              }}
                            />
                            <motion.circle 
                               initial={{ scale: 0, opacity: 0 }}
                               animate={{ scale: 1, opacity: 1 }}
                               transition={{ duration: 0.3, ease: "easeOut", delay: i * 0.1 + 1.5 }}
                               cx="395" cy="65" r="5" 
                               fill="#0A0E17" 
                               stroke="#94a3b8" 
                               strokeWidth="3" 
                               style={{ filter: "drop-shadow(0 0 12px rgba(148,163,184,0.8))" }}
                            />
                          </>
                        )}
                      </svg>
                    </div>
                  </div>

                  {/* Bottom Stats Panel */}
                  <div className="px-5 pb-5 pt-0 ml-1">
                    <div className="bg-[#151C28] rounded-[16px] p-5 flex relative border border-white/[0.02] shadow-inner">
                       {/* Middle Divider */}
                       <div className="absolute left-[47%] top-5 bottom-5 w-[1px] bg-white/[0.04]" />
                       
                       {/* Left Stat */}
                       <div className="w-[47%] flex flex-col gap-1 pr-4">
                         <div className="text-[9px] text-slate-400/90 uppercase tracking-[0.15em] font-semibold mb-2">Growth Slope</div>
                         <div className="flex items-baseline gap-1">
                           <span className="text-[24px] font-extrabold text-white tracking-tight">
                             {isUp ? '+' : ''}<AnimatedNumber value={trend.slope} />
                           </span>
                           <span className="text-[11px] font-semibold text-slate-500">/ mo</span>
                         </div>
                         <div className="text-[11px] text-slate-500/80 mt-2 font-medium leading-snug">Average monthly<br/>{isUp ? 'increase' : isDown ? 'decrease' : 'change'}</div>
                       </div>

                       {/* Right Stat */}
                       <div className="flex-1 flex flex-col gap-1 pl-5">
                         <div className="text-[9px] text-slate-400/90 uppercase tracking-[0.15em] font-semibold mb-2 leading-snug">R-Value •<br/>Confidence</div>
                         <div className="flex items-end gap-2">
                           <span className="text-[24px] font-extrabold text-white tracking-tight leading-none">
                             {trend.r_value != null ? <AnimatedNumber value={trend.r_value} isPercent /> : "N/A"}
                           </span>
                           {trend.r_value != null && (
                             <span className="text-[11px] font-bold leading-tight" style={{ color: isUp ? '#60a5fa' : isDown ? '#fb7185' : '#94a3b8' }}>
                               {trend.r_value > 0.6 ? <>Strong<br/>fit</> : trend.r_value > 0.3 ? <>Moderate<br/>fit</> : <>Weak<br/>fit</>}
                             </span>
                           )}
                         </div>
                         {trend.r_value != null && (
                           <div className="w-[85%] h-1.5 bg-[#0A0E17] rounded-full overflow-hidden mt-3 shadow-inner">
                             <div 
                               className="h-full rounded-full relative" 
                               style={{ 
                                 width: `${trend.r_value * 100}%`,
                                 backgroundColor: isUp ? '#3b82f6' : isDown ? '#f43f5e' : '#64748b',
                                 boxShadow: `0 0 10px ${isUp ? 'rgba(59,130,246,0.9)' : isDown ? 'rgba(244,63,94,0.9)' : 'rgba(100,116,139,0.9)'}`
                               }}
                             >
                               <div className="absolute right-0 top-0 bottom-0 w-4 bg-white/30 rounded-full" />
                             </div>
                           </div>
                         )}
                       </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}
    </StudioPage>
  );
}

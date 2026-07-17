"use client";

import React, { useState, useEffect, useRef } from "react";
import { datasetsApi, BASE_URL } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";
import { AnimatedLogo } from "@/components/ui/AnimatedLogo";
import { useLayoutStore } from "@/hooks/useLayoutStore";

interface WelcomeFlowProps {
  userName?: string;
}

export const WelcomeFlow: React.FC<WelcomeFlowProps> = ({ userName = "Aadhar" }) => {
  const [phase, setPhase] = useState<"deck" | "loading" | "dashboard">("deck");
  const [active, setActive] = useState(0);
  const [loadPct, setLoadPct] = useState(0);
  const [currentStatusMsg, setCurrentStatusMsg] = useState("");
  const [isClient, setIsClient] = useState(false);
  
  // Dashboard mock animation state
  const [progress, setProgress] = useState(0);
  const [barsGrow, setBarsGrow] = useState(false);
  const [aiRevealed, setAiRevealed] = useState(0);
  
  const queryClient = useQueryClient();
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const setLayoutState = useLayoutStore((s) => s.setLayoutState);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Dashboard animation orchestration
  useEffect(() => {
    if (phase === 'dashboard') {
      const start = performance.now();
      const dur = 1400;
      let frameId: number;
      const step = (t: number) => { 
        const p = Math.min(1, (t - start) / dur); 
        setProgress(p); 
        if (p < 1) {
            frameId = requestAnimationFrame(step); 
        }
      };
      frameId = requestAnimationFrame(step);
      
      const barsTimer = setTimeout(() => setBarsGrow(true), 80);
      const aiTimer = setInterval(() => {
        setAiRevealed(prev => {
          if (prev >= 3) {
            clearInterval(aiTimer);
            return prev;
          }
          return prev + 1;
        });
      }, 520);
      
      const transitionTimer = setTimeout(() => {
          queryClient.invalidateQueries({ queryKey: ["active-dataset"] });
          queryClient.invalidateQueries({ queryKey: ["datasets"] });
          queryClient.invalidateQueries({ queryKey: ["analytics-kpis"] });
          queryClient.invalidateQueries({ queryKey: ["insights"] });
          queryClient.invalidateQueries({ queryKey: ["executiveSummary"] });
          setLayoutState({ isWelcomeActive: false });
      }, 4000);

      return () => {
        cancelAnimationFrame(frameId);
        clearTimeout(barsTimer);
        clearInterval(aiTimer);
        clearTimeout(transitionTimer);
      };
    }
  }, [phase, queryClient]);

  const onScroll = () => {
    if (!scrollRef.current) return;
    const i = Math.round(scrollRef.current.scrollTop / scrollRef.current.clientHeight);
    if (i !== active) setActive(i);
  };

  const goTo = (i: number) => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: i * scrollRef.current.clientHeight, behavior: 'smooth' });
    }
  };

  const triggerUpload = () => fileInputRef.current?.click();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setPhase("loading");
    setLoadPct(0);
    setCurrentStatusMsg("Uploading file...");

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("dataset_name", file.name.replace(/\.[^/.]+$/, ""));
      formData.append("force", "true");

      const res = await datasetsApi.upload(formData);
      const eventSource = new EventSource(`${BASE_URL}/api/v1/datasets/upload/status/${res.job_id}/stream`, { withCredentials: true });
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.status === "failed") {
          setCurrentStatusMsg(data.error_message || "Upload Failed");
          eventSource.close();
        } else if (data.status === "completed") {
          setLoadPct(100);
          setCurrentStatusMsg("Completed! Preparing dashboard...");
          eventSource.close();
          setPhase("dashboard");
        } else {
          setLoadPct(data.progress || 0);
          setCurrentStatusMsg(data.current_step || "Processing...");
        }
      };

      eventSource.onerror = (error) => {
        console.error("SSE Error:", error);
        setCurrentStatusMsg("Connection lost");
        eventSource.close();
      };
    } catch (err) {
      console.error(err);
      setCurrentStatusMsg("Upload failed");
    }
  };

  if (!isClient) return null;

  // Helpers for inline styles based on scroll position
  const rev = (idx: number, delay: number, opts: React.CSSProperties = {}) => {
    const on = active === idx;
    return {
      transition: 'opacity .7s cubic-bezier(.16,1,.3,1), transform .7s cubic-bezier(.16,1,.3,1)',
      transitionDelay: (on ? delay : 0) + 'ms',
      opacity: on ? 1 : 0,
      transform: on ? 'none' : 'translateY(28px)',
      ...opts
    };
  };

  const bars = [
    {m:'Feb',v:182},{m:'Mar',v:214},{m:'Apr',v:258},{m:'May',v:240},
    {m:'Jun',v:302},{m:'Jul',v:331},{m:'Aug',v:295},{m:'Sep',v:358},
    {m:'Oct',v:406},{m:'Nov',v:378},{m:'Dec',v:452},{m:'Jan',v:474,proj:true}
  ];
  
  const ai = [
    "Processed volume rose 12.4% to ₹4,82,750, driven mainly by the Sales category.",
    "1,284 active users this cycle — the highest in the last six months.",
    "3 payments are pending review, ₹6,420 outstanding. Verify before month-end close."
  ];

  const railLabels = ['Welcome','Real-time','Secure','AI','Upload'];
  
  const inDeck = phase === 'deck';
  
  const fmtR = (n: number) => '₹' + Math.round(n).toLocaleString('en-IN');
  const ease = 1 - Math.pow(1 - progress, 3);
  
  const cardBase = (i: number): React.CSSProperties => ({
    background:'rgba(13,17,28,.92)', border:'1px solid rgba(59,130,246,.18)', borderRadius:'20px', padding:'24px', backdropFilter:'blur(16px)',
    transition:'opacity .6s ease, transform .6s ease', transitionDelay:(i*90)+'ms', opacity:phase==='dashboard'?1:0, transform:phase==='dashboard'?'none':'translateY(20px)'
  });
  
  const bigCard = (d: number): React.CSSProperties => ({
    background:'rgba(13,17,28,.92)', border:'1px solid rgba(59,130,246,.18)', borderRadius:'20px', padding:'26px 28px', display:'flex', flexDirection:'column', backdropFilter:'blur(16px)',
    transition:'opacity .6s ease, transform .6s ease', transitionDelay:d+'ms', opacity:phase==='dashboard'?1:0, transform:phase==='dashboard'?'none':'translateY(20px)'
  });

  return (
    <div className="relative h-screen w-full overflow-hidden bg-[#080a11] text-white font-sans antialiased">
      <div className="ws-grain" />

      {/* ambient glow */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-160px] left-[-120px] w-[620px] h-[620px] rounded-full blur-[16px] animate-ws-blob1" style={{background:'radial-gradient(circle,rgba(37,99,235,.16),transparent 68%)'}} />
        <div className="absolute bottom-[-220px] right-[-140px] w-[560px] h-[560px] rounded-full blur-[18px] animate-ws-blob2" style={{background:'radial-gradient(circle,rgba(59,130,246,.1),transparent 70%)'}} />
      </div>

      {/* progress rail */}
      <div className="fixed right-[34px] top-[50%] -translate-y-1/2 z-40 flex flex-col gap-3 items-center" style={{opacity:inDeck?1:0, transition:'opacity .4s ease', pointerEvents:inDeck?'auto':'none'}}>
        {railLabels.map((label, i) => (
          <button key={i} onClick={() => goTo(i)} title={label} style={{
            width: i === active ? '10px' : '8px',
            height: i === active ? '26px' : '8px',
            borderRadius: '99px',
            border: 'none',
            cursor: 'pointer',
            padding: 0,
            transition: 'all .4s cubic-bezier(.16,1,.3,1)',
            background: i === active ? 'linear-gradient(180deg,#4d8bff,#2563eb)' : 'rgba(255,255,255,.18)'
          }} />
        ))}
      </div>

      {/* SCROLL DECK */}
      <div ref={scrollRef} onScroll={onScroll} className="ws-scroll absolute inset-0 h-screen overflow-y-auto z-10" style={{transition:'opacity .5s ease, transform .5s ease', opacity:inDeck?1:0, pointerEvents:inDeck?'auto':'none', transform:inDeck?'none':'scale(1.04)'}}>
        
        {/* 00 — HERO */}
        <section className="ws-snap h-screen flex items-center justify-center relative p-8">
          <div className="text-center max-w-[820px]">
            <div style={rev(0,0)}>
              <div className="mx-auto mb-[30px] flex justify-center animate-ws-float">
                <AnimatedLogo size={96} className="shadow-[inset_0_0_34px_rgba(77,139,255,.3),0_0_48px_rgba(37,99,235,.35)]" />
              </div>
            </div>
            <h1 style={rev(0,140,{margin:'0 0 26px'})}>
              <span className="block text-[15px] font-medium text-[#8b93a3] tracking-[.3px] mb-4">You're signed in</span>
              <span className="block text-[clamp(48px,8vw,88px)] font-extrabold leading-none tracking-[-.03em] text-white">Welcome back, {userName}</span>
            </h1>
            <p style={{...rev(0,320), fontSize:'17px', lineHeight:1.55, color:'#9aa4b5', maxWidth:'540px', margin:'0 auto'}}>Let's get your workspace live. A quick 30-second tour, then drop in a dataset and your dashboard comes alive.</p>
          </div>
          <div style={{...rev(0,620), position:'absolute', bottom:'42px', left:'50%', transform:'translateX(-50%)', display:'flex', flexDirection:'column', alignItems:'center', gap:'10px'}}>
            <span className="text-[11px] tracking-[2px] text-[#5c6473]">SCROLL</span>
            <div className="w-[22px] h-[36px] border-[1.5px] border-white/20 rounded-xl flex justify-center pt-[7px]">
              <div className="w-[3px] h-[7px] rounded-sm bg-[#4d8bff] animate-ws-scroll-hint"></div>
            </div>
          </div>
        </section>

        {/* 01 — REAL-TIME ANALYTICS */}
        <section className="ws-snap h-screen flex items-center justify-center p-8">
          <div className="w-full max-w-[1040px] grid grid-cols-2 gap-[64px] items-center">
            <div>
              <div style={{...rev(1,0), display:'inline-flex', alignItems:'center', gap:'14px', marginBottom:'22px'}}><span className="w-[44px] h-[44px] rounded-xl bg-blue-600/12 border border-blue-500/25 flex items-center justify-center animate-ws-float"><svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M3 12h4l2 6 4-12 2 6h6" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg></span><span className="text-[12px] tracking-[2px] text-[#5c6473]">01 · REAL-TIME</span></div>
              <h2 style={{...rev(1,90), fontSize:'clamp(30px,4vw,46px)', fontWeight:800, lineHeight:1.08, tracking:'-.03em', margin:'0 0 20px'}}>Track metrics & KPIs<br/><em className="not-italic bg-clip-text text-transparent bg-gradient-to-r from-[#4d8bff] to-[#8ab8ff]">as they happen.</em></h2>
              <p style={{...rev(1,170), fontSize:'15.5px', lineHeight:1.6, color:'#9aa4b5', margin:0, maxWidth:'420px'}}>Four headline cards keep KPIs monitored, recent outliers, active trends and forecast horizons in view — refreshing the instant new data lands.</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div style={{...rev(1,180), background:'rgba(13,17,28,.92)', border:'1px solid rgba(59,130,246,.18)', borderRadius:'20px', padding:'22px', backdropFilter:'blur(16px)', boxShadow:'inset 0 1px 0 0 rgba(255,255,255,.05),0 16px 40px -8px rgba(0,0,0,.4)'}}><div className="w-[30px] h-[30px] rounded-[9px] bg-blue-600/20 mb-[34px]"></div><div className="text-[26px] font-extrabold">12</div><div className="text-[12px] text-[#8b93a3] mt-1">KPIs Monitored</div></div>
              <div style={{...rev(1,260), background:'rgba(13,17,28,.92)', border:'1px solid rgba(59,130,246,.18)', borderRadius:'20px', padding:'22px', backdropFilter:'blur(16px)', boxShadow:'inset 0 1px 0 0 rgba(255,255,255,.05),0 16px 40px -8px rgba(0,0,0,.4)'}}><div className="w-[30px] h-[30px] rounded-[9px] bg-[#FFB020]/20 mb-[34px]"></div><div className="text-[26px] font-extrabold text-[#FFB020]">3</div><div className="text-[12px] text-[#8b93a3] mt-1">Recent Outliers</div></div>
              <div style={{...rev(1,340), background:'rgba(13,17,28,.92)', border:'1px solid rgba(59,130,246,.18)', borderRadius:'20px', padding:'22px', backdropFilter:'blur(16px)', boxShadow:'inset 0 1px 0 0 rgba(255,255,255,.05),0 16px 40px -8px rgba(0,0,0,.4)'}}><div className="w-[30px] h-[30px] rounded-[9px] bg-[#37D67A]/20 mb-[34px]"></div><div className="text-[26px] font-extrabold text-[#37D67A]">8</div><div className="text-[12px] text-[#8b93a3] mt-1">Active Trends</div></div>
              <div style={{...rev(1,420), background:'rgba(13,17,28,.92)', border:'1px solid rgba(59,130,246,.18)', borderRadius:'20px', padding:'22px', backdropFilter:'blur(16px)', boxShadow:'inset 0 1px 0 0 rgba(255,255,255,.05),0 16px 40px -8px rgba(0,0,0,.4)'}}><div className="w-[30px] h-[30px] rounded-[9px] bg-indigo-500/20 mb-[34px]"></div><div className="text-[26px] font-extrabold">3</div><div className="text-[12px] text-[#8b93a3] mt-1">Forecast Horizons</div></div>
            </div>
          </div>
        </section>

        {/* 02 — SECURE & RELIABLE */}
        <section className="ws-snap h-screen flex items-center justify-center p-8">
          <div className="w-full max-w-[1040px] grid grid-cols-[1fr_1.1fr] gap-[64px] items-center">
            <div>
              <div style={{...rev(2,0), display:'inline-flex', alignItems:'center', gap:'14px', marginBottom:'22px'}}><span className="w-[44px] h-[44px] rounded-xl bg-blue-600/12 border border-blue-500/25 flex items-center justify-center animate-ws-float" style={{animationDelay:'0.6s'}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z" stroke="#4d8bff" strokeWidth="1.8" strokeLinejoin="round"/><path d="M9 12l2 2 4-4" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg></span><span className="text-[12px] tracking-[2px] text-[#5c6473]">02 · SECURE</span></div>
              <h2 style={{...rev(2,90), fontSize:'clamp(30px,4vw,46px)', fontWeight:800, lineHeight:1.08, tracking:'-.03em', margin:'0 0 20px'}}>Watch it move,<br/><em className="not-italic bg-clip-text text-transparent bg-gradient-to-r from-[#4d8bff] to-[#8ab8ff]">safely stored.</em></h2>
              <p style={{...rev(2,170), fontSize:'15.5px', lineHeight:1.6, color:'#9aa4b5', margin:0, maxWidth:'420px'}}>The main chart plots processed volume month by month and projects the next — all on enterprise-grade security that protects your data.</p>
            </div>
            <div style={{...rev(2,180), background:'rgba(13,17,28,.92)', border:'1px solid rgba(59,130,246,.18)', borderRadius:'20px', padding:'26px', backdropFilter:'blur(16px)', boxShadow:'inset 0 1px 0 0 rgba(255,255,255,.05),0 16px 40px -8px rgba(0,0,0,.4)'}}>
              <div className="flex justify-between items-start mb-[22px]">
                <div><div className="text-[14px] font-semibold text-[#c5cbd6] mb-[7px]">Processed Volume</div><div className="text-[30px] font-extrabold">₹4,82,750</div></div>
                <span className="bg-[#37D67A]/15 text-[#37D67A] text-[12.5px] font-bold py-1 px-[11px] rounded-full">↑ 12.4%</span>
              </div>
              <div className="h-[180px] flex items-end gap-2">
                {bars.map((b, i) => (
                  <div key={i} className="flex-1 flex items-end h-full">
                    <div style={{
                      width: '100%', borderRadius: '5px 5px 0 0',
                      height: (active===2 ? (b.v/480*100) : 0) + '%',
                      transition: 'height .8s cubic-bezier(.16,1,.3,1)', transitionDelay: (active===2 ? 200+i*45 : 0) + 'ms',
                      background: b.proj ? 'repeating-linear-gradient(135deg,rgba(77,139,255,.6) 0 5px,rgba(77,139,255,.22) 5px 10px)' : 'linear-gradient(180deg,#4d8bff,#2563eb)'
                    }}></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* 03 — COLLABORATE / AI */}
        <section className="ws-snap h-screen flex items-center justify-center p-8">
          <div className="w-full max-w-[1040px] grid grid-cols-2 gap-[64px] items-center">
            <div>
              <div style={{...rev(3,0), display:'inline-flex', alignItems:'center', gap:'14px', marginBottom:'22px'}}><span className="w-[44px] h-[44px] rounded-xl bg-blue-600/12 border border-blue-500/25 flex items-center justify-center animate-ws-float" style={{animationDelay:'1.2s'}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="9" cy="8" r="3" stroke="#4d8bff" strokeWidth="1.8"/><path d="M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round"/><circle cx="17" cy="9" r="2.4" stroke="#4d8bff" strokeWidth="1.8"/><path d="M16 14.2c2.4.3 4 2.1 4 5.8" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round"/></svg></span><span className="text-[12px] tracking-[2px] text-[#5c6473]">03 · COLLABORATE</span></div>
              <h2 style={{...rev(3,90), fontSize:'clamp(30px,4vw,46px)', fontWeight:800, lineHeight:1.08, tracking:'-.03em', margin:'0 0 20px'}}>Just <em className="not-italic bg-clip-text text-transparent bg-gradient-to-r from-[#4d8bff] to-[#8ab8ff]">ask the AI.</em></h2>
              <p style={{...rev(3,170), fontSize:'15.5px', lineHeight:1.6, color:'#9aa4b5', margin:0, maxWidth:'420px'}}>The search bar is an AI assistant — ask in plain English, get an executive summary, and share insights with your team. Always mark figures as verified before you rely on them.</p>
            </div>
            <div style={{...rev(3,180), background:'rgba(13,17,28,.92)', border:'1px solid rgba(59,130,246,.18)', borderRadius:'20px', padding:'22px', backdropFilter:'blur(16px)', boxShadow:'inset 0 1px 0 0 rgba(255,255,255,.05),0 16px 40px -8px rgba(0,0,0,.4)'}}>
              <div className="flex items-center gap-[10px] bg-white/5 border border-white/10 rounded-full py-[13px] px-[18px] mb-[18px]">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6b7280" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
                <span className="text-[13px] text-[#8b93a3]">Which category grew fastest?</span>
              </div>
              <div style={rev(3,360)}><div className="flex gap-[10px] text-[13.5px] leading-[1.6] text-[#c5cbd6]"><span className="text-[#4d8bff]">•</span>Sales grew fastest — up 18% month over month.</div></div>
              <div style={rev(3,480)}><div className="flex gap-[10px] text-[13.5px] leading-[1.6] text-[#c5cbd6]"><span className="text-[#4d8bff]">•</span>1,284 active users — a six-month high.</div></div>
              <div style={rev(3,600)}><div className="flex gap-[10px] items-center text-[11.5px] text-[#FFB020] mt-1"><span className="w-[7px] h-[7px] rounded-full bg-[#FFB020] animate-ws-pulse"></span>Mark as verified before relying on this</div></div>
            </div>
          </div>
        </section>

        {/* 04 — UPLOAD */}
        <section className="ws-snap h-screen flex items-center justify-center p-8">
          <div className="w-full max-w-[560px] text-center">
            <div style={{...rev(4,0), display:'inline-flex', alignItems:'center', gap:'14px', marginBottom:'22px'}}><span className="text-[12px] tracking-[2px] text-[#5c6473]">04 · GO LIVE</span></div>
            <h2 style={{...rev(4,90), fontSize:'clamp(30px,4vw,46px)', fontWeight:800, lineHeight:1.08, tracking:'-.03em', margin:'0 0 20px'}}>Drop it in.<br/><em className="not-italic bg-clip-text text-transparent bg-gradient-to-r from-[#4d8bff] to-[#8ab8ff]">Come alive.</em></h2>
            <div style={rev(4,180)}>
              <div className="relative">
                <div className="absolute -inset-0.5 rounded-[22px] overflow-hidden opacity-60 pointer-events-none"><div className="absolute top-1/2 left-1/2 w-[180%] h-[180%] bg-[conic-gradient(from_0deg,transparent_0%,rgba(77,139,255,0.5)_8%,transparent_16%)] -translate-x-1/2 -translate-y-1/2 animate-ws-border-travel"></div></div>
                <div onClick={triggerUpload} className="relative block border-[1.5px] border-dashed border-blue-500/40 rounded-[20px] bg-gradient-to-b from-blue-600/10 to-[#0d111c]/60 py-10 px-8 cursor-pointer transition-all duration-250 backdrop-blur-[20px] hover:border-blue-500/80 hover:bg-blue-600/10 hover:-translate-y-[3px]">
                  <div className="w-[56px] h-[56px] mx-auto mb-4 rounded-[15px] bg-blue-600/15 flex items-center justify-center">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#8ab8ff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 15V3"/><path d="M7 8l5-5 5 5"/><path d="M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"/></svg>
                  </div>
                  <div className="text-[15.5px] font-bold mb-1.5">Click to browse or drag a file here</div>
                  <div className="text-[12.5px] text-[#8b93a3]">CSV or Excel · up to 25 MB · header row required</div>
                </div>
              </div>
              <div className="flex items-center gap-[14px] my-5"><div className="flex-1 h-[1px] bg-white/10"></div><span className="text-[12px] text-gray-500">or</span><div className="flex-1 h-[1px] bg-white/10"></div></div>
              <button onClick={triggerUpload} className="relative overflow-hidden inline-flex items-center gap-[10px] py-[14px] px-[26px] border-none rounded-[14px] bg-gradient-to-r from-blue-600 to-blue-500 text-white text-[15px] font-bold cursor-pointer shadow-[0_10px_30px_rgba(37,99,235,0.4)] transition-all hover:-translate-y-0.5 hover:shadow-[0_14px_36px_rgba(37,99,235,0.55)]">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="#fff"><path d="M12 2l2 6 6 .5-4.6 4 1.5 6L12 15l-4.4 3.5 1.5-6L4.5 8.5 10.5 8z"/></svg>
                <span className="relative z-10">Explore with sample data</span>
                <div className="absolute inset-0 bg-[linear-gradient(100deg,transparent_30%,rgba(255,255,255,0.35)_50%,transparent_70%)] bg-[length:200%_100%] animate-ws-shimmer"></div>
              </button>
            </div>
          </div>
        </section>
      </div>

      {/* ================= LOADING ================= */}
      <section className={`fixed inset-0 z-50 flex items-center justify-center bg-[#05070d]/90 transition-opacity duration-[600ms] ${phase === 'loading' ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
        <div className="text-center w-full max-w-[420px] p-8">
          <div className="w-[64px] h-[64px] mx-auto mb-[28px] border-[3px] border-blue-500/20 border-t-[#4d8bff] rounded-full animate-ws-spin"></div>
          <div className="text-[26px] font-extrabold mb-2.5">Bringing it to life…</div>
          <div className="text-[13.5px] text-[#9aa4b5] mb-6">{currentStatusMsg}</div>
          <div className="h-[6px] rounded-full bg-white/10 overflow-hidden"><div className="h-full bg-gradient-to-r from-blue-600 to-[#4d8bff] rounded-full transition-all duration-100 ease-linear" style={{width: loadPct + '%'}}></div></div>
          <div className="mt-3 text-[13px] font-bold text-[#4d8bff]">{loadPct}%</div>
        </div>
      </section>

      {/* ================= DASHBOARD MOCK ================= */}
      <section className={`fixed inset-0 z-50 flex items-stretch bg-[#05070d] overflow-y-auto transition-opacity duration-[600ms] ${phase === 'dashboard' ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
        <div className="min-h-full w-full bg-[radial-gradient(1000px_560px_at_50%_-10%,rgba(37,99,235,.12),transparent_60%)]">
          <header className="flex items-center gap-6 p-[16px_32px] border-b border-white/5">
            <div className="flex items-center gap-2.5">
              <div className="relative w-[28px] h-[28px]">
                <div className="absolute inset-0 rounded-full border border-[rgba(77,139,255,.32)] shadow-[inset_0_0_10px_rgba(77,139,255,.28)]" style={{background:'radial-gradient(circle at 62% 38%,#101a30,#080c16)'}}></div>
                <div className="absolute inset-0 animate-ws-orbit"><div className="absolute top-1/2 right-[-1px] -translate-y-1/2 w-[5px] h-[5px] rounded-full bg-[#9ac2ff] shadow-[0_0_7px_2px_rgba(122,170,255,.9)]"></div></div>
              </div>
              <span className="text-[17px] font-extrabold tracking-[-.02em] whitespace-nowrap">DataMind</span>
            </div>
            <div className="flex-1 flex items-center gap-2.5 max-w-[560px] mx-auto bg-white/5 border border-white/10 rounded-xl p-[11px_16px]">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6b7280" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
              <span className="text-[13.5px] text-gray-500">Ask AI or search metrics…</span>
            </div>
            <div className="flex items-center gap-4 text-[#8b93a3]">
              <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M18 8A6 6 0 1 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>
              <div className="w-[30px] h-[30px] rounded-full bg-gradient-to-br from-[#4d8bff] to-blue-600"></div>
            </div>
          </header>
          <div className="p-[28px_32px_40px] max-w-[1400px] mx-auto">
            <div className="grid grid-cols-4 gap-4 mb-[22px]">
              <div style={cardBase(0)}><div className="flex items-center gap-3 text-[#9aa4b5] mb-[18px]"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0070F3" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg><span className="text-[14px] font-medium">KPIs Monitored</span></div><div className="text-[38px] font-semibold">{Math.round(12*ease)}</div></div>
              <div style={cardBase(1)}><div className="flex items-center gap-3 text-[#9aa4b5] mb-[18px]"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFB020" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round"><path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg><span className="text-[14px] font-medium">Recent Outliers</span></div><div className="text-[38px] font-semibold text-[#FFB020]">{Math.round(3*ease)}</div></div>
              <div style={cardBase(2)}><div className="flex items-center gap-3 text-[#9aa4b5] mb-[18px]"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#37D67A" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round"><path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/></svg><span className="text-[14px] font-medium">Active Trends</span></div><div className="text-[38px] font-semibold">{Math.round(8*ease)}</div></div>
              <div style={cardBase(3)}><div className="flex items-center gap-3 text-[#9aa4b5] mb-[18px]"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round"><path d="M18 20V10M12 20V4M6 20v-6"/></svg><span className="text-[14px] font-medium">Forecast Horizons</span></div><div className="text-[38px] font-semibold">{Math.round(3*ease)}</div></div>
            </div>
            <div className="grid grid-cols-[1.9fr_1fr] gap-4">
              <div style={bigCard(380)}>
                <div className="flex items-start justify-between mb-1.5"><div><h3 className="text-[20px] font-bold m-0 mb-1.5">Monthly Transaction Performance</h3><p className="text-[13.5px] text-[#9aa4b5] m-0">Total processed volume, with next-month projection</p></div><div className="flex items-center gap-[7px] border border-white/10 rounded-[9px] p-[8px_13px] text-[13px] text-[#c5cbd6]">Last 12 Months <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#8b93a3" strokeWidth="2"><path d="M6 9l6 6 6-6"/></svg></div></div>
                <div className="flex items-center gap-[14px] my-4"><span className="text-[32px] font-extrabold">{fmtR(482750*ease)}</span><span className="inline-flex items-center gap-1 bg-[#37D67A]/15 text-[#37D67A] text-[13px] font-bold p-[5px_10px] rounded-full">↑ 12.4%</span><span className="text-[13px] text-[#9aa4b5]">vs. previous period</span></div>
                <div className="h-[220px] flex items-end gap-2.5 pt-2">
                  {bars.map((b, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center justify-end h-full gap-2"><div className="w-full flex-1 flex items-end"><div style={{width:'100%', borderRadius:'6px 6px 0 0', height:(barsGrow?(b.v/500*100):0)+'%', transition:'height .85s cubic-bezier(.16,1,.3,1)', transitionDelay:(i*55)+'ms', background:b.proj?'repeating-linear-gradient(135deg,rgba(77,139,255,.55) 0 6px,rgba(77,139,255,.2) 6px 12px)':'linear-gradient(180deg,#4d8bff,#2563eb)'}}></div></div><span className="text-[10.5px] text-[#5c6473]">{b.m}</span></div>
                  ))}
                </div>
              </div>
              <div style={bigCard(460)}>
                <div className="flex items-center justify-between mb-[18px]"><div className="flex items-center gap-2"><svg width="17" height="17" viewBox="0 0 24 24" fill="#4d8bff"><path d="M12 2l1.6 4.4L18 8l-4.4 1.6L12 14l-1.6-4.4L6 8l4.4-1.6z"/></svg><span className="text-[13px] font-bold tracking-[.6px] text-[#4d8bff]">AI EXECUTIVE SUMMARY</span></div><span className="inline-flex items-center gap-1 text-[11px] text-[#FFB020]"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#FFB020" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v5M12 16h.01"/></svg>UNVERIFIED</span></div>
                <div className="flex flex-col gap-[14px] flex-1">
                  {ai.map((text, i) => (
                    <div key={i} style={{transition:'opacity .5s ease, transform .5s ease', opacity:i<aiRevealed?1:0, transform:i<aiRevealed?'none':'translateY(8px)'}}><div className="flex gap-2.5 text-[13.5px] leading-[1.55] text-[#c5cbd6]"><span className="text-[#4d8bff] shrink-0">•</span>{text}</div></div>
                  ))}
                </div>
                <button className="self-end mt-5 inline-flex items-center gap-2 p-[11px_18px] border border-white/10 rounded-xl bg-white/5 text-white text-[13.5px] font-semibold cursor-pointer"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3v12M8 11l4 4 4-4"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>Download Report</button>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".csv,.xlsx,.xls" className="hidden" />
    </div>
  );
};

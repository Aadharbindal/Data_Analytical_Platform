"use client";

import React, { useState, useEffect, useRef } from "react";
import { datasetsApi, BASE_URL } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";
import { AnimatedLogo } from "@/components/ui/AnimatedLogo";
import { useLayoutStore } from "@/hooks/useLayoutStore";
import { GuidedTourModal } from "@/components/GuidedTourModal";
import {
  PlayCircle,
  Activity,
  AlertTriangle,
  TrendingUp,
  BarChart2,
  type LucideIcon,
} from "lucide-react";

interface WelcomeFlowProps {
  userName?: string;
}

function StatCard({
  val, label, valColor, accent, icon: Icon, delayMs, isActive
}: {
  val: number,
  label: string,
  valColor: string,
  /** Drives the rim, the face wash, the icon tile and the hover glow, so each
   *  card carries one colour throughout instead of only in its figure. */
  accent: string,
  icon: LucideIcon,
  delayMs: number,
  isActive: boolean
}) {
  const [mounted, setMounted] = useState(false);
  const [count, setCount] = useState(0);

  useEffect(() => {
    let timer1: any;
    let timer2: any;
    if (isActive) {
      timer1 = setTimeout(() => {
        setMounted(true);
        const duration = 900;
        const countDelay = delayMs + 150;
        
        timer2 = setTimeout(() => {
          const startTime = performance.now();
          const step = (now: number) => {
            const progress = Math.min(1, (now - startTime) / duration);
            const eased = 1 - Math.pow(1 - progress, 3);
            setCount(val * eased);
            if (progress < 1) requestAnimationFrame(step);
          };
          requestAnimationFrame(step);
        }, countDelay);
      }, 50);
    } else {
      setMounted(false);
      setCount(0);
    }
    return () => { clearTimeout(timer1); clearTimeout(timer2); };
  }, [isActive, val, delayMs]);

  const baseStyle = {
    opacity: mounted ? 1 : 0,
    transform: mounted ? 'translateY(0) scale(1)' : 'translateY(18px) scale(0.97)',
    transition: `opacity 0.55s cubic-bezier(0.22,1,0.36,1) ${delayMs}ms, transform 0.55s cubic-bezier(0.22,1,0.36,1) ${delayMs}ms`,
  };

  const iconStyle = {
    transform: mounted ? 'scale(1)' : 'scale(0.5)',
    opacity: mounted ? 1 : 0,
    transition: `transform 0.5s cubic-bezier(0.34,1.56,0.64,1) ${delayMs + 120}ms, opacity 0.4s ease ${delayMs + 120}ms`,
  };

  return (
    /* The entrance transform stays on this wrapper by itself. It is an inline
       style, so a Tailwind hover:-translate on the same element would lose to
       it - the card below is free to move because nothing inline touches it. */
    <div style={baseStyle}>
      <div
        className="group relative overflow-hidden rounded-[20px] p-px shadow-[0_8px_24px_rgba(0,0,0,0.35)] transition-transform duration-300 hover:-translate-y-1"
        /* Published as a variable so the icon tile below can glow in this
           card's colour: a Tailwind hover class cannot interpolate a prop. */
        style={{ ["--accent" as string]: accent } as React.CSSProperties}
      >
        {/* Rim in the card's own colour, brightest at the top-left. */}
        <span
          aria-hidden
          className="absolute inset-0 rounded-[20px]"
          style={{
            backgroundImage: `linear-gradient(140deg, ${accent}80 0%, rgba(255,255,255,0.06) 42%, ${accent}1f 100%)`,
          }}
        />

        <div
          className="relative overflow-hidden rounded-[20px] p-[28px_32px]"
          style={{
            backgroundImage: `linear-gradient(180deg, ${accent}14 0%, oklch(0.2 0.012 260) 55%, oklch(0.175 0.012 260) 100%)`,
          }}
        >
          <div className="absolute top-0 left-0 bottom-0 w-[60%] bg-gradient-to-r from-transparent via-[rgba(255,255,255,0.05)] to-transparent pointer-events-none -translate-x-[120%]"
               style={{ animation: mounted ? `wsGlowSweep 1.1s ease-out ${delayMs + 250}ms forwards` : 'none' }}></div>

          {/* Gathers in the corner the rim is brightest at, so hovering reads
              as the card turning toward the light. */}
          <span
            aria-hidden
            className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100"
            style={{
              backgroundImage: `radial-gradient(115% 80% at 12% 0%, ${accent}2e 0%, transparent 70%)`,
            }}
          />

          <div className="flex items-center gap-[14px] relative z-10 mb-[18px]">
            {/* This tile was empty: it carried the centring styles for a child
                that was never there, which is why it read as a plain coloured
                square. The icons match the ones /analytics uses for these same
                four figures. */}
            <div
              className="w-[44px] h-[44px] rounded-[12px] flex items-center justify-center shrink-0 ring-1 ring-inset ring-white/10 transition-shadow duration-300 group-hover:shadow-[0_0_22px_-4px_var(--accent)]"
              style={{
                ...iconStyle,
                backgroundImage: `linear-gradient(160deg, ${accent}4d 0%, ${accent}12 100%)`,
              }}
            >
              <Icon
                className="h-5 w-5 transition-transform duration-300 group-hover:scale-110"
                style={{ color: accent }}
                strokeWidth={2.2}
              />
            </div>
            <div className="text-[14px] font-medium text-[#8b93a3] leading-[1.3]">{label}</div>
          </div>
          <div className={`relative text-[34px] font-bold tracking-tight tabular-nums ${valColor}`}>{Math.round(count)}</div>
        </div>
      </div>
    </div>
  );
}

export const WelcomeFlow: React.FC<WelcomeFlowProps> = ({ userName = "Aadhar" }) => {
  const [phase, setPhase] = useState<"deck" | "loading">("deck");
  const [active, setActive] = useState(0);
  const [loadPct, setLoadPct] = useState(0);
  const [currentStatusMsg, setCurrentStatusMsg] = useState("");
  const [isClient, setIsClient] = useState(false);
  const [pageEntered, setPageEntered] = useState(false);

  const queryClient = useQueryClient();
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const setWelcomeActive = useLayoutStore((s) => s.setWelcomeActive);
  const [tourOpen, setTourOpen] = useState(false);

  useEffect(() => {
    setIsClient(true);
    const t = setTimeout(() => setPageEntered(true), 80);
    return () => clearTimeout(t);
  }, []);

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
      setCurrentStatusMsg("Reading columns and profiling data...");

      // The backend now processes the file on a background thread and
      // reports real progress via this job — no more faking a progress bar
      // while blindly waiting for one request to resolve. EventSource can't
      // set an Authorization header, so the token rides along as a query
      // param instead (get_current_user has a fallback for exactly this).
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      let streamUrl = `${BASE_URL}/api/v1/datasets/upload/status/${res.job_id}/stream`;
      if (token) streamUrl += `?token=${token}`;
      const eventSource = new EventSource(streamUrl, { withCredentials: true });

      eventSource.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        if (data.status === "failed") {
          eventSource.close();
          setCurrentStatusMsg(data.error_message || "Upload failed. Please try again.");
        } else if (data.status === "completed") {
          eventSource.close();
          setLoadPct(100);
          setCurrentStatusMsg("Completed! Preparing dashboard...");
          // No decorative mock step — as soon as these queries refetch, the
          // parent Dashboard swaps WelcomeFlow out for the real dashboard.
          // Invalidating only a handful of keys left every other page's
          // cache (statistics, trend, distribution, ...) pointing at
          // nothing/stale data for this dataset until a hard refresh, same
          // gap as the dataset-switch and later-upload paths.
          await queryClient.invalidateQueries();
          setWelcomeActive(false);
        } else {
          setLoadPct(Math.round(data.progress ?? 0));
          if (data.current_step) setCurrentStatusMsg(data.current_step);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setCurrentStatusMsg((prev) => (prev === "Completed! Preparing dashboard..." ? prev : "Connection lost — please try again."));
      };
    } catch (err) {
      console.error(err);
      setCurrentStatusMsg("Upload failed. Please try again.");
    }
  };

  if (!isClient) return null;

  // Helpers for inline styles based on scroll position
  const rev = (idx: number, delay: number, opts: React.CSSProperties = {}) => {
    const on = idx === 0 ? pageEntered : active === idx;
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

  const inDeck = phase === 'deck';

  return (
    <div className="relative h-screen w-full overflow-hidden bg-[#080a11] text-white font-sans antialiased">
      <div className="ws-grain" />

      {/* ambient glow */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-160px] left-[-120px] w-[620px] h-[620px] rounded-full blur-[16px] animate-ws-blob1" style={{background:'radial-gradient(circle,rgba(37,99,235,.16),transparent 68%)'}} />
        <div className="absolute bottom-[-220px] right-[-140px] w-[560px] h-[560px] rounded-full blur-[18px] animate-ws-blob2" style={{background:'radial-gradient(circle,rgba(59,130,246,.1),transparent 70%)'}} />
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

        </section>

        {/* 01 — REAL-TIME ANALYTICS */}
        <section className="ws-snap h-screen flex items-center justify-center p-8">
          <div className="w-full max-w-[1040px] grid grid-cols-2 gap-[64px] items-center">
            <div>
              <div style={{...rev(1,0), display:'inline-flex', alignItems:'center', gap:'14px', marginBottom:'22px'}}><span className="w-[44px] h-[44px] rounded-xl bg-blue-600/12 border border-blue-500/25 flex items-center justify-center animate-ws-float"><svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M3 12h4l2 6 4-12 2 6h6" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg></span><span className="text-[12px] tracking-[2px] text-[#5c6473]">01 · REAL-TIME</span></div>
              <h2 style={{...rev(1,90), fontSize:'clamp(30px,4vw,46px)', fontWeight:800, lineHeight:1.08, letterSpacing:'-.03em', margin:'0 0 20px'}}>Track metrics & KPIs<br/><em className="not-italic bg-clip-text text-transparent bg-gradient-to-r from-[#4d8bff] to-[#8ab8ff]">as they happen.</em></h2>
              <p style={{...rev(1,170), fontSize:'15.5px', lineHeight:1.6, color:'#9aa4b5', margin:0, maxWidth:'420px'}}>Four headline cards keep KPIs monitored, recent outliers, active trends and forecast horizons in view — refreshing the instant new data lands.</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {[
                /* The accents are the app's own semantic colours - the warning
                   and success tokens, and the violet already established for
                   prediction - rather than four blues picked to look nice. */
                { val: 12, label: 'KPIs Monitored', valColor: 'text-white', accent: '#3b82f6', icon: Activity },
                { val: 3, label: 'Recent Outliers', valColor: 'text-[#FFB020]', accent: '#FFB020', icon: AlertTriangle },
                { val: 8, label: 'Active Trends', valColor: 'text-[#37D67A]', accent: '#37D67A', icon: TrendingUp },
                { val: 3, label: 'Forecast Horizons', valColor: 'text-[#8b5cf6]', accent: '#8b5cf6', icon: BarChart2 }
              ].map((c, i) => (
                <StatCard 
                  key={i}
                  val={c.val}
                  label={c.label}
                  valColor={c.valColor}
                  accent={c.accent}
                  icon={c.icon}
                  delayMs={i * 90}
                  isActive={active === 1}
                />
              ))}
            </div>
          </div>
        </section>

        {/* 02 — SECURE & RELIABLE */}
        <section className="ws-snap h-screen flex items-center justify-center p-8">
          <div className="w-full max-w-[1040px] grid grid-cols-[1fr_1.1fr] gap-[64px] items-center">
            <div>
              <div style={{...rev(2,0), display:'inline-flex', alignItems:'center', gap:'14px', marginBottom:'22px'}}><span className="w-[44px] h-[44px] rounded-xl bg-blue-600/12 border border-blue-500/25 flex items-center justify-center animate-ws-float" style={{animationDelay:'0.6s'}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z" stroke="#4d8bff" strokeWidth="1.8" strokeLinejoin="round"/><path d="M9 12l2 2 4-4" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg></span><span className="text-[12px] tracking-[2px] text-[#5c6473]">02 · SECURE</span></div>
              <h2 style={{...rev(2,90), fontSize:'clamp(30px,4vw,46px)', fontWeight:800, lineHeight:1.08, letterSpacing:'-.03em', margin:'0 0 20px'}}>Watch it move,<br/><em className="not-italic bg-clip-text text-transparent bg-gradient-to-r from-[#4d8bff] to-[#8ab8ff]">safely stored.</em></h2>
              <p style={{...rev(2,170), fontSize:'15.5px', lineHeight:1.6, color:'#9aa4b5', margin:0, maxWidth:'420px'}}>The main chart plots processed volume month by month and projects the next — all on enterprise-grade security that protects your data.</p>
            </div>
            {/* The entrance stays alone on this wrapper: it is an inline style,
                and a Tailwind hover:-translate on the same element would lose
                to it. The card inside is free to move. */}
            <div style={rev(2,180)}>
              <div className="group relative overflow-hidden rounded-[20px] p-px shadow-[0_16px_40px_-8px_rgba(0,0,0,.4)] transition-transform duration-300 hover:-translate-y-1">
                {/* Lit rim, brightest top-left, matching the stat cards on the
                    section before this one. */}
                <span
                  aria-hidden
                  className="absolute inset-0 rounded-[20px]"
                  style={{ backgroundImage: 'linear-gradient(140deg, rgba(77,139,255,.55) 0%, rgba(255,255,255,.06) 42%, rgba(77,139,255,.12) 100%)' }}
                />

                <div
                  className="relative overflow-hidden rounded-[20px] p-[26px] backdrop-blur-[16px]"
                  style={{ backgroundImage: 'linear-gradient(180deg, rgba(37,99,235,.10) 0%, rgba(13,17,28,.95) 55%, rgba(9,12,20,.97) 100%)' }}
                >
                  <div className="flex justify-between items-start mb-[22px] relative">
                    <div><div className="text-[14px] font-semibold text-[#c5cbd6] mb-[7px]">Processed Volume</div><div className="text-[30px] font-extrabold">₹4,82,750</div></div>
                    <span className="bg-[#37D67A]/15 text-[#37D67A] text-[12.5px] font-bold py-1 px-[11px] rounded-full ring-1 ring-inset ring-[#37D67A]/25">↑ 12.4%</span>
                  </div>

                  <div className="relative h-[180px]">
                    {/* Gridlines and a baseline. Bars floating on nothing read
                        as decoration; sitting them on a scale reads as a chart. */}
                    <div aria-hidden className="pointer-events-none absolute inset-0">
                      {[0, 25, 50, 75].map(t => (
                        <div key={t} className="absolute inset-x-0 h-px bg-white/[0.045]" style={{ top: t + '%' }} />
                      ))}
                      <div className="absolute inset-x-0 bottom-0 h-px bg-white/15" />
                    </div>

                    <div className="relative h-full flex items-end gap-2">
                      {bars.map((b, i) => (
                        <div key={i} className="flex-1 flex items-end h-full">
                          <div
                            className="group-hover:brightness-110"
                            style={{
                              width: '100%', borderRadius: '5px 5px 0 0',
                              height: (active===2 ? (b.v/480*100) : 0) + '%',
                              // Both transitions declared here, because an
                              // inline `transition` replaces whatever a utility
                              // class sets. The stagger is written into the
                              // height half only: as a separate transitionDelay
                              // it would apply to filter too, and the last bar
                              // would take most of a second to react to hover.
                              transition: `height .8s cubic-bezier(.16,1,.3,1) ${active===2 ? 200+i*45 : 0}ms, filter .3s ease`,
                              background: b.proj ? 'repeating-linear-gradient(135deg,rgba(77,139,255,.6) 0 5px,rgba(77,139,255,.22) 5px 10px)' : 'linear-gradient(180deg,#4d8bff,#2563eb)',
                              // A lit cap on every bar, from the same direction
                              // the rim is lit, plus its own colour cast below.
                              boxShadow: b.proj
                                ? 'inset 0 1px 0 rgba(255,255,255,.22)'
                                : 'inset 0 1px 0 rgba(255,255,255,.38), 0 6px 18px -8px rgba(77,139,255,.75)',
                            }}
                          ></div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 03 — COLLABORATE / AI */}
        <section className="ws-snap h-screen flex items-center justify-center p-8">
          <div className="w-full max-w-[1040px] grid grid-cols-2 gap-[64px] items-center">
            <div>
              <div style={{...rev(3,0), display:'inline-flex', alignItems:'center', gap:'14px', marginBottom:'22px'}}><span className="w-[44px] h-[44px] rounded-xl bg-blue-600/12 border border-blue-500/25 flex items-center justify-center animate-ws-float" style={{animationDelay:'1.2s'}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="9" cy="8" r="3" stroke="#4d8bff" strokeWidth="1.8"/><path d="M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round"/><circle cx="17" cy="9" r="2.4" stroke="#4d8bff" strokeWidth="1.8"/><path d="M16 14.2c2.4.3 4 2.1 4 5.8" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round"/></svg></span><span className="text-[12px] tracking-[2px] text-[#5c6473]">03 · COLLABORATE</span></div>
              <h2 style={{...rev(3,90), fontSize:'clamp(30px,4vw,46px)', fontWeight:800, lineHeight:1.08, letterSpacing:'-.03em', margin:'0 0 20px'}}>Just <em className="not-italic bg-clip-text text-transparent bg-gradient-to-r from-[#4d8bff] to-[#8ab8ff]">ask the AI.</em></h2>
              <p style={{...rev(3,170), fontSize:'15.5px', lineHeight:1.6, color:'#9aa4b5', margin:0, maxWidth:'420px'}}>The search bar is an AI assistant — ask in plain English, get an executive summary, and share insights with your team. Always mark figures as verified before you rely on them.</p>
            </div>
            {/* Entrance alone on the wrapper, hover on the card inside - the
                same split as the two sections before this one, and for the same
                reason: an inline transform beats a utility class. */}
            <div style={rev(3,180)}>
              <div className="group relative overflow-hidden rounded-[20px] p-px shadow-[0_16px_40px_-8px_rgba(0,0,0,.4)] transition-transform duration-300 hover:-translate-y-1">
                <span
                  aria-hidden
                  className="absolute inset-0 rounded-[20px]"
                  style={{ backgroundImage: 'linear-gradient(140deg, rgba(77,139,255,.55) 0%, rgba(255,255,255,.06) 42%, rgba(77,139,255,.12) 100%)' }}
                />

                <div
                  className="relative overflow-hidden rounded-[20px] p-[22px] backdrop-blur-[16px]"
                  style={{ backgroundImage: 'linear-gradient(180deg, rgba(37,99,235,.10) 0%, rgba(13,17,28,.95) 55%, rgba(9,12,20,.97) 100%)' }}
                >
                  {/* The search bar reads as something typed into rather than a
                      label: it sits in a well, catches light along its top edge,
                      and carries a caret after the question. */}
                  <div
                    className="relative flex items-center gap-[10px] rounded-full py-[13px] px-[18px] mb-[18px] ring-1 ring-inset ring-white/10"
                    style={{ backgroundImage: 'linear-gradient(180deg, rgba(0,0,0,.35) 0%, rgba(255,255,255,.05) 100%)' }}
                  >
                    <span aria-hidden className="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6b7280" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
                    <span className="text-[13px] text-[#8b93a3]">Which category grew fastest?</span>
                    <span aria-hidden className="h-[15px] w-px bg-[#4d8bff] animate-ws-pulse" />
                  </div>

                  <div style={rev(3,360)}><div className="flex gap-[10px] items-baseline text-[13.5px] leading-[1.6] text-[#c5cbd6]"><span aria-hidden className="mt-[7px] h-[5px] w-[5px] shrink-0 rounded-full bg-[#4d8bff] shadow-[0_0_8px_1px_rgba(77,139,255,.6)]" />Sales grew fastest — up 18% month over month.</div></div>
                  <div style={rev(3,480)}><div className="flex gap-[10px] items-baseline text-[13.5px] leading-[1.6] text-[#c5cbd6]"><span aria-hidden className="mt-[7px] h-[5px] w-[5px] shrink-0 rounded-full bg-[#4d8bff] shadow-[0_0_8px_1px_rgba(77,139,255,.6)]" />1,284 active users — a six-month high.</div></div>

                  {/* Given a surface of its own, because it is a caution about
                      the two lines above it rather than a third bullet. */}
                  <div style={rev(3,600)}>
                    <div className="mt-3 flex items-center gap-[10px] rounded-lg py-2 px-[11px] text-[11.5px] text-[#FFB020] ring-1 ring-inset ring-[#FFB020]/25 bg-[#FFB020]/[0.07]">
                      <span aria-hidden className="w-[7px] h-[7px] shrink-0 rounded-full bg-[#FFB020] animate-ws-pulse"></span>
                      Mark as verified before relying on this
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 04 — UPLOAD */}
        <section className="ws-snap h-screen flex items-center justify-center p-8">
          <div className="w-full max-w-[560px] text-center">
            <div style={{...rev(4,0), display:'inline-flex', alignItems:'center', gap:'14px', marginBottom:'22px'}}><span className="text-[12px] tracking-[2px] text-[#5c6473]">04 · GO LIVE</span></div>
            <h2 style={{...rev(4,90), fontSize:'clamp(30px,4vw,46px)', fontWeight:800, lineHeight:1.08, letterSpacing:'-.03em', margin:'0 0 20px'}}>Drop it in.<br/><em className="not-italic bg-clip-text text-transparent bg-gradient-to-r from-[#4d8bff] to-[#8ab8ff]">Come alive.</em></h2>
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
              <div className="flex flex-wrap items-center justify-center gap-3">
                <button
                  onClick={() => setTourOpen(true)}
                  className="relative overflow-hidden inline-flex items-center gap-[10px] py-[14px] px-[26px] border-none rounded-[14px] bg-gradient-to-r from-blue-600 to-blue-500 text-white text-[15px] font-bold cursor-pointer shadow-[0_10px_30px_rgba(37,99,235,0.4)] transition-all hover:-translate-y-0.5 hover:shadow-[0_14px_36px_rgba(37,99,235,0.55)]"
                >
                  <PlayCircle className="relative z-10 h-[18px] w-[18px]" />
                  <span className="relative z-10">Take a guided tour</span>
                  <div className="absolute inset-0 bg-[linear-gradient(100deg,transparent_30%,rgba(255,255,255,0.35)_50%,transparent_70%)] bg-[length:200%_100%] animate-ws-shimmer"></div>
                </button>
              </div>
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

      <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".csv,.xlsx,.xls" className="hidden" />

      <GuidedTourModal open={tourOpen} onClose={() => setTourOpen(false)} />
    </div>
  );
};

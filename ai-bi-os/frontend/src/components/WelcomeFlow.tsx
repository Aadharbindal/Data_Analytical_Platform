"use client";

import React, { useState, useEffect, useRef } from "react";

import { AnimatedLogo } from "@/components/ui/AnimatedLogo";
import { datasetsApi, BASE_URL } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";

interface WelcomeFlowProps {
  userName?: string;
}

export const WelcomeFlow: React.FC<WelcomeFlowProps> = ({ userName = "Aarav" }) => {
  const [phase, setPhase] = useState<"welcome" | "guide" | "upload" | "loading" | "dashboard">("welcome");
  const [slide, setSlide] = useState(0);
  const [loadPct, setLoadPct] = useState(0);
  const [currentStatusMsg, setCurrentStatusMsg] = useState("Initializing…");
  const [isClient, setIsClient] = useState(false);

  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setIsClient(true);
  }, []);



  const goGuide = () => {
    setSlide(0);
    setPhase("guide");
  };
  const triggerUpload = () => {
    fileInputRef.current?.click();
  };

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
          
          queryClient.invalidateQueries({ queryKey: ["active-dataset"] });
          queryClient.invalidateQueries({ queryKey: ["datasets"] });
          queryClient.invalidateQueries({ queryKey: ["analytics-kpis"] });
          queryClient.invalidateQueries({ queryKey: ["insights"] });
          queryClient.invalidateQueries({ queryKey: ["executiveSummary"] });
          
          setTimeout(() => {
            setPhase("dashboard");
          }, 1000);
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
    } catch (err: any) {
      console.error(err);
      setCurrentStatusMsg("Upload failed");
    }
  };

  const nextSlide = () => {
    if (slide < 3) setSlide(s => s + 1);
    else triggerUpload();
  };

  const panelClass = (active: boolean) => 
    `absolute inset-0 flex items-center justify-center transition-all duration-500 ease-in-out ${
      active ? "opacity-100 pointer-events-auto transform-none" : "opacity-0 pointer-events-none translate-y-6"
    }`;

  if (!isClient) return null; // Avoid hydration mismatch

  if (phase === "dashboard") {
    return null;
  }

  const loadStatuses = ['Reading columns…','Mapping fields…','Building charts…','Generating AI summary…'];
  const currentStatus = loadStatuses[Math.min(3, Math.floor(loadPct / 26))];

  return (
    <div className="relative h-full w-full overflow-hidden bg-transparent text-[#e7eaef]">
      {/* Ambient Orbs */}
      <div className="absolute -top-[160px] -left-[120px] w-[460px] h-[460px] rounded-full blur-[30px] pointer-events-none animate-ws-float" style={{ background: 'radial-gradient(circle, rgba(0,112,243,0.12), transparent 70%)' }}></div>
      <div className="absolute -bottom-[180px] -right-[100px] w-[520px] h-[520px] rounded-full blur-[30px] pointer-events-none animate-ws-float-reverse" style={{ background: 'radial-gradient(circle, rgba(0,112,243,0.08), transparent 70%)' }}></div>

      {/* WELCOME PHASE */}
      <section className={panelClass(phase === 'welcome')}>
        <div className="text-center max-w-[600px] p-8">
          <div className="mx-auto mb-[30px] flex justify-center animate-ws-pop">
            <AnimatedLogo size={74} />
          </div>
          <div className="text-[14px] tracking-[0.4px] text-[#8a93a3] mb-3 animate-ws-up" style={{ animationDelay: '0.15s' }}>
            You're signed in
          </div>
          <h1 className="font-bold text-[46px] leading-[1.1] tracking-[-0.6px] m-0 mb-4 font-sans animate-ws-up" style={{ animationDelay: '0.28s' }}>
            Welcome back, {userName}
          </h1>
          <p className="text-[17px] leading-[1.6] text-[#9aa3b2] mx-auto mb-[34px] max-w-[460px] animate-ws-up" style={{ animationDelay: '0.42s' }}>
            Let's get your workspace live. A quick 30-second tour, then drop in a dataset and your dashboard comes alive.
          </p>
          <div className="flex gap-[14px] justify-center animate-ws-up" style={{ animationDelay: '0.56s' }}>
            <button onClick={goGuide} className="px-[30px] py-[14px] border-none rounded-xl text-white font-semibold text-[15px] cursor-pointer shadow-[0_10px_28px_rgba(91,147,240,0.34)] transition-all hover:-translate-y-0.5 hover:shadow-[0_16px_34px_rgba(91,147,240,0.46)]" style={{ background: 'linear-gradient(120deg,#5b93f0,#8b5cf6)' }}>
              Take the tour
            </button>
            <button onClick={triggerUpload} className="px-[26px] py-[14px] border border-white/15 rounded-xl bg-transparent text-[#c9d0da] font-semibold text-[15px] cursor-pointer transition-all hover:bg-white/5">
              Skip to upload
            </button>
          </div>
        </div>
      </section>

      {/* GUIDE PHASE */}
      <section className={panelClass(phase === 'guide')}>
        <div className="w-full max-w-[900px] p-8 flex flex-col items-center">
          <div className="w-full overflow-hidden rounded-[22px] border border-white/10 bg-[#10141d]/60 backdrop-blur-md">
            <div className="flex w-[400%] h-[340px] transition-transform duration-[600ms] ease-[cubic-bezier(0.65,0,0.35,1)]" style={{ transform: `translateX(-${slide * 25}%)` }}>
              
              {/* Slide 1 */}
              <div className="w-1/4 flex items-center gap-[44px] py-[44px] px-[54px]">
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-[11px] tracking-[1.4px] text-[#8b5cf6] mb-[14px] font-sans">STEP 01</div>
                  <h2 className="font-bold text-[28px] leading-[1.2] mb-[14px] font-sans">Your metrics, at a glance</h2>
                  <p className="text-[15px] leading-[1.65] text-[#9aa3b2] m-0">Four headline cards keep the numbers that matter on top — total value, active users, transactions and system health. They refresh the moment new data lands.</p>
                </div>
                <div className="flex-none w-[300px] grid grid-cols-2 gap-3">
                  {[{bg:'rgba(139,92,246,0.18)'},{bg:'rgba(91,147,240,0.18)'},{bg:'rgba(16,185,129,0.18)'},{bg:'rgba(245,158,11,0.18)'}].map((c, i) => (
                    <div key={i} className="bg-[#11151d] border border-white/5 rounded-xl p-[14px]">
                      <div className="w-[26px] h-[26px] rounded-lg mb-[26px]" style={{ background: c.bg }}></div>
                      <div className="w-[60%] h-2 rounded bg-white/15"></div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Slide 2 */}
              <div className="w-1/4 flex items-center gap-[44px] py-[44px] px-[54px]">
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-[11px] tracking-[1.4px] text-[#5b93f0] mb-[14px] font-sans">STEP 02</div>
                  <h2 className="font-bold text-[28px] leading-[1.2] mb-[14px] font-sans">Track performance over time</h2>
                  <p className="text-[15px] leading-[1.65] text-[#9aa3b2] m-0">The main chart plots your processed volume month by month and even projects the next one. Switch the range anytime from the dropdown.</p>
                </div>
                <div className="flex-none w-[300px] bg-[#11151d] border border-white/5 rounded-[14px] p-5 h-[180px] flex items-end gap-[9px]">
                  {[40,62,50,80,66,92].map((h, i) => (
                    <div key={i} className={`flex-1 rounded-t-md origin-bottom animate-ws-bar`} style={{ height: `${h}%`, background: i===5 ? 'linear-gradient(180deg,#8b5cf6,#6d43d8)' : 'linear-gradient(180deg,#5b93f0,#3b6fd0)', animationDelay: `${i*0.2}s` }}></div>
                  ))}
                </div>
              </div>

              {/* Slide 3 */}
              <div className="w-1/4 flex items-center gap-[44px] py-[44px] px-[54px]">
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-[11px] tracking-[1.4px] text-[#10b981] mb-[14px] font-sans">STEP 03</div>
                  <h2 className="font-bold text-[28px] leading-[1.2] mb-[14px] font-sans">Just ask the AI</h2>
                  <p className="text-[15px] leading-[1.65] text-[#9aa3b2] m-0">The top search bar is an assistant. Ask in plain English and it writes an executive summary of your data. Always mark AI figures as verified before you rely on them.</p>
                </div>
                <div className="flex-none w-[300px] flex flex-col gap-3">
                  <div className="flex items-center gap-2.5 bg-[#11151d] border border-white/10 rounded-full py-3 px-4">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6b7484" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
                    <span className="text-[13px] text-[#8a93a3]">Ask AI or search metrics…</span>
                  </div>
                  <div className="self-end max-w-[82%] bg-[#5b93f0]/15 border border-[#5b93f0]/30 rounded-[14px_14px_4px_14px] py-[11px] px-[14px] text-[12.5px] text-[#c9d0da]">Which category grew fastest?</div>
                  <div className="self-start max-w-[88%] bg-[#11151d] border border-white/10 rounded-[14px_14px_14px_4px] py-[11px] px-[14px] text-[12.5px] text-[#9aa3b2]">Sales grew fastest — up 18% MoM. <span className="text-[#f0b429]">● unverified</span></div>
                </div>
              </div>

              {/* Slide 4 */}
              <div className="w-1/4 flex items-center gap-[44px] py-[44px] px-[54px]">
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-[11px] tracking-[1.4px] text-[#f59e0b] mb-[14px] font-sans">STEP 04</div>
                  <h2 className="font-bold text-[28px] leading-[1.2] mb-[14px] font-sans">Upload & you're live</h2>
                  <p className="text-[15px] leading-[1.65] text-[#9aa3b2] m-0 mb-3">Drop a CSV or Excel file (max 25 MB) with a clean header row, or load a sample to explore first. The empty dashboard fills in instantly.</p>
                  <p className="text-[13px] text-[#6b7484] m-0">Tip: keep numbers plain — no currency symbols or commas.</p>
                </div>
                <div className="flex-none w-[300px] border-[1.5px] border-dashed border-[#5b93f0]/40 rounded-2xl bg-[#5b93f0]/5 p-[30px] flex flex-col items-center gap-3.5">
                  <div className="w-[52px] h-[52px] rounded-xl bg-[#5b93f0]/15 flex items-center justify-center">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#5b93f0" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 15V3"/><path d="M7 8l5-5 5 5"/><path d="M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"/></svg>
                  </div>
                  <div className="text-[13.5px] text-[#c9d0da] font-semibold">Drag your file here</div>
                  <div className="text-[12px] text-[#6b7484]">.csv · .xlsx · .xls</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex items-center justify-between w-full mt-6">
            <button onClick={triggerUpload} className="py-2.5 px-4 bg-transparent border-none text-[#8a93a3] font-semibold text-[14px] cursor-pointer">Skip tour</button>
            <div className="flex gap-2">
              {[0,1,2,3].map(i => (
                <button key={i} onClick={() => setSlide(i)} className={`h-[9px] rounded-full border-none cursor-pointer transition-all duration-300 p-0 ${i === slide ? 'w-[26px] bg-gradient-to-r from-[#5b93f0] to-[#8b5cf6]' : 'w-[9px] bg-white/15'}`} />
              ))}
            </div>
            <button onClick={nextSlide} className="flex items-center gap-2 py-3 px-6 rounded-xl text-white font-semibold text-[14px] cursor-pointer shadow-[0_8px_22px_rgba(91,147,240,0.3)] bg-gradient-to-r from-[#5b93f0] to-[#8b5cf6] border-none">
              {slide < 3 ? 'Next' : 'Upload data'}
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
            </button>
          </div>
        </div>
      </section>

      {/* LOADING PHASE */}
      <section className={panelClass(phase === 'loading')}>
        <div className="text-center w-full max-w-[400px] p-8">
          <div className="w-[60px] h-[60px] mx-auto mb-[26px] border-[3px] border-[#5b93f0]/20 border-t-[#5b93f0] rounded-full animate-ws-spin"></div>
          <div className="font-semibold text-[20px] leading-[1.3] mb-2.5 font-sans">Processing your dataset…</div>
          <div className="text-[13.5px] text-[#8a93a3] mb-6">{currentStatusMsg}</div>
          <div className="h-[7px] rounded-full bg-white/10 overflow-hidden">
            <div className="h-full rounded-full transition-[width] duration-100 ease-linear" style={{ width: `${loadPct}%`, background: 'linear-gradient(90deg,#5b93f0,#8b5cf6)' }}></div>
          </div>
          <div className="mt-2.5 font-semibold text-[13px] text-[#5b93f0] font-sans">{loadPct}%</div>
        </div>
      </section>

      {/* HIDDEN FILE INPUT */}
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        accept=".csv,.xlsx,.xls" 
        className="hidden" 
      />
    </div>
  );
};

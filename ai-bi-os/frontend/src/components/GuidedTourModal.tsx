"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";

const N = 7;

// One-time Inter font load, scoped to this modal (rest of the app uses Geist).
function useInterFont() {
  useEffect(() => {
    if (document.getElementById("gt-inter-font")) return;
    const link1 = document.createElement("link");
    link1.rel = "preconnect";
    link1.href = "https://fonts.googleapis.com";
    const link2 = document.createElement("link");
    link2.rel = "preconnect";
    link2.href = "https://fonts.gstatic.com";
    link2.crossOrigin = "anonymous";
    const link3 = document.createElement("link");
    link3.id = "gt-inter-font";
    link3.rel = "stylesheet";
    link3.href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap";
    document.head.append(link1, link2, link3);
  }, []);
}

const Dot = () => <span style={{ width: 11, height: 11, borderRadius: "50%", background: "#33383f" }} />;
const Dots = () => (
  <div style={{ display: "flex", gap: 7, padding: "2px 6px 12px" }}>
    <Dot />
    <Dot />
    <Dot />
  </div>
);

function Slide1() {
  return (
    <section style={{ flex: "0 0 14.2857%", height: "100%", padding: "24px 54px 16px 54px", display: "flex", flexDirection: "column" }}>
      <div style={{ maxWidth: 820 }}>
        <div className="gt-float-in" style={{ fontSize: 12.5, letterSpacing: ".22em", color: "#5b6474", fontWeight: 600, animationDelay: ".02s" }}>
          01 · GET STARTED
        </div>
        <h1 className="gt-float-in" style={{ fontSize: 38, lineHeight: 1.06, fontWeight: 800, margin: "10px 0 10px", color: "#f6f7fa", letterSpacing: "-.02em", animationDelay: ".08s" }}>
          Bring in your data
        </h1>
        <p className="gt-float-in" style={{ fontSize: 16.5, lineHeight: 1.45, color: "#98a1b2", margin: 0, maxWidth: 760, animationDelay: ".14s" }}>
          Drop a CSV, JSON, Parquet or Excel file — DataMind reads the columns and gets to work in seconds.
        </p>
      </div>
      <div
        className="gt-float-in"
        style={{
          marginTop: 16,
          flex: 1,
          border: "1px solid rgba(255,255,255,.07)",
          borderRadius: 16,
          background: "linear-gradient(180deg,rgba(255,255,255,.025),rgba(255,255,255,.005))",
          padding: 12,
          display: "flex",
          flexDirection: "column",
          animationDelay: ".2s",
          overflow: "hidden",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "2px 6px 10px" }}>
          <div style={{ display: "flex", gap: 7 }}>
            <Dot />
            <Dot />
            <Dot />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "#9aa3b3", padding: "4px 10px", border: "1px solid rgba(255,255,255,.08)", borderRadius: 999 }}>
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#3b82f6" }} />0 datasets
          </div>
        </div>
        <div style={{ flex: 1, border: "1.5px dashed rgba(255,255,255,.12)", borderRadius: 14, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8, minHeight: 110 }}>
          <div style={{ width: 44, height: 44, borderRadius: 11, background: "rgba(59,130,246,.12)", display: "flex", alignItems: "center", justifyContent: "center", color: "#5b93ff" }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 16V4M7 9l5-5 5 5" />
              <path d="M4 17v2a1 1 0 001 1h14a1 1 0 001-1v-2" />
            </svg>
          </div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#e9ebf1" }}>
            Drop files here or <span style={{ color: "#5b93ff" }}>browse</span>
          </div>
          <div style={{ fontSize: 12, color: "#6b7382" }}>Supports CSV, JSON, Parquet, Excel</div>
        </div>
        <div style={{ paddingTop: 10, textAlign: "center", color: "#5b6474" }}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" style={{ opacity: 0.7 }}>
            <ellipse cx="12" cy="5" rx="8" ry="3" />
            <path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
          </svg>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#c4cad6", marginTop: 4 }}>No datasets yet</div>
          <div style={{ fontSize: 11.5, marginTop: 2 }}>Upload your first file above to get started.</div>
        </div>
      </div>
    </section>
  );
}

function SlideHeader({ eyebrow, title, caption }: { eyebrow: string; title: string; caption: string }) {
  return (
    <div style={{ maxWidth: 900 }}>
      <div style={{ fontSize: 12.5, letterSpacing: ".22em", color: "#5b6474", fontWeight: 600 }}>{eyebrow}</div>
      <h1 style={{ fontSize: 38, lineHeight: 1.06, fontWeight: 800, margin: "10px 0 10px", color: "#f6f7fa", letterSpacing: "-.02em" }}>{title}</h1>
      <p style={{ fontSize: 16.5, lineHeight: 1.45, color: "#98a1b2", margin: 0 }}>{caption}</p>
    </div>
  );
}

function Slide2() {
  return (
    <section style={{ flex: "0 0 14.2857%", height: "100%", padding: "24px 54px 16px 54px", display: "flex", flexDirection: "column" }}>
      <SlideHeader
        eyebrow="02 · DASHBOARD"
        title="Metrics, computed automatically"
        caption="The moment your data loads, KPI cards, trend charts, and an AI executive summary appear — no dashboard building required."
      />
      <div style={{ marginTop: 16, flex: 1, border: "1px solid rgba(255,255,255,.07)", borderRadius: 16, background: "linear-gradient(180deg,rgba(255,255,255,.025),rgba(255,255,255,.005))", padding: 12, display: "flex", flexDirection: "column", gap: 10, overflow: "hidden" }}>
        <Dots />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
          <div style={{ border: "1px solid rgba(255,255,255,.06)", borderRadius: 12, padding: 12, background: "rgba(255,255,255,.015)" }}>
            <div style={{ width: 30, height: 30, borderRadius: 8, background: "rgba(139,92,246,.14)", color: "#b79bff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 14 }}>$</div>
            <div style={{ fontSize: 12, color: "#8a93a4", marginTop: 8 }}>Total Transaction Value</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#f2f4f8", marginTop: 2 }}>₹34.01L</div>
          </div>
          <div style={{ border: "1px solid rgba(255,255,255,.06)", borderRadius: 12, padding: 12, background: "rgba(255,255,255,.015)" }}>
            <div style={{ width: 30, height: 30, borderRadius: 8, background: "rgba(59,130,246,.14)", color: "#6ea0ff", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="9" cy="8" r="3" />
                <path d="M3 20c0-3 3-5 6-5s6 2 6 5" />
                <circle cx="17" cy="8" r="2.4" />
                <path d="M15 15c3 0 6 1.8 6 5" />
              </svg>
            </div>
            <div style={{ fontSize: 12, color: "#8a93a4", marginTop: 8 }}>Total Transactions</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#f2f4f8", marginTop: 2 }}>971</div>
          </div>
          <div style={{ border: "1px solid rgba(255,255,255,.06)", borderRadius: 12, padding: 12, background: "rgba(255,255,255,.015)" }}>
            <div style={{ width: 30, height: 30, borderRadius: 8, background: "rgba(34,197,94,.14)", color: "#59d996", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="6" width="18" height="12" rx="2" />
                <path d="M3 10h18" />
              </svg>
            </div>
            <div style={{ fontSize: 12, color: "#8a93a4", marginTop: 8 }}>Payment Clearance Rate</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#f2f4f8", marginTop: 2 }}>65.6%</div>
          </div>
        </div>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1.9fr 1fr", gap: 10, minHeight: 0 }}>
          <div style={{ border: "1px solid rgba(255,255,255,.06)", borderRadius: 12, padding: 12, background: "rgba(255,255,255,.015)", display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <div style={{ fontSize: 12, color: "#9aa3b3" }}>Monthly Transaction Activity</div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 2 }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: "#f2f4f8" }}>₹10.16L</div>
              <span style={{ fontSize: 11, fontWeight: 600, color: "#59d996", background: "rgba(34,197,94,.12)", padding: "2px 6px", borderRadius: 999 }}>↑ 0.0%</span>
            </div>
            <svg viewBox="0 0 520 180" preserveAspectRatio="none" style={{ flex: 1, width: "100%", marginTop: 4 }}>
              <defs>
                <linearGradient id="gt-lg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0" stopColor="rgba(59,130,246,.28)" />
                  <stop offset="1" stopColor="rgba(59,130,246,0)" />
                </linearGradient>
              </defs>
              <path d="M10 150 L90 120 L170 155 L250 70 L330 40 L410 95 L500 120 L500 180 L10 180 Z" fill="url(#gt-lg)" />
              <path d="M10 150 L90 120 L170 155 L250 70 L330 40 L410 95 L500 120" fill="none" stroke="#4d8dff" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="900" className="gt-draw-line" />
            </svg>
          </div>
          <div style={{ border: "1px solid rgba(59,130,246,.18)", borderRadius: 12, padding: 12, background: "linear-gradient(180deg,rgba(59,130,246,.07),rgba(59,130,246,.01))" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, letterSpacing: ".16em", color: "#6ea0ff", fontWeight: 700 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l1.8 5.2L19 9l-5.2 1.8L12 16l-1.8-5.2L5 9l5.2-1.8z" />
              </svg>
              AI SUMMARY
            </div>
            <p style={{ fontSize: 12.5, lineHeight: 1.45, color: "#aeb6c5", margin: "8px 0 0" }}>
              The dataset contains 971 transactions worth ₹34.01L, indicating a net outflow this period.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function Slide3() {
  return (
    <section style={{ flex: "0 0 14.2857%", height: "100%", padding: "24px 54px 16px 54px", display: "flex", flexDirection: "column" }}>
      <SlideHeader
        eyebrow="03 · DATA CATALOG"
        title="Every dataset, organized"
        caption="Search across all your datasets by name, domain, or description — with quality and lineage metadata generated automatically."
      />
      <div style={{ marginTop: 16, flex: 1, border: "1px solid rgba(255,255,255,.07)", borderRadius: 16, background: "linear-gradient(180deg,rgba(255,255,255,.025),rgba(255,255,255,.005))", padding: 12, display: "flex", flexDirection: "column", gap: 10, overflow: "hidden" }}>
        <Dots />
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, border: "1px solid rgba(255,255,255,.08)", borderRadius: 12, padding: "10px 14px", background: "rgba(0,0,0,.2)", color: "#727b8c" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="7" />
              <path d="M21 21l-4-4" />
            </svg>
            <span style={{ fontSize: 13 }}>Search by name, domain, or description…</span>
          </div>
          <div style={{ fontSize: 12, color: "#727b8c" }}>1 entries</div>
        </div>
        <div style={{ border: "1px solid rgba(255,255,255,.07)", borderRadius: 14, padding: "12px 14px", background: "rgba(255,255,255,.018)", display: "flex", gap: 12 }}>
          <div style={{ width: 38, height: 38, borderRadius: 9, background: "rgba(59,130,246,.12)", color: "#5b93ff", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <ellipse cx="12" cy="5" rx="8" ry="3" />
              <path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
              <path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" />
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: "#f2f4f8" }}>dataset (3).csv</div>
              <div style={{ fontSize: 11, color: "#727b8c", textAlign: "right" }}>
                7 cols
                <br />
                DataMind OS
              </div>
            </div>
            <div style={{ fontSize: 12.5, color: "#8a93a4", marginTop: 4, maxWidth: 560 }}>Auto-generated catalog entry. Contains 971 rows and 7 columns.</div>
            <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
              <span style={{ fontSize: 11, color: "#6ea0ff", border: "1px solid rgba(59,130,246,.3)", background: "rgba(59,130,246,.08)", padding: "2px 8px", borderRadius: 999 }}>auto-inferred</span>
              <span style={{ fontSize: 11, color: "#6ea0ff", border: "1px solid rgba(59,130,246,.3)", background: "rgba(59,130,246,.08)", padding: "2px 8px", borderRadius: 999 }}>raw-data</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Slide4() {
  return (
    <section style={{ flex: "0 0 14.2857%", height: "100%", padding: "24px 54px 16px 54px", display: "flex", flexDirection: "column" }}>
      <SlideHeader
        eyebrow="04 · ASK"
        title="Ask in plain English"
        caption="Type a question the way you'd say it. DataMind writes the query, runs it, and hands back the answer — with the SQL if you want to check its work."
      />
      <div style={{ marginTop: 16, flex: 1, border: "1px solid rgba(255,255,255,.07)", borderRadius: 16, background: "linear-gradient(180deg,rgba(255,255,255,.025),rgba(255,255,255,.005))", padding: 12, display: "flex", flexDirection: "column", gap: 10, overflow: "hidden" }}>
        <Dots />
        <div style={{ display: "flex", alignItems: "center", gap: 10, border: "1px solid rgba(59,130,246,.25)", borderRadius: 12, padding: "10px 14px", background: "rgba(59,130,246,.05)" }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6ea0ff" strokeWidth="2">
            <path d="M4 12h16M4 6h16M4 18h10" />
          </svg>
          <span style={{ fontSize: 14, color: "#e6e9f0" }}>Show me total revenue by month for 2024</span>
          <span className="gt-pulse" style={{ marginLeft: "auto", width: 2, height: 16, background: "#6ea0ff" }} />
        </div>
        <div style={{ border: "1px solid rgba(255,255,255,.06)", borderRadius: 12, background: "#0a0d13", padding: "10px 14px", fontFamily: "ui-monospace,SFMono-Regular,Menlo,monospace", fontSize: 12.5, color: "#8a93a4" }}>
          <span style={{ color: "#c792ea" }}>SELECT</span> month, <span style={{ color: "#82aaff" }}>SUM</span>(amount) <span style={{ color: "#c792ea" }}>FROM</span> transactions{" "}
          <span style={{ color: "#c792ea" }}>GROUP BY</span> month;
        </div>
        <div style={{ flex: 1, border: "1px solid rgba(255,255,255,.06)", borderRadius: 12, background: "rgba(255,255,255,.015)", padding: "4px 4px", overflow: "hidden" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 0, fontSize: 12.5 }}>
            <div style={{ padding: "8px 14px", color: "#727b8c", borderBottom: "1px solid rgba(255,255,255,.06)" }}>Month</div>
            <div style={{ padding: "8px 14px", color: "#727b8c", borderBottom: "1px solid rgba(255,255,255,.06)" }}>Revenue</div>
            <div style={{ padding: "8px 14px", color: "#727b8c", borderBottom: "1px solid rgba(255,255,255,.06)" }}>Δ MoM</div>
            <div style={{ padding: "8px 14px", color: "#d6dae3" }}>January</div>
            <div style={{ padding: "8px 14px", color: "#d6dae3" }}>₹8.2L</div>
            <div style={{ padding: "8px 14px", color: "#59d996" }}>+4.1%</div>
            <div style={{ padding: "8px 14px", color: "#d6dae3", borderTop: "1px solid rgba(255,255,255,.04)" }}>February</div>
            <div style={{ padding: "8px 14px", color: "#d6dae3", borderTop: "1px solid rgba(255,255,255,.04)" }}>₹9.6L</div>
            <div style={{ padding: "8px 14px", color: "#59d996", borderTop: "1px solid rgba(255,255,255,.04)" }}>+17.0%</div>
            <div style={{ padding: "8px 14px", color: "#d6dae3", borderTop: "1px solid rgba(255,255,255,.04)" }}>March</div>
            <div style={{ padding: "8px 14px", color: "#d6dae3", borderTop: "1px solid rgba(255,255,255,.04)" }}>₹8.9L</div>
            <div style={{ padding: "8px 14px", color: "#ff8686", borderTop: "1px solid rgba(255,255,255,.04)" }}>−7.3%</div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Slide5() {
  return (
    <section style={{ flex: "0 0 14.2857%", height: "100%", padding: "24px 54px 16px 54px", display: "flex", flexDirection: "column" }}>
      <SlideHeader
        eyebrow="05 · INSIGHTS"
        title="The signal, surfaced"
        caption="DataMind reads every column so you don't have to — flagging anomalies, trends, and the one number worth acting on this week."
      />
      <div style={{ marginTop: 16, flex: 1, display: "flex", flexDirection: "column", gap: 10, overflow: "hidden" }}>
        <div style={{ border: "1px solid rgba(255,193,7,.22)", borderRadius: 14, padding: "12px 16px", background: "linear-gradient(180deg,rgba(255,193,7,.06),transparent)", display: "flex", gap: 12 }}>
          <div style={{ width: 34, height: 34, borderRadius: 8, background: "rgba(255,193,7,.14)", color: "#f2c14e", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 9v4M12 17h.01M10.3 4l-8 14a2 2 0 001.7 3h16a2 2 0 001.7-3l-8-14a2 2 0 00-3.4 0z" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 11.5, letterSpacing: ".14em", color: "#f2c14e", fontWeight: 700 }}>ANOMALY</div>
            <div style={{ fontSize: 14, color: "#e6e9f0", marginTop: 3 }}>March clearance rate dropped 7.3% — driven by 41 delayed settlements.</div>
          </div>
        </div>
        <div style={{ border: "1px solid rgba(34,197,94,.22)", borderRadius: 14, padding: "12px 16px", background: "linear-gradient(180deg,rgba(34,197,94,.06),transparent)", display: "flex", gap: 12 }}>
          <div style={{ width: 34, height: 34, borderRadius: 8, background: "rgba(34,197,94,.14)", color: "#59d996", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 17l6-6 4 4 7-7" />
              <path d="M14 8h6v6" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 11.5, letterSpacing: ".14em", color: "#59d996", fontWeight: 700 }}>TREND</div>
            <div style={{ fontSize: 14, color: "#e6e9f0", marginTop: 3 }}>Transaction volume is up 22% quarter-over-quarter, led by the retail segment.</div>
          </div>
        </div>
        <div style={{ border: "1px solid rgba(59,130,246,.24)", borderRadius: 14, padding: "12px 16px", background: "linear-gradient(180deg,rgba(59,130,246,.07),transparent)", display: "flex", gap: 12 }}>
          <div style={{ width: 34, height: 34, borderRadius: 8, background: "rgba(59,130,246,.16)", color: "#6ea0ff", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l1.8 5.2L19 9l-5.2 1.8L12 16l-1.8-5.2L5 9l5.2-1.8z" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 11.5, letterSpacing: ".14em", color: "#6ea0ff", fontWeight: 700 }}>RECOMMENDATION</div>
            <div style={{ fontSize: 14, color: "#e6e9f0", marginTop: 3 }}>Prioritise the 41 delayed settlements to recover ~₹2.4L in pending clearance.</div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Slide6() {
  const tiles = [
    {
      bg: "rgba(59,130,246,.12)",
      color: "#6ea0ff",
      label: "PDF report",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
          <path d="M14 2v6h6" />
        </svg>
      ),
    },
    {
      bg: "rgba(139,92,246,.14)",
      color: "#b79bff",
      label: "Live link",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M10 13a5 5 0 007 0l3-3a5 5 0 00-7-7l-1 1" />
          <path d="M14 11a5 5 0 00-7 0l-3 3a5 5 0 007 7l1-1" />
        </svg>
      ),
    },
    {
      bg: "rgba(34,197,94,.14)",
      color: "#59d996",
      label: "Slack post",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 2L11 13" />
          <path d="M22 2l-7 20-4-9-9-4z" />
        </svg>
      ),
    },
    {
      bg: "rgba(245,158,11,.14)",
      color: "#f2c14e",
      label: "Embed",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M16 18l6-6-6-6" />
          <path d="M8 6l-6 6 6 6" />
        </svg>
      ),
    },
  ];
  return (
    <section style={{ flex: "0 0 14.2857%", height: "100%", padding: "24px 54px 16px 54px", display: "flex", flexDirection: "column" }}>
      <SlideHeader
        eyebrow="06 · SHARE"
        title="Ship it anywhere"
        caption="Turn any view into a link, a PDF, a Slack post, or an embed — permissions and freshness handled for you."
      />
      <div style={{ marginTop: 16, flex: 1, display: "flex", flexDirection: "column", gap: 10, overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10 }}>
          {tiles.map((t) => (
            <div key={t.label} style={{ border: "1px solid rgba(255,255,255,.07)", borderRadius: 13, padding: "12px 14px", background: "rgba(255,255,255,.02)", display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: t.bg, color: t.color, display: "flex", alignItems: "center", justifyContent: "center" }}>{t.icon}</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#e6e9f0" }}>{t.label}</div>
            </div>
          ))}
        </div>
        <div style={{ border: "1px solid rgba(255,255,255,.07)", borderRadius: 13, padding: "6px 6px 6px 12px", background: "rgba(0,0,0,.25)", display: "flex", alignItems: "center", gap: 10 }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6ea0ff" strokeWidth="2">
            <path d="M10 13a5 5 0 007 0l3-3a5 5 0 00-7-7l-1 1" />
            <path d="M14 11a5 5 0 00-7 0l-3 3a5 5 0 007 7l1-1" />
          </svg>
          <span style={{ flex: 1, fontSize: 13, color: "#9aa3b3", fontFamily: "ui-monospace,monospace" }}>datamind.app/s/97a1-transactions</span>
          <button
            type="button"
            style={{ border: "1px solid rgba(59,130,246,.4)", background: "rgba(59,130,246,.12)", color: "#8fb4ff", fontSize: 12.5, fontWeight: 600, padding: "7px 14px", borderRadius: 8, cursor: "pointer" }}
          >
            Copy link
          </button>
        </div>
      </div>
    </section>
  );
}

function Slide7() {
  return (
    <section style={{ flex: "0 0 14.2857%", height: "100%", padding: "24px 54px 16px 54px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center" }}>
      <div style={{ position: "relative", width: 96, height: 96, marginBottom: 8 }}>
        <div className="gt-pulse-glow" style={{ position: "absolute", inset: 0, borderRadius: "50%", background: "radial-gradient(circle, rgba(59,130,246,.35), transparent 70%)" }} />
        <div className="gt-ring-pop" style={{ position: "absolute", inset: 0, borderRadius: "50%", background: "rgba(59,130,246,.14)", border: "1px solid rgba(59,130,246,.4)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#7fb0ff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path className="gt-check-draw" d="M4 12l5 5L20 6" strokeDasharray="60" />
          </svg>
        </div>
      </div>
      <h1 style={{ fontSize: 44, fontWeight: 800, margin: "22px 0 12px", color: "#f6f7fa", letterSpacing: "-.02em" }}>You&apos;re all set</h1>
      <p style={{ fontSize: 18, lineHeight: 1.5, color: "#98a1b2", margin: 0, maxWidth: 520 }}>
        Your workspace is ready. Upload a dataset and DataMind takes it from raw file to executive dashboard — automatically.
      </p>
      <div style={{ display: "flex", gap: 10, marginTop: 26, flexWrap: "wrap", justifyContent: "center" }}>
        <span style={{ fontSize: 13, color: "#aeb6c5", border: "1px solid rgba(255,255,255,.1)", padding: "8px 15px", borderRadius: 999 }}>Auto dashboards</span>
        <span style={{ fontSize: 13, color: "#aeb6c5", border: "1px solid rgba(255,255,255,.1)", padding: "8px 15px", borderRadius: 999 }}>Plain-English queries</span>
        <span style={{ fontSize: 13, color: "#aeb6c5", border: "1px solid rgba(255,255,255,.1)", padding: "8px 15px", borderRadius: 999 }}>AI insights</span>
      </div>
    </section>
  );
}

const SLIDES = [Slide1, Slide2, Slide3, Slide4, Slide5, Slide6, Slide7];

export function GuidedTourModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  useInterFont();
  const [index, setIndex] = useState(0);
  const vpRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const progRef = useRef<HTMLDivElement>(null);
  const backBtnRef = useRef<HTMLButtonElement>(null);
  const dragRef = useRef({ active: false, startX: 0, startY: 0, dx: 0, decided: null as "x" | "y" | null });
  const indexRef = useRef(0);
  indexRef.current = index;

  useEffect(() => {
    if (open) setIndex(0);
  }, [open]);

  const apply = useCallback((dx: number) => {
    const track = trackRef.current;
    const vp = vpRef.current;
    if (!track || !vp) return;
    const idx = indexRef.current;
    const w = vp.clientWidth || 1;
    const pos = idx - dx / w;
    track.style.transform = `translateX(calc(${-idx * (100 / N)}% + ${dx}px))`;
    Array.from(track.children).forEach((p, i) => {
      const el = p as HTMLElement;
      const d = Math.abs(i - pos);
      el.style.opacity = String(Math.max(0.15, 1 - d * 0.85));
      el.style.transform = `scale(${Math.max(0.9, 1 - d * 0.06)})`;
      el.style.transformOrigin = "center";
      el.style.transition = dragRef.current.active ? "none" : "opacity .55s ease, transform .55s ease";
    });
    const rounded = Math.round(pos);
    if (progRef.current) {
      Array.from(progRef.current.children).forEach((s, i) => {
        (s as HTMLElement).style.background = i <= rounded ? "#3b82f6" : "rgba(255,255,255,.09)";
        (s as HTMLElement).style.transition = "background .35s ease";
      });
    }
    if (backBtnRef.current) {
      const atStart = idx === 0;
      backBtnRef.current.style.opacity = atStart ? "0.35" : "1";
      backBtnRef.current.style.pointerEvents = atStart ? "none" : "auto";
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    requestAnimationFrame(() => apply(0));
  }, [open, index, apply]);

  useEffect(() => {
    if (!open) return;
    const vp = vpRef.current;
    if (!vp) return;

    const getX = (e: MouseEvent | TouchEvent) => ("touches" in e ? e.touches[0].clientX : (e as MouseEvent).clientX);
    const getY = (e: MouseEvent | TouchEvent) => ("touches" in e ? e.touches[0].clientY : (e as MouseEvent).clientY);

    const down = (e: MouseEvent | TouchEvent) => {
      dragRef.current = { active: true, startX: getX(e), startY: getY(e), dx: 0, decided: null };
      if (trackRef.current) trackRef.current.style.transition = "none";
      vp.style.cursor = "grabbing";
    };
    const move = (e: MouseEvent | TouchEvent) => {
      const drag = dragRef.current;
      if (!drag.active) return;
      const dx = getX(e) - drag.startX;
      const dy = getY(e) - drag.startY;
      if (drag.decided === null) {
        if (Math.abs(dx) > 6 || Math.abs(dy) > 6) drag.decided = Math.abs(dx) > Math.abs(dy) ? "x" : "y";
      }
      if (drag.decided !== "x") return;
      let d = dx;
      const idx = indexRef.current;
      if ((idx === 0 && d > 0) || (idx === N - 1 && d < 0)) d *= 0.35;
      drag.dx = d;
      apply(d);
    };
    const up = () => {
      const drag = dragRef.current;
      if (!drag.active) return;
      drag.active = false;
      vp.style.cursor = "grab";
      const w = vp.clientWidth;
      const d = drag.dx;
      if (trackRef.current) trackRef.current.style.transition = "";
      const idx = indexRef.current;
      let ni = idx;
      if (d < -w * 0.16) ni = Math.min(N - 1, idx + 1);
      else if (d > w * 0.16) ni = Math.max(0, idx - 1);
      drag.dx = 0;
      if (ni !== idx) setIndex(ni);
      else apply(0);
    };

    vp.addEventListener("mousedown", down);
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
    vp.addEventListener("touchstart", down, { passive: true });
    vp.addEventListener("touchmove", move, { passive: true });
    vp.addEventListener("touchend", up);

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") setIndex((i) => Math.min(N - 1, i + 1));
      else if (e.key === "ArrowLeft") setIndex((i) => Math.max(0, i - 1));
      else if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);

    return () => {
      vp.removeEventListener("mousedown", down);
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
      vp.removeEventListener("touchstart", down);
      vp.removeEventListener("touchmove", move);
      vp.removeEventListener("touchend", up);
      window.removeEventListener("keydown", onKey);
    };
  }, [open, apply, onClose]);

  if (!open) return null;

  const isLast = index === N - 1;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 200,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 32,
        background: "rgba(0,0,0,.75)",
        backdropFilter: "blur(4px)",
        fontFamily: "'Inter', system-ui, sans-serif",
      }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        style={{
          position: "relative",
          width: "100%",
          maxWidth: 1180,
          height: "min(90vh, 830px)",
          background: "linear-gradient(180deg,#12151d 0%,#0a0c12 100%)",
          border: "1px solid rgba(255,255,255,.09)",
          borderRadius: 26,
          boxShadow: "0 40px 120px -30px rgba(0,0,0,.9), 0 0 0 1px rgba(255,255,255,.02) inset",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          color: "#e9ebf1",
        }}
      >
        <div style={{ position: "absolute", inset: 0, pointerEvents: "none", background: "radial-gradient(600px 260px at 78% 0%, rgba(47,107,255,.10), transparent 70%)" }} />

        <div ref={progRef} style={{ display: "flex", gap: 10, padding: "26px 34px 0 34px" }}>
          {Array.from({ length: N }).map((_, i) => (
            <div key={i} style={{ flex: 1, height: 3, borderRadius: 3, background: i === 0 ? "#3b82f6" : "rgba(255,255,255,.09)" }} />
          ))}
        </div>

        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          style={{
            position: "absolute",
            top: 20,
            right: 26,
            width: 34,
            height: 34,
            borderRadius: 10,
            border: "1px solid rgba(255,255,255,.08)",
            background: "rgba(255,255,255,.03)",
            color: "#8b93a3",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 5,
            transition: "background .15s, color .15s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(255,255,255,.09)";
            e.currentTarget.style.color = "#fff";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(255,255,255,.03)";
            e.currentTarget.style.color = "#8b93a3";
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>

        <div ref={vpRef} style={{ flex: 1, position: "relative", overflow: "hidden", cursor: "grab", touchAction: "pan-y" }}>
          <div ref={trackRef} style={{ display: "flex", height: "100%", width: "700%", transition: "transform .55s cubic-bezier(.22,.61,.24,1)", willChange: "transform" }}>
            {SLIDES.map((Slide, i) => (
              <Slide key={i} />
            ))}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 40px 30px 40px", position: "relative", zIndex: 3 }}>
          <button
            ref={backBtnRef}
            type="button"
            onClick={() => setIndex((i) => Math.max(0, i - 1))}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 7,
              padding: "12px 22px",
              borderRadius: 999,
              border: "1px solid rgba(255,255,255,.1)",
              background: "rgba(255,255,255,.03)",
              color: "#c4cad6",
              fontSize: 15,
              fontWeight: 600,
              cursor: "pointer",
              opacity: index === 0 ? 0.35 : 1,
              pointerEvents: index === 0 ? "none" : "auto",
              transition: "opacity .25s, background .2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,.08)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,.03)")}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
              <path d="M15 6l-6 6 6 6" />
            </svg>
            Back
          </button>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#5b6474", letterSpacing: ".05em" }}>
            {index + 1} / {N}
          </div>
          <button
            type="button"
            onClick={() => (isLast ? onClose() : setIndex((i) => Math.min(N - 1, i + 1)))}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "13px 26px",
              borderRadius: 999,
              border: "none",
              background: "linear-gradient(180deg,#4d8dff,#2f6bff)",
              color: "#fff",
              fontSize: 15,
              fontWeight: 700,
              cursor: "pointer",
              boxShadow: "0 8px 26px -6px rgba(47,107,255,.7)",
              transition: "transform .2s, box-shadow .2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-1px)";
              e.currentTarget.style.boxShadow = "0 12px 32px -6px rgba(47,107,255,.85)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "none";
              e.currentTarget.style.boxShadow = "0 8px 26px -6px rgba(47,107,255,.7)";
            }}
          >
            {isLast ? "Enter DataMind" : "Next"}
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
              <path d="M9 6l6 6-6 6" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

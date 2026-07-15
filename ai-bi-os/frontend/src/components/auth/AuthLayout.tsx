"use client";

import React from "react";
import Link from "next/link";
import { AnimatedLogo } from "@/components/ui/AnimatedLogo";

interface AuthLayoutProps {
  children: React.ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  const features = [
    {
      title: "Real-time Analytics",
      desc: "Track metrics and KPIs as they happen.",
      delay: "0.45s",
      floatDelay: "0s",
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M3 12h4l2 6 4-12 2 6h6" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
    },
    {
      title: "Secure & Reliable",
      desc: "Enterprise-grade security to protect your data.",
      delay: "0.55s",
      floatDelay: "0.6s",
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z" stroke="#4d8bff" strokeWidth="1.8" strokeLinejoin="round" />
          <path d="M9 12l2 2 4-4" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
    },
    {
      title: "Collaborate Easily",
      desc: "Work with your team and share insights.",
      delay: "0.65s",
      floatDelay: "1.2s",
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <circle cx="9" cy="8" r="3" stroke="#4d8bff" strokeWidth="1.8" />
          <path d="M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round" />
          <circle cx="17" cy="9" r="2.4" stroke="#4d8bff" strokeWidth="1.8" />
          <path d="M16 14.2c2.4.3 4 2.1 4 5.8" stroke="#4d8bff" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      ),
    },
  ];

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100vh",
        background: "#05070d",
        overflow: "hidden",
        fontFamily: "'Inter', sans-serif",
        boxSizing: "border-box",
        display: "flex",
        alignItems: "center",
      }}
    >
      {/* Ambient background blobs */}
      <div
        className="animate-auth-blob-drift-1"
        style={{
          position: "absolute",
          top: "-120px",
          left: "-80px",
          width: "420px",
          height: "420px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(37,99,235,0.28) 0%, rgba(37,99,235,0) 70%)",
          filter: "blur(10px)",
          pointerEvents: "none",
        }}
      ></div>
      <div
        className="animate-auth-blob-drift-2"
        style={{
          position: "absolute",
          bottom: "-140px",
          right: "120px",
          width: "520px",
          height: "520px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(59,130,246,0.22) 0%, rgba(59,130,246,0) 70%)",
          filter: "blur(10px)",
          pointerEvents: "none",
        }}
      ></div>
      <div
        className="animate-auth-blob-drift-1-reverse"
        style={{
          position: "absolute",
          top: "30%",
          right: "-100px",
          width: "360px",
          height: "360px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(96,165,250,0.18) 0%, rgba(96,165,250,0) 70%)",
          filter: "blur(10px)",
          pointerEvents: "none",
        }}
      ></div>

      <div
        style={{
          position: "relative",
          zIndex: 1,
          display: "flex",
          flexWrap: "nowrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "40px",
          maxWidth: "1400px",
          width: "100%",
          margin: "0 auto",
          padding: "32px 48px",
          boxSizing: "border-box",
          maxHeight: "100vh",
        }}
      >
        {/* LEFT COLUMN */}
        <div style={{ flex: "1 1 480px", minWidth: 0, maxWidth: "640px" }}>
          
          <div className="animate-auth-fade-up" style={{ display: "flex", alignItems: "center", gap: "14px", animationDelay: "0.05s" }}>
            <AnimatedLogo size={56} className="animate-auth-glow-pulse" />
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#fff", letterSpacing: "-0.02em" }}>
              DataMind
            </div>
          </div>

          <div className="animate-auth-fade-up" style={{ display: "inline-flex", marginTop: "20px", animationDelay: "0.15s" }}>
            <div
              style={{
                position: "relative",
                overflow: "hidden",
                padding: "10px 22px",
                borderRadius: "999px",
                background: "rgba(37,99,235,0.12)",
                border: "1px solid rgba(59,130,246,0.35)",
                color: "#6ea3ff",
                fontSize: "14px",
                fontWeight: 600,
                whiteSpace: "nowrap",
              }}
            >
              <span style={{ position: "relative", zIndex: 1, whiteSpace: "nowrap" }}>
                Smart Analytics. Better Decisions.
              </span>
              <div
                className="animate-auth-shimmer"
                style={{
                  position: "absolute",
                  inset: 0,
                  background: "linear-gradient(100deg, transparent 30%, rgba(120,170,255,0.35) 50%, transparent 70%)",
                  backgroundSize: "200% 100%",
                }}
              ></div>
            </div>
          </div>

          <h1
            className="animate-auth-fade-up"
            style={{
              margin: "20px 0 0",
              fontSize: "42px",
              lineHeight: 1.1,
              fontWeight: 800,
              color: "#fff",
              letterSpacing: "-0.02em",
              animationDelay: "0.25s",
            }}
          >
            Welcome back<br />
            to{" "}
            <span
              className="animate-auth-text-glow"
              style={{
                background: "linear-gradient(90deg,#4d8bff,#8ab8ff)",
                WebkitBackgroundClip: "text",
                backgroundClip: "text",
                color: "transparent",
                display: "inline-block",
              }}
            >
              DataMind
            </span>
          </h1>

          <p
            className="animate-auth-fade-up"
            style={{
              margin: "16px 0 0",
              fontSize: "16px",
              lineHeight: 1.5,
              color: "#9aa4b5",
              maxWidth: "520px",
              animationDelay: "0.35s",
            }}
          >
            Access your analytics workspace and turn data into meaningful insights.
          </p>

          <div style={{ display: "flex", gap: "20px", marginTop: "28px", flexWrap: "nowrap" }}>
            {features.map((feat, idx) => (
              <div
                key={idx}
                className="animate-auth-fade-up"
                style={{
                  flex: "1 1 0",
                  minWidth: 0,
                  animationDelay: feat.delay,
                }}
              >
                <div
                  className="animate-auth-icon-float"
                  style={{
                    width: "44px",
                    height: "44px",
                    borderRadius: "12px",
                    background: "rgba(37,99,235,0.12)",
                    border: "1px solid rgba(59,130,246,0.25)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: "12px",
                    animationDelay: feat.floatDelay,
                    transition: "transform 0.2s, background 0.2s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = "scale(1.08)";
                    e.currentTarget.style.background = "rgba(37,99,235,0.2)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = "scale(1)";
                    e.currentTarget.style.background = "rgba(37,99,235,0.12)";
                  }}
                >
                  {feat.icon}
                </div>
                <div style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "4px" }}>
                  {feat.title}
                </div>
                <div style={{ fontSize: "13px", lineHeight: 1.4, color: "#8b93a3" }}>
                  {feat.desc}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT COLUMN: Auth Card passed via children */}
        <div
          className="animate-auth-slide-in-right"
          style={{
            flex: "1 1 380px",
            minWidth: "320px",
            maxWidth: "440px",
            position: "relative",
            animationDelay: "0.3s",
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

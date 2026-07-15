"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import Link from "next/link";
import { AuthLayout } from "@/components/auth/AuthLayout";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await api.post("/api/v1/auth/signup", {
        email,
        password,
        full_name: fullName,
      });

      await api.post("/api/v1/auth/login", {
        email,
        password
      });
      
      const user = await api.get("/api/v1/auth/me");
      login("cookie-auth", user as any);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An error occurred during signup. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout>
      <div
        style={{
          position: "absolute",
          inset: "-2px",
          borderRadius: "26px",
          overflow: "hidden",
          opacity: 0.6,
          pointerEvents: "none",
        }}
      >
        <div
          className="animate-auth-border-travel"
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: "180%",
            height: "180%",
            background: "conic-gradient(from 0deg, transparent 0%, rgba(77,139,255,0.5) 8%, transparent 16%)",
            transformOrigin: "center",
            transform: "translate(-50%, -50%)",
          }}
        ></div>
      </div>

      <div
        style={{
          position: "relative",
          background: "rgba(13,17,28,0.92)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(59,130,246,0.18)",
          borderRadius: "24px",
          padding: "32px 36px",
          boxShadow: "0 30px 80px rgba(0,0,0,0.55)",
        }}
      >
        <h2 style={{ margin: 0, fontSize: "32px", fontWeight: 800, color: "#fff", letterSpacing: "-0.01em" }}>
          Sign up
        </h2>
        <p style={{ margin: "10px 0 0", fontSize: "15px", color: "#8b93a3" }}>
          Create an account to continue
        </p>

        <form onSubmit={handleSignup}>
          <div style={{ marginTop: "22px" }}>
            <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#c5cbd6", marginBottom: "8px" }}>
              Full Name
            </label>
            <div style={{ position: "relative" }}>
              <span style={{ position: "absolute", left: "16px", top: "50%", transform: "translateY(-50%)", color: "#6b7280", display: "flex" }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              </span>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                required
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  padding: "14px 16px 14px 46px",
                  borderRadius: "14px",
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  color: "#fff",
                  fontSize: "15px",
                  fontFamily: "inherit",
                  outline: "none",
                  transition: "border-color 0.25s, box-shadow 0.25s",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "#4d8bff";
                  e.currentTarget.style.boxShadow = "0 0 0 3px rgba(77,139,255,0.18)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              />
            </div>
          </div>

          <div style={{ marginTop: "16px" }}>
            <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#c5cbd6", marginBottom: "8px" }}>
              Email address
            </label>
            <div style={{ position: "relative" }}>
              <span style={{ position: "absolute", left: "16px", top: "50%", transform: "translateY(-50%)", color: "#6b7280", display: "flex" }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M3 6h18v12H3z" stroke="currentColor" strokeWidth="1.6" />
                  <path d="M3 6l9 7 9-7" stroke="currentColor" strokeWidth="1.6" />
                </svg>
              </span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                required
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  padding: "14px 16px 14px 46px",
                  borderRadius: "14px",
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  color: "#fff",
                  fontSize: "15px",
                  fontFamily: "inherit",
                  outline: "none",
                  transition: "border-color 0.25s, box-shadow 0.25s",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "#4d8bff";
                  e.currentTarget.style.boxShadow = "0 0 0 3px rgba(77,139,255,0.18)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              />
            </div>
          </div>

          <div style={{ marginTop: "16px" }}>
            <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#c5cbd6", marginBottom: "8px" }}>
              Password
            </label>
            <div style={{ position: "relative" }}>
              <span style={{ position: "absolute", left: "16px", top: "50%", transform: "translateY(-50%)", color: "#6b7280", display: "flex" }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <rect x="5" y="10" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.6" />
                  <path d="M8 10V7a4 4 0 018 0v3" stroke="currentColor" strokeWidth="1.6" />
                </svg>
              </span>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Create a password"
                required
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  padding: "14px 46px 14px 46px",
                  borderRadius: "14px",
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  color: "#fff",
                  fontSize: "15px",
                  fontFamily: "inherit",
                  outline: "none",
                  transition: "border-color 0.25s, box-shadow 0.25s",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "#4d8bff";
                  e.currentTarget.style.boxShadow = "0 0 0 3px rgba(77,139,255,0.18)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: "absolute",
                  right: "12px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  color: "#6b7280",
                  cursor: "pointer",
                  padding: "6px",
                  display: "flex",
                  transition: "color 0.2s, transform 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = "#9aa4b5";
                  e.currentTarget.style.transform = "translateY(-50%) scale(1.12)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = "#6b7280";
                  e.currentTarget.style.transform = "translateY(-50%) scale(1)";
                }}
              >
                {!showPassword ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M3 12s3.5-7 9-7 9 7 9 7-3.5 7-9 7-9-7-9-7z" stroke="currentColor" strokeWidth="1.6" />
                    <circle cx="12" cy="12" r="2.6" stroke="currentColor" strokeWidth="1.6" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M3 12s3.5-7 9-7c1.6 0 3 .4 4.2 1M21 12s-3.5 7-9 7c-1.6 0-3-.4-4.2-1" stroke="currentColor" strokeWidth="1.6" />
                    <path d="M3 3l18 18" stroke="currentColor" strokeWidth="1.6" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {error && (
            <div style={{ marginTop: "16px", fontSize: "14px", color: "#f87171", background: "rgba(248,113,113,0.1)", padding: "10px 14px", borderRadius: "10px", border: "1px solid rgba(248,113,113,0.2)" }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            style={{
              position: "relative",
              overflow: "hidden",
              width: "100%",
              marginTop: "22px",
              padding: "14px",
              border: "none",
              borderRadius: "14px",
              background: "linear-gradient(90deg,#2563eb,#3b82f6)",
              color: "#fff",
              fontSize: "16px",
              fontWeight: 700,
              fontFamily: "inherit",
              cursor: isLoading ? "not-allowed" : "pointer",
              boxShadow: "0 10px 30px rgba(37,99,235,0.4)",
              transition: "transform 0.15s, boxShadow 0.25s",
              opacity: isLoading ? 0.8 : 1,
            }}
            onMouseEnter={(e) => {
              if (!isLoading) {
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow = "0 14px 36px rgba(37,99,235,0.55)";
              }
            }}
            onMouseLeave={(e) => {
              if (!isLoading) {
                e.currentTarget.style.transform = "translateY(0px)";
                e.currentTarget.style.boxShadow = "0 10px 30px rgba(37,99,235,0.4)";
              }
            }}
            onMouseDown={(e) => {
              if (!isLoading) e.currentTarget.style.transform = "translateY(0px) scale(0.98)";
            }}
            onMouseUp={(e) => {
              if (!isLoading) e.currentTarget.style.transform = "translateY(-2px)";
            }}
          >
            <div
              className="animate-auth-shimmer"
              style={{
                position: "absolute",
                inset: 0,
                background: "linear-gradient(100deg, transparent 30%, rgba(255,255,255,0.35) 50%, transparent 70%)",
                backgroundSize: "200% 100%",
              }}
            ></div>
            {isLoading ? (
              <span style={{ position: "relative", display: "inline-flex", alignItems: "center", gap: "10px", justifyContent: "center", width: "100%" }}>
                <span className="animate-auth-spin" style={{ width: "16px", height: "16px", borderRadius: "50%", border: "2px solid rgba(255,255,255,0.35)", borderTopColor: "#fff", display: "inline-block" }}></span>
                Signing up…
              </span>
            ) : (
              <span style={{ position: "relative" }}>Sign up</span>
            )}
          </button>
        </form>

        <div style={{ marginTop: "18px", textAlign: "center", fontSize: "14px", color: "#8b93a3" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "#5b9dff", textDecoration: "none", fontWeight: 500 }} onMouseEnter={(e) => e.currentTarget.style.textDecoration = "underline"} onMouseLeave={(e) => e.currentTarget.style.textDecoration = "none"}>
            Sign in
          </Link>
        </div>
      </div>
    </AuthLayout>
  );
}

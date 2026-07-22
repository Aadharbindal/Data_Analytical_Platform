"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api";
import { AuthLayout } from "@/components/auth/AuthLayout";

// useSearchParams() must be wrapped in Suspense for production builds
// (works fine without it in dev, which is why this was easy to miss).
export default function VerifyEmailPage() {
  return (
    <AuthLayout>
      <Suspense fallback={<StatusCard status="loading" />}>
        <VerifyEmailInner />
      </Suspense>
    </AuthLayout>
  );
}

function VerifyEmailInner() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setError("Missing verification token.");
      return;
    }
    authApi
      .verifyEmail(token)
      .then(() => setStatus("success"))
      .catch((err: unknown) => {
        setStatus("error");
        setError(err instanceof Error ? err.message : "Verification failed.");
      });
  }, [token]);

  return <StatusCard status={status} error={error} />;
}

function StatusCard({
  status,
  error,
}: {
  status: "loading" | "success" | "error";
  error?: string;
}) {
  return (
    <div
      style={{
        position: "relative",
        background: "rgba(13,17,28,0.92)",
        backdropFilter: "blur(20px)",
        border: "1px solid rgba(59,130,246,0.18)",
        borderRadius: "24px",
        padding: "40px 36px",
        boxShadow: "0 30px 80px rgba(0,0,0,0.55)",
        textAlign: "center",
      }}
    >
      {status === "loading" && (
        <>
          <span
            className="animate-auth-spin"
            style={{
              display: "inline-block",
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              border: "3px solid rgba(255,255,255,0.15)",
              borderTopColor: "#4d8bff",
              marginBottom: "18px",
            }}
          />
          <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "#fff" }}>Verifying your email…</h2>
        </>
      )}

      {status === "success" && (
        <>
          <div
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "50%",
              background: "rgba(16,185,129,0.15)",
              border: "1px solid rgba(16,185,129,0.4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 18px",
            }}
          >
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17l-5-5" stroke="#10b981" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "#fff" }}>Email verified</h2>
          <p style={{ margin: "10px 0 0", fontSize: "14px", color: "#8b93a3" }}>
            Your email address has been confirmed.
          </p>
          <Link
            href="/"
            style={{
              display: "inline-block",
              marginTop: "24px",
              padding: "12px 28px",
              borderRadius: "12px",
              background: "linear-gradient(90deg,#2563eb,#3b82f6)",
              color: "#fff",
              fontSize: "15px",
              fontWeight: 700,
              textDecoration: "none",
            }}
          >
            Go to Dashboard
          </Link>
        </>
      )}

      {status === "error" && (
        <>
          <div
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "50%",
              background: "rgba(244,63,94,0.15)",
              border: "1px solid rgba(244,63,94,0.4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 18px",
            }}
          >
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
              <path d="M12 8v5M12 16h.01" stroke="#f43f5e" strokeWidth="2.4" strokeLinecap="round" />
              <circle cx="12" cy="12" r="9" stroke="#f43f5e" strokeWidth="1.8" />
            </svg>
          </div>
          <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "#fff" }}>Verification failed</h2>
          <p style={{ margin: "10px 0 0", fontSize: "14px", color: "#8b93a3" }}>
            {error || "This link is invalid or has already been used."}
          </p>
          <Link
            href="/settings"
            style={{
              display: "inline-block",
              marginTop: "24px",
              padding: "12px 28px",
              borderRadius: "12px",
              background: "transparent",
              border: "1px solid rgba(255,255,255,0.15)",
              color: "#fff",
              fontSize: "15px",
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            Go to Settings
          </Link>
        </>
      )}
    </div>
  );
}

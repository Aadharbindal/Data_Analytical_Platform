"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { useAuth } from "@/context/AuthContext";
import { Loader2 } from "lucide-react";
import { useLayoutStore } from "@/hooks/useLayoutStore";

export function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, loading } = useAuth();
  const { isWelcomeActive } = useLayoutStore();
  const isAnalytics = (pathname?.startsWith("/analytics") || pathname?.startsWith("/chat")) ?? false;
  const isAuthPage = pathname === "/login" || pathname === "/signup";

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (isAuthPage) {
    return <>{children}</>;
  }

  if (!user) {
    return null; // Will redirect via AuthContext
  }

  const isDashboard = pathname === "/";
  const effectivelyWelcomeActive = isDashboard && isWelcomeActive;

  return (
    <>
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        {!effectivelyWelcomeActive && <Header />}
        <main id="main-layout" className={`flex-1 relative bg-background [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] ${isAnalytics || effectivelyWelcomeActive ? "overflow-hidden" : "overflow-y-auto p-6 pb-12"}`}>
          <div className={`${isAnalytics || effectivelyWelcomeActive ? "h-full w-full" : "mx-auto max-w-7xl"}`}>
            {children}
          </div>
        </main>
      </div>
    </>
  );
}

"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { useAuth } from "@/context/AuthContext";
import { Loader2 } from "lucide-react";
import { useLayoutStore } from "@/hooks/useLayoutStore";
import { useQueryClient } from "@tanstack/react-query";
import { analyticsApi, datasetsApi } from "@/lib/api";

export function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, loading } = useAuth();
  const { isWelcomeActive } = useLayoutStore();
  const queryClient = useQueryClient();
  const isAnalytics = (pathname?.startsWith("/analytics") || pathname?.startsWith("/chat")) ?? false;
  const isAuthPage = pathname === "/login" || pathname === "/signup";
  const isPublicSharePage = pathname?.startsWith("/shared/") ?? false;

  // ── Background prefetch: warm backend + React Query caches on mount ──────────
  React.useEffect(() => {
    if (!user) return;

    // Fire-and-forget: calls /analytics/prefetch which warms backend DataFrame
    // cache + result cache in one request. Seed React Query cache with results.
    queryClient.prefetchQuery({
      queryKey: ["analytics-prefetch"],
      queryFn: async () => {
        const data = await analyticsApi.prefetch();
        // Seed individual query caches from the batch response
        if (data?.kpis) {
          queryClient.setQueryData(["analytics-kpis"], data.kpis);
        }
        if (data?.active_dataset) {
          queryClient.setQueryData(["active-dataset"], data.active_dataset);
        }
        return data;
      },
      staleTime: 5 * 60 * 1000,
    });

    // Also prefetch the datasets list silently
    queryClient.prefetchQuery({
      queryKey: ["datasets"],
      queryFn: () => datasetsApi.list(),
      staleTime: 5 * 60 * 1000,
    });
  }, [user, queryClient]);

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (isAuthPage || isPublicSharePage) {
    return <>{children}</>;
  }

  if (!user && !isAuthPage) {
    // loading=false (spinner already shown above) and no user → redirect
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    return null;
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

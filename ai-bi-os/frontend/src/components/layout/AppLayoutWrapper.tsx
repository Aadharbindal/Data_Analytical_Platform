"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { useAuth } from "@/context/AuthContext";
import { Loader2, Menu } from "lucide-react";
import { useLayoutStore } from "@/hooks/useLayoutStore";
import { useQueryClient } from "@tanstack/react-query";
import { analyticsApi, datasetsApi } from "@/lib/api";

export function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, loading } = useAuth();
  const { isWelcomeActive, setMobileNavOpen } = useLayoutStore();
  const queryClient = useQueryClient();
  const isAnalytics = (pathname?.startsWith("/analytics") || pathname?.startsWith("/chat")) ?? false;
  const isAuthPage = pathname === "/login" || pathname === "/signup";
  const isPublicSharePage = pathname?.startsWith("/shared/") ?? false;
  // The marketing page has to render for people who have never signed in —
  // without this the redirect below would bounce every visitor to /login,
  // which is the problem it exists to solve.
  const isLandingPage = pathname === "/landing";

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

  if (isAuthPage || isPublicSharePage || isLandingPage) {
    return <>{children}</>;
  }

  if (!user && !isAuthPage) {
    // loading=false (spinner already shown above) and no user → redirect.
    // Someone arriving at the root has not asked for anything in particular,
    // so they get the marketing page; someone who typed a deeper URL wanted
    // that page, and sending them to sign in is the shortest way back to it.
    if (typeof window !== "undefined") {
      window.location.href = pathname === "/" ? "/landing" : "/login";
    }
    return null;
  }

  const isDashboard = pathname === "/";
  const effectivelyWelcomeActive = isDashboard && isWelcomeActive;
  const isSettings = pathname?.startsWith("/settings") ?? false;
  const isFullWidthPage = isAnalytics || effectivelyWelcomeActive;
  const isNoPaddingPage = isSettings;

  return (
    <>
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {/* The welcome flow hides the header, which on desktop is fine because
            the sidebar is always on screen. On mobile the sidebar is an
            off-canvas drawer, so without this the drawer would have no trigger
            at all and navigation would be unreachable from the welcome screen. */}
        {effectivelyWelcomeActive && (
          <button
            onClick={() => setMobileNavOpen(true)}
            aria-label="Open navigation"
            className="fixed left-4 top-4 z-30 flex h-10 w-10 items-center justify-center rounded-xl border border-border/60 bg-surface/80 text-muted-foreground backdrop-blur-md transition-colors hover:text-foreground lg:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}
        {!effectivelyWelcomeActive && <Header />}
        <main id="main-layout" className={`flex-1 relative bg-background [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] ${isFullWidthPage || isNoPaddingPage ? "overflow-hidden" : "overflow-y-auto"} ${isNoPaddingPage || isFullWidthPage ? "" : "p-6 pb-12"}`}>
          <div className={`${isFullWidthPage || isNoPaddingPage ? "h-full w-full" : "mx-auto max-w-7xl"}`}>
            {children}
          </div>
        </main>
      </div>
    </>
  );
}

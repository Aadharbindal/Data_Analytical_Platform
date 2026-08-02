"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { AuthProvider } from "@/context/AuthContext";

import { ThemeProvider } from "@/components/ThemeProvider";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000,   // 5 min — data stays fresh across page navigations
            gcTime: 10 * 60 * 1000,     // 10 min — keep in memory even when unmounted
            retry: 1,
            refetchOnWindowFocus: false,
            // `false` here was the reason switching or uploading a dataset
            // left old numbers on screen until a hard refresh: activating a
            // dataset calls invalidateQueries() to mark every page's cached
            // query stale, but that only forces an immediate refetch for
            // pages mounted at that moment. Any page you navigate to *after*
            // switching was inactive at invalidation time, so it just shows
            // its (now-stale) cached data forever — refetchOnMount:false
            // means a mount never rechecks staleness. `true` makes a mount
            // refetch exactly when data is actually stale (elapsed staleTime
            // or an explicit invalidate) and skip the network call otherwise,
            // so normal in-dataset navigation stays cache-fast.
            refetchOnMount: true,
            refetchOnReconnect: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <AuthProvider>
          {children}
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

"use client";

import { useEffect, useState } from "react";

/**
 * Subscribes to a CSS media query from JS.
 *
 * Returns `false` on the server and during the first client render, then the
 * real value immediately after mount. That initial `false` is deliberate:
 * the server has no viewport, so any other default would render one layout on
 * the server and a different one on the client and trip a hydration mismatch.
 * Components that need to avoid a visible flash should render the mobile-safe
 * markup for the false case rather than branching on it for layout-critical
 * structure — Tailwind breakpoints handle pure styling without JS at all.
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia(query);
    setMatches(mql.matches);

    const onChange = (e: MediaQueryListEvent) => setMatches(e.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, [query]);

  return matches;
}

// Matches Tailwind's `lg` breakpoint. The sidebar is a permanent rail at lg and
// above and an off-canvas drawer below it, so this is the one threshold the
// layout shell actually branches on.
export const MOBILE_BREAKPOINT = "(max-width: 1023px)";

export function useIsMobile(): boolean {
  return useMediaQuery(MOBILE_BREAKPOINT);
}

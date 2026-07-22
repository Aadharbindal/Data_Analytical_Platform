"use client";

import * as React from "react";
import { ThemeProvider as NextThemesProvider, useTheme } from "next-themes";
import { type ThemeProviderProps } from "next-themes";

// next-themes (attribute="class") only toggles the class on <html>. <body>'s
// own class list never changes, so some browsers don't reprocess its
// inherited, custom-property-driven background — it visibly lags one theme
// behind everything nested inside it until something changes body's class
// directly. Mirroring the resolved theme onto body's class list too forces
// a direct (not just inherited) style match there, every time it changes.
function BodyThemeSync() {
  const { resolvedTheme } = useTheme();

  React.useEffect(() => {
    if (!resolvedTheme) return;
    document.body.classList.remove("light", "dark");
    document.body.classList.add(resolvedTheme);
  }, [resolvedTheme]);

  return null;
}

export const ACCENT_STORAGE_KEY = "accent-color";

// Applies whatever accent color was picked on the Settings page. Reads
// localStorage directly (not React state) since this needs to run on every
// page, not just Settings, and there's no server-side preference to fetch.
function AccentSync() {
  React.useEffect(() => {
    const saved = localStorage.getItem(ACCENT_STORAGE_KEY);
    if (saved) {
      document.documentElement.style.setProperty("--primary", saved);
      document.documentElement.style.setProperty("--ring", saved);
    }
  }, []);

  return null;
}

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return (
    <NextThemesProvider {...props}>
      <BodyThemeSync />
      <AccentSync />
      {children}
    </NextThemesProvider>
  );
}

import { create } from "zustand";

interface LayoutState {
  isWelcomeActive: boolean;
  setWelcomeActive: (active: boolean) => void;
  /** Off-canvas sidebar drawer, mobile only. Always closed on desktop, where
   *  the sidebar is a permanent rail and this flag is simply unused. */
  isMobileNavOpen: boolean;
  setMobileNavOpen: (open: boolean) => void;
  toggleMobileNav: () => void;
}

export const useLayoutStore = create<LayoutState>((set) => ({
  isWelcomeActive: true,
  setWelcomeActive: (active) => set({ isWelcomeActive: active }),
  isMobileNavOpen: false,
  setMobileNavOpen: (open) => set({ isMobileNavOpen: open }),
  toggleMobileNav: () => set((s) => ({ isMobileNavOpen: !s.isMobileNavOpen })),
}));

import { create } from "zustand";

interface LayoutState {
  isWelcomeActive: boolean;
  setWelcomeActive: (active: boolean) => void;
}

export const useLayoutStore = create<LayoutState>((set) => ({
  isWelcomeActive: true,
  setWelcomeActive: (active) => set({ isWelcomeActive: active }),
}));

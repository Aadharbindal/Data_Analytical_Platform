"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";

export function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAnalytics = pathname?.startsWith("/analytics") ?? false;

  return (
    <>
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className={`flex-1 overflow-y-auto bg-background ${isAnalytics ? "" : "p-6 pb-12"}`}>
          <div className={`${isAnalytics ? "h-full" : "mx-auto max-w-7xl"}`}>
            {children}
          </div>
        </main>
      </div>
    </>
  );
}

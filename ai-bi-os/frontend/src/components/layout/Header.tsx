"use client";

import { Bell, Search, Sun, Moon } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function Header() {
  return (
    <header className="flex h-[72px] shrink-0 items-center gap-x-4 border-b border-border/60 bg-background px-8">
      {/* Breadcrumbs or Context */}
      <div className="flex flex-1 items-center gap-x-4">
        <div className="flex items-center text-[13px] tracking-wide">
          <span className="text-muted-foreground/80 font-medium">Workspace</span>
          <span className="mx-2 text-muted-foreground/50">/</span>
          <span className="font-semibold text-foreground/90">Global Analytics</span>
        </div>
      </div>

      {/* Search and AI Tools */}
      <div className="flex flex-1 items-center justify-end gap-x-5">
        <div className="relative w-full max-w-md group">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search className="h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
          </div>
          <Input
            type="text"
            className="w-full bg-surface border-border/80 pl-9 pr-4 h-10 rounded-xl placeholder:text-muted-foreground/70 focus-visible:ring-2 focus-visible:ring-primary/20 shadow-sm transition-all"
            placeholder="Ask AI or search metrics..."
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-x-1.5 border-l border-border/40 pl-5">
          <Button variant="ghost" size="icon" className="h-9 w-9 rounded-lg text-muted-foreground hover:text-foreground hover:bg-surface transition-all">
            <Bell className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-9 w-9 rounded-lg text-muted-foreground hover:text-foreground hover:bg-surface transition-all">
            <Sun className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}

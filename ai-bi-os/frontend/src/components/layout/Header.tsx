"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { datasetsApi } from "@/lib/api";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { Search, Bell, Sun, Moon } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useTheme } from "next-themes";

export function Header() {
  const qc = useQueryClient();
  const { theme, setTheme } = useTheme();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearch = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && searchQuery.trim()) {
      router.push(`/chat?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery("");
    }
  };

  const { data: activeDataset } = useQuery({
    queryKey: ["activeDataset"],
    queryFn: () => datasetsApi.getActive(),
  });

  const { data: datasets } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => datasetsApi.list(),
  });

  const activateMutation = useMutation({
    mutationFn: (id: string) => datasetsApi.activate(id),
    onSuccess: () => {
      qc.invalidateQueries(); // invalidate all queries so the whole app updates!
    },
  });

  return (
    <header className="flex h-[72px] shrink-0 items-center gap-x-4 border-b border-border/60 bg-background px-8">
      {/* Breadcrumbs or Context */}
      <div className="flex flex-1 items-center gap-x-4">
        <div className="flex items-center text-[13px] tracking-wide">
          <span className="font-semibold text-foreground/90 mr-2">Global Analytics</span>
          
          {datasets && datasets.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger 
                disabled={activateMutation.isPending}
                className="flex items-center gap-1.5 bg-surface border border-border/80 text-xs font-semibold text-foreground rounded-lg px-3 py-1.5 outline-none hover:bg-white/5 transition-colors focus:ring-2 focus:ring-primary/30 shadow-sm cursor-pointer ml-2 max-w-[250px]"
              >
                <span className="truncate">
                  {activeDataset ? activeDataset.name : "Select Dataset"}
                  {activeDataset?.version && activeDataset.version > 1 && ` (v${activeDataset.version})`}
                </span>
                <svg className="h-3 w-3 text-muted-foreground ml-1 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56 bg-surface border border-border">
                {datasets.map((ds) => (
                  <DropdownMenuItem 
                    key={ds.id} 
                    className={`cursor-pointer ${activeDataset?.id === ds.id ? "bg-primary/10 font-semibold text-primary" : ""}`}
                    onClick={() => activateMutation.mutate(ds.id)}
                  >
                    <div className="flex items-center justify-between w-full overflow-hidden">
                      <span className="truncate mr-2" title={ds.name}>{ds.name}</span>
                      {ds.version && ds.version > 1 && (
                        <span className="text-[10px] bg-primary/10 text-primary border border-primary/20 px-1 py-0.2 rounded font-bold">
                          v{ds.version}
                        </span>
                      )}
                    </div>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
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
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearch}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-x-1.5 border-l border-border/40 pl-5">
          <Button variant="ghost" size="icon" className="h-9 w-9 rounded-lg text-muted-foreground hover:text-foreground hover:bg-surface transition-all">
            <Bell className="h-4 w-4" />
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-9 w-9 rounded-lg text-muted-foreground hover:text-foreground hover:bg-surface transition-all"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme</span>
          </Button>
        </div>
      </div>
    </header>
  );
}

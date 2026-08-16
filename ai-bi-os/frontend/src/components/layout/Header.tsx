"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { datasetsApi, notificationsApi } from "@/lib/api";
import type { AppNotification } from "@/lib/types";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { Search, Bell, GitBranch, CheckCheck, Inbox, X, Menu } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useLayoutStore } from "@/hooks/useLayoutStore";

// Backend timestamps are naive UTC strings (datetime.utcnow().isoformat()),
// with no trailing "Z" or offset. `new Date()` treats a date-time string
// with no timezone as *local* time, not UTC — without this normalization,
// every relative time is off by however far the browser's timezone is from
// UTC (e.g. "5h ago" for something that just happened, in UTC+5:30).
function parseUtc(iso: string): Date {
  return new Date(/[Zz]|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : `${iso}Z`);
}

function relativeTime(iso: string): string {
  const diffMs = Date.now() - parseUtc(iso).getTime();
  const min = Math.floor(diffMs / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  if (day < 7) return `${day}d ago`;
  return parseUtc(iso).toLocaleDateString();
}

function NotificationBell() {
  const router = useRouter();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);

  const { data } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationsApi.list(20),
    refetchInterval: 45_000,
    refetchOnWindowFocus: true,
  });

  const items = data?.items ?? [];
  const unreadCount = data?.unread_count ?? 0;

  const markReadMut = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
  const markAllReadMut = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
  const deleteMut = useMutation({
    mutationFn: (id: string) => notificationsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const handleItemClick = (n: AppNotification) => {
    if (!n.is_read) markReadMut.mutate(n.id);
    setOpen(false);
    if (n.rule_id) router.push("/rules");
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger className="relative flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground outline-none transition-all hover:bg-surface hover:text-foreground">
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute right-1.5 top-1.5 flex h-2 w-2">
            <motion.span
              animate={{ scale: [1, 2.4], opacity: [0.65, 0] }}
              transition={{ duration: 1.6, repeat: Infinity, ease: "easeOut" }}
              className="absolute inline-flex h-full w-full rounded-full bg-error"
            />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-error" />
          </span>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={10} className="dock-panel w-[380px] max-w-[92vw] rounded-2xl border border-border/60 bg-popover/95 p-0 shadow-2xl backdrop-blur-xl">
        <div className="flex items-center justify-between border-b border-border/40 px-4 py-3.5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-blue-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_10px_-3px_var(--primary)]">
              <Bell className="h-4 w-4 text-white" />
            </div>
            <span className="text-sm font-semibold text-foreground">Notifications</span>
          </div>
          {unreadCount > 0 && (
            <button
              onClick={() => markAllReadMut.mutate()}
              className="flex items-center gap-1 text-[11px] font-medium text-primary transition-colors hover:text-primary/80"
            >
              <CheckCheck className="h-3 w-3" /> Mark all read
            </button>
          )}
        </div>

        <div className="max-h-[420px] overflow-y-auto">
          {items.length === 0 ? (
            <div className="relative flex flex-col items-center gap-3 overflow-hidden px-6 py-12 text-center">
              <div className="relative flex h-14 w-14 items-center justify-center">
                <motion.div
                  animate={{ scale: [1, 1.25, 1], opacity: [0.5, 0.15, 0.5] }}
                  transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute inset-0 rounded-full bg-primary/40 blur-md"
                />
                <div className="relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-primary to-blue-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_16px_-3px_var(--primary)]">
                  <Inbox className="h-6 w-6 text-white" />
                </div>
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">No notifications yet</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  You&apos;ll see rule triggers and alerts here.
                </p>
              </div>
            </div>
          ) : (
            // Not AnimatePresence-wrapped: this list shrinks (mark-read count
            // changes, and now deletes), and gating the DOM removal on an
            // exit animation completing has left stale rows behind before in
            // this app (see ChatUI.tsx / CustomizeDashboardModal.tsx) — each
            // row still gets its own mount-in fade via `initial`/`animate`.
            items.map((n) => (
              <motion.div
                key={n.id}
                layout
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={() => handleItemClick(n)}
                className={`group relative flex w-full cursor-pointer items-start gap-3 border-b border-border/20 px-4 py-3 text-left transition-colors last:border-b-0 hover:bg-white/[0.03] ${
                  n.is_read ? "" : "bg-primary/[0.04]"
                }`}
              >
                <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-error to-red-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_0_8px_-3px_var(--error)]">
                  <GitBranch className="h-3.5 w-3.5 text-white" />
                </div>
                <div className="min-w-0 flex-1 pr-5">
                  <div className="flex items-center gap-1.5">
                    {!n.is_read && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />}
                    <p className="truncate text-[13px] font-medium text-foreground">{n.title}</p>
                  </div>
                  <p className="mt-0.5 line-clamp-2 text-[12px] text-muted-foreground">{n.message}</p>
                  <p className="mt-1 text-[10px] uppercase tracking-wide text-muted-foreground/50">
                    {relativeTime(n.created_at)}
                  </p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteMut.mutate(n.id); }}
                  title="Dismiss"
                  className="absolute right-2.5 top-3 flex h-5 w-5 items-center justify-center rounded-md text-muted-foreground opacity-0 transition-opacity hover:bg-white/10 hover:text-foreground group-hover:opacity-100"
                >
                  <X className="h-3 w-3" />
                </button>
              </motion.div>
            ))
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function Header() {
  const qc = useQueryClient();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const { toggleMobileNav } = useLayoutStore();

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
    <header className="flex h-[64px] shrink-0 items-center gap-x-2 border-b border-border/60 bg-background px-4 sm:gap-x-4 sm:px-8 lg:h-[72px]">
      {/* Hamburger — opens the off-canvas sidebar drawer. Mobile only; on
          desktop the sidebar is always on screen. */}
      <button
        onClick={toggleMobileNav}
        aria-label="Open navigation"
        className="-ml-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-surface hover:text-foreground lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Breadcrumbs or Context */}
      <div className="flex min-w-0 flex-1 items-center gap-x-4">
        <div className="flex min-w-0 items-center text-[13px] tracking-wide">
          <span className="mr-2 hidden font-semibold text-foreground/90 lg:inline">Global Analytics</span>

          {datasets && datasets.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger
                disabled={activateMutation.isPending}
                className="flex min-w-0 items-center gap-1.5 bg-surface border border-border/80 text-xs font-semibold text-foreground rounded-lg px-3 py-1.5 outline-none hover:bg-white/5 transition-colors focus:ring-2 focus:ring-primary/30 shadow-sm cursor-pointer lg:ml-2 max-w-[160px] sm:max-w-[250px]"
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
      <div className="flex shrink-0 items-center justify-end gap-x-1 md:flex-1 md:gap-x-5">
        {/* Full search field needs room the phone viewport doesn't have once
            the dataset switcher is on screen, so below md it collapses to an
            icon that opens the same AI chat the Enter key here would. */}
        <div className="group relative hidden w-full max-w-md md:block">
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

        <button
          onClick={() => router.push("/chat")}
          aria-label="Ask AI"
          className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-surface hover:text-foreground md:hidden"
        >
          <Search className="h-4 w-4" />
        </button>

        {/* Action Buttons */}
        <div className="flex items-center gap-x-1.5 md:border-l md:border-border/40 md:pl-5">
          <NotificationBell />
        </div>
      </div>
    </header>
  );
}

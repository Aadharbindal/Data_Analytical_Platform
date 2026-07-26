"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageSquarePlus, Pin, PinOff, Trash2, MessagesSquare, MessageSquare, Edit } from "lucide-react";
import { chatApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ChatSession } from "@/lib/types";

const scrollbarHideClass = "[scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden";

function relativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diffMs / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  if (day < 7) return `${day}d ago`;
  return new Date(iso).toLocaleDateString();
}

interface SessionRowProps {
  session: ChatSession;
  active: boolean;
  onSelect: () => void;
}

function SessionRow({ session, active, onSelect }: SessionRowProps) {
  const qc = useQueryClient();
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [hovered, setHovered] = useState(false);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["chat-sessions"] });

  const togglePin = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await chatApi.pin(session.id, !session.is_pinned);
    invalidate();
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirmingDelete) {
      setConfirmingDelete(true);
      return;
    }
    await chatApi.delete(session.id);
    invalidate();
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.12 } }}
      transition={{ type: "spring", stiffness: 450, damping: 34 }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => {
        setHovered(false);
        setConfirmingDelete(false);
      }}
      onClick={onSelect}
      className={cn(
        "group relative flex cursor-pointer items-center gap-3 rounded-[20px] border px-3 py-3 transition-all duration-300",
        active
          ? "border-[#2684FF]/40 bg-[#2684FF]/[0.03] shadow-[0_0_20px_rgba(38,132,255,0.06)]"
          : "border-transparent hover:border-white/[0.08] hover:bg-white/[0.02]"
      )}
    >
      <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-full border bg-[#0a0d14] transition-colors", active ? "border-[#2684FF]/30 shadow-[0_0_10px_rgba(38,132,255,0.15)]" : "border-white/10 group-hover:border-white/20")}>
        <MessagesSquare
          className={cn("h-[18px] w-[18px]", active ? "text-[#2684FF]" : "text-muted-foreground/60 group-hover:text-muted-foreground/80")}
        />
      </div>
      <div className="min-w-0 flex-1">
        <p className={cn("truncate text-[15px] font-medium leading-none mb-1.5 transition-colors", active ? "text-white" : "text-white/70 group-hover:text-white/90")}>
          {session.title || "New chat"}
        </p>
        <div className="flex items-center gap-1.5 text-[12px] text-muted-foreground/70 font-medium tracking-wide whitespace-nowrap overflow-hidden">
          <span className="truncate">{relativeTime(session.updated_at)}</span>
          <span className="text-[#2684FF] text-[6px] opacity-80 shrink-0">●</span>
          <span className="truncate">{session.message_count} msgs</span>
        </div>
      </div>

      <AnimatePresence>
        {(hovered || session.is_pinned) && (
          <motion.div
            initial={{ opacity: 0, x: 6 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 6 }}
            transition={{ duration: 0.12 }}
            className="flex shrink-0 items-center gap-1.5"
          >
            <motion.button
              type="button"
              onClick={togglePin}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              title={session.is_pinned ? "Unpin" : "Pin conversation"}
              className={cn(
                "flex h-[34px] w-[34px] items-center justify-center rounded-xl border transition-all",
                session.is_pinned
                  ? "border-[#2684FF]/30 bg-[#2684FF]/10 text-[#2684FF]"
                  : "border-white/10 bg-white/[0.02] text-muted-foreground/60 hover:text-white hover:bg-white/[0.06] opacity-0 group-hover:opacity-100"
              )}
            >
              {session.is_pinned ? <PinOff className="h-4 w-4" /> : <Pin className="h-4 w-4" />}
            </motion.button>
            {hovered && (
              <motion.button
                type="button"
                onClick={handleDelete}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                title={confirmingDelete ? "Click again to confirm" : "Delete conversation"}
                className={cn(
                  "flex h-[34px] w-[34px] items-center justify-center rounded-xl border transition-all",
                  confirmingDelete 
                    ? "border-red-500/50 bg-red-500/10 text-red-500" 
                    : "border-red-500/20 bg-red-500/[0.02] text-red-400/70 hover:border-red-500/40 hover:text-red-400 hover:bg-red-500/[0.05]"
                )}
              >
                <Trash2 className="h-4 w-4" />
              </motion.button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

interface ChatSessionSidebarProps {
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
}

export function ChatSessionSidebar({ activeSessionId, onSelect, onNewChat }: ChatSessionSidebarProps) {
  const { data: sessions } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: () => chatApi.sessions(),
    refetchOnWindowFocus: false,
  });

  const pinned = (sessions ?? []).filter((s) => s.is_pinned);
  const recent = (sessions ?? []).filter((s) => !s.is_pinned);

  return (
    <div className="flex h-full w-[280px] shrink-0 flex-col border-r border-border/40 bg-background/40 backdrop-blur-sm">
      <div className="p-3">
        <motion.button
          type="button"
          onClick={onNewChat}
          whileHover={{ scale: 1.015 }}
          whileTap={{ scale: 0.98 }}
          className="flex w-full items-center justify-center gap-2 rounded-2xl border border-primary/25 bg-gradient-to-b from-primary/15 to-primary/5 px-3 py-2.5 text-sm font-medium text-primary shadow-[0_0_0_rgba(59,130,246,0)] transition-all hover:border-primary/40 hover:from-primary/20 hover:to-primary/10 hover:shadow-[0_0_16px_rgba(59,130,246,0.15)]"
        >
          <MessageSquarePlus className="h-4 w-4" />
          New chat
        </motion.button>
      </div>

      <div className={cn("flex-1 overflow-y-auto px-3 pb-3", scrollbarHideClass)}>
        {!sessions ? (
          <div className="flex flex-col gap-2 pt-1">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-[52px] animate-pulse rounded-2xl bg-white/[0.03]" />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-4 flex flex-col items-center justify-center rounded-[20px] border border-white/[0.04] bg-[#0c0e14]/40 p-6 shadow-[inset_0_1px_1px_rgba(255,255,255,0.02)]"
          >
            {/* Glowing Icon Section */}
            <div className="relative mb-5 mt-2 flex items-center justify-center">
              {/* Spotlight base */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-8 w-16 bg-[#2684FF]/30 blur-[20px]" />
              <div className="absolute top-full left-1/2 -translate-x-1/2 -translate-y-2 h-1.5 w-10 bg-[#2684FF]/60 blur-[4px]" />
              
              {/* Sparkles */}
              <motion.div animate={{ opacity: [0.2, 1, 0.2] }} transition={{ duration: 3, repeat: Infinity, delay: 0.2 }} className="absolute -left-5 -top-1">
                <svg width="8" height="8" viewBox="0 0 24 24" fill="#2684FF" className="opacity-80"><path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z"/></svg>
              </motion.div>
              <motion.div animate={{ opacity: [0.2, 1, 0.2] }} transition={{ duration: 4, repeat: Infinity, delay: 1 }} className="absolute -right-6 top-3">
                <svg width="6" height="6" viewBox="0 0 24 24" fill="#2684FF" className="opacity-60"><path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z"/></svg>
              </motion.div>
              <motion.div animate={{ opacity: [0.1, 0.8, 0.1] }} transition={{ duration: 2.5, repeat: Infinity, delay: 0.5 }} className="absolute -left-2 top-7">
                <svg width="4" height="4" viewBox="0 0 24 24" fill="#2684FF" className="opacity-70"><path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z"/></svg>
              </motion.div>
              <motion.div animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 3.5, repeat: Infinity, delay: 1.5 }} className="absolute right-0 -top-4">
                <svg width="5" height="5" viewBox="0 0 24 24" fill="#2684FF" className="opacity-90"><path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z"/></svg>
              </motion.div>

              {/* Main Icon with 3 dots */}
              <div className="relative">
                <MessageSquare className="h-11 w-11 text-[#2684FF] drop-shadow-[0_0_12px_rgba(38,132,255,0.7)]" strokeWidth={1.5} />
                <div className="absolute left-1/2 top-[45%] flex -translate-x-1/2 -translate-y-1/2 gap-1">
                  <div className="h-1.5 w-1.5 rounded-full bg-[#2684FF] shadow-[0_0_8px_rgba(38,132,255,0.9)]" />
                  <div className="h-1.5 w-1.5 rounded-full bg-[#2684FF] shadow-[0_0_8px_rgba(38,132,255,0.9)]" />
                  <div className="h-1.5 w-1.5 rounded-full bg-[#2684FF] shadow-[0_0_8px_rgba(38,132,255,0.9)]" />
                </div>
              </div>
            </div>

            <h3 className="mb-1.5 text-[14px] font-semibold text-white/90 tracking-wide">
              No conversations yet
            </h3>
            <p className="mb-5 text-[12px] leading-[1.6] text-muted-foreground/60 text-center px-1">
              Start a new chat and your conversations will show up here.
            </p>

            <button
              onClick={onNewChat}
              className="group flex items-center gap-2 rounded-xl border border-[#2684FF]/25 bg-[#2684FF]/[0.05] px-4 py-2 text-[12px] font-medium text-[#2684FF] transition-all hover:border-[#2684FF]/50 hover:bg-[#2684FF]/[0.1] active:scale-95 shadow-[0_0_15px_rgba(38,132,255,0.05)]"
            >
              <Edit className="h-3.5 w-3.5" />
              Start chatting
            </button>
          </motion.div>
        ) : (
          <>
            {pinned.length > 0 && (
              <div className="mb-1 mt-1">
                <div className="mb-1.5 flex items-center gap-1.5 px-1">
                  <Pin className="h-3 w-3 text-muted-foreground/50" />
                  <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground/60">
                    Pinned
                  </span>
                </div>
                <div className="flex flex-col gap-1">
                  {pinned.map((s) => (
                    <SessionRow key={s.id} session={s} active={s.id === activeSessionId} onSelect={() => onSelect(s.id)} />
                  ))}
                </div>
              </div>
            )}

            {recent.length > 0 && (
              <div className="mt-3">
                <div className="mb-1.5 px-1">
                  <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground/60">
                    Recent
                  </span>
                </div>
                <div className="flex flex-col gap-1">
                  {recent.map((s) => (
                    <SessionRow key={s.id} session={s} active={s.id === activeSessionId} onSelect={() => onSelect(s.id)} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

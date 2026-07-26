"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageSquarePlus, Pin, PinOff, Trash2, MessagesSquare } from "lucide-react";
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
        "group relative flex cursor-pointer items-center gap-2.5 rounded-2xl border px-3 py-2.5 transition-colors",
        active
          ? "border-primary/30 bg-primary/[0.08]"
          : "border-transparent hover:border-border/50 hover:bg-white/[0.03]"
      )}
    >
      <MessagesSquare
        className={cn("h-3.5 w-3.5 shrink-0", active ? "text-primary" : "text-muted-foreground/50")}
      />
      <div className="min-w-0 flex-1">
        <p className={cn("truncate text-[13px] font-medium", active ? "text-foreground" : "text-foreground/80")}>
          {session.title || "New chat"}
        </p>
        <p className="truncate text-[11px] text-muted-foreground/60">
          {relativeTime(session.updated_at)} · {session.message_count} msg{session.message_count === 1 ? "" : "s"}
        </p>
      </div>

      <AnimatePresence>
        {(hovered || session.is_pinned) && (
          <motion.div
            initial={{ opacity: 0, x: 6 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 6 }}
            transition={{ duration: 0.12 }}
            className="flex shrink-0 items-center gap-1"
          >
            <motion.button
              type="button"
              onClick={togglePin}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              title={session.is_pinned ? "Unpin" : "Pin conversation"}
              className={cn(
                "flex h-6 w-6 items-center justify-center rounded-lg transition-colors",
                session.is_pinned
                  ? "text-primary"
                  : "text-muted-foreground/50 opacity-0 group-hover:opacity-100 hover:text-primary"
              )}
            >
              {session.is_pinned ? <PinOff className="h-3.5 w-3.5" /> : <Pin className="h-3.5 w-3.5" />}
            </motion.button>
            {hovered && (
              <motion.button
                type="button"
                onClick={handleDelete}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                title={confirmingDelete ? "Click again to confirm" : "Delete conversation"}
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-lg transition-colors",
                  confirmingDelete ? "bg-error/15 text-error" : "text-muted-foreground/50 hover:text-error"
                )}
              >
                <Trash2 className="h-3.5 w-3.5" />
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
    <div className="flex h-full w-[260px] shrink-0 flex-col border-r border-border/40 bg-background/40 backdrop-blur-sm">
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
            className="mt-4 rounded-2xl border border-dashed border-border/40 bg-white/[0.02] px-4 py-8 text-center text-[13px] leading-relaxed text-muted-foreground/70"
          >
            No conversations yet — start chatting and it&apos;ll show up here.
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

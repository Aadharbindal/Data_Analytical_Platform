"use client";
import React, { useState, useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { chatApi } from "@/lib/api";
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import { Bot, Send, Database, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ChatSessionSidebar } from "@/components/chat/ChatSessionSidebar";
import type { ChatMessage } from "@/lib/types";

// ─── Page-level entrance variants ───────────────────────────────────────────────
const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.04 },
  },
};

// Badge slides in from the right with a rubber-band bounce
const badgeVariants = {
  hidden:  { opacity: 0, x: 32, scale: 0.82 },
  show: {
    opacity: 1, x: 0, scale: 1,
    transition: { type: "spring", stiffness: 380, damping: 18, delay: 0.08 },
  },
};

// Each chat message: blur → clear + slide up
const messageVariants = {
  hidden: { opacity: 0, y: 28, scale: 0.97, filter: "blur(6px)" },
  show: {
    opacity: 1, y: 0, scale: 1, filter: "blur(0px)",
    transition: { type: "spring", stiffness: 240, damping: 26 },
  },
};

// Input bar rises dramatically from below with a spring
const inputVariants = {
  hidden: { opacity: 0, y: 64, scale: 0.96 },
  show: {
    opacity: 1, y: 0, scale: 1,
    transition: { type: "spring", stiffness: 220, damping: 28, delay: 0.28 },
  },
};


function TypewriterText({
  text,
  delay = 300,
  instant = false,
  onComplete,
  onTyping,
}: {
  text: string;
  delay?: number;
  /** Show the full text immediately — used for messages restored from a
   *  saved session, so reopening a conversation doesn't re-type it out. */
  instant?: boolean;
  onComplete?: () => void;
  onTyping?: () => void;
}) {
  const [displayedText, setDisplayedText] = useState(instant ? text : "");

  useEffect(() => {
    if (!text) return;
    if (instant) {
      // Restoring a saved message — set synchronously in the same tick as
      // the state that made `instant` true (session switch), not reacting
      // to an external system, so this is the legitimate "derive state from
      // a changed prop" case React's own docs carve out from the rule.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setDisplayedText(text);
      return;
    }

    setDisplayedText("");
    let currentIndex = 0;

    const startDelay = setTimeout(() => {
      const interval = setInterval(() => {
        if (currentIndex < text.length) {
          setDisplayedText(text.slice(0, currentIndex + 1));
          currentIndex++;
          if (currentIndex % 3 === 0 && onTyping) {
            onTyping();
          }
        } else {
          clearInterval(interval);
        }
      }, 15); // Fast character typing

      return () => clearInterval(interval);
    }, delay);

    return () => clearTimeout(startDelay);
    // onTyping/instant intentionally excluded — onTyping is a fresh inline
    // callback every parent render, and instant never changes for a given
    // message instance, so depending on either would just restart the
    // typewriter mid-animation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, delay]);

  const isTyping = displayedText.length < text.length;

  useEffect(() => {
    if (!isTyping && text.length > 0) {
      onComplete?.();
    }
    // onComplete intentionally excluded — same fresh-inline-callback reason as above.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isTyping, text.length]);

  return (
    <span className="text-[15px] leading-relaxed text-foreground/90 whitespace-pre-wrap break-words">
      {displayedText}
      {isTyping && (
        <motion.span
          animate={{ opacity: [1, 0, 1] }}
          transition={{ duration: 0.6, repeat: Infinity }}
          className="text-primary ml-[2px] inline-block -mb-[2px]"
        >
          ▍
        </motion.span>
      )}
    </span>
  );
}

interface Message {
  id?: string;
  role: "user" | "ai";
  content: string;
  executedSql?: string[];
  chartConfig?: {
    type: "bar" | "line" | "area";
    data: any[];
  };
  /** True for messages restored from a saved session — renders instantly
   *  instead of replaying the typewriter effect. */
  instant?: boolean;
}

const AIMessageBubble: React.FC<{ msg: Message; onTyping?: () => void }> = ({
  msg,
  onTyping,
}) => {
  const [showSql, setShowSql] = useState(false);
  const [isTyping, setIsTyping] = useState(!msg.instant);

  return (
    <div className="flex justify-start gap-5 mb-8 group w-full">
      <div className="relative shrink-0 flex items-center justify-center h-9 w-9 mt-0">
        {/* Ambient halo — a soft, continuous pulse behind the avatar so the
            assistant always reads as "alive", independent of typing state */}
        <motion.div
          animate={{ scale: [1, 1.28, 1], opacity: [0.55, 0.18, 0.55] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          className="absolute w-9 h-9 rounded-full bg-[#2684FF]/40 blur-[6px] pointer-events-none"
        />
        {isTyping && (
          <>
            <motion.div
              animate={{ scale: [1, 1.8], opacity: [1, 0] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
              className="absolute w-9 h-9 rounded-full border-[1.5px] border-[#2684FF] shadow-[0_0_8px_#2684FF] pointer-events-none"
            />
            <motion.div
              animate={{ scale: [1, 1.8], opacity: [1, 0] }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeOut",
                delay: 1,
              }}
              className="absolute w-9 h-9 rounded-full border-[1.5px] border-[#2684FF] shadow-[0_0_8px_#2684FF] pointer-events-none"
            />
          </>
        )}
        <Avatar className="h-9 w-9 shrink-0 bg-[#040812] border border-[#1e3a8a] shadow-[0_0_8px_1px_rgba(38,132,255,0.7)] relative z-10">
          <AvatarFallback className="bg-transparent text-[#3b82f6]">
            <Bot
              size={16}
              strokeWidth={2.5}
              className="drop-shadow-[0_0_8px_rgba(38,132,255,1)]"
            />
          </AvatarFallback>
        </Avatar>
      </div>

      <div className="flex-1 space-y-4 max-w-full overflow-hidden pt-1">
        <div className="w-full">
          <TypewriterText
            text={msg.content}
            delay={400}
            instant={msg.instant}
            onComplete={() => setIsTyping(false)}
            onTyping={onTyping}
          />
        </div>

        {/* Inline Chart Rendering */}
        {msg.chartConfig &&
          msg.chartConfig.data &&
          msg.chartConfig.data.length > 0 && (
            <div className="h-64 w-full glass-panel rounded-[20px] p-4 shadow-sm mt-3">
              <ResponsiveContainer width="100%" height="100%">
                {msg.chartConfig.type === "bar" ? (
                  <BarChart data={msg.chartConfig.data}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="rgba(255,255,255,0.03)"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="name"
                      stroke="#80848E"
                      fontSize={11}
                      fontWeight={500}
                      axisLine={false}
                      tickLine={false}
                      dy={10}
                    />
                    <YAxis
                      stroke="#80848E"
                      fontSize={11}
                      fontWeight={500}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(19, 23, 34, 0.85)",
                        backdropFilter: "blur(12px)",
                        borderColor: "rgba(255,255,255,0.08)",
                        borderRadius: "12px",
                        padding: "8px 12px",
                      }}
                      itemStyle={{
                        color: "#fff",
                        fontWeight: 600,
                        fontSize: "13px",
                      }}
                    />
                    <Bar dataKey="value" fill="#0070F3" radius={[4, 4, 0, 0]} />
                  </BarChart>
                ) : msg.chartConfig.type === "line" ? (
                  <LineChart data={msg.chartConfig.data}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="rgba(255,255,255,0.05)"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="name"
                      stroke="#A0A4AE"
                      fontSize={12}
                      axisLine={false}
                      tickLine={false}
                      dy={10}
                    />
                    <YAxis
                      stroke="#A0A4AE"
                      fontSize={12}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#171B27",
                        borderColor: "rgba(255,255,255,0.1)",
                        borderRadius: "8px",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#0070F3"
                      strokeWidth={3}
                      dot={{
                        r: 4,
                        fill: "#0070F3",
                        stroke: "#131722",
                        strokeWidth: 2,
                      }}
                    />
                  </LineChart>
                ) : (
                  <AreaChart data={msg.chartConfig.data}>
                    <defs>
                      <linearGradient
                        id="colorArea"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#0070F3"
                          stopOpacity={0.3}
                        />
                        <stop
                          offset="95%"
                          stopColor="#0070F3"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="rgba(255,255,255,0.05)"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="name"
                      stroke="#A0A4AE"
                      fontSize={12}
                      axisLine={false}
                      tickLine={false}
                      dy={10}
                    />
                    <YAxis
                      stroke="#A0A4AE"
                      fontSize={12}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#171B27",
                        borderColor: "rgba(255,255,255,0.1)",
                        borderRadius: "8px",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#0070F3"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorArea)"
                    />
                  </AreaChart>
                )}
              </ResponsiveContainer>
            </div>
          )}

        {msg.executedSql && msg.executedSql.length > 0 && (
          <div className="mt-2">
            <button
              onClick={() => setShowSql(!showSql)}
              className="text-xs text-muted-foreground hover:text-foreground font-medium flex items-center gap-1.5 transition-colors"
            >
              <Database size={12} />
              {showSql ? "Hide Database Query" : "View Executed SQL"}
            </button>
            {showSql && (
              <div className="mt-3 p-4 bg-[#0a0a0a] border border-border rounded-lg overflow-x-auto">
                <pre className="text-xs text-[#d4d4d4] font-mono leading-relaxed">
                  <code>{msg.executedSql.join("\n\n")}</code>
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const GREETING: Message = {
  role: "ai",
  content:
    "Hello! I am DataMind Copilot. I can query your databases, generate charts, and provide strategic insights. What would you like to know today?",
  instant: true,
};

function dbMessageToLocal(m: ChatMessage): Message {
  return {
    id: m.id,
    role: m.role,
    content: m.content,
    executedSql: m.executed_sql ?? undefined,
    chartConfig: m.chart_config ?? undefined,
    instant: true,
  };
}

export const ChatUI: React.FC = () => {
  const qc = useQueryClient();
  const [messages, setMessages] = useState<Message[]>([GREETING]);
  // Bumped whenever the *whole* conversation is swapped out (new chat /
  // switch session) so the list remounts cleanly instead of asking
  // AnimatePresence to individually exit-animate every old message at once
  // — that per-item diffing was leaving stale nodes behind when a swap
  // landed while an earlier swap's exit animations hadn't settled yet.
  const [listGeneration, setListGeneration] = useState(0);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessionLoading, setSessionLoading] = useState(false);

  // ── Reliable page entrance: trigger CSS transitions after mount ──────────────
  const [pageEntered, setPageEntered] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setPageEntered(true), 60);
    return () => clearTimeout(t);
  }, []);

  const entered = {
    transition: "opacity 0.55s cubic-bezier(0.22,1,0.36,1), transform 0.55s cubic-bezier(0.22,1,0.36,1), filter 0.55s cubic-bezier(0.22,1,0.36,1)",
  };

  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = (force = false) => {
    const container = document.getElementById("chat-scroll-container");
    if (container && messagesEndRef.current) {
      const isNearBottom =
        container.scrollHeight - container.scrollTop - container.clientHeight <
        150;
      if (isNearBottom || force) {
        messagesEndRef.current.scrollIntoView({
          behavior: force ? "smooth" : "auto",
        });
      }
    }
  };

  useEffect(() => {
    if (messages.length > 1) {
      scrollToBottom(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages]);

  const handleSend = async (
    overrideMessage?: string | React.MouseEvent | React.KeyboardEvent,
  ) => {
    const userMsg =
      typeof overrideMessage === "string"
        ? overrideMessage.trim()
        : input.trim();
    if (!userMsg || loading) return;
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    if (typeof overrideMessage !== "string") setInput("");
    setLoading(true);

    try {
      const data = await chatApi.send(userMsg, sessionId);

      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: data.response,
          chartConfig: data.chart_config ?? undefined,
          executedSql: data.executed_sql,
        },
      ]);

      if (data.session_id !== sessionId) setSessionId(data.session_id);
      qc.invalidateQueries({ queryKey: ["chat-sessions"] });
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: `Error: ${err instanceof Error ? err.message : "Something went wrong"}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const query = params.get("q");
      if (query) {
        // Clear query param so it doesn't stay in the URL
        window.history.replaceState({}, "", window.location.pathname);
        setTimeout(() => handleSend(query), 100);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleNewChat = () => {
    setSessionId(null);
    setMessages([GREETING]);
    setListGeneration((g) => g + 1);
    setInput("");
  };

  const handleSelectSession = async (id: string) => {
    if (id === sessionId || sessionLoading) return;
    setSessionLoading(true);
    setSessionId(id);
    try {
      const history = await chatApi.messages(id);
      setMessages(history.length > 0 ? history.map(dbMessageToLocal) : [GREETING]);
    } catch {
      setMessages([{ role: "ai", content: "Could not load this conversation. Try again in a moment.", instant: true }]);
    } finally {
      setListGeneration((g) => g + 1);
      setSessionLoading(false);
      requestAnimationFrame(() => scrollToBottom(false));
    }
  };

  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* Kept permanently mounted and width-toggled with a plain CSS
          transition (rather than conditionally mounted through
          AnimatePresence, or animated via framer-motion's `animate` prop)
          so collapsing it can't leave a stale full-width copy behind if an
          exit/animate cycle doesn't get applied. Width is the ONLY animated
          property — the inner sidebar is a fixed 260px slab that gets
          clip-revealed by this wrapper's overflow-hidden, like a panel
          sliding out from behind an edge. Pairing that clip with an opacity
          fade (as an earlier version did) made in-progress text look
          half-cut, since it was being clipped and faded at once. */}
      <div
        className={`min-w-0 overflow-hidden shrink-0 transition-[width] duration-300 ease-in-out ${
          sidebarOpen ? "w-[280px]" : "w-0"
        }`}
      >
        <ChatSessionSidebar
          activeSessionId={sessionId}
          onSelect={handleSelectSession}
          onNewChat={handleNewChat}
        />
      </div>

      <div className="flex flex-col flex-1 w-full relative overflow-hidden">
        
        {/* Sidebar Toggle Strip */}
        <button
          type="button"
          onClick={() => setSidebarOpen((v) => !v)}
          title={sidebarOpen ? "Hide chat history" : "Show chat history"}
          className="absolute left-0 top-1/2 -translate-y-1/2 h-20 w-4 flex items-center justify-start group z-50 focus:outline-none cursor-pointer"
        >
          <div className="h-full w-1 bg-white/[0.06] group-hover:bg-primary/80 group-hover:w-1.5 transition-all duration-300 rounded-r-md" />
        </button>

      {/* Top bar — normal document flow (not absolutely positioned), so it
          always reserves real space above the messages instead of floating
          over them. Sits flush against the flex-1 content area regardless
          of whether the sidebar is open (260px) or collapsed (0px). */}
      <div className="flex shrink-0 items-center justify-end px-6 py-4 border-b border-border/40 h-[61px]">

        <div
          style={{
            ...entered,
            opacity: pageEntered ? 1 : 0,
            transform: pageEntered ? "translateX(0) scale(1)" : "translateX(28px) scale(0.88)",
          }}
          className="flex items-center gap-2 bg-emerald-500/[0.08] backdrop-blur-sm px-3 py-1.5 rounded-full border border-emerald-500/20"
        >
          <div className="relative flex h-2 w-2">
            <motion.span
              animate={{ scale: [1, 2.6], opacity: [0.6, 0] }}
              transition={{ duration: 1.8, repeat: Infinity, ease: "easeOut" }}
              className="absolute inline-flex h-full w-full rounded-full bg-emerald-400"
            />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </div>
          <span className="text-xs font-medium text-emerald-400/90">Connected</span>
        </div>
      </div>

      {/* Messages scroll area — fades up after the top bar */}
      <div
        style={{
          ...entered,
          transitionDelay: pageEntered ? "80ms" : "0ms",
          opacity: pageEntered ? 1 : 0,
          transform: pageEntered ? "translateY(0) scale(1)" : "translateY(22px) scale(0.98)",
          filter: pageEntered ? "blur(0px)" : "blur(5px)",
        }}
        id="chat-scroll-container"
        className="flex-1 overflow-y-auto w-full pb-40 scroll-smooth"
      >
        <motion.div
          key={listGeneration}
          animate={{ opacity: sessionLoading ? 0.35 : 1 }}
          transition={{ duration: 0.15 }}
          className="max-w-4xl mx-auto w-full px-6 md:px-12 space-y-8 pt-8"
        >
          <AnimatePresence mode="popLayout">
            {messages.map((msg, idx) =>
              msg.role === "user" ? (
                <motion.div
                  key={msg.id ?? `local-${idx}`}
                  layout
                  variants={messageVariants}
                  initial="hidden"
                  animate="show"
                  exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.12 } }}
                  className="flex justify-end gap-3 mb-8 group w-full"
                >
                  <div className="max-w-[80%] px-5 py-3 rounded-tl-2xl rounded-tr-2xl rounded-bl-2xl rounded-br-md bg-white/[0.06] border border-white/[0.06] text-foreground text-[15px] leading-relaxed whitespace-pre-wrap break-words">
                    {msg.content}
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key={msg.id ?? `local-${idx}`}
                  layout
                  variants={messageVariants}
                  initial="hidden"
                  animate="show"
                  exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.12 } }}
                  className="w-full"
                >
                  <AIMessageBubble
                    msg={msg}
                    onTyping={() => scrollToBottom(false)}
                  />
                </motion.div>
              ),
            )}
            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex justify-start gap-5 mb-6"
              >
                <div className="relative shrink-0 flex items-center justify-center h-9 w-9 mt-0">
                  <motion.div
                    animate={{ scale: [1, 1.28, 1], opacity: [0.55, 0.18, 0.55] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute w-9 h-9 rounded-full bg-[#2684FF]/40 blur-[6px] pointer-events-none"
                  />
                  <motion.div
                    animate={{ scale: [1, 1.8], opacity: [1, 0] }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeOut",
                    }}
                    className="absolute w-9 h-9 rounded-full border-[1.5px] border-[#2684FF] shadow-[0_0_8px_#2684FF] pointer-events-none"
                  />
                  <motion.div
                    animate={{ scale: [1, 1.8], opacity: [1, 0] }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeOut",
                      delay: 1,
                    }}
                    className="absolute w-9 h-9 rounded-full border-[1.5px] border-[#2684FF] shadow-[0_0_8px_#2684FF] pointer-events-none"
                  />
                  <Avatar className="h-9 w-9 shrink-0 bg-[#040812] border border-[#1e3a8a] shadow-[0_0_8px_1px_rgba(38,132,255,0.7)] relative z-10">
                    <AvatarFallback className="bg-transparent text-[#3b82f6]">
                      <Bot
                        size={16}
                        strokeWidth={2.5}
                        className="drop-shadow-[0_0_8px_rgba(38,132,255,1)]"
                      />
                    </AvatarFallback>
                  </Avatar>
                </div>
                <div className="flex items-center gap-1.5 pt-2.5">
                  {[0, 1, 2].map((i) => (
                    <motion.span
                      key={i}
                      animate={{ y: [0, -5, 0], opacity: [0.4, 1, 0.4] }}
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: i * 0.2,
                      }}
                      className="h-1.5 w-1.5 rounded-full bg-[#2684FF]"
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </motion.div>
      </div>

      {/* Input bar — rises from below, longest delay */}
      <div
        style={{
          ...entered,
          transitionDelay: pageEntered ? "200ms" : "0ms",
          opacity: pageEntered ? 1 : 0,
          transform: pageEntered ? "translateY(0) scale(1)" : "translateY(48px) scale(0.97)",
        }}
        className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-background via-background/90 to-transparent pt-16 pointer-events-none flex flex-col items-start"
      >
        <div className="w-full max-w-4xl pointer-events-auto flex flex-col items-center px-6 md:px-12 mx-auto">
          <div className="relative flex items-center w-full shadow-[0_8px_32px_rgba(0,0,0,0.4)] rounded-2xl bg-white/[0.03] backdrop-blur-[24px] border border-white/10 overflow-hidden group/input transition-colors duration-300 focus-within:border-[#2684FF]/50 focus-within:shadow-[0_8px_32px_rgba(38,132,255,0.15)]">
            <div className="absolute inset-0 bg-gradient-to-tr from-white/[0.07] via-transparent to-white/[0.03] pointer-events-none opacity-50" />
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask DataMind to query datasets, generate charts, or predict trends..."
              className="w-full pl-5 pr-14 py-4 min-h-[56px] rounded-2xl bg-transparent border-0 text-foreground placeholder:text-muted-foreground focus-visible:ring-0 shadow-none text-[15px]"
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              size="icon"
              className="group absolute right-2 h-10 w-10 flex items-center justify-center rounded-full bg-[#2684ff]/90 hover:bg-[#2684ff] hover:scale-105 transition-all duration-300 active:scale-95 shadow-[0_0_15px_rgba(38,132,255,0.4)] hover:shadow-[0_0_20px_rgba(38,132,255,0.6)] disabled:opacity-50 disabled:hover:scale-100 z-10"
            >
              <Send className="h-[18px] w-[18px] text-white/90 group-hover:text-white group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all duration-300 pr-[2px] pt-[2px]" />
            </Button>
          </div>
          <p className="text-center text-[11px] text-muted-foreground mt-3 font-medium tracking-wide">
            AI can make mistakes. Consider verifying critical business metrics.
          </p>
        </div>
      </div>
      </div>
    </div>
  );
};

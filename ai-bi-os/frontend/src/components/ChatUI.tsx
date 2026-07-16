"use client";
import React, { useState, useEffect, useRef } from 'react';
import api, { BASE_URL } from "@/lib/api";
import { BarChart, Bar, LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Bot, User, Send, Database, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from '@/lib/utils';

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.05 }
  }
};

const badgeVariants = {
  hidden: { opacity: 0, x: 20, scale: 0.9 },
  show: { opacity: 1, x: 0, scale: 1, transition: { type: "spring", stiffness: 280, damping: 20 } }
};

const messageVariants = {
  hidden: { opacity: 0, y: 25, scale: 0.95 },
  show: { opacity: 1, y: 0, scale: 1, transition: { type: "spring", stiffness: 220, damping: 22 } }
};

const inputVariants = {
  hidden: { opacity: 0, y: 50 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 200, damping: 25, delay: 0.25 } }
};

function TypewriterText({ text, delay = 300, onComplete, onTyping }: { text: string, delay?: number, onComplete?: () => void, onTyping?: () => void }) {
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    if (!text) return;
    
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
  }, [text, delay]);

  const isTyping = displayedText.length < text.length;

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!isTyping && text.length > 0) {
      onComplete?.();
    }
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
  role: 'user' | 'ai';
  content: string;
  executedSql?: string[];
  chartConfig?: {
    type: 'bar' | 'line' | 'area';
    data: any[];
  };
}

const AIMessageBubble: React.FC<{ msg: Message, onTyping?: () => void }> = ({ msg, onTyping }) => {
  const [showSql, setShowSql] = useState(false);
  const [isTyping, setIsTyping] = useState(true);
  
  return (
    <div className="flex justify-start gap-4 mb-8 group w-full">
      <div className="relative shrink-0 flex items-center justify-center h-8 w-8 mt-0">
        {isTyping && (
          <>
            <motion.div 
              animate={{ scale: [1, 1.8], opacity: [1, 0] }} 
              transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
              className="absolute w-8 h-8 rounded-full border-[1.5px] border-[#2684FF] shadow-[0_0_8px_#2684FF] pointer-events-none"
            />
            <motion.div 
              animate={{ scale: [1, 1.8], opacity: [1, 0] }} 
              transition={{ duration: 2, repeat: Infinity, ease: "easeOut", delay: 1 }}
              className="absolute w-8 h-8 rounded-full border-[1.5px] border-[#2684FF] shadow-[0_0_8px_#2684FF] pointer-events-none"
            />
          </>
        )}
        <Avatar className="h-8 w-8 shrink-0 bg-[#040812] border border-[#1e3a8a] shadow-[0_0_8px_1px_rgba(38,132,255,0.7)] relative z-10">
          <AvatarFallback className="bg-transparent text-[#3b82f6]"><Bot size={15} strokeWidth={2.5} className="drop-shadow-[0_0_8px_rgba(38,132,255,1)]" /></AvatarFallback>
        </Avatar>
      </div>
      
      <div className="flex-1 space-y-4 max-w-full overflow-hidden pt-1">
        <div className="w-full">
          <TypewriterText text={msg.content} delay={400} onComplete={() => setIsTyping(false)} onTyping={onTyping} />
        </div>
        
        {/* Inline Chart Rendering */}
        {msg.chartConfig && msg.chartConfig.data && msg.chartConfig.data.length > 0 && (
          <div className="h-64 w-full glass-panel rounded-[20px] p-4 shadow-sm mt-3">
            <ResponsiveContainer width="100%" height="100%">
              {msg.chartConfig.type === 'bar' ? (
                <BarChart data={msg.chartConfig.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                  <XAxis dataKey="name" stroke="#80848E" fontSize={11} fontWeight={500} axisLine={false} tickLine={false} dy={10} />
                  <YAxis stroke="#80848E" fontSize={11} fontWeight={500} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'rgba(19, 23, 34, 0.85)', backdropFilter: 'blur(12px)', borderColor: 'rgba(255,255,255,0.08)', borderRadius: '12px', padding: '8px 12px' }} 
                    itemStyle={{ color: '#fff', fontWeight: 600, fontSize: '13px' }}
                  />
                  <Bar dataKey="value" fill="#0070F3" radius={[4, 4, 0, 0]} />
                </BarChart>
              ) : msg.chartConfig.type === 'line' ? (
                <LineChart data={msg.chartConfig.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="name" stroke="#A0A4AE" fontSize={12} axisLine={false} tickLine={false} dy={10} />
                  <YAxis stroke="#A0A4AE" fontSize={12} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#171B27', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }} 
                  />
                  <Line type="monotone" dataKey="value" stroke="#0070F3" strokeWidth={3} dot={{ r: 4, fill: '#0070F3', stroke: '#131722', strokeWidth: 2 }} />
                </LineChart>
              ) : (
                <AreaChart data={msg.chartConfig.data}>
                  <defs>
                    <linearGradient id="colorArea" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0070F3" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#0070F3" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="name" stroke="#A0A4AE" fontSize={12} axisLine={false} tickLine={false} dy={10} />
                  <YAxis stroke="#A0A4AE" fontSize={12} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#171B27', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }} 
                  />
                  <Area type="monotone" dataKey="value" stroke="#0070F3" strokeWidth={2} fillOpacity={1} fill="url(#colorArea)" />
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
                  <code>{msg.executedSql.join('\n\n')}</code>
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export const ChatUI: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'ai', content: 'Hello! I am DataMind Copilot. I can query your databases, generate charts, and provide strategic insights. What would you like to know today?' }
  ]);
  const [input, setInput] = useState('');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const query = params.get('q');
      if (query) {
        // Clear query param so it doesn't stay in the URL
        window.history.replaceState({}, '', window.location.pathname);
        setTimeout(() => handleSend(query), 100);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = (force = false) => {
    const container = document.getElementById("chat-scroll-container");
    if (container && messagesEndRef.current) {
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 150;
      if (isNearBottom || force) {
        messagesEndRef.current.scrollIntoView({ behavior: force ? "smooth" : "auto" });
      }
    }
  };

  useEffect(() => {
    if (messages.length > 1) {
      scrollToBottom(true);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages]);

  const handleSend = async (overrideMessage?: string | React.MouseEvent | React.KeyboardEvent) => {
    const userMsg = typeof overrideMessage === 'string' ? overrideMessage.trim() : input.trim();
    if (!userMsg || loading) return;
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    if (typeof overrideMessage !== 'string') setInput('');
    setLoading(true);

    try {
      const data = await api.post<any>('/api/v1/chat', { message: userMsg });
      let aiContent = data.response;
      let chartConfig = undefined;

      try {
        let cleanText = aiContent.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
        if (cleanText.startsWith('{') && cleanText.endsWith('}')) {
          const parsed = JSON.parse(cleanText);
          if (parsed.text_response) {
            aiContent = parsed.text_response;
            chartConfig = parsed.chart_config;
          }
        }
      } catch (e) {
        // Fallback to text
      }

      setMessages(prev => [...prev, { 
        role: 'ai', 
        content: aiContent,
        chartConfig: chartConfig,
        executedSql: data.executed_sql 
      }]);
    } catch (err: any) {
      setMessages(prev => [...prev, { role: 'ai', content: `Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div 
      initial="hidden"
      animate="show"
      variants={containerVariants}
      className="flex flex-col flex-1 w-full relative overflow-hidden"
    >
      
      {/* Connection Status Indicator */}
      <motion.div variants={badgeVariants} className="absolute top-6 right-8 flex items-center gap-2 z-20 bg-surface/40 backdrop-blur-sm px-3 py-1.5 rounded-full border border-white/5">
        <div className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </div>
        <span className="text-xs font-medium text-muted-foreground">Connected</span>
      </motion.div>

      <div id="chat-scroll-container" className="flex-1 overflow-y-auto w-full pb-40 scroll-smooth">
        <div className="max-w-3xl mr-auto ml-4 md:ml-12 lg:ml-24 w-full px-4 md:px-0 space-y-6 pt-8">
        <AnimatePresence initial={false}>
          {messages.map((msg, idx) => (
            msg.role === 'user' ? (
              <motion.div 
                key={idx} 
                layout
                variants={messageVariants}
                initial="hidden"
                animate="show"
                className="flex justify-end gap-3 mb-8 group w-full"
              >
                <div className="max-w-[80%] px-5 py-3 rounded-2xl bg-white/[0.06] text-foreground text-[15px] leading-relaxed whitespace-pre-wrap break-words">
                  {msg.content}
                </div>
              </motion.div>
            ) : (
              <motion.div 
                key={idx}
                layout
                variants={messageVariants}
                initial="hidden"
                animate="show" 
                className="w-full"
              >
                <AIMessageBubble msg={msg} onTyping={() => scrollToBottom(false)} />
              </motion.div>
            )
          ))}
          {loading && (
            <motion.div 
              initial={{ opacity: 0, y: 15 }} 
              animate={{ opacity: 1, y: 0 }} 
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex justify-start gap-4 mb-6"
            >
              <div className="relative shrink-0 flex items-center justify-center h-8 w-8 mt-0">
                <motion.div 
                  animate={{ scale: [1, 1.8], opacity: [1, 0] }} 
                  transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
                  className="absolute w-8 h-8 rounded-full border-[1.5px] border-[#2684FF] shadow-[0_0_8px_#2684FF] pointer-events-none"
                />
                <motion.div 
                  animate={{ scale: [1, 1.8], opacity: [1, 0] }} 
                  transition={{ duration: 2, repeat: Infinity, ease: "easeOut", delay: 1 }}
                  className="absolute w-8 h-8 rounded-full border-[1.5px] border-[#2684FF] shadow-[0_0_8px_#2684FF] pointer-events-none"
                />
                <Avatar className="h-8 w-8 shrink-0 bg-[#040812] border border-[#1e3a8a] shadow-[0_0_8px_1px_rgba(38,132,255,0.7)] relative z-10">
                  <AvatarFallback className="bg-transparent text-[#3b82f6]"><Bot size={15} strokeWidth={2.5} className="drop-shadow-[0_0_8px_rgba(38,132,255,1)] animate-pulse" /></AvatarFallback>
                </Avatar>
              </div>
              <div className="flex items-center text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Analyzing data...
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
        </div>
      </div>

      <motion.div variants={inputVariants} className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-background via-background/90 to-transparent pt-16 pointer-events-none flex flex-col items-start">
        <div className="w-full max-w-3xl pointer-events-auto flex flex-col items-center px-4 md:px-0 ml-4 md:ml-12 lg:ml-24 mr-auto">
          <div className="relative flex items-center w-full shadow-[0_8px_32px_rgba(0,0,0,0.4)] rounded-2xl bg-white/[0.03] backdrop-blur-[24px] border border-white/10 overflow-hidden group/input">
            <div className="absolute inset-0 bg-gradient-to-tr from-white/[0.07] via-transparent to-white/[0.03] pointer-events-none opacity-50" />
            <Input 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
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
      </motion.div>
    </motion.div>
  );
};

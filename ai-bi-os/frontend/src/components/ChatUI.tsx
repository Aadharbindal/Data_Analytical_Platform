"use client";
import React, { useState, useEffect, useRef } from 'react';
import api, { BASE_URL } from "@/lib/api";
import { BarChart, Bar, LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Bot, User, Send, Database, Loader2 } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from '@/lib/utils';

interface Message {
  role: 'user' | 'ai';
  content: string;
  executedSql?: string[];
  chartConfig?: {
    type: 'bar' | 'line' | 'area';
    data: any[];
  };
}

const AIMessageBubble: React.FC<{ msg: Message }> = ({ msg }) => {
  const [showSql, setShowSql] = useState(false);
  
  return (
    <div className="flex justify-start gap-4 mb-8 group w-full">
      <Avatar className="h-8 w-8 shrink-0 shadow-sm border border-primary/20 bg-primary/10 mt-0">
        <AvatarFallback className="bg-transparent text-primary"><Bot size={14} /></AvatarFallback>
      </Avatar>
      
      <div className="flex-1 space-y-4 max-w-full overflow-hidden pt-1">
        <div className="text-[15px] leading-relaxed text-foreground/90 whitespace-pre-wrap break-words">
          {msg.content}
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

  useEffect(() => {
    if (messages.length > 1) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
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
    <div className="flex flex-col flex-1 w-full relative overflow-hidden">
      
      <div className="flex-1 overflow-y-auto w-full pb-40 scroll-smooth">
        <div className="max-w-3xl mx-auto w-full px-4 md:px-0 space-y-6 pt-4">
        {messages.map((msg, idx) => (
          msg.role === 'user' ? (
            <div key={idx} className="flex justify-end gap-3 mb-8 group w-full">
              <div className="max-w-[80%] px-5 py-3 rounded-2xl bg-white/[0.06] text-foreground text-[15px] leading-relaxed whitespace-pre-wrap break-words">
                {msg.content}
              </div>
            </div>
          ) : (
            <AIMessageBubble key={idx} msg={msg} />
          )
        ))}
        {loading && (
          <div className="flex justify-start gap-4 mb-6">
            <Avatar className="h-8 w-8 shrink-0 mt-0.5 border border-primary/20 bg-primary/10">
              <AvatarFallback className="bg-transparent text-primary"><Bot size={16} /></AvatarFallback>
            </Avatar>
            <div className="flex items-center text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Analyzing data...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-background via-background/90 to-transparent pt-16 pointer-events-none flex flex-col items-center">
        <div className="w-full max-w-3xl pointer-events-auto flex flex-col items-center px-4 md:px-0">
          <div className="relative flex items-center w-full shadow-lg rounded-2xl bg-surface/80 backdrop-blur-xl border border-white/10">
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
              className="absolute right-2 h-10 w-10 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-transform active:scale-95"
            >
              <Send className="h-4 w-4 ml-0.5" />
            </Button>
          </div>
          <p className="text-center text-[11px] text-muted-foreground mt-3 font-medium tracking-wide">
            AI can make mistakes. Consider verifying critical business metrics.
          </p>
        </div>
      </div>
    </div>
  );
};

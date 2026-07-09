"use client";
import React, { useState, useEffect, useRef } from 'react';
import { BASE_URL } from "@/lib/api";
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
    <div className="flex justify-start gap-4 mb-6">
      <Avatar className="h-8 w-8 shrink-0 mt-0.5 border border-primary/20 bg-primary/10">
        <AvatarFallback className="bg-transparent text-primary"><Bot size={16} /></AvatarFallback>
      </Avatar>
      
      <div className="flex-1 space-y-4 max-w-[85%]">
        <div className="text-sm leading-relaxed text-foreground whitespace-pre-wrap mt-1">
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
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${BASE_URL}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg })
      });
      
      if (!res.ok) throw new Error("Failed to connect to agent");
      
      const data = await res.json();
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
    <div className="flex flex-col h-[calc(100vh-12rem)] max-w-4xl mx-auto w-full">
      
      <div className="flex-1 overflow-y-auto px-4 py-8 space-y-2">
        {messages.map((msg, idx) => (
          msg.role === 'user' ? (
            <div key={idx} className="flex justify-end gap-4 mb-6">
              <div className="max-w-[75%] px-5 py-3 rounded-2xl rounded-tr-sm bg-primary text-primary-foreground text-sm font-medium shadow-sm">
                {msg.content}
              </div>
              <Avatar className="h-8 w-8 shrink-0 mt-0.5">
                <AvatarFallback className="bg-surface text-foreground border border-border"><User size={16} /></AvatarFallback>
              </Avatar>
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

      <div className="p-4 bg-background/80 backdrop-blur-md border-t border-border mt-auto shrink-0 sticky bottom-0">
        <div className="relative flex items-center w-full max-w-4xl mx-auto">
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
            className="w-full pl-4 pr-14 py-6 rounded-2xl bg-surface border-border text-foreground placeholder:text-muted-foreground focus-visible:ring-1 focus-visible:ring-primary shadow-sm"
          />
          <Button 
            onClick={handleSend}
            disabled={!input.trim() || loading}
            size="icon"
            className="absolute right-2 h-9 w-9 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-center text-xs text-muted-foreground mt-3">
          AI can make mistakes. Consider verifying critical business metrics.
        </p>
      </div>
    </div>
  );
};

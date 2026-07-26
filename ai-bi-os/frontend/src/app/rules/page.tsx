"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { rulesApi, datasetsApi, analyticsApi } from "@/lib/api";
import type { BusinessRule, RuleEvent } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import { GitBranch, Plus, CheckCircle, XCircle, AlertCircle, X, Loader2, Trash2, History, RefreshCw, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";

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

function RuleHistoryPanel({ rule, onClose }: { rule: BusinessRule; onClose: () => void }) {
  const { data: events, isLoading } = useQuery({
    queryKey: ["rule-history", rule.id],
    queryFn: () => rulesApi.history(rule.id),
  });

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ x: 32, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 32, opacity: 0 }}
        transition={{ type: "spring", stiffness: 320, damping: 32 }}
        className="flex h-full w-full max-w-md flex-col rounded-[24px] border border-border/60 bg-background shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border/40 px-5 py-4">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-foreground">{rule.name}</p>
            <p className="text-[11px] text-muted-foreground">Trigger history</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-16 animate-pulse rounded-xl bg-white/[0.03]" />
              ))}
            </div>
          ) : !events || events.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-16 text-center">
              <History className="h-6 w-6 text-muted-foreground/40" />
              <p className="text-xs text-muted-foreground">
                No trigger events yet. This rule hasn&apos;t crossed its threshold since it was created.
              </p>
            </div>
          ) : (
            <div className="relative space-y-4 pl-5">
              <div className="absolute left-[7px] top-1 bottom-1 w-px bg-border/50" />
              {events.map((event: RuleEvent, idx: number) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.04 }}
                  className="relative"
                >
                  <span className="absolute -left-5 top-1 h-3.5 w-3.5 rounded-full border-2 border-background bg-error shadow-[0_0_8px_rgba(239,68,68,0.6)]" />
                  <div className="rounded-xl border border-border/40 bg-white/[0.02] px-3.5 py-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="inline-flex items-center gap-1 rounded-full border border-error/20 bg-error/10 px-2 py-0.5 text-[10px] font-medium text-error">
                        <AlertCircle className="h-2.5 w-2.5" /> TRIGGERED
                      </span>
                      <span className="text-[10px] text-muted-foreground/60">{relativeTime(event.created_at)}</span>
                    </div>
                    <p className="mt-2 text-[12px] leading-relaxed text-foreground/80">{event.message}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

function RuleCard({ rule, onViewHistory }: { rule: BusinessRule; onViewHistory: () => void }) {
  const qc = useQueryClient();
  const deleteMut = useMutation({
    mutationFn: () => rulesApi.delete(rule.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });
  const updateMut = useMutation({
    mutationFn: (data: Partial<BusinessRule>) => rulesApi.update(rule.id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });

  const isTriggered = rule.status === "TRIGGERED";
  const isOk = rule.status === "OK";
  const isErrorStatus = rule.status?.startsWith("ERROR") || false;
  const isPending = rule.status?.startsWith("PENDING") || false;
  const isInactive = !rule.is_active || rule.status === "INACTIVE";

  return (
    <div className={`relative glass-card rounded-[20px] p-5 flex flex-col gap-3 border-l-2 transition-all ${
      isInactive ? 'opacity-50 border-l-muted' :
      isTriggered ? 'border-l-error' :
      isOk ? 'border-l-success' :
      isErrorStatus ? 'border-l-amber-500' :
      isPending ? 'border-l-primary' : 'border-l-muted'
    }`}>
      {isTriggered && (
        <motion.div
          animate={{ opacity: [0.5, 0.15, 0.5] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
          className="pointer-events-none absolute inset-0 rounded-[20px] bg-error/[0.04]"
        />
      )}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 shrink-0">
            <GitBranch className="h-3.5 w-3.5 text-primary" />
          </div>
          <h3 className="text-sm font-semibold text-foreground truncate">{rule.name}</h3>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => updateMut.mutate({ is_active: !rule.is_active })}
            className={`w-8 h-4 rounded-full transition-colors relative focus:outline-none ${rule.is_active ? 'bg-primary' : 'bg-muted-foreground/30'}`}
          >
            <span className={`absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-white transition-transform ${rule.is_active ? 'translate-x-4' : 'translate-x-0'}`} />
          </button>
          <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${
            isInactive ? "bg-muted/10 text-muted-foreground border-border/40" :
            isTriggered ? "bg-error/10 text-error border-error/20" :
            isOk ? "bg-success/10 text-success border-success/20" :
            isErrorStatus ? "bg-amber-500/10 text-amber-500 border-amber-500/20" :
            isPending ? "bg-primary/10 text-primary border-primary/20" :
            "bg-muted/10 text-muted-foreground border-border/40"
          }`}>
            {isInactive ? <span className="h-2.5 w-2.5 rounded-full bg-muted-foreground/50" /> :
             isTriggered ? <AlertCircle className="h-2.5 w-2.5" /> :
             isOk ? <CheckCircle className="h-2.5 w-2.5" /> :
             isPending ? <Clock className="h-2.5 w-2.5" /> :
             <AlertCircle className="h-2.5 w-2.5" />}
            {rule.status}
          </span>
          <button onClick={onViewHistory} title="View trigger history" className="text-muted-foreground hover:text-primary transition-colors">
            <History className="h-3.5 w-3.5" />
          </button>
          <button onClick={() => deleteMut.mutate()} className="text-muted-foreground hover:text-error transition-colors">
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <div className="space-y-2 mt-2">
        <div className="px-3 py-2 rounded-lg bg-white/[0.02] border border-border/40 flex justify-between items-center">
          <p className="text-xs font-mono text-muted-foreground">
            {rule.metric_column} {rule.condition} {rule.threshold}
          </p>
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{rule.window}</span>
        </div>
        {rule.current_value !== null && rule.current_value !== undefined && (
          <div className="px-3 py-2 rounded-lg bg-white/[0.02] border border-border/40 flex justify-between items-center">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Current Value</span>
            <span className="text-sm font-semibold text-foreground tabular-nums">
              {rule.window === 'MoM' ? `${rule.current_value.toFixed(2)}%` : rule.current_value.toLocaleString()}
            </span>
          </div>
        )}
        {rule.last_triggered_at && (
          <div className="flex items-center gap-1.5 px-1 text-[11px] text-muted-foreground/70">
            <Clock className="h-3 w-3" />
            Last triggered {relativeTime(rule.last_triggered_at)}
          </div>
        )}
      </div>

      <p className="text-[11px] text-muted-foreground/60 mt-auto">
        Created {new Date(rule.created_at).toLocaleDateString()}
      </p>
    </div>
  );
}

function NewRuleModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [tab, setTab] = useState<"nl" | "manual">("nl");
  
  const [nlText, setNlText] = useState("");
  const [parsedRule, setParsedRule] = useState<any>(null);

  const [manualForm, setManualForm] = useState({
    name: "",
    metric_column: "",
    condition: ">",
    threshold: 0,
    window: "latest"
  });

  const { data: edaData } = useQuery({
    queryKey: ["eda"],
    queryFn: () => analyticsApi.eda(),
    enabled: tab === "manual",
  });

  // GET /analytics/eda returns { summary: [{ column, mean?, min?, max?, ... }] },
  // not a `schema` map — numeric columns are the ones with a computed mean.
  const numericColumns: string[] = Array.isArray(edaData?.summary)
    ? edaData.summary.filter((c: { mean?: number }) => c.mean != null).map((c: { column: string }) => c.column)
    : [];

  const parseMut = useMutation({
    mutationFn: () => rulesApi.parseText(nlText),
    onSuccess: (res) => {
      if (res.success) setParsedRule(res.parsed);
      else alert("Could not parse rule: " + res.error);
    }
  });

  const createMut = useMutation({
    mutationFn: (ruleData: any) => rulesApi.create(ruleData),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["rules"] }); onClose(); },
  });

  const handleManualSubmit = () => {
    if (!manualForm.name || !manualForm.metric_column) {
      alert("Please fill out name and select a metric column.");
      return;
    }
    createMut.mutate(manualForm);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6 overflow-y-auto"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.96, y: 8 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.96, y: 8 }}
        className="bg-background border border-border/60 rounded-[24px] p-6 w-full max-w-lg shadow-2xl my-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-foreground">New Deterministic Rule</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
        </div>

        <div className="flex gap-2 p-1 bg-muted/30 rounded-lg mb-6">
          <button 
            className={`flex-1 text-sm font-medium py-1.5 rounded-md transition-all ${tab === 'nl' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            onClick={() => setTab("nl")}
          >
            Describe in English
          </button>
          <button 
            className={`flex-1 text-sm font-medium py-1.5 rounded-md transition-all ${tab === 'manual' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            onClick={() => setTab("manual")}
          >
            Manual Setup
          </button>
        </div>
        
        {tab === "nl" ? (
          !parsedRule ? (
            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Describe the rule in plain English</label>
                <textarea
                  value={nlText}
                  onChange={(e) => setNlText(e.target.value)}
                  placeholder="e.g., Alert me if revenue drops by more than 10% MoM"
                  className="w-full h-24 bg-surface border border-border/80 rounded-xl p-3 text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none"
                />
              </div>
              <div className="flex gap-3 mt-6">
                <Button variant="outline" className="flex-1" onClick={onClose}>Cancel</Button>
                <Button className="flex-1 gap-2" onClick={() => parseMut.mutate()} disabled={parseMut.isPending || !nlText}>
                  {parseMut.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  Parse Rule
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-4 bg-primary/5 rounded-xl border border-primary/20 space-y-2">
                <p className="text-xs font-semibold text-primary">Parsed Rule Confirmation</p>
                <div className="text-sm"><strong>Name:</strong> {parsedRule.name}</div>
                <div className="text-sm"><strong>Metric Column:</strong> {parsedRule.metric_column}</div>
                <div className="text-sm"><strong>Condition:</strong> {parsedRule.condition}</div>
                <div className="text-sm"><strong>Threshold:</strong> {parsedRule.threshold}</div>
                <div className="text-sm"><strong>Window:</strong> {parsedRule.window}</div>
              </div>
              <div className="flex gap-3 mt-6">
                <Button variant="outline" className="flex-1" onClick={() => setParsedRule(null)}>Edit Prompt</Button>
                <Button className="flex-1 gap-2" onClick={() => createMut.mutate(parsedRule)} disabled={createMut.isPending}>
                  {createMut.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  Save Active Rule
                </Button>
              </div>
            </div>
          )
        ) : (
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Rule Name</label>
              <input 
                type="text" 
                value={manualForm.name} 
                onChange={e => setManualForm({...manualForm, name: e.target.value})}
                placeholder="e.g. Revenue Drop Alert"
                className="w-full bg-surface border border-border/80 rounded-lg p-2.5 text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
            
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Metric Column</label>
              <select 
                value={manualForm.metric_column}
                onChange={e => setManualForm({...manualForm, metric_column: e.target.value})}
                className="w-full bg-surface border border-border/80 rounded-lg p-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">Select a column...</option>
                {numericColumns.map((col: string) => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Condition</label>
                <select 
                  value={manualForm.condition}
                  onChange={e => setManualForm({...manualForm, condition: e.target.value})}
                  className="w-full bg-surface border border-border/80 rounded-lg p-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  <option value=">">&gt; (Greater than)</option>
                  <option value="<">&lt; (Less than)</option>
                  <option value=">=">&gt;= (Greater or eq)</option>
                  <option value="<=">&lt;= (Less or eq)</option>
                  <option value="==">== (Equals)</option>
                  <option value="pct_change_gt">% Change &gt;</option>
                  <option value="pct_change_lt">% Change &lt;</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Threshold</label>
                <input 
                  type="number" 
                  value={manualForm.threshold}
                  onChange={e => setManualForm({...manualForm, threshold: parseFloat(e.target.value) || 0})}
                  className="w-full bg-surface border border-border/80 rounded-lg p-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Window</label>
              <select 
                value={manualForm.window}
                onChange={e => setManualForm({...manualForm, window: e.target.value})}
                className="w-full bg-surface border border-border/80 rounded-lg p-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="latest">Latest Value</option>
                <option value="MoM">Month over Month (MoM)</option>
              </select>
            </div>

            <div className="flex gap-3 mt-6">
              <Button variant="outline" className="flex-1" onClick={onClose}>Cancel</Button>
              <Button className="flex-1 gap-2" onClick={handleManualSubmit} disabled={createMut.isPending}>
                {createMut.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Save Rule
              </Button>
            </div>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 26 } },
};

export default function RulesPage() {
  const qc = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [historyRule, setHistoryRule] = useState<BusinessRule | null>(null);

  const { data: activeDataset } = useQuery({
    queryKey: ["activeDataset"],
    queryFn: () => datasetsApi.getActive(),
  });

  const { data: rules, isLoading, isError, refetch } = useQuery({
    queryKey: ["rules", activeDataset?.id],
    queryFn: () => rulesApi.list(),
    enabled: !!activeDataset?.id,
  });

  const evaluateMut = useMutation({
    mutationFn: () => rulesApi.evaluate(),
    onSuccess: (updated) => {
      qc.setQueryData(["rules", activeDataset?.id], updated);
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div></div>
        {rules && rules.length > 0 && (
          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              onClick={() => evaluateMut.mutate()}
              disabled={evaluateMut.isPending}
              className="gap-2"
            >
              <motion.span
                animate={evaluateMut.isPending ? { rotate: 360 } : { rotate: 0 }}
                transition={evaluateMut.isPending ? { duration: 0.8, repeat: Infinity, ease: "linear" } : {}}
                className="flex"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </motion.span>
              Run checks now
            </Button>
            <Button onClick={() => setShowModal(true)} className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
              <Plus className="h-4 w-4" /> New Rule
            </Button>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} lines={4} />)}
        </div>
      ) : isError ? (
        <ErrorState onRetry={refetch} />
      ) : !rules || rules.length === 0 ? (
        <EmptyState
          icon={<GitBranch className="h-7 w-7 text-muted-foreground/50" />}
          title="No rules yet"
          description="Create your first business rule to automatically monitor metrics."
          action={<Button onClick={() => setShowModal(true)} className="gap-2"><Plus className="h-4 w-4" />New Rule</Button>}
        />
      ) : (
        <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {rules.map((rule) => (
            <motion.div key={rule.id} variants={itemVariants}>
              <RuleCard rule={rule} onViewHistory={() => setHistoryRule(rule)} />
            </motion.div>
          ))}
        </motion.div>
      )}

      <AnimatePresence>
        {showModal && <NewRuleModal onClose={() => setShowModal(false)} />}
      </AnimatePresence>
      {/* Not AnimatePresence-wrapped: unmounting here must track React state
          directly. Gating removal on an exit animation's onComplete firing
          has left stale slide-over panels behind before (see ChatUI.tsx /
          CustomizeDashboardModal.tsx) — the panel's own mount-in transition
          still plays via its `animate` prop regardless. */}
      {historyRule && <RuleHistoryPanel rule={historyRule} onClose={() => setHistoryRule(null)} />}
    </div>
  );
}

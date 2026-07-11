"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { rulesApi } from "@/lib/api";
import type { BusinessRule } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import { GitBranch, Plus, CheckCircle, XCircle, AlertCircle, X, Loader2, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";

function RuleCard({ rule }: { rule: BusinessRule }) {
  const qc = useQueryClient();
  const deleteMut = useMutation({
    mutationFn: () => rulesApi.delete(rule.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });

  const isTriggered = rule.status === "TRIGGERED";
  const isOk = rule.status === "OK";
  
  return (
    <div className={`glass-card rounded-[20px] p-5 flex flex-col gap-3 border-l-2 ${isTriggered ? 'border-l-error' : isOk ? 'border-l-success' : 'border-l-muted'}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 shrink-0">
            <GitBranch className="h-3.5 w-3.5 text-primary" />
          </div>
          <h3 className="text-sm font-semibold text-foreground truncate">{rule.name}</h3>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${
            isTriggered
              ? "bg-error/10 text-error border-error/20"
              : isOk 
              ? "bg-success/10 text-success border-success/20"
              : "bg-muted/10 text-muted-foreground border-border/40"
          }`}>
            {isTriggered ? <AlertCircle className="h-2.5 w-2.5" /> : isOk ? <CheckCircle className="h-2.5 w-2.5" /> : <XCircle className="h-2.5 w-2.5" />}
            {rule.status}
          </span>
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
      </div>

      <p className="text-[11px] text-muted-foreground/60 mt-auto">
        Created {new Date(rule.created_at).toLocaleDateString()}
      </p>
    </div>
  );
}

function NewRuleModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [nlText, setNlText] = useState("");
  const [parsedRule, setParsedRule] = useState<any>(null);

  const parseMut = useMutation({
    mutationFn: () => rulesApi.parseText(nlText),
    onSuccess: (res) => {
      if (res.success) setParsedRule(res.parsed);
      else alert("Could not parse rule: " + res.error);
    }
  });

  const createMut = useMutation({
    mutationFn: () => rulesApi.create(parsedRule),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["rules"] }); onClose(); },
  });

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.96, y: 8 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.96, y: 8 }}
        className="bg-background border border-border/60 rounded-[24px] p-6 w-full max-w-lg shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-foreground">New Deterministic Rule</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
        </div>
        
        {!parsedRule ? (
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
              <Button className="flex-1 gap-2" onClick={() => createMut.mutate()} disabled={createMut.isPending}>
                {createMut.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Save Active Rule
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
  const [showModal, setShowModal] = useState(false);
  const { data: rules, isLoading, isError, refetch } = useQuery({
    queryKey: ["rules"],
    queryFn: () => rulesApi.list(),
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">Rules & Decisions</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Deterministic business rules evaluated against your latest data.
          </p>
        </div>
        <Button onClick={() => setShowModal(true)} className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
          <Plus className="h-4 w-4" /> New Rule
        </Button>
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
              <RuleCard rule={rule} />
            </motion.div>
          ))}
        </motion.div>
      )}

      <AnimatePresence>
        {showModal && <NewRuleModal onClose={() => setShowModal(false)} />}
      </AnimatePresence>
    </div>
  );
}

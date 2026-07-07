"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { rulesApi } from "@/lib/api";
import type { BusinessRule } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import { GitBranch, Plus, CheckCircle, XCircle, AlertCircle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CardSkeleton } from "@/components/ui/skeleton-loader";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Badge } from "@/components/ui/badge";

const priorityColors: Record<number, string> = {
  1: "bg-error/10 text-error border-error/20",
  2: "bg-warning/10 text-warning border-warning/20",
  3: "bg-primary/10 text-primary border-primary/20",
};

function RuleCard({ rule }: { rule: BusinessRule }) {
  const prioColor = priorityColors[rule.priority] ?? priorityColors[3];
  return (
    <div className="glass-card rounded-[20px] p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 shrink-0">
            <GitBranch className="h-3.5 w-3.5 text-primary" />
          </div>
          <h3 className="text-sm font-semibold text-foreground truncate">{rule.name}</h3>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-[11px] font-medium border px-2 py-0.5 rounded-full ${prioColor}`}>
            P{rule.priority}
          </span>
          <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${
            rule.status === "active"
              ? "bg-success/10 text-success border-success/20"
              : "bg-muted/10 text-muted-foreground border-border/40"
          }`}>
            {rule.status === "active" ? <CheckCircle className="h-2.5 w-2.5" /> : <XCircle className="h-2.5 w-2.5" />}
            {rule.status}
          </span>
        </div>
      </div>

      {rule.description && (
        <p className="text-xs text-muted-foreground">{rule.description}</p>
      )}

      <div className="space-y-2">
        <div className="px-3 py-2 rounded-lg bg-white/[0.02] border border-border/40">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Condition</p>
          <p className="text-xs font-mono text-foreground">{rule.condition}</p>
        </div>
        <div className="px-3 py-2 rounded-lg bg-white/[0.02] border border-border/40">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Action</p>
          <p className="text-xs font-mono text-foreground">{rule.action}</p>
        </div>
      </div>

      <p className="text-[11px] text-muted-foreground/60">
        Created {new Date(rule.created_at).toLocaleDateString()}
      </p>
    </div>
  );
}

function NewRuleModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState({ name: "", condition: "", action: "", priority: 2 });
  const mutation = useMutation({
    mutationFn: () => rulesApi.create({ ...form, workspace_id: "workspace-123", status: "active" }),
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
          <h2 className="text-base font-semibold text-foreground">New Business Rule</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
        </div>
        <div className="space-y-4">
          {[
            { label: "Rule Name", key: "name", placeholder: "e.g., Flag High-Value Transactions" },
            { label: "Condition", key: "condition", placeholder: "e.g., transaction_amount > 10000" },
            { label: "Action", key: "action", placeholder: "e.g., ALERT:finance-team" },
          ].map(({ label, key, placeholder }) => (
            <div key={key}>
              <label className="text-xs font-medium text-muted-foreground mb-1.5 block">{label}</label>
              <input
                value={(form as any)[key]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                placeholder={placeholder}
                className="w-full h-10 bg-surface border border-border/80 rounded-xl px-3 text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
          ))}
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Priority</label>
            <select
              value={form.priority}
              onChange={(e) => setForm((f) => ({ ...f, priority: Number(e.target.value) }))}
              className="w-full h-10 bg-surface border border-border/80 rounded-xl px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value={1}>1 — Critical</option>
              <option value={2}>2 — High</option>
              <option value={3}>3 — Medium</option>
            </select>
          </div>
        </div>
        <div className="flex gap-3 mt-6">
          <Button variant="outline" className="flex-1" onClick={onClose}>Cancel</Button>
          <Button className="flex-1" onClick={() => mutation.mutate()} disabled={mutation.isPending || !form.name || !form.condition}>
            {mutation.isPending ? "Creating..." : "Create Rule"}
          </Button>
        </div>
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
            Deterministic business rules that govern automated decisions.
          </p>
        </div>
        <Button onClick={() => setShowModal(true)} className="gap-2">
          <Plus className="h-4 w-4" /> New Rule
        </Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 gap-5">
          {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} lines={4} />)}
        </div>
      ) : isError ? (
        <ErrorState onRetry={refetch} />
      ) : !rules || rules.length === 0 ? (
        <EmptyState
          icon={<GitBranch className="h-7 w-7 text-muted-foreground/50" />}
          title="No rules yet"
          description="Create your first business rule to govern automated decisions."
          action={<Button onClick={() => setShowModal(true)} className="gap-2"><Plus className="h-4 w-4" />New Rule</Button>}
        />
      ) : (
        <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-2 gap-5">
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

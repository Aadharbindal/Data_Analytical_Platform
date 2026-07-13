"use client";

import React, { useState } from "react";
import { Card } from "@/components/ui/card";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Database, Landmark, Users, Heart, Package, 
  Megaphone, Target, Coins, ShoppingCart, ChevronDown, ChevronUp,
  Calendar, Binary, Layers, Fingerprint, ToggleLeft, Globe
} from "lucide-react";
import { SemanticDict } from "@/lib/types";

interface DatasetProfileCardProps {
  semanticDict: SemanticDict;
  datasetName: string;
}

const DOMAIN_CONFIGS: Record<string, { label: string; icon: any; color: string; bg: string; desc: string }> = {
  banking: {
    label: "Banking & Accounts",
    icon: Landmark,
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/25",
    desc: "Contains transaction logs, balance histories, and banking product details."
  },
  HR: {
    label: "HR & Workforce Operations",
    icon: Users,
    color: "text-purple-400",
    bg: "bg-purple-500/10 border-purple-500/25",
    desc: "Tracks employee headcounts, salaries, roles, departments, or attritions."
  },
  healthcare: {
    label: "Healthcare & Patient Care",
    icon: Heart,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/25",
    desc: "Captures patient admissions, diagnosis codes, treatment logs, or medical charges."
  },
  inventory: {
    label: "Inventory Control",
    icon: Package,
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/25",
    desc: "Manages warehousing stocks, product SKUs, supplier info, or logistics levels."
  },
  marketing: {
    label: "Marketing Campaigns",
    icon: Megaphone,
    color: "text-rose-400",
    bg: "bg-rose-500/10 border-rose-500/25",
    desc: "Monitors campaign performance, impressions, CTRs, spend levels, and conversions."
  },
  CRM: {
    label: "CRM & Sales Pipeline",
    icon: Target,
    color: "text-cyan-400",
    bg: "bg-cyan-500/10 border-cyan-500/25",
    desc: "Logs customer interactions, opportunity deal sizes, lead phases, or win status."
  },
  finance: {
    label: "Corporate Finance",
    icon: Coins,
    color: "text-indigo-400",
    bg: "bg-indigo-500/10 border-indigo-500/25",
    desc: "Aggregates revenue metrics, balance sheets, expenses, and cashflow details."
  },
  sales: {
    label: "Sales & E-Commerce",
    icon: ShoppingCart,
    color: "text-sky-400",
    bg: "bg-sky-500/10 border-sky-500/25",
    desc: "Summarizes order volumes, revenues, customer identifiers, and products."
  },
  generic: {
    label: "General Enterprise Data",
    icon: Database,
    color: "text-slate-400",
    bg: "bg-slate-500/10 border-slate-500/25",
    desc: "A generic multi-purpose dataset modeled for standard custom metric analytics."
  }
};

export function DatasetProfileCard({ semanticDict, datasetName }: DatasetProfileCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const domain = semanticDict?.domain || "generic";
  const config = DOMAIN_CONFIGS[domain] || DOMAIN_CONFIGS.generic;
  const Icon = config.icon;

  const dict = semanticDict?.semantic_dictionary || {
    date_columns: [],
    numeric_metrics: [],
    categorical_fields: [],
    entity_identifiers: [],
    status_fields: [],
    geographic_fields: []
  };

  const terms = semanticDict?.business_terminology || {
    dashboard_title: "Analytics Hub",
    primary_metric_label: "Primary Value",
    entity_count_label: "Total Entities",
    chart_title: "Trend Analytics"
  };

  const categories = [
    { key: "date_columns", label: "Date & Time Columns", icon: Calendar, color: "text-blue-400", list: dict.date_columns },
    { key: "numeric_metrics", label: "Numeric Metrics", icon: Binary, color: "text-amber-400", list: dict.numeric_metrics },
    { key: "categorical_fields", label: "Categorical Dimensions", icon: Layers, color: "text-purple-400", list: dict.categorical_fields },
    { key: "entity_identifiers", label: "Entity Identifiers", icon: Fingerprint, color: "text-pink-400", list: dict.entity_identifiers },
    { key: "status_fields", label: "Status & Phase Fields", icon: ToggleLeft, color: "text-cyan-400", list: dict.status_fields },
    { key: "geographic_fields", label: "Geographic Fields", icon: Globe, color: "text-emerald-400", list: dict.geographic_fields }
  ];

  return (
    <Card className="glass-card border border-border/50 rounded-[20px] overflow-hidden relative p-5 mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 z-10 relative">
        <div className="flex items-start gap-4">
          <div className={`p-3 rounded-2xl flex items-center justify-center border ${config.bg}`}>
            <Icon className={`w-8 h-8 ${config.color}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[13px] font-semibold text-muted-foreground uppercase tracking-wider">Dataset Profile: {datasetName}</span>
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium border ${config.bg} ${config.color}`}>
                {config.label}
              </span>
            </div>
            <h2 className="text-xl font-bold mt-1 text-foreground">
              {terms.dashboard_title}
            </h2>
            <p className="text-sm text-muted-foreground mt-1.5 max-w-2xl">
              {config.desc} Dynamically maps <strong>{terms.primary_metric_label}</strong> as primary metric and <strong>{terms.entity_count_label}</strong> as key entity indicator.
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 text-sm font-semibold text-foreground/80 hover:text-foreground px-4 py-2 rounded-xl bg-surface hover:bg-surface/80 border border-border/40 transition-all self-start md:self-auto"
        >
          {isOpen ? (
            <>
              Hide Semantic Schema <ChevronUp className="w-4 h-4" />
            </>
          ) : (
            <>
              Show Semantic Schema <ChevronDown className="w-4 h-4" />
            </>
          )}
        </button>
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden mt-5 pt-5 border-t border-border/40"
          >
            <h3 className="text-sm font-bold text-foreground/90 mb-4 tracking-tight">Semantic Data Dictionary</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {categories.map((cat) => {
                const CatIcon = cat.icon;
                return (
                  <div key={cat.key} className="p-4 rounded-xl bg-surface/30 border border-border/30 flex flex-col">
                    <div className="flex items-center gap-2 mb-3">
                      <CatIcon className={`w-4 h-4 ${cat.color}`} />
                      <span className="text-xs font-bold text-foreground/80">{cat.label}</span>
                      <span className="text-[10px] ml-auto px-1.5 py-0.5 bg-border/20 rounded font-semibold text-muted-foreground">
                        {cat.list?.length || 0}
                      </span>
                    </div>
                    {cat.list && cat.list.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5 mt-auto">
                        {cat.list.map((colName) => (
                          <span 
                            key={colName} 
                            className="text-[11px] px-2 py-0.5 rounded bg-foreground/5 hover:bg-foreground/10 border border-border/20 font-medium text-foreground/80 transition-all"
                          >
                            {colName}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground/60 italic mt-auto">None identified</span>
                    )}
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

"use client";

import React, { useLayoutEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { FileSpreadsheet, ShieldCheck, Search, LucideIcon } from "lucide-react";
import { AnimatedLogo } from "@/components/ui/AnimatedLogo";
import { getMetricTheme } from "./MetricCard";
import { formatKpiValue } from "@/lib/utils";
import type { Dataset } from "@/lib/types";

interface HubKpi {
  id?: string;
  name: string;
  value: number;
  type?: string;
}

interface DashboardHubProps {
  datasets: Dataset[];
  qualityScore?: number;
  kpis: HubKpi[];
  onInspectKpi?: (kpi: HubKpi) => void;
}

interface Node {
  icon: LucideIcon;
  label: string;
  value: string;
  gradient: string;
  glow: string;
  stroke: string;
  /** Set only on the KPI nodes — clicking opens the provenance view. The
   *  dataset/quality nodes on the left aren't computed figures, so there is
   *  nothing to trace and they stay inert. */
  onInspect?: () => void;
}

interface Point {
  x: number;
  y: number;
  r?: number;
}

// Same >=80/>=60 split already used for the quality-score color elsewhere
// (DatasetDetailDrawer) -- reused here so "Healthy" always means the same
// number range across the app instead of inventing a second threshold.
function qualityLabel(score?: number): string {
  if (score === undefined || score === null) return "Unknown";
  if (score >= 80) return "Healthy";
  if (score >= 60) return "Fair";
  return "Needs Attention";
}

function fileFormatLabel(datasets: Dataset[]): string {
  const exts = new Set(
    datasets.map((d) => d.name.split(".").pop()?.toLowerCase()).filter(Boolean)
  );
  const hasCsv = exts.has("csv");
  const hasExcel = exts.has("xlsx") || exts.has("xls");
  if (hasCsv && hasExcel) return "CSV / Excel";
  if (hasExcel) return "Excel";
  return "CSV";
}

function buildPath(from: Point, to: Point) {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const midX = from.x + dx / 2;

  if (Math.abs(dy) >= 30) {
    // Start and end are already far enough apart in height that a plain
    // S-curve diverges from both rows well before reaching the endpoint.
    return `M ${from.x} ${from.y} C ${midX} ${from.y}, ${midX} ${to.y}, ${to.x} ${to.y}`;
  }

  // Same-row connection: a plain S-curve stays level with the destination
  // row for most of its length, cutting straight under the label sitting
  // right next to the icon. Bow up early and hold that height until just
  // short of the icon, so only a brief final hook -- not the whole
  // approach -- passes anywhere near the label.
  const bow = 34;
  const c1x = from.x + dx * 0.4;
  const dockX = to.x - Math.max(24, dx * 0.08);
  return `M ${from.x} ${from.y} C ${c1x} ${from.y - bow}, ${dockX} ${from.y - bow}, ${to.x} ${to.y}`;
}

// Stops the line `dist` px short of `to`, so it ends at the icon's edge
// instead of running under it (and, for near-level nodes, under the label
// text sitting between the hub and the icon) -- the endpoint dot marks
// exactly where it should visually stop.
function shortenTowards(from: Point, to: Point, dist: number): Point {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const len = Math.hypot(dx, dy) || 1;
  const t = Math.max(0, (len - dist) / len);
  return { x: from.x + dx * t, y: from.y + dy * t };
}

// Where the line from `from` to `to` crosses a given x. Used to end a line at
// the label's edge: shortening by a distance would depend on how far away the
// node happens to sit, whereas the text always begins at a known x.
function pointAtX(from: Point, to: Point, x: number): Point {
  const dx = to.x - from.x;
  // Degenerate case: nothing sensible to interpolate, so leave it where it is.
  if (Math.abs(dx) < 0.5) return { x, y: to.y };
  const t = Math.min(1, Math.max(0, (x - from.x) / dx));
  return { x, y: from.y + (to.y - from.y) * t };
}

function centerOf(el: HTMLElement, containerRect: DOMRect): Point {
  const r = el.getBoundingClientRect();
  return {
    x: r.left + r.width / 2 - containerRect.left,
    y: r.top + r.height / 2 - containerRect.top,
    r: r.width / 2,
  };
}

export function DashboardHub({ datasets, qualityScore, kpis, onInspectKpi }: DashboardHubProps) {
  const leftNodes: Node[] = [
    {
      icon: FileSpreadsheet,
      label: fileFormatLabel(datasets),
      value: `${datasets.length} Dataset${datasets.length === 1 ? "" : "s"}`,
      gradient: "from-[#60a5fa] to-[#2563eb]",
      glow: "rgba(96, 165, 250, 0.55)",
      stroke: "#60a5fa",
    },
    {
      icon: ShieldCheck,
      label: "Data Quality",
      value: qualityLabel(qualityScore),
      gradient: "from-[#34d399] to-[#059669]",
      glow: "rgba(52, 211, 153, 0.55)",
      stroke: "#34d399",
    },
  ];

  const rightNodes: Node[] = kpis.slice(0, 4).map((k, i) => {
    const theme = getMetricTheme(k.type, i);
    return {
      onInspect: k.id ? () => onInspectKpi?.(k) : undefined,
      icon: theme.icon,
      label: k.name,
      value: formatKpiValue(k.value, k.type),
      gradient: theme.gradient,
      glow: theme.glow,
      stroke: theme.stroke,
    };
  });

  const containerRef = useRef<HTMLDivElement>(null);
  const centerRef = useRef<HTMLDivElement>(null);
  const leftIconRefs = useRef<(HTMLDivElement | null)[]>([]);
  const rightIconRefs = useRef<(HTMLDivElement | null)[]>([]);
  const leftTextRefs = useRef<(HTMLDivElement | null)[]>([]);
  const rightTextRefs = useRef<(HTMLDivElement | null)[]>([]);

  const [geometry, setGeometry] = useState<{
    size: { width: number; height: number };
    center: Point;
    left: Point[];
    right: Point[];
    /** x of each label's near edge, measured on the side the line approaches
     *  from. The endpoint is derived from this rather than from the icon. */
    leftTextEdge: number[];
    rightTextEdge: number[];
  } | null>(null);

  // The icon circles are laid out by flexbox (justify-around inside
  // absolutely-positioned left/right columns), not by anything the SVG
  // knows about -- a fixed viewBox of made-up coordinates drifts from the
  // real icon positions the moment the container width, node count, or
  // font metrics differ from whatever the numbers were eyeballed against.
  // Measuring the actual DOM boxes keeps every line's endpoint pinned to
  // the circle it's supposed to touch, at any width or KPI count.
  useLayoutEffect(() => {
    const measure = () => {
      const container = containerRef.current;
      const center = centerRef.current;
      if (!container || !center) return;
      const containerRect = container.getBoundingClientRect();
      setGeometry({
        size: { width: containerRect.width, height: containerRect.height },
        center: centerOf(center, containerRect),
        left: leftIconRefs.current
          .filter((el): el is HTMLDivElement => !!el)
          .map((el) => centerOf(el, containerRect)),
        right: rightIconRefs.current
          .filter((el): el is HTMLDivElement => !!el)
          .map((el) => centerOf(el, containerRect)),
        // A line reaches a left node from its right, and a right node from its
        // left, so the edge that matters is the one facing the hub.
        leftTextEdge: leftTextRefs.current
          .filter((el): el is HTMLDivElement => !!el)
          .map((el) => el.getBoundingClientRect().right - containerRect.left),
        rightTextEdge: rightTextRefs.current
          .filter((el): el is HTMLDivElement => !!el)
          .map((el) => el.getBoundingClientRect().left - containerRect.left),
      });
    };

    measure();
    const ro = new ResizeObserver(measure);
    if (containerRef.current) ro.observe(containerRef.current);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [leftNodes.length, rightNodes.length]);

  return (
    <>
    {/* Mobile: the hub diagram needs horizontal room for two node columns plus
        the logo between them — well past a phone's width, where the columns
        would collide. Below lg the same nodes render as a plain stacked grid
        and the connectors are dropped, since curves between stacked cards
        carry no meaning. */}
    <div className="grid grid-cols-1 gap-3 py-2 sm:grid-cols-2 lg:hidden">
      {[...leftNodes, ...rightNodes].map((node, i) => (
        <HubNode key={i} node={node} align="left" delay={0.1 + i * 0.08} iconRef={() => {}} />
      ))}
    </div>

    <div ref={containerRef} className="relative hidden w-full overflow-hidden px-6 py-8 lg:block">
      {geometry && (
        <svg
          viewBox={`0 0 ${geometry.size.width} ${geometry.size.height}`}
          className="absolute inset-0 w-full h-full pointer-events-none"
        >
          {[...leftNodes.slice(0, geometry.left.length), ...rightNodes.slice(0, geometry.right.length)].map(
            (node, i) => {
              const isLeft = i < geometry.left.length;
              const idx = isLeft ? i : i - geometry.left.length;
              const iconPos = isLeft ? geometry.left[idx] : geometry.right[idx];
              const textEdge = isLeft ? geometry.leftTextEdge[idx] : geometry.rightTextEdge[idx];

              // Stop at the label, not at the icon behind it. Ending on the
              // circle meant the last stretch of every line ran underneath the
              // text, which is the one place a line has nothing to say and
              // makes the words harder to read. Falls back to the icon edge if
              // the label has not been measured yet.
              const GAP = 12;
              const endPos =
                textEdge != null
                  ? pointAtX(
                      geometry.center,
                      iconPos,
                      isLeft ? textEdge + GAP : textEdge - GAP
                    )
                  : shortenTowards(geometry.center, iconPos, (iconPos.r ?? 22) + 3);
              const d = buildPath(geometry.center, endPos);
              return (
                <g key={i}>
                  <motion.path
                    d={d}
                    fill="none"
                    stroke={node.stroke}
                    strokeWidth={1.5}
                    strokeOpacity={0.45}
                    initial={{ pathLength: 0, opacity: 0 }}
                    animate={{ pathLength: 1, opacity: 1 }}
                    transition={{ duration: 1.1, ease: "easeOut", delay: 0.2 + i * 0.1 }}
                  />
                  <motion.circle
                    cx={endPos.x}
                    cy={endPos.y}
                    r={3}
                    fill={node.stroke}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3, delay: 0.2 + i * 0.1 + 1.1 }}
                  />
                  <circle r={2.5} fill={node.stroke}>
                    <animateMotion dur="3s" repeatCount="indefinite" path={d} begin={`${i * 0.35}s`} />
                  </circle>
                </g>
              );
            }
          )}
        </svg>
      )}

      <div className="relative flex items-center justify-center min-h-[280px]">
        <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-around py-6">
          {leftNodes.map((node, i) => (
            <HubNode
              key={i}
              node={node}
              align="left"
              delay={0.5 + i * 0.12}
              iconRef={(el) => (leftIconRefs.current[i] = el)}
              textRef={(el) => (leftTextRefs.current[i] = el)}
            />
          ))}
        </div>

        <motion.div
          ref={centerRef}
          initial={{ scale: 0.6, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 18, delay: 0.1 }}
          className="relative z-10"
        >
          <div
            className="absolute inset-0 rounded-full blur-2xl"
            style={{ background: "radial-gradient(circle, rgba(59,130,246,0.35) 0%, transparent 70%)" }}
          />
          <AnimatedLogo size={68} />
        </motion.div>

        <div className="absolute right-0 top-0 bottom-0 flex flex-col justify-around py-2">
          {rightNodes.map((node, i) => (
            <HubNode
              key={i}
              node={node}
              align="right"
              delay={0.5 + (i + leftNodes.length) * 0.12}
              iconRef={(el) => (rightIconRefs.current[i] = el)}
              textRef={(el) => (rightTextRefs.current[i] = el)}
            />
          ))}
        </div>
      </div>
    </div>
    </>
  );
}

function HubNode({
  node,
  align,
  delay,
  iconRef,
  textRef,
}: {
  node: Node;
  align: "left" | "right";
  delay: number;
  iconRef: (el: HTMLDivElement | null) => void;
  /** The label block. Lines end at its near edge, so the text is never
   *  something a connector has to pass underneath. */
  textRef?: (el: HTMLDivElement | null) => void;
}) {
  const Icon = node.icon;
  const clickable = !!node.onInspect;
  return (
    <motion.div
      initial={{ opacity: 0, x: align === "left" ? -12 : 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay }}
      onClick={node.onInspect}
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
      title={clickable ? "See where this number came from" : undefined}
      onKeyDown={
        clickable
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                node.onInspect?.();
              }
            }
          : undefined
      }
      className={`group flex items-center gap-3 rounded-xl ${
        align === "right" ? "flex-row-reverse text-right" : ""
      } ${
        // No hover background: these nodes sit on the hub's open canvas, and a
        // filled panel behind one of them reads as a stray card rather than a
        // hover state. The "Where from?" label and the icon brightening are
        // enough of a cue. Padding stays for the larger tap target.
        clickable
          ? "cursor-pointer -m-2 p-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
          : ""
      }`}
    >
      <div
        ref={iconRef}
        className={`flex shrink-0 items-center justify-center w-11 h-11 rounded-full bg-gradient-to-br ${node.gradient} ${
          clickable ? "transition-[filter] duration-200 group-hover:brightness-110" : ""
        }`}
        style={{ boxShadow: `inset 0 1px 0 rgba(255,255,255,0.35), 0 0 16px -4px ${node.glow}` }}
      >
        <Icon className="w-5 h-5 text-white" strokeWidth={2.25} />
      </div>
      <div ref={textRef} className="min-w-0">
        <p className="text-xs text-foreground/60 truncate max-w-[140px]">{node.label}</p>
        <p className="text-sm font-semibold text-foreground truncate max-w-[140px]">{node.value}</p>
        {clickable && (
          <p className="flex items-center gap-1 text-[10px] font-medium text-primary opacity-0 transition-opacity duration-200 group-hover:opacity-100">
            <Search className="h-2.5 w-2.5" /> Where from?
          </p>
        )}
      </div>
    </motion.div>
  );
}

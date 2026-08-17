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

// One source for the node entrance, because two things depend on it: the
// animation itself, and the moment the connector endpoints can be measured
// without catching a node mid-flight.
const NODE_ENTRANCE_DELAY = 0.5;
const NODE_ENTRANCE_STAGGER = 0.12;
const NODE_ENTRANCE_DURATION = 0.5;

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

/** Where a wire meets its icon: on the circle itself, up and toward the hub.
 *  Landing side-on would send the final stretch straight through the label
 *  sitting between the two; coming in over the top clears it, and puts the
 *  arrival where the orbit below can pick it up. */
function dockOnCircle(icon: Point, fromLeft: boolean): Point {
  const r = icon.r ?? 22;
  const k = Math.SQRT1_2; // 45 degrees, so the wire lands on the shoulder
  return { x: icon.x + (fromLeft ? -k : k) * r, y: icon.y - k * r };
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

  const [geometry, setGeometry] = useState<{
    size: { width: number; height: number };
    center: Point;
    left: Point[];
    right: Point[];
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
      });
    };

    measure();

    // Measured again once the nodes have finished arriving. Each one enters
    // translated 12px sideways, and getBoundingClientRect reports the
    // transformed box — so the first measurement pins every endpoint to where
    // its node was passing through rather than where it came to rest. The
    // container never changes size during that, so the ResizeObserver below
    // does not catch it.
    const lastEntranceEndsAt =
      (NODE_ENTRANCE_DELAY + (leftNodes.length + rightNodes.length - 1) * NODE_ENTRANCE_STAGGER +
        NODE_ENTRANCE_DURATION) * 1000;
    const settle = window.setTimeout(measure, lastEntranceEndsAt + 60);

    const ro = new ResizeObserver(measure);
    if (containerRef.current) ro.observe(containerRef.current);
    window.addEventListener("resize", measure);
    return () => {
      window.clearTimeout(settle);
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

              // The wire runs all the way to its icon and lands on the circle
              // itself, on the shoulder facing the hub rather than the side —
              // side-on would put the last stretch straight through the label.
              const endPos = dockOnCircle(iconPos, !isLeft);
              const d = buildPath(geometry.center, endPos);

              // The ring the wire feeds into. One short arc chasing its own
              // circumference: a dash pattern of "visible arc, then a gap the
              // length of everything else", offset over time, so a single
              // segment travels the rim instead of the whole outline pulsing.
              const orbitR = (iconPos.r ?? 22) + 5;
              const circumference = 2 * Math.PI * orbitR;
              const arcLength = circumference * 0.22;

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
                    cx={iconPos.x}
                    cy={iconPos.y}
                    r={orbitR}
                    fill="none"
                    stroke={node.stroke}
                    strokeWidth={1.5}
                    strokeLinecap="round"
                    strokeDasharray={`${arcLength} ${circumference - arcLength}`}
                    // Held back until the wire has finished drawing, so the
                    // ring reads as something the wire arrives and starts,
                    // rather than as decoration that was always spinning.
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.85 }}
                    transition={{ duration: 0.4, delay: 0.2 + i * 0.1 + 1.0 }}
                  >
                    <animate
                      attributeName="stroke-dashoffset"
                      from={circumference}
                      to="0"
                      dur="3.2s"
                      repeatCount="indefinite"
                      begin={`${i * 0.25}s`}
                    />
                  </motion.circle>

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
              delay={NODE_ENTRANCE_DELAY + i * NODE_ENTRANCE_STAGGER}
              iconRef={(el) => (leftIconRefs.current[i] = el)}
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
              delay={NODE_ENTRANCE_DELAY + (i + leftNodes.length) * NODE_ENTRANCE_STAGGER}
              iconRef={(el) => (rightIconRefs.current[i] = el)}
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
}: {
  node: Node;
  align: "left" | "right";
  delay: number;
  iconRef: (el: HTMLDivElement | null) => void;
}) {
  const Icon = node.icon;
  const clickable = !!node.onInspect;
  return (
    <motion.div
      initial={{ opacity: 0, x: align === "left" ? -12 : 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: NODE_ENTRANCE_DURATION, delay }}
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
      <div className="min-w-0">
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

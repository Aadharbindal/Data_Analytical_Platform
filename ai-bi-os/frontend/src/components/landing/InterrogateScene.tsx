"use client";

import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Check, MousePointerClick } from "lucide-react";

/** The rows are fixed sample data, not a live query — this page is public and
 *  must render before any backend is awake. They mirror the shape a real
 *  drilldown returns so the demonstration isn't misleading about the product. */
const ROWS = [
  { id: "TXN-4471", party: "Meridian Foods", city: "Pune", amount: 214500 },
  { id: "TXN-4472", party: "Kalpataru Retail", city: "Mumbai", amount: 318000 },
  { id: "TXN-4473", party: "Anand Traders", city: "Nashik", amount: 96750 },
  { id: "TXN-4474", party: "Sunrise Exports", city: "Surat", amount: 402300 },
  { id: "TXN-4475", party: "Vertex Supply Co", city: "Pune", amount: 158900 },
];

const TOTAL_LABEL = "₹34.01L";

const EASE = [0.22, 1, 0.36, 1] as const;

/** Both panels expand and collapse by animating their own height, so whatever
 *  sits below moves with them instead of being shoved. Opacity finishes ahead
 *  of the height on the way in and leads it on the way out, which stops the
 *  content from appearing to slide out of a clipped edge. */
function useSwapMotion(reduce: boolean | null) {
  if (reduce) {
    return {
      initial: { opacity: 0 },
      animate: { opacity: 1, height: "auto" as const },
      exit: { opacity: 0 },
      transition: { duration: 0.15 },
    };
  }
  return {
    initial: { opacity: 0, height: 0 },
    animate: { opacity: 1, height: "auto" as const },
    exit: { opacity: 0, height: 0 },
    transition: {
      height: { duration: 0.42, ease: EASE },
      opacity: { duration: 0.26, ease: "easeOut" as const },
    },
  };
}

export function InterrogateScene() {
  const [open, setOpen] = useState(false);
  const reduce = useReducedMotion();
  const wrapRef = useRef<HTMLDivElement>(null);
  const [pointer, setPointer] = useState({ x: 0, y: 0 });
  const swap = useSwapMotion(reduce);

  // The ambient glow tracks the cursor. Stored as an offset from centre in a
  // -1..1 range so the same values drive both the glow position and the very
  // slight parallax on the figure, keeping them visually coupled.
  useEffect(() => {
    if (reduce) return;
    const el = wrapRef.current;
    if (!el) return;
    const onMove = (e: PointerEvent) => {
      const r = el.getBoundingClientRect();
      setPointer({
        x: ((e.clientX - r.left) / r.width - 0.5) * 2,
        y: ((e.clientY - r.top) / r.height - 0.5) * 2,
      });
    };
    el.addEventListener("pointermove", onMove);
    return () => el.removeEventListener("pointermove", onMove);
  }, [reduce]);

  return (
    <div ref={wrapRef} className="relative w-full">
      {/* Cursor-tracked glow. Pure decoration, so it never intercepts clicks. */}
      <motion.div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-1/2 -z-10 h-[520px] w-[520px] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[90px]"
        animate={{
          x: reduce ? 0 : pointer.x * 60,
          y: reduce ? 0 : pointer.y * 40,
          opacity: open ? 0.5 : 0.32,
        }}
        transition={{ type: "spring", stiffness: 40, damping: 20 }}
        style={{
          background:
            "radial-gradient(circle, rgba(59,130,246,0.55) 0%, rgba(59,130,246,0) 70%)",
        }}
      />

      <div className="flex w-full flex-col items-center">
        {/* The figure. Clicking is the whole point of the page, so it is a real
            button rather than a div with a handler — reachable by keyboard and
            announced as interactive. */}
        <motion.button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-label={open ? "Hide how this number was computed" : "Show how this number was computed"}
          animate={{
            x: reduce ? 0 : pointer.x * 8,
            y: reduce ? 0 : pointer.y * 5,
            scale: open ? 0.82 : 1,
          }}
          whileHover={reduce ? undefined : { scale: open ? 0.84 : 1.02 }}
          whileTap={reduce ? undefined : { scale: open ? 0.8 : 0.98 }}
          transition={{ type: "spring", stiffness: 160, damping: 20 }}
          className="group relative cursor-pointer rounded-3xl px-4 py-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/60"
        >
          <span className="block bg-gradient-to-b from-white to-white/55 bg-clip-text text-[clamp(3.5rem,13vw,9rem)] font-bold leading-[0.95] tracking-[-0.04em] text-transparent tabular-metrics">
            {TOTAL_LABEL}
          </span>
        </motion.button>

        {/* One AnimatePresence rather than the two that ran side by side: the
            outgoing panel collapses its height while the incoming one expands,
            so the pair occupies a single continuous block instead of fighting
            over the same vertical space, which is what made the panel look
            like it opened in halves.

            Deliberately NOT mode="wait" — that makes the new panel wait on the
            old one's exit animation, so anything that stalls the animation
            leaves the number permanently unopenable. Overlapping the two is
            both smoother and impossible to deadlock. */}
        <div className="relative w-full">
          <AnimatePresence initial={false}>
            {open ? (
              <motion.div key="proof" {...swap} className="overflow-hidden">
                <div className="mx-auto mt-6 w-full max-w-2xl">
                  <div className="rounded-2xl border border-border/60 bg-background/60 p-5 backdrop-blur-xl">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <code className="font-mono text-sm text-foreground">
                        SUM(amount) WHERE status = &lsquo;Cleared&rsquo;
                      </code>
                      <span className="flex items-center gap-1.5 text-xs font-medium text-success">
                        <Check className="h-3.5 w-3.5" /> Recomputed — matches
                      </span>
                    </div>

                    <p className="mt-2 text-xs text-muted-foreground">
                      638 of 971 rows used · 333 left out because amount is empty
                    </p>

                    {/* The rows carry no entrance animation of their own. The
                        panel unrolling already reveals them in order, and
                        staggering them on top of that was what read as the
                        table filling in piece by piece. */}
                    <div className="mt-4 overflow-x-auto rounded-xl border border-border/40">
                      <table className="w-full min-w-max text-left text-[12px]">
                        <thead className="bg-surface/50">
                          <tr>
                            {["amount", "id", "party", "city"].map((h) => (
                              <th
                                key={h}
                                className={`whitespace-nowrap px-3 py-2 font-medium ${
                                  h === "amount" ? "text-primary" : "text-muted-foreground"
                                }`}
                              >
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {ROWS.map((r) => (
                            <tr key={r.id} className="border-t border-border/25">
                              <td className="whitespace-nowrap px-3 py-2 font-semibold text-foreground tabular-metrics">
                                {r.amount.toLocaleString("en-IN")}
                              </td>
                              <td className="whitespace-nowrap px-3 py-2 text-muted-foreground">{r.id}</td>
                              <td className="whitespace-nowrap px-3 py-2 text-muted-foreground">{r.party}</td>
                              <td className="whitespace-nowrap px-3 py-2 text-muted-foreground">{r.city}</td>
                            </tr>
                          ))}
                          <tr className="border-t border-border/25">
                            <td colSpan={4} className="px-3 py-2 text-[11px] text-muted-foreground/70">
                              …633 more rows
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    <button
                      onClick={() => setOpen(false)}
                      className="mt-4 text-xs text-muted-foreground underline-offset-4 transition-colors hover:text-foreground hover:underline"
                    >
                      Collapse
                    </button>
                  </div>
                </div>
              </motion.div>
            ) : (
              <motion.div key="prompt" {...swap} className="overflow-hidden">
                <div className="mt-5 flex flex-col items-center gap-3">
                  <p className="text-sm text-muted-foreground">
                    Total payments this year. Where did it come from?
                  </p>
                  <motion.button
                    onClick={() => setOpen(true)}
                    whileHover={reduce ? undefined : { scale: 1.04 }}
                    whileTap={reduce ? undefined : { scale: 0.97 }}
                    transition={{ type: "spring", stiffness: 400, damping: 22 }}
                    className="flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-5 py-2.5 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
                  >
                    <MousePointerClick className="h-4 w-4" />
                    Interrogate this number
                  </motion.button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

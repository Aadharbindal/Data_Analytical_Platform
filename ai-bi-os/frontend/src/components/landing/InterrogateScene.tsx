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
 *  content from appearing to slide out of a clipped edge.
 *
 *  This is deliberately identical under prefers-reduced-motion. That setting
 *  asks for less motion, not none, and an accordion that snaps open is not an
 *  accessible accordion — it is a broken one. What the setting does switch off
 *  here is the cursor parallax, the blur and the scale, which are the effects
 *  it actually exists for. */
const SWAP_MOTION = {
  initial: { opacity: 0, height: 0 },
  animate: { opacity: 1, height: "auto" as const },
  exit: { opacity: 0, height: 0 },
  transition: {
    height: { duration: 0.42, ease: EASE },
    opacity: { duration: 0.26, ease: "easeOut" as const },
  },
};

/** Starting state for an entrance. Under prefers-reduced-motion the movement,
 *  scale and blur are dropped but the fade and its timing survive — the setting
 *  asks for less motion, not for a page that arrives already finished. */
function enterFrom(reduce: boolean | null, moving: Record<string, number | string>) {
  return reduce ? { opacity: 0 } : { opacity: 0, ...moving };
}

interface InterrogateSceneProps {
  /** Seconds to wait before this scene plays its entrance, so it can take its
   *  turn in the page's opening sequence rather than arriving with the text. */
  entranceDelay?: number;
}

export function InterrogateScene({ entranceDelay = 0 }: InterrogateSceneProps) {
  const [open, setOpen] = useState(false);
  const reduce = useReducedMotion();
  const wrapRef = useRef<HTMLDivElement>(null);
  const [pointer, setPointer] = useState({ x: 0, y: 0 });
  const swap = SWAP_MOTION;

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
          // A slow breath underneath everything, on its own clock, so the page
          // keeps moving faintly long after the entrance has finished.
          scale: reduce ? 1 : [1, 1.08, 1],
        }}
        transition={{
          x: { type: "spring", stiffness: 40, damping: 20 },
          y: { type: "spring", stiffness: 40, damping: 20 },
          opacity: { duration: 0.6, ease: "easeOut" },
          scale: { duration: 9, ease: "easeInOut", repeat: Infinity },
        }}
        style={{
          background:
            "radial-gradient(circle, rgba(59,130,246,0.55) 0%, rgba(59,130,246,0) 70%)",
        }}
      />

      <div className="flex w-full flex-col items-center">
        {/* Entrance lives on a wrapper rather than on the button itself: the
            button's own animate prop is already driving the cursor parallax and
            the open/closed scale, and a second one would overwrite it. The
            figure resolves out of a blur, which reads as it coming into
            focus — apt for the thing the page asks you to examine. */}
        <motion.div
          initial={enterFrom(reduce, { scale: 0.88, filter: "blur(18px)" })}
          animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
          transition={{ duration: 1.45, delay: entranceDelay, ease: EASE }}
        >
        {/* A separate layer for the perpetual drift, because the wrapper above
            it is busy finishing the entrance and the button below it is busy
            with the cursor parallax — three jobs, three elements. Six seconds
            for six pixels: enough that the page is never quite still, not
            enough to notice it moving. */}
        <motion.div
          animate={reduce ? undefined : { y: [0, -6, 0] }}
          transition={{ duration: 6, ease: "easeInOut", repeat: Infinity }}
        >
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
        </motion.div>
        </motion.div>

        {/* One AnimatePresence rather than the two that ran side by side: the
            outgoing panel collapses its height while the incoming one expands,
            so the pair occupies a single continuous block instead of fighting
            over the same vertical space, which is what made the panel look
            like it opened in halves.

            Deliberately NOT mode="wait" — that makes the new panel wait on the
            old one's exit animation, so anything that stalls the animation
            leaves the number permanently unopenable. Overlapping the two is
            both smoother and impossible to deadlock. */}
        {/* The entrance sits on this wrapper rather than inside the presence,
            so the swap between prompt and proof stays untouched by it. */}
        <motion.div
          className="relative w-full"
          initial={enterFrom(reduce, { y: 18 })}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.1, delay: entranceDelay + 0.22, ease: EASE }}
        >
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
                {/* The gap does the work rather than the top margin: the caption
                    belongs close under the figure, and only the button needed
                    to come down. */}
                <div className="mt-5 flex flex-col items-center gap-6">
                  <p className="text-sm text-muted-foreground">
                    Total payments this year. Where did it come from?
                  </p>
                  {/* Everything here is CSS: a gradient rim, a gradient face, a
                      hairline along the top edge and a glow, none of which move.
                      That is deliberate — anyone with reduced motion turned on
                      sees no perpetual animation at all, so the button has to
                      carry itself standing still. The hover effects are plain
                      transitions, which run for everyone. */}
                  <motion.button
                    onClick={() => setOpen(true)}
                    whileHover={reduce ? undefined : { scale: 1.04 }}
                    whileTap={reduce ? undefined : { scale: 0.97 }}
                    transition={{ type: "spring", stiffness: 400, damping: 22 }}
                    className="group relative overflow-hidden rounded-full p-px shadow-[0_0_26px_-14px_var(--primary)] transition-shadow duration-500 hover:shadow-[0_0_30px_-10px_var(--primary)] focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                  >
                    {/* Every colour here is mixed from --primary and --surface
                        rather than picked by hand. Hard-coded blues were a shade
                        brighter and greener than the theme's #0070F3, which is
                        what made this read as borrowed from another site. */}
                    <span
                      aria-hidden
                      className="absolute inset-0 rounded-full"
                      style={{
                        backgroundImage:
                          "linear-gradient(135deg, color-mix(in srgb, var(--primary) 65%, transparent) 0%, rgba(255,255,255,0.07) 45%, color-mix(in srgb, var(--primary) 25%, transparent) 100%)",
                      }}
                    />

                    <span
                      className="relative flex items-center gap-2.5 rounded-full px-6 py-3 text-sm font-medium tracking-[0.01em] text-primary transition-colors duration-300 group-hover:text-foreground"
                      style={{
                        backgroundImage:
                          "linear-gradient(180deg, color-mix(in srgb, var(--primary) 13%, var(--surface)) 0%, var(--surface) 60%, var(--background) 100%)",
                      }}
                    >
                      {/* A hairline along the top edge, faint enough to read as a
                          catch of light rather than a stroke of white. */}
                      <span
                        aria-hidden
                        className="pointer-events-none absolute inset-x-5 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent"
                      />

                      <span aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden rounded-full">
                        <span className="absolute inset-y-0 -left-full w-1/2 -skew-x-12 bg-gradient-to-r from-transparent via-white/15 to-transparent transition-[left] duration-700 ease-out group-hover:left-[150%]" />
                      </span>

                      <MousePointerClick
                        className="relative h-4 w-4 text-primary transition-transform duration-300 group-hover:-rotate-12 group-hover:scale-110"
                        strokeWidth={2.2}
                      />
                      <span className="relative">Interrogate this number</span>
                    </span>
                  </motion.button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}

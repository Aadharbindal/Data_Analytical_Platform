"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useReducedMotion } from "framer-motion";

/** Sweeps across the face on hover. Kept even under reduced motion: it runs
 *  only on a deliberate hover and is over in well under a second, which is a
 *  different thing from something that moves on its own indefinitely. */
function Shine({ gradient }: { gradient: string }) {
  return (
    <span aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden rounded-full">
      {/* `gradient` arrives as a complete class string. Composing it here from a
          fragment (via-${x}) would produce a class Tailwind never sees in the
          source and therefore never generates, and the shine would silently be
          invisible. */}
      <span
        className={`absolute inset-y-0 -left-full w-1/2 -skew-x-12 bg-gradient-to-r transition-[left] duration-700 ease-out group-hover:left-[150%] ${gradient}`}
      />
    </span>
  );
}

/**
 * The quiet one. A single point of light travels the rim: a conic gradient
 * spins inside a clipped, 1.5px-padded rounded box, and the opaque pill on top
 * covers everything but the padding, so only the ring lights up.
 *
 * Reuses `animate-auth-border-travel`, the keyframe the sign-in page already
 * uses for its travelling border, rather than adding a second one that does the
 * same job. Under reduced motion the rim stops turning and settles into a fixed
 * gradient.
 */
export function RimButton({
  href,
  children,
  size = "sm",
}: {
  href: string;
  children: React.ReactNode;
  /** "lg" matches the primary button's height so the two sit level when they
   *  appear side by side in the closing call to action. */
  size?: "sm" | "lg";
}) {
  const reduce = useReducedMotion();
  // 12.5px rather than 14: the rim adds 1.5px above and below, and "lg" has to
  // finish at the same height as the primary button standing next to it.
  const pad = size === "lg" ? "px-6 py-[12.5px]" : "px-5 py-2";

  return (
    <Link
      href={href}
      className="group relative inline-flex overflow-hidden rounded-full p-[1.5px] transition-shadow duration-500 hover:shadow-[0_0_24px_-4px_var(--primary)]"
    >
      {/* Sized well past the box and centred, so the gradient's corners never
          swing into view as it turns. */}
      <span
        aria-hidden
        className={`absolute left-1/2 top-1/2 h-[320%] w-[320%] -translate-x-1/2 -translate-y-1/2 ${
          reduce ? "" : "animate-auth-border-travel"
        }`}
        style={{
          background: reduce
            ? "linear-gradient(120deg, rgba(255,255,255,0.14), var(--primary), rgba(255,255,255,0.14))"
            : "conic-gradient(from 0deg, transparent 0deg, transparent 250deg, var(--primary) 320deg, #a5c8ff 345deg, transparent 360deg)",
        }}
      />

      <span
        className={`relative flex items-center rounded-full bg-[#080b12] ${pad} text-sm text-muted-foreground transition-colors duration-300 group-hover:text-foreground`}
      >
        <span
          aria-hidden
          className="absolute inset-0 rounded-full bg-primary/10 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        />
        <Shine gradient="from-transparent via-white/20 to-transparent" />
        <span className="relative">{children}</span>
        {/* The arrow and its spacing both collapse to zero at rest, so the pill
            keeps its resting width and the label stays centred rather than
            carrying a gap to an arrow that isn't there. */}
        <ArrowRight
          className="relative ml-0 h-3.5 w-0 opacity-0 transition-all duration-300 group-hover:ml-1.5 group-hover:w-3.5 group-hover:opacity-100"
          strokeWidth={2.2}
        />
      </span>
    </Link>
  );
}

/**
 * The loud one, for the page's single most important action.
 *
 * The fill is a wide gradient drifting sideways under a mask twice its width,
 * driven by `animate-auth-shimmer` — again the existing house keyframe rather
 * than a new one. The effect is a slow shift in the blue rather than anything
 * that reads as animating, which is what keeps it from looking like a loading
 * state. Under reduced motion the gradient holds still.
 */
export function PrimaryButton({ href, children }: { href: string; children: React.ReactNode }) {
  const reduce = useReducedMotion();

  return (
    <Link
      href={href}
      className="group relative inline-flex overflow-hidden rounded-full shadow-[0_10px_34px_-10px_var(--primary)] transition-shadow duration-500 hover:shadow-[0_14px_46px_-8px_var(--primary)]"
    >
      <span
        aria-hidden
        className={`absolute inset-0 ${reduce ? "" : "animate-auth-shimmer"}`}
        style={{
          background: "linear-gradient(100deg, #1d4ed8, #3b82f6, #60a5fa, #3b82f6, #1d4ed8)",
          backgroundSize: "200% 100%",
        }}
      />
      {/* Brighter than the rim button's shine because it has a saturated blue
          to cut through rather than near-black. */}
      <Shine gradient="from-transparent via-white/35 to-transparent" />
      <span className="relative flex items-center gap-2 px-7 py-3.5 text-sm font-medium text-white">
        {children}
        <ArrowRight
          className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1"
          strokeWidth={2.2}
        />
      </span>
    </Link>
  );
}

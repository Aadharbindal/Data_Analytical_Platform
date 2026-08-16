"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useReducedMotion } from "framer-motion";

/**
 * The header's sign-in control.
 *
 * A single point of light travels around the rim, produced by spinning a conic
 * gradient inside a clipped, rounded, 1.5px-padded box: the child pill covers
 * the middle, so only the padding ring shows the gradient underneath. This
 * reuses `animate-auth-border-travel`, the same keyframe the sign-in page
 * already uses for its travelling border, rather than inventing a second one.
 *
 * On hover a shine crosses the face and the arrow slides out from behind the
 * label. Under prefers-reduced-motion the rim stops travelling and settles into
 * a fixed gradient, and the shine never runs — a light circling the screen
 * forever is precisely what that setting is asking to be spared.
 */
export function SignInButton() {
  const reduce = useReducedMotion();

  return (
    <Link
      href="/login"
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

      {/* The face. Opaque enough to hide the gradient behind it, leaving only
          the ring lit. */}
      <span className="relative flex items-center rounded-full bg-[#080b12] px-5 py-2 text-sm text-muted-foreground transition-colors duration-300 group-hover:text-foreground">
        {/* Fills in behind the label on hover so the button reads as pressed
            into the page rather than sitting flat on it. */}
        <span
          aria-hidden
          className="absolute inset-0 rounded-full bg-primary/10 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        />

        {/* Kept for reduced motion too: this only runs on a deliberate hover
            and is over in well under a second, which is a different thing from
            the rim light that would otherwise circle forever. */}
        <span
          aria-hidden
          className="pointer-events-none absolute inset-0 overflow-hidden rounded-full"
        >
          <span className="absolute inset-y-0 -left-full w-1/2 -skew-x-12 bg-gradient-to-r from-transparent via-white/20 to-transparent transition-[left] duration-700 ease-out group-hover:left-[150%]" />
        </span>

        <span className="relative">Sign in</span>
        {/* Collapsed to nothing until hover, and the spacing collapses with it,
            so the label stays centred in the pill at rest instead of carrying a
            gap to an arrow that isn't there. */}
        <ArrowRight
          className="relative ml-0 h-3.5 w-0 opacity-0 transition-all duration-300 group-hover:ml-1.5 group-hover:w-3.5 group-hover:opacity-100"
          strokeWidth={2.2}
        />
      </span>
    </Link>
  );
}

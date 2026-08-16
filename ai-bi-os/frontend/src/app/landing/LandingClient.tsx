"use client";

import React from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, FileSpreadsheet, Sheet, MessageSquareText } from "lucide-react";
import { AnimatedLogo } from "@/components/ui/AnimatedLogo";
import { InterrogateScene } from "@/components/landing/InterrogateScene";

/* Deliberately not built like the signed-in welcome flow, which is already a
   numbered scroll tour of alternating text-and-mockup panels. Repeating that
   shape here would give the product two tours and no argument. This page makes
   one point — that a figure can be taken apart — and lets the visitor do it. */

function Rule() {
  return <div className="mx-auto h-px w-full max-w-3xl bg-border/40" />;
}

export function LandingClient() {
  const reduce = useReducedMotion();

  return (
    <div className="relative min-h-screen w-full overflow-x-hidden bg-background text-foreground">
      {/* Static field behind everything. Kept extremely subtle so the figure in
          the hero is the only thing competing for attention. */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 -z-20 opacity-[0.35]"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 15%, rgba(59,130,246,0.16) 0%, transparent 45%), radial-gradient(circle at 82% 70%, rgba(99,102,241,0.12) 0%, transparent 45%)",
        }}
      />

      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-5 py-6 sm:px-8">
        <Link href="/landing" className="flex items-center gap-2.5">
          <AnimatedLogo size={30} />
          <span className="text-[15px] font-semibold tracking-wide">Numerate</span>
        </Link>
        <Link
          href="/login"
          className="rounded-full border border-border/60 px-4 py-2 text-sm text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
        >
          Sign in
        </Link>
      </header>

      <main className="mx-auto w-full max-w-6xl px-5 sm:px-8">
        <section className="flex min-h-[78vh] flex-col items-center justify-center py-10 text-center">
          <motion.h1
            initial={reduce ? false : { opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="max-w-3xl text-balance text-[clamp(1.6rem,4.4vw,2.75rem)] font-semibold leading-[1.15] tracking-[-0.02em]"
          >
            Ask your spreadsheet anything.
            <span className="block text-muted-foreground">Then check the answer.</span>
          </motion.h1>

          <motion.p
            initial={reduce ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.12 }}
            className="mt-4 max-w-xl text-[15px] leading-relaxed text-muted-foreground"
          >
            Every figure is computed by code, never guessed by a model — and any of
            them can be taken apart. Try it on this one.
          </motion.p>

          <div className="mt-12 w-full">
            <InterrogateScene />
          </div>
        </section>

        <Rule />

        {/* The honest contrast, stated in prose rather than as a feature grid.
            This is the argument the product is built on, so it gets words, not
            iconography. */}
        <section className="mx-auto max-w-2xl py-20 text-center">
          <p className="text-[clamp(1.15rem,2.6vw,1.5rem)] leading-relaxed tracking-[-0.01em]">
            Ask most AI tools about your sales data and you get a number that sounds
            certain.{" "}
            <span className="text-muted-foreground">
              You have no way to tell whether it is. For a business decision, a wrong
              number that looks right is worse than no number at all.
            </span>
          </p>
        </section>

        <Rule />

        <section className="py-20">
          <div className="mx-auto grid max-w-4xl gap-8 sm:grid-cols-3">
            {[
              {
                icon: FileSpreadsheet,
                title: "Bring your data",
                body: "Upload a CSV or Excel file, or connect a Google Sheet that keeps itself current.",
              },
              {
                icon: MessageSquareText,
                title: "Ask in plain English",
                body: "No SQL, no dashboard to build. Questions like you'd ask a colleague.",
              },
              {
                icon: Sheet,
                title: "Check anything",
                body: "Click a figure for its formula, how much of the data it used, and the rows themselves.",
              },
            ].map((s, i) => (
              <motion.div
                key={s.title}
                initial={reduce ? false : { opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="text-left"
              >
                <s.icon className="h-5 w-5 text-primary" strokeWidth={2} />
                <h3 className="mt-3 text-[15px] font-semibold">{s.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
              </motion.div>
            ))}
          </div>
        </section>

        <Rule />

        {/* Stating the limits is unusual on a marketing page and is the point:
            a tool that claims everything is harder to trust than one that says
            where it stops. */}
        <section className="mx-auto max-w-2xl py-20">
          <h2 className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">
            What it does, and doesn&apos;t
          </h2>
          <ul className="mt-5 space-y-3 text-[15px] leading-relaxed">
            <li className="text-foreground">
              Totals, trends, top and bottom performers, breakdowns, change over time.
            </li>
            <li className="text-muted-foreground">
              Not forecasting the future, and not questions your data doesn&apos;t contain.
            </li>
            <li className="text-muted-foreground">
              It will say it can&apos;t answer rather than produce something approximate.
            </li>
          </ul>
        </section>

        <section className="flex flex-col items-center gap-5 py-24 text-center">
          <h2 className="text-[clamp(1.4rem,3.4vw,2rem)] font-semibold tracking-[-0.02em]">
            Bring one spreadsheet. See what it says.
          </h2>
          <Link
            href="/signup"
            className="group flex items-center gap-2 rounded-full bg-primary px-7 py-3.5 text-sm font-medium text-primary-foreground shadow-[0_10px_34px_-10px_var(--primary)] transition-transform hover:scale-[1.03] active:scale-[0.98]"
          >
            Get started free
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </section>
      </main>

      <footer className="border-t border-border/40 py-8 text-center text-xs text-muted-foreground">
        Numerate — Smart Analytics. Better Decisions.
      </footer>
    </div>
  );
}

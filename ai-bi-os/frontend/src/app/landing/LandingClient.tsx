"use client";

import React from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  FileSpreadsheet,
  Sheet,
  MessageSquareText,
  TrendingUp,
  LineChart,
  ScatterChart,
  Layers,
  AlertTriangle,
  Sigma,
  PieChart,
  Share2,
  History,
} from "lucide-react";
import { AnimatedLogo } from "@/components/ui/AnimatedLogo";
import { InterrogateScene } from "@/components/landing/InterrogateScene";

/* Deliberately not built like the signed-in welcome flow, which is already a
   numbered scroll tour of alternating text-and-mockup panels. Repeating that
   shape here would give the product two tours and no argument. This page makes
   one point — that a figure can be taken apart — and lets the visitor do it. */

/** Phrased the way someone actually types, not as feature names. */
const QUESTIONS = [
  "Which city fell the most last quarter?",
  "Show revenue by month",
  "Who are my top 10 customers?",
  "Is anything unusual in September?",
  "Compare this month to last",
  "What is my average deal size?",
];

/** Every one of these is a real analysis page in the product — nothing here is
 *  aspirational. Naming them is also the honest answer to "is this just a
 *  chatbot?", which is the first thing a sceptical visitor will assume. */
const CAPABILITIES = [
  { icon: TrendingUp, label: "Trends" },
  { icon: LineChart, label: "Forecasts" },
  { icon: ScatterChart, label: "Correlation" },
  { icon: AlertTriangle, label: "Outliers" },
  { icon: Layers, label: "Segments" },
  { icon: Sigma, label: "Regression" },
  { icon: PieChart, label: "Distribution" },
  { icon: History, label: "Time series" },
];

const STEPS = [
  {
    icon: FileSpreadsheet,
    title: "Bring your data",
    body: "Upload a CSV or Excel file, or connect a Google Sheet that pulls the latest rows whenever you refresh it.",
  },
  {
    icon: MessageSquareText,
    title: "Ask in plain English",
    body: "No SQL, no dashboard to assemble first. Ask the way you'd ask the person who owns the spreadsheet.",
  },
  {
    icon: Sheet,
    title: "Check anything",
    body: "Click any figure for the formula behind it, how many rows it used, how many it skipped and why, and the rows themselves.",
  },
];

const EASE = [0.22, 1, 0.36, 1] as const;

/** Starting state for an entrance. Under prefers-reduced-motion the movement,
 *  scale and blur are dropped but the fade and its timing survive.
 *
 *  Gating the whole animation on that setting — which is what this page did at
 *  first — means anyone who has turned animation effects off in Windows or
 *  macOS sees the page arrive already finished, with nothing to look at. The
 *  setting asks for less motion, not for none. */
function enterFrom(reduce: boolean | null, moving: Record<string, number | string>) {
  return reduce ? { opacity: 0 } : { opacity: 0, ...moving };
}

/** Draws itself outward from the centre as it comes into view. A hairline that
 *  simply appears is the one element on the page that would look pasted on. */
function Rule() {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className="mx-auto h-px w-full max-w-5xl origin-center bg-border/40"
      initial={enterFrom(reduce, { scaleX: 0 })}
      whileInView={{ scaleX: 1, opacity: 1 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 1.0, ease: EASE }}
    />
  );
}

/** Small caps label. Used instead of headlines so the page never competes with
 *  the one number in the hero. */
function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground/70">
      {children}
    </p>
  );
}

function Reveal({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      initial={enterFrom(reduce, { y: 14 })}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-70px" }}
      transition={{ duration: 0.95, delay, ease: EASE }}
    >
      {children}
    </motion.div>
  );
}

/** The opening sequence. The gap between elements is far shorter than how long
 *  each one takes, so every element is still settling when the next begins —
 *  five overlapping moves read as one continuous rise, where an interval wider
 *  than the duration would read as five separate arrivals. */
const HERO_STEP = 0.15;
const HERO_DURATION = 1.3;

/** Lift on hover. Kept to two pixels and a border brighten — enough to say the
 *  card is a surface, not enough to make the page bounce as the cursor crosses
 *  it. Skipped entirely under reduced motion. */
function useHoverLift(reduce: boolean | null) {
  if (reduce) return {};
  return {
    whileHover: { y: -3 },
    transition: { type: "spring" as const, stiffness: 320, damping: 24 },
  };
}

export function LandingClient() {
  const reduce = useReducedMotion();
  const lift = useHoverLift(reduce);

  return (
    <div className="relative min-h-screen w-full overflow-x-hidden bg-background text-foreground">
      {/* Static field behind everything. Kept extremely subtle so the figure in
          the hero is the only thing competing for attention. */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 -z-20 opacity-[0.35]"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 12%, rgba(59,130,246,0.16) 0%, transparent 45%), radial-gradient(circle at 84% 68%, rgba(99,102,241,0.12) 0%, transparent 45%)",
        }}
      />

      {/* Full-bleed rather than centred on the reading column: the brand belongs
          at the edge of the screen the way it does in the sidebar and on the
          sign-in page, otherwise on a wide monitor it floats hundreds of
          pixels in. The reading content below stays constrained. */}
      <header className="flex w-full items-center justify-between px-5 py-6 sm:px-8">
        <motion.div
          initial={enterFrom(reduce, { x: -16 })}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: HERO_DURATION, ease: EASE }}
        >
          <Link href="/landing" className="flex items-center gap-3">
            {/* The glow is a fixed 15px blur that doesn't scale with the logo, so
                anything under ~32px gets swamped by its own halo. 36 keeps it in
                proportion and in line with every other place the mark appears. */}
            <AnimatedLogo size={36} />
            <span className="text-base font-semibold tracking-wide">Numerate</span>
          </Link>
        </motion.div>
        <motion.div
          initial={enterFrom(reduce, { x: 16 })}
          animate={{ opacity: 1, x: 0 }}
          whileHover={reduce ? undefined : { y: -2 }}
          transition={{ duration: HERO_DURATION, delay: HERO_STEP * 0.6, ease: EASE }}
        >
          <Link
            href="/login"
            className="block rounded-full border border-border/60 px-4 py-2 text-sm text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
          >
            Sign in
          </Link>
        </motion.div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-5 sm:px-8">
        {/* ---------------------------------------------------------------- */}
        <section className="flex min-h-[72vh] flex-col items-center justify-center py-8 text-center">
          {/* The two lines arrive separately: the claim, then the qualifier that
              makes it worth reading. Landing them together loses that turn. */}
          <h1 className="max-w-3xl text-balance text-[clamp(1.6rem,4.4vw,2.75rem)] font-semibold leading-[1.15] tracking-[-0.02em]">
            <motion.span
              className="block"
              initial={enterFrom(reduce, { y: 22, filter: "blur(8px)" })}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              transition={{ duration: HERO_DURATION, delay: HERO_STEP, ease: EASE }}
            >
              Ask your spreadsheet anything.
            </motion.span>
            <motion.span
              className="block text-muted-foreground"
              initial={enterFrom(reduce, { y: 22, filter: "blur(8px)" })}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              transition={{ duration: HERO_DURATION, delay: HERO_STEP * 2, ease: EASE }}
            >
              Then check the answer.
            </motion.span>
          </h1>

          <motion.p
            initial={enterFrom(reduce, { y: 14 })}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: HERO_DURATION, delay: HERO_STEP * 3, ease: EASE }}
            className="mt-4 max-w-xl text-[15px] leading-relaxed text-muted-foreground"
          >
            Every figure is computed by code, never guessed by a model — and any of
            them can be taken apart. Try it on this one.
          </motion.p>

          <div className="mt-10 w-full">
            <InterrogateScene entranceDelay={HERO_STEP * 4} />
          </div>
        </section>

        <Rule />

        {/* ---------------------------------------------------------------- */}
        {/* The argument, stated in prose rather than as a feature grid. It is
            what the product is built on, so it gets words, not iconography. */}
        <section className="mx-auto max-w-2xl py-14 text-center sm:py-16">
          <p className="text-[clamp(1.1rem,2.4vw,1.4rem)] leading-relaxed tracking-[-0.01em]">
            {/* The two halves are timed apart so the concession lands after the
                setup, the way it would be said aloud. */}
            <motion.span
              initial={enterFrom(reduce, { y: 12 })}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-70px" }}
              transition={{ duration: HERO_DURATION, ease: EASE }}
              className="inline-block"
            >
              Ask most AI tools about your sales data and you get a number that sounds
              certain.{" "}
            </motion.span>
            <motion.span
              initial={enterFrom(reduce, { y: 12 })}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-70px" }}
              transition={{ duration: HERO_DURATION, delay: 0.25, ease: EASE }}
              className="inline-block text-muted-foreground"
            >
              You have no way to tell whether it is. For a business decision, a wrong
              number that looks right is worse than no number at all.
            </motion.span>
          </p>
        </section>

        <Rule />

        {/* ---------------------------------------------------------------- */}
        {/* Concrete phrasing does more than an abstract promise of "natural
            language": it shows the register, and quietly sets expectations
            about what is worth asking. */}
        <section className="py-14 sm:py-16">
          <Reveal>
            <div className="flex flex-col items-center gap-6">
              <Eyebrow>Things people actually type</Eyebrow>
              <div className="flex max-w-4xl flex-wrap justify-center gap-2.5">
                {QUESTIONS.map((q, i) => (
                  <motion.span
                    key={q}
                    initial={enterFrom(reduce, { scale: 0.94, y: 8 })}
                    whileInView={{ opacity: 1, scale: 1, y: 0 }}
                    whileHover={reduce ? undefined : { y: -3, scale: 1.03 }}
                    viewport={{ once: true, margin: "-60px" }}
                    transition={{
                      opacity: { duration: 0.7, delay: i * 0.055 },
                      default: { type: "spring", stiffness: 150, damping: 24, delay: i * 0.055 },
                    }}
                    className="cursor-default rounded-full border border-border/60 bg-surface/40 px-4 py-2 text-[13px] text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
                  >
                    {q}
                  </motion.span>
                ))}
              </div>
            </div>
          </Reveal>
        </section>

        <Rule />

        {/* ---------------------------------------------------------------- */}
        <section className="py-14 sm:py-16">
          <div className="grid gap-4 sm:grid-cols-3">
            {STEPS.map((s, i) => (
              <Reveal key={s.title} delay={i * 0.09}>
                <motion.div
                  {...lift}
                  className="group h-full rounded-2xl border border-border/60 bg-surface/30 p-6 transition-colors hover:border-primary/30"
                >
                  <motion.div
                    whileHover={reduce ? undefined : { rotate: -6, scale: 1.08 }}
                    transition={{ type: "spring", stiffness: 400, damping: 18 }}
                    className="flex h-10 w-10 items-center justify-center rounded-xl border border-primary/25 bg-primary/10"
                  >
                    <s.icon className="h-[18px] w-[18px] text-primary" strokeWidth={2} />
                  </motion.div>
                  <h3 className="mt-4 text-[15px] font-semibold">{s.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
                </motion.div>
              </Reveal>
            ))}
          </div>
        </section>

        <Rule />

        {/* ---------------------------------------------------------------- */}
        {/* The obvious objection is "so it's a chatbot over my CSV". Naming the
            analyses answers it without arguing. */}
        <section className="py-14 sm:py-16">
          <Reveal>
            <div className="flex flex-col items-center gap-3 text-center">
              <Eyebrow>Not just a chat box</Eyebrow>
              <p className="max-w-xl text-[15px] leading-relaxed text-muted-foreground">
                Behind the answers is a full analysis suite. Ask for any of these in
                conversation, or open the page and drive it yourself.
              </p>
            </div>
          </Reveal>

          <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {CAPABILITIES.map((c, i) => (
              <motion.div
                key={c.label}
                initial={enterFrom(reduce, { y: 14, scale: 0.97 })}
                whileInView={{ opacity: 1, y: 0, scale: 1 }}
                whileHover={reduce ? undefined : { y: -3, scale: 1.02 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ type: "spring", stiffness: 145, damping: 24, delay: 0.05 * i }}
                className="group flex h-full items-center gap-3 rounded-xl border border-border/50 bg-surface/25 px-4 py-3.5 transition-colors hover:border-primary/35 hover:bg-surface/45"
              >
                <c.icon
                  className="h-4 w-4 shrink-0 text-primary/80 transition-colors group-hover:text-primary"
                  strokeWidth={2}
                />
                <span className="text-sm text-foreground">{c.label}</span>
              </motion.div>
            ))}
          </div>
        </section>

        <Rule />

        {/* ---------------------------------------------------------------- */}
        <section className="py-14 sm:py-16">
          <Reveal>
            <div className="grid gap-4 sm:grid-cols-3">
              {[
                {
                  icon: Share2,
                  title: "Share a read-only link",
                  body: "Send a dashboard to someone without an account. They see the figures, not your file.",
                },
                {
                  icon: History,
                  title: "Every version kept",
                  body: "Re-upload or refresh and the previous version stays. Numbers from last month still recompute.",
                },
                {
                  icon: Sheet,
                  title: "Sheets stay connected",
                  body: "A linked Google Sheet pulls the latest rows on refresh, and tells you when nothing changed.",
                },
              ].map((f, i) => (
                <motion.div
                  key={f.title}
                  initial={enterFrom(reduce, { y: 16 })}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-60px" }}
                  transition={{ duration: 0.95, delay: 0.09 * i, ease: EASE }}
                  className="flex flex-col gap-2.5"
                >
                  <f.icon className="h-[18px] w-[18px] text-primary" strokeWidth={2} />
                  <h3 className="text-sm font-semibold">{f.title}</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">{f.body}</p>
                </motion.div>
              ))}
            </div>
          </Reveal>
        </section>

        {/* ---------------------------------------------------------------- */}
        <section className="flex flex-col items-center gap-5 py-16 text-center sm:py-20">
          <Reveal>
            <h2 className="text-[clamp(1.4rem,3.4vw,2rem)] font-semibold tracking-[-0.02em]">
              Bring one spreadsheet. See what it says.
            </h2>
            <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-muted-foreground">
              Free to start, no card needed. If the first answer isn&apos;t one you can
              check, nothing else on this page matters.
            </p>
            <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
              <motion.div
                whileHover={reduce ? undefined : { scale: 1.04, y: -2 }}
                whileTap={reduce ? undefined : { scale: 0.98 }}
                transition={{ type: "spring", stiffness: 380, damping: 22 }}
              >
                <Link
                  href="/signup"
                  className="group flex items-center gap-2 rounded-full bg-primary px-7 py-3.5 text-sm font-medium text-primary-foreground shadow-[0_10px_34px_-10px_var(--primary)]"
                >
                  Get started free
                  <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
                </Link>
              </motion.div>
              <motion.div
                whileHover={reduce ? undefined : { y: -2 }}
                whileTap={reduce ? undefined : { scale: 0.98 }}
                transition={{ type: "spring", stiffness: 380, damping: 22 }}
              >
                <Link
                  href="/login"
                  className="block rounded-full border border-border/60 px-6 py-3.5 text-sm text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
                >
                  I already have an account
                </Link>
              </motion.div>
            </div>
          </Reveal>
        </section>
      </main>

      {/* No links down here: the header carries sign-in and the closing call to
          action carries both, so a third copy sits directly under the second. */}
      <footer className="border-t border-border/40 py-8 text-center text-xs text-muted-foreground">
        Numerate — Smart Analytics. Better Decisions.
      </footer>
    </div>
  );
}

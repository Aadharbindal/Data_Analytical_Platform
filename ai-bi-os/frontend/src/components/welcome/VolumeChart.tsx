"use client";

import React from "react";

/** Depth of the solid, in pixels, along the up-and-right diagonal. Both
 *  receding faces derive from it, so they cannot disagree about thickness. */
const DEPTH = 10;

/** Headroom above the tallest bar, so the markers and the trend line have
 *  somewhere to sit instead of touching the card's edge. */
const SCALE_MAX = 515;

// ── Timing ──────────────────────────────────────────────────────────────────
// Two phases, and the second is derived from the first rather than guessed at.
// The blocks rise; only once the last one has settled is the trend drawn across
// them. Writing the start time by hand would go stale the moment any of the
// three numbers above it changed, and the line would cut across bars that were
// still moving.
const BAR_DELAY = 220;
const BAR_STAGGER = 65;
const BAR_DUR = 1150;
const barsSettle = (n: number) => BAR_DELAY + (n - 1) * BAR_STAGGER + BAR_DUR;
/** A breath between the last block landing and the trend appearing. */
const PHASE_GAP = 160;
/** How long the line takes to travel from the first bar to the last. */
const DRAW_DUR = 1250;

/** Direction, in the app's own colours: the same green as the "up 12.4%" pill,
 *  and the theme's error red. A rise and a fall should not look alike. */
const UP = "#37D67A";
const DOWN = "#F04438";

/**
 * One material, described once.
 *
 * A solid does not change colour from face to face - only how much light
 * reaches it. Giving the top a blue tint, the front a magenta-to-cyan ramp and
 * the side a purple ramp made three different substances stuck together, which
 * is why it read as flat panels rather than a block. So the front carries the
 * material, the side carries the same ramp under a shadow, and the top is that
 * ramp's own top colour with light on it.
 *
 * The blues are the two this page already uses everywhere else (#4d8bff for
 * accents, #8ab8ff for the lighter end of its headings). A violet ramp looked
 * well made on its own and wrong on the page, because nothing else in the deck
 * is violet - the eye reads a colour belonging to no other element as a
 * foreign object, however nicely it is shaded.
 */
const MATERIAL = "linear-gradient(180deg,#bcd8ff 0%,#8ab8ff 15%,#4d8bff 42%,#2f74ee 68%,#2a9df4 87%,#4fc9f8 100%)";
/** The material's topmost colour, lit. This is the surface facing the light. */
const MATERIAL_LIT = "linear-gradient(115deg,#eaf4ff 0%,#d2e5ff 55%,#b6d4ff 100%)";
/** The same ramp, in shadow: a scrim over it rather than a different colour. */
const MATERIAL_SHADE = `linear-gradient(180deg, rgba(4,6,20,.62), rgba(4,6,20,.74)), ${MATERIAL}`;

/**
 * The forecast block: the same material, not yet filled in.
 *
 * Distinguishing a projection from a measurement does not require a different
 * material, only a different state of the same one - so these are the
 * material's own colours at low opacity. Outlined and hollow reads as "not
 * built yet" while still plainly belonging to the row.
 */
const PROJ_FACE =
  "radial-gradient(circle at center, rgba(198,224,255,.5) 1.1px, transparent 1.5px) 0 0/6px 6px," +
  "linear-gradient(180deg, rgba(138,184,255,.20) 0%, rgba(77,139,255,.17) 45%, rgba(79,201,248,.20) 100%)";
const PROJ_LIT = "linear-gradient(115deg, rgba(234,244,255,.55), rgba(182,212,255,.34))";
const PROJ_SHADE =
  "linear-gradient(180deg, rgba(4,6,20,.5), rgba(4,6,20,.6)), " +
  "linear-gradient(180deg, rgba(138,184,255,.30), rgba(79,201,248,.30))";

export interface Bar {
  m: string;
  v: number;
  proj?: boolean;
}

/**
 * The Processed Volume chart on the welcome deck.
 *
 * Each bar is a box: a front face, a top face receding up-and-right, and a
 * right face doing the same. The geometry is the part worth being careful
 * about. The top face sits at `top: -DEPTH` with `height: DEPTH`, so its lower
 * edge lands exactly on the bar's top edge and adds thickness instead of
 * covering the face; the right face sits at `right: -DEPTH` for the same
 * reason on the other axis. Offset either by less and the two overlap in the
 * top-right corner - and since one is lit and the other is in shadow, that
 * overlap reads as a dark wedge stuck to the bar.
 */
export function VolumeChart({ active, bars }: { active: boolean; bars: Bar[] }) {
  const lineStart = barsSettle(bars.length) + PHASE_GAP;
  /** Markers arrive with the line, one as it reaches each peak. */
  const markerAt = (i: number) => lineStart + (i * DRAW_DUR) / Math.max(1, bars.length - 1);
  /** Rising or falling against the month before it. The first has nothing to
   *  compare against, so it takes the direction of the step leaving it. */
  const rising = (i: number) => (i === 0 ? bars[1].v >= bars[0].v : bars[i].v >= bars[i - 1].v);

  // Both the line and the markers use this y, which is the whole reason they
  // meet. The value is the height of the front face, so the point marking it
  // belongs on that edge. Putting the markers on the top face instead left
  // them half a depth up and to the right of the line, and nudging the line to
  // follow was not an option: a pixel offset has no fixed size inside a viewBox
  // that stretches with the card.
  const yOf = (b: Bar) => (active ? 100 - (b.v / SCALE_MAX) * 100 : 100);

  return (
    <div className="relative h-[196px]">
      {/* Gridlines only. A hard white rule along the bottom read as a stray
          line under the chart rather than as a scale - the blocks already say
          where the floor is by standing on it. */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        {[0, 25, 50, 75].map((t) => (
          <div key={t} className="absolute inset-x-0 h-px bg-white/[0.04]" style={{ top: t + "%" }} />
        ))}
      </div>

      {/* The reveal is a clip-path on this wrapper, not an animated width on an
          SVG <rect>. SVG geometry attributes are only animatable as CSS in some
          engines, and where they are not the clip jumps straight to full -
          which is why a finished line was turning up before the blocks had even
          started. clip-path on an ordinary div transitions everywhere. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 z-20"
        style={{
          clipPath: active ? "inset(-40% 0% -40% 0%)" : "inset(-40% 100% -40% 0%)",
          transition: `clip-path ${DRAW_DUR}ms linear ${lineStart}ms`,
        }}
      >
        <svg
          className="h-full w-full overflow-visible"
          viewBox={`0 0 ${bars.length * 100} 100`}
          preserveAspectRatio="none"
        >
          {/* One line per step, so a fall can be red while a rise is green. A
              single polyline can only be one colour, and a chart that draws a
              drop the same way it draws a climb hides the thing a reader most
              wants to see. */}
          {bars.slice(1).map((b, i) => {
            const up = b.v >= bars[i].v;
            return (
              <line
                key={i}
                x1={i * 100 + 50}
                y1={yOf(bars[i])}
                x2={(i + 1) * 100 + 50}
                y2={yOf(b)}
                stroke={up ? UP : DOWN}
                strokeOpacity="0.95"
                strokeWidth="1.75"
                vectorEffect="non-scaling-stroke"
                strokeLinecap="round"
                style={{ filter: `drop-shadow(0 0 4px ${up ? UP : DOWN}aa)` }}
              />
            );
          })}
        </svg>
      </div>

      <div className="relative h-full flex items-end">
        {bars.map((b, i) => {
          const h = active ? (b.v / SCALE_MAX) * 100 : 0;
          // Long and gentle, declared once so every surface of a bar and its
          // marker rise together. This curve decelerates without the overshoot
          // that makes a solid look springy - a block of glass should arrive,
          // not bounce.
          const ease = "cubic-bezier(.22,.61,.36,1)";
          const delay = active ? BAR_DELAY + i * BAR_STAGGER : 0;
          const up = rising(i);

          return (
            <div key={i} className="flex-1 px-[4.5px] relative flex items-end h-full">
              {/* Contact shadow, kept narrow. At 150% width these merged into
                  one continuous band and read as a line ruled under the whole
                  chart instead of light pooling under each block. */}
              <span
                aria-hidden
                className="pointer-events-none absolute left-1/2 bottom-0 h-[12px] w-[88%] -translate-x-1/2"
                style={{
                  background: `radial-gradient(ellipse at center, rgba(96,160,255,${b.proj ? ".22" : ".38"}), transparent 72%)`,
                  filter: "blur(3px)",
                  opacity: active ? 1 : 0,
                  transition: `opacity .8s ease ${delay + 200}ms`,
                }}
              />

              <div
                className="relative w-full"
                style={{ height: h + "%", transition: `height ${BAR_DUR}ms ${ease} ${delay}ms` }}
              >
                {/* Top face: the material's own colour with light on it. */}
                <div
                  aria-hidden
                  className="absolute left-0 right-0"
                  style={{
                    top: -DEPTH,
                    height: DEPTH,
                    transform: "skewX(-45deg)",
                    transformOrigin: "bottom left",
                    background: b.proj ? PROJ_LIT : MATERIAL_LIT,
                  }}
                />

                {/* Right face: the same ramp under a shadow scrim. */}
                <div
                  aria-hidden
                  className="absolute top-0 bottom-0"
                  style={{
                    right: -DEPTH,
                    width: DEPTH,
                    transform: "skewY(-45deg)",
                    transformOrigin: "top left",
                    background: b.proj ? PROJ_SHADE : MATERIAL_SHADE,
                  }}
                />

                {/* Front face. */}
                <div
                  className="relative h-full w-full overflow-hidden"
                  style={{
                    background: b.proj ? PROJ_FACE : MATERIAL,
                    border: b.proj ? "1px solid rgba(150,193,255,.6)" : "none",
                    boxShadow: b.proj
                      ? "0 0 22px -4px rgba(77,139,255,.6), inset 0 1px 0 rgba(226,240,255,.6)"
                      : [
                          // Lit along the two edges facing the light, dark along
                          // the two that do not - the whole reason the block
                          // reads as having volume.
                          "inset 0 1px 0 rgba(255,255,255,.95)",
                          "inset 1px 0 0 rgba(255,255,255,.34)",
                          "inset -1px 0 0 rgba(6,16,46,.45)",
                          "0 0 16px -3px rgba(77,139,255,.85)",
                          "0 0 34px -8px rgba(56,189,248,.55)",
                        ].join(","),
                  }}
                >
                  {/* Specular band down the left third. Glass picks up a soft
                      vertical highlight; without it the face is a flat ramp. */}
                  {!b.proj && (
                    <span
                      aria-hidden
                      className="absolute inset-y-0 left-0 w-1/3"
                      style={{ background: "linear-gradient(90deg, rgba(255,255,255,.20), transparent)" }}
                    />
                  )}
                </div>
              </div>

              {/* The value marker, centred on the front face's top edge - the
                  same point the line is drawn through, which is what makes the
                  two meet. */}
              <span
                aria-hidden
                className="absolute left-1/2 z-30 h-[9px] w-[9px] rounded-full"
                style={{
                  bottom: `calc(${h}% - 4.5px)`,
                  marginLeft: -4.5,
                  background: `radial-gradient(circle at 35% 32%, #ffffff, ${up ? "#8df0b6" : "#ffb4b4"} 55%, ${up ? UP : DOWN} 100%)`,
                  boxShadow: `0 0 10px 2px ${up ? UP : DOWN}d9`,
                  // Rises with its block, then appears as the line arrives - so
                  // each marker reads as the trend touching that peak rather
                  // than as twelve dots switching on together.
                  transition: `bottom ${BAR_DUR}ms ${ease} ${delay}ms, opacity 260ms ease ${markerAt(i)}ms, transform 340ms ${ease} ${markerAt(i)}ms`,
                  opacity: active ? 1 : 0,
                  transform: active ? "scale(1)" : "scale(.4)",
                }}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

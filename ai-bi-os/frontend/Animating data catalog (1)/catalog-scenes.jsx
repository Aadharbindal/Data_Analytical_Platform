/* catalog-scenes.jsx — "DataMind OS" data-catalog motion piece.
   Requires animations-v2.jsx + tweaks-panel.jsx loaded first (globals). */

const { SceneStage, useScene, useTweaks, TweaksPanel, TweakSection, TweakToggle, TweakColor } = window;

/* ---------- helpers ---------- */
const clamp01 = v => Math.max(0, Math.min(1, v));
const eo  = x => 1 - Math.pow(1 - x, 3);                       // easeOutCubic
const eio = x => (x < .5 ? 4*x*x*x : 1 - Math.pow(-2*x+2,3)/2); // easeInOutCubic
const backOut = x => { const c = 1.70158, c3 = c + 1; return 1 + c3*Math.pow(x-1,3) + c*Math.pow(x-1,2); };
const seg = (t, s, d) => clamp01((t - s) / d);
const lerp = (a, b, p) => a + (b - a) * p;
const cubicOut = x => 1 - Math.pow(1 - x, 3);
const cubicIn = x => x * x * x;

const SANS = "'Space Grotesk','Helvetica Neue',sans-serif";
const MONO = "'IBM Plex Mono',monospace";

const C = {
  bg: '#0a0e17',
  panel: '#0f1623',
  card: '#141c2e',
  cardHover: '#1a2436',
  border: 'rgba(148,163,184,0.12)',
  text: '#e7edf7',
  muted: '#8a95a8',
  faint: '#5b6575',
};

let THEME = { accent: '#3B82F6' };
const alpha = (hex, a) => hex + Math.round(a * 255).toString(16).padStart(2, '0');

const DATASETS = [
  { name: 'software_licenses_FINAL_VERIFY.csv', cols: 12, rows: 3412, tags: ['auto-inferred', 'raw-data'], system: 'DataMind OS' },
  { name: 'user_behavior_analytics.parquet', cols: 28, rows: 1250000, tags: ['inferred', 'timeseries'], system: 'DataMind OS' },
  { name: 'product_catalog_v3.json', cols: 45, rows: 8924, tags: ['raw-data', 'nested'], system: 'DataMind OS' },
  { name: 'sales_transactions_2024.csv', cols: 19, rows: 445678, tags: ['auto-inferred', 'sales'], system: 'DataMind OS' },
  { name: 'customer_demographics.tsv', cols: 22, rows: 52341, tags: ['raw-data', 'demographics'], system: 'DataMind OS' },
];

/* ---------- shared bits ---------- */

function GridBG({ time, opacity = 1 }) {
  return (
    <div style={{ position: 'absolute', inset: 0, opacity, pointerEvents: 'none' }}>
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'radial-gradient(rgba(148,163,184,0.14) 1px, transparent 1px)',
        backgroundSize: '36px 36px',
        backgroundPosition: `${(time * 7) % 36}px ${(time * 4.5) % 36}px`,
      }} />
      <div style={{
        position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse 70% 60% at 50% 42%, transparent 40%, rgba(4,6,10,0.85) 100%)',
      }} />
    </div>
  );
}

function DatasetCard({ dataset, idx, total, spreadP, accent, isTop }) {
  // spreadP: 0 = stacked as stairs, 1 = fully spread into list
  const rowH = 66;      // height of each row when spread
  const gap = 12;
  const stairStep = 14; // vertical offset per card when stacked (stairs look)
  const stairX = 22;    // horizontal offset per card when stacked

  const s = eio(clamp01(spreadP));

  // stacked position (stairs): cascading down-right, small
  const stackY = idx * stairStep;
  const stackX = idx * stairX;
  const stackScale = 1 - idx * 0.015;

  // spread position (clean list)
  const spreadY = idx * (rowH + gap);
  const spreadX = 0;

  const y = lerp(stackY, spreadY, s);
  const x = lerp(stackX, spreadX, s);
  const scale = lerp(stackScale, 1, s);
  const contentReveal = clamp01((spreadP - 0.35) / 0.5);

  // in stacked mode, deeper cards are dimmer
  const dimStacked = 1 - idx * 0.08;
  const cardOpacity = lerp(dimStacked, 1, s);

  return (
    <div style={{
      position: 'absolute', top: 0, left: 0,
      width: 560, height: rowH,
      transform: `translate(${x}px, ${y}px) scale(${scale})`,
      transformOrigin: 'top center',
      zIndex: total - idx,
      opacity: cardOpacity,
    }}>
      <div style={{
        width: '100%', height: '100%', boxSizing: 'border-box',
        display: 'flex', alignItems: 'center', gap: 14, padding: '0 20px',
        background: lerp(0, 1, s) > 0.5 ? C.card : C.cardHover,
        border: `1px solid ${lerp(0, 1, s) > 0.5 ? C.border : alpha(accent, 0.25)}`,
        borderRadius: 12,
        boxShadow: `0 ${lerp(4, 10, s)}px ${lerp(14, 28, s)}px rgba(0,0,0,${lerp(0.5, 0.32, s)})`,
      }}>
        <div style={{
          width: 34, height: 34, borderRadius: 9, flex: 'none',
          background: alpha(accent, 0.15), border: `1px solid ${alpha(accent, 0.35)}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: SANS, fontSize: 16, fontWeight: 700, color: accent,
        }}>{idx + 1}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontFamily: MONO, fontSize: 14, fontWeight: 600, color: C.text,
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>{dataset.name}</div>
          <div style={{
            fontFamily: MONO, fontSize: 11.5, color: C.muted, marginTop: 2,
            opacity: contentReveal, height: contentReveal > 0 ? 'auto' : 0,
          }}>{dataset.cols} cols · {dataset.rows.toLocaleString()} rows</div>
        </div>
        <div style={{
          display: 'flex', gap: 6, flex: 'none', opacity: contentReveal,
        }}>
          {dataset.tags.map((tag, i) => (
            <span key={i} style={{
              fontFamily: MONO, fontSize: 11, color: accent,
              background: alpha(accent, 0.12), border: `1px solid ${alpha(accent, 0.3)}`,
              borderRadius: 999, padding: '3px 9px', whiteSpace: 'nowrap',
            }}>{tag}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

function TopBar({ pressed, spreadP, accent }) {
  const press = pressed ? 1 : 0;
  return (
    <div style={{
      width: 560, height: 46, boxSizing: 'border-box',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 18px', marginBottom: 18,
      background: press ? alpha(accent, 0.14) : C.panel,
      border: `1px solid ${press ? alpha(accent, 0.5) : C.border}`,
      borderRadius: 11,
      transform: `scale(${1 - press * 0.02})`,
      transition: 'all 0.15s ease',
      boxShadow: press ? `0 0 0 3px ${alpha(accent, 0.12)}` : '0 6px 18px rgba(0,0,0,0.35)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
        <div style={{
          width: 26, height: 26, borderRadius: 7, flex: 'none',
          background: alpha(accent, 0.2),
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={accent} strokeWidth="2.2">
            <rect x="3" y="3" width="7" height="7" rx="1" />
            <rect x="14" y="3" width="7" height="7" rx="1" />
            <rect x="3" y="14" width="7" height="7" rx="1" />
            <rect x="14" y="14" width="7" height="7" rx="1" />
          </svg>
        </div>
        <span style={{ fontFamily: SANS, fontSize: 14.5, fontWeight: 600, color: C.text }}>
          All datasets
        </span>
        <span style={{
          fontFamily: MONO, fontSize: 12, color: C.muted,
          background: '#0d1420', border: `1px solid ${C.border}`, borderRadius: 999, padding: '2px 9px',
        }}>{DATASETS.length}</span>
      </div>
      <div style={{
        transform: `rotate(${spreadP * 180}deg)`, transition: 'transform 0.3s ease',
        display: 'flex',
      }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={accent} strokeWidth="2.2">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </div>
    </div>
  );
}

function AccordionScene() {
  const { localTime: t } = useScene();
  const A = THEME.accent;

  const intro = seg(t, 0.2, 0.6);

  // cycle: start stacked, press → spread open, hold, press → collapse, hold
  // t timeline (8s):
  //  0.0-1.2  intro, cards stacked as stairs
  //  1.2      press (open)
  //  1.3-2.6  spread open
  //  2.6-4.6  hold open (browsing)
  //  4.6      press (close)
  //  4.7-6.0  collapse to stairs
  //  6.0-8.0  hold stacked
  const openP = seg(t, 1.3, 1.3);
  const closeP = seg(t, 4.7, 1.3);
  const spreadP = clamp01(openP - closeP);

  const pressed = (t > 1.15 && t < 1.45) || (t > 4.55 && t < 4.85);

  // container vertical centering: spread list is tall, stacked is short
  const listShift = lerp(-40, -230, eio(spreadP));

  return (
    <div style={{
      position: 'absolute', inset: 0, background: C.bg, overflow: 'hidden',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'radial-gradient(rgba(148,163,184,0.07) 1px, transparent 1px)',
        backgroundSize: '40px 40px', opacity: 0.6,
      }} />

      <div style={{
        position: 'relative', zIndex: 1,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        opacity: intro, transform: `translateY(${(1 - eo(intro)) * -16}px)`,
      }}>
        <TopBar pressed={pressed} spreadP={spreadP} accent={A} />

        {/* card stack area — position:relative so absolute cards layer */}
        <div style={{
          position: 'relative', width: 560, height: 470,
          transform: `translateY(${listShift + 230}px)`,
        }}>
          {DATASETS.map((ds, i) => (
            <DatasetCard
              key={i}
              dataset={ds}
              idx={i}
              total={DATASETS.length}
              spreadP={spreadP}
              accent={A}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function Frame({ children, label }) {
  return (
    <div data-screen-label={label} style={{
      position: 'absolute', inset: 0, background: C.bg, overflow: 'hidden',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>{children}</div>
  );
}

/* ---------- root ---------- */

window.AccordionScene = AccordionScene;

window.CatalogVideo = function CatalogVideo() {
  const [tw, setTweak] = useTweaks(window.TWEAK_DEFAULTS);
  THEME = { accent: tw.accent };
  return (
    <>
      <div style={{ width: '100%', aspectRatio: '16/9' }}>
        <SceneStage width={1280} height={720} bg={C.bg}
          scenes={window.OM_SCENES} playback={window.OM_PLAYBACK}>
          {{ AccordionScene: window.AccordionScene }}
        </SceneStage>
      </div>
      <TweaksPanel>
        <TweakSection label="Style" />
        <TweakColor label="Accent" value={tw.accent}
          options={['#3B82F6', '#22D3EE', '#A78BFA', '#34D399']}
          onChange={v => setTweak('accent', v)} />
        <TweakSection label="Editing" />
        <TweakToggle label="Motion editor" value={tw.motionEditor}
          onChange={v => setTweak('motionEditor', v)} />
      </TweaksPanel>
    </>
  );
};

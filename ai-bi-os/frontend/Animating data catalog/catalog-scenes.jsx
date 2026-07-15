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

const SANS = "'Space Grotesk','Helvetica Neue',sans-serif";
const MONO = "'IBM Plex Mono',monospace";

const C = {
  bg: '#080b12',
  panel: '#0e1420',
  card: '#111827',
  border: 'rgba(148,163,184,0.14)',
  text: '#e7edf7',
  muted: '#8a95a8',
  faint: '#5b6575',
};

let THEME = { accent: '#3B82F6' };
const alpha = (hex, a) => hex + Math.round(a * 255).toString(16).padStart(2, '0');

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

function DbMark({ size = 64, p = 1, accent }) {
  const s = 0.6 + 0.4 * clamp01(p);
  const barW = size * 0.44, barH = Math.max(3, size * 0.085), gap = size * 0.075;
  return (
    <div style={{
      width: size, height: size, borderRadius: size * 0.28,
      background: `linear-gradient(145deg, ${accent}, ${alpha(accent, 0.55)})`,
      boxShadow: `0 0 ${size * 0.8}px ${alpha(accent, 0.35 * clamp01(p))}, inset 0 1px 0 rgba(255,255,255,0.35)`,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap, transform: `scale(${s})`, opacity: clamp01(p * 1.4),
    }}>
      {[0.9, 0.68, 0.9].map((w, i) => (
        <div key={i} style={{ width: barW * w, height: barH, borderRadius: barH, background: 'rgba(255,255,255,0.92)' }} />
      ))}
    </div>
  );
}

function Brand({ mark, word, tag, tagText, accent }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 26 }}>
      <DbMark size={72} p={backOut(mark) * (mark > 0 ? 1 : 0)} accent={accent} />
      <div style={{
        fontFamily: SANS, fontWeight: 700, fontSize: 54, letterSpacing: '-0.02em', color: C.text,
        opacity: word, transform: `translateY(${(1 - eo(word)) * 18}px)`,
      }}>
        DataMind <span style={{ color: accent }}>OS</span>
      </div>
      <div style={{
        fontFamily: MONO, fontSize: 17, color: C.muted, letterSpacing: '0.14em', textTransform: 'uppercase',
        opacity: tag, transform: `translateY(${(1 - eo(tag)) * 14}px)`,
      }}>{tagText}</div>
    </div>
  );
}

function Chip({ p, children, style }) {
  const pp = clamp01(p);
  return (
    <div style={{
      fontFamily: MONO, fontSize: 15, color: C.text,
      background: '#141c2c', border: `1px solid ${C.border}`, borderRadius: 999,
      padding: '8px 16px', whiteSpace: 'nowrap',
      opacity: Math.min(1, pp * 1.6), transform: `scale(${0.5 + 0.5 * backOut(pp)})`,
      boxShadow: '0 8px 24px rgba(0,0,0,0.45)',
      ...style,
    }}>{children}</div>
  );
}

function Tag({ p, label, accent }) {
  const pp = clamp01(p);
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 7,
      fontFamily: MONO, fontSize: 13.5, color: accent,
      background: alpha(accent, 0.10), border: `1px solid ${alpha(accent, 0.35)}`,
      borderRadius: 999, padding: '5px 13px',
      opacity: Math.min(1, pp * 1.6), transform: `scale(${0.6 + 0.4 * backOut(pp)})`,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: 3, background: accent }} />
      {label}
    </span>
  );
}

const FILE_PRE = 'software_', FILE_MID = 'licenses', FILE_POST = '_FINAL_VERIFY.csv';
const FILE_FULL = FILE_PRE + FILE_MID + FILE_POST;

function FileName({ typedP = 1, matchP = 0, accent }) {
  const base = { fontFamily: MONO, fontWeight: 600, fontSize: 19, color: C.text, letterSpacing: '-0.01em' };
  if (typedP < 1) {
    const n = Math.round(eio(typedP) * FILE_FULL.length);
    return (
      <div style={base}>
        {FILE_FULL.slice(0, n)}
        <span style={{ color: accent }}>{typedP > 0 && typedP < 1 ? '▍' : ''}</span>
      </div>
    );
  }
  return (
    <div style={base}>
      {FILE_PRE}
      <span style={{
        background: alpha(accent, 0.22 * clamp01(matchP)),
        boxShadow: matchP > 0 ? `inset 0 -2px 0 ${alpha(accent, 0.85 * clamp01(matchP))}` : 'none',
        borderRadius: 4, padding: '1px 2px', margin: '-1px -2px',
      }}>{FILE_MID}</span>
      {FILE_POST}
    </div>
  );
}

/* The catalog UI (search bar + entry card), driven by build progresses. */
function CatalogUI({ b, query = '', caret = false, matchP = 0, lift = 0 }) {
  const A = THEME.accent;
  const liftE = clamp01(lift);
  return (
    <div style={{ width: 1080, display: 'flex', flexDirection: 'column', gap: 26 }}>
      {/* top row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        <div style={{
          flex: 1, display: 'flex', alignItems: 'center', gap: 14, height: 56,
          background: C.panel, border: `1px solid ${matchP > 0.01 ? alpha(A, 0.5) : C.border}`, borderRadius: 16,
          padding: '0 22px',
          boxShadow: matchP > 0.01 ? `0 0 0 3px ${alpha(A, 0.12)}` : '0 10px 30px rgba(0,0,0,0.35)',
          opacity: b.bar, transform: `translateY(${(1 - eo(b.bar)) * -18}px)`,
        }}>
          <div style={{
            width: 15, height: 15, border: `2px solid ${C.muted}`, borderRadius: '50%',
            position: 'relative', flex: 'none',
          }}>
            <div style={{ position: 'absolute', width: 2, height: 7, background: C.muted, borderRadius: 2, left: 13, top: 12, transform: 'rotate(-45deg)' }} />
          </div>
          <div style={{ fontFamily: MONO, fontSize: 16.5, color: query ? C.text : C.faint, display: 'flex', alignItems: 'center' }}>
            {query || 'Search by name, domain, or description…'}
            {caret && <span style={{ width: 2, height: 20, background: A, marginLeft: 2, display: 'inline-block' }} />}
          </div>
        </div>
        <div style={{ fontFamily: MONO, fontSize: 15, color: C.muted, opacity: b.count, whiteSpace: 'nowrap' }}>
          1 entry
        </div>
      </div>

      {/* entry card */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 24,
        background: liftE > 0 ? '#131b2b' : C.card,
        border: `1px solid ${liftE > 0 ? alpha(A, 0.30 + 0.35 * liftE) : C.border}`,
        borderRadius: 20, padding: '26px 30px', minHeight: 118, boxSizing: 'border-box',
        opacity: b.card,
        transform: `translateY(${(1 - eo(b.card)) * 26 - liftE * 6}px) scale(${1 + liftE * 0.012})`,
        boxShadow: liftE > 0
          ? `0 ${14 + liftE * 14}px ${40 + liftE * 30}px rgba(0,0,0,0.5), 0 0 ${liftE * 46}px ${alpha(A, 0.16 * liftE)}`
          : '0 12px 34px rgba(0,0,0,0.4)',
      }}>
        <div style={{ flex: 'none' }}>
          <DbMark size={52} p={b.icon} accent={A} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 11, flex: 1, minWidth: 0 }}>
          <FileName typedP={b.name} matchP={matchP} accent={A} />
          <div style={{
            fontFamily: SANS, fontSize: 15.5, color: C.muted, lineHeight: 1.45,
            opacity: b.desc, transform: `translateY(${(1 - eo(b.desc)) * 8}px)`,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}>
            Auto-generated catalog entry. Contains 12 inferred columns across 3,412 rows.
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <Tag p={b.tag1} label="auto-inferred" accent={A} />
            <Tag p={b.tag2} label="raw-data" accent={A} />
          </div>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 18, flex: 'none',
          fontFamily: MONO, fontSize: 14.5, color: C.muted,
          opacity: b.meta, transform: `translateX(${(1 - eo(b.meta)) * 14}px)`,
        }}>
          <span style={{ color: C.text }}>12 cols</span>
          <span style={{ width: 1, height: 18, background: C.border }} />
          <span>DataMind OS</span>
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

/* ---------- scenes ---------- */

function Opening() {
  const { localTime: t, progress } = useScene();
  return (
    <Frame label={`Opening ${Math.floor(t)}s`}>
      <GridBG time={t} opacity={0.6 * seg(t, 0, 0.8)} />
      <div style={{ transform: `scale(${1 + progress * 0.03})` }}>
        <Brand
          mark={seg(t, 0.15, 0.6)}
          word={eo(seg(t, 0.55, 0.6))}
          tag={eo(seg(t, 1.05, 0.6))}
          tagText="the data catalog"
          accent={THEME.accent}
        />
      </div>
    </Frame>
  );
}

function Ingest({ dur }) {
  const { localTime: t } = useScene();
  const A = THEME.accent;
  const drop = seg(t, 0.1, 0.6);
  const scanOn = t > 0.9 && t < 2.3;
  const scanY = (eio(seg(t, 0.9, 1.4)) * 2 % 1) * 150 - 10; // two sweeps
  const chips = [
    { s: 2.25, label: '12 columns',  x: -330, y: -95 },
    { s: 2.45, label: '3,412 rows',  x:  330, y: -75 },
    { s: 2.65, label: 'utf-8 · csv', x: -300, y: 105 },
    { s: 2.85, label: 'schema inferred', x: 315, y: 115 },
  ];
  return (
    <Frame label={`Ingest ${Math.floor(t)}s`}>
      <GridBG time={t} opacity={0.6} />
      <div style={{
        position: 'absolute', top: 74, left: 0, right: 0, textAlign: 'center',
        fontFamily: MONO, fontSize: 15, letterSpacing: '0.18em', color: C.faint, textTransform: 'uppercase',
        opacity: seg(t, 0.3, 0.5),
      }}>01 · a file arrives</div>

      <div style={{ position: 'relative' }}>
        {/* file card */}
        <div style={{
          position: 'relative', width: 520, borderRadius: 18, overflow: 'hidden',
          background: C.panel, border: `1px solid ${scanOn ? alpha(A, 0.55) : C.border}`,
          padding: '26px 28px', display: 'flex', alignItems: 'center', gap: 20,
          opacity: Math.min(1, drop * 1.5),
          transform: `translateY(${(1 - backOut(drop)) * -120}px)`,
          boxShadow: scanOn ? `0 0 60px ${alpha(A, 0.18)}` : '0 16px 44px rgba(0,0,0,0.5)',
        }}>
          <div style={{
            width: 46, height: 56, borderRadius: 8, background: '#1a2334',
            border: `1px solid ${C.border}`, flex: 'none',
            display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'center', justifyContent: 'center',
          }}>
            {[22, 22, 14].map((w, i) => <div key={i} style={{ width: w, height: 3, borderRadius: 2, background: C.faint }} />)}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minWidth: 0 }}>
            <div style={{ fontFamily: MONO, fontWeight: 600, fontSize: 17, color: C.text, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              software_licenses_FINAL_VERIFY.csv
            </div>
            <div style={{ fontFamily: MONO, fontSize: 13.5, color: C.muted }}>48 KB · dropped into /inbox</div>
          </div>
          {/* scan beam */}
          {scanOn && (
            <div style={{
              position: 'absolute', left: 0, right: 0, top: scanY, height: 3,
              background: `linear-gradient(90deg, transparent, ${A}, transparent)`,
              boxShadow: `0 0 22px ${A}`,
            }} />
          )}
        </div>

        {/* extracted metadata chips */}
        {chips.map((ch, i) => {
          const p = seg(t, ch.s, 0.5);
          return (
            <div key={i} style={{
              position: 'absolute', left: '50%', top: '50%',
              transform: `translate(-50%,-50%) translate(${ch.x * (0.7 + 0.3 * eo(p))}px, ${ch.y * (0.7 + 0.3 * eo(p))}px)`,
            }}>
              <Chip p={p}>{ch.label}</Chip>
            </div>
          );
        })}
      </div>
    </Frame>
  );
}

function Catalog() {
  const { localTime: t, progress } = useScene();
  const b = {
    bar:  eo(seg(t, 0.15, 0.55)),
    count: seg(t, 0.5, 0.5),
    card: seg(t, 0.55, 0.55),
    icon: seg(t, 1.0, 0.5),
    name: seg(t, 1.15, 1.0),
    desc: seg(t, 2.25, 0.5),
    tag1: seg(t, 2.7, 0.45),
    tag2: seg(t, 2.9, 0.45),
    meta: eo(seg(t, 3.2, 0.5)),
  };
  return (
    <Frame label={`Catalog ${Math.floor(t)}s`}>
      <GridBG time={t} opacity={0.45} />
      <div style={{
        position: 'absolute', top: 74, left: 0, right: 0, textAlign: 'center',
        fontFamily: MONO, fontSize: 15, letterSpacing: '0.18em', color: C.faint, textTransform: 'uppercase',
        opacity: seg(t, 0.2, 0.5),
      }}>02 · catalogued automatically</div>
      <div style={{ transform: `scale(${lerp(1.05, 1, eio(progress))})` }}>
        <CatalogUI b={b} />
      </div>
    </Frame>
  );
}

const QUERY = 'licenses';

function Search() {
  const { localTime: t } = useScene();
  const b = { bar: 1, count: 1, card: 1, icon: 1, name: 1, desc: 1, tag1: 1, tag2: 1, meta: 1 };
  const typeP = seg(t, 0.6, 1.4);
  const query = QUERY.slice(0, Math.round(eio(typeP) * QUERY.length));
  const caret = t > 0.25 && t < 2.4 && Math.floor(t * 2.4) % 2 === 0;
  const matchP = eo(seg(t, 2.15, 0.5));
  const zoom = eio(seg(t, 2.4, 1.5));
  return (
    <Frame label={`Search ${Math.floor(t)}s`}>
      <GridBG time={t} opacity={0.45 * (1 - zoom * 0.6)} />
      <div style={{
        position: 'absolute', top: 74, left: 0, right: 0, textAlign: 'center',
        fontFamily: MONO, fontSize: 15, letterSpacing: '0.18em', color: C.faint, textTransform: 'uppercase',
        opacity: seg(t, 0.15, 0.4) * (1 - seg(t, 2.4, 0.6)),
      }}>03 · found in milliseconds</div>
      <div style={{
        transform: `scale(${lerp(1, 1.22, zoom)}) translateY(${lerp(0, -34, zoom)}px)`,
        transformOrigin: '42% 68%',
      }}>
        <CatalogUI b={b} query={query} caret={caret} matchP={matchP} lift={matchP} />
      </div>
    </Frame>
  );
}

function Outro() {
  const { localTime: t, progress } = useScene();
  return (
    <Frame label={`Outro ${Math.floor(t)}s`}>
      <GridBG time={t} opacity={0.6} />
      <div style={{ transform: `scale(${1 + progress * 0.025})` }}>
        <Brand
          mark={seg(t, 0.1, 0.55)}
          word={eo(seg(t, 0.45, 0.55))}
          tag={eo(seg(t, 0.95, 0.55))}
          tagText="every file, findable"
          accent={THEME.accent}
        />
      </div>
    </Frame>
  );
}

/* ---------- root ---------- */

window.CatalogVideo = function CatalogVideo() {
  const [tw, setTweak] = useTweaks(window.TWEAK_DEFAULTS);
  THEME = { accent: tw.accent };
  return (
    <>
      <div style={{ width: '100%', aspectRatio: '16/9' }}>
        <SceneStage width={1280} height={720} bg={C.bg}
          scenes={window.OM_SCENES} playback={window.OM_PLAYBACK}>
          {{ Opening, Ingest, Catalog, Search, Outro }}
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

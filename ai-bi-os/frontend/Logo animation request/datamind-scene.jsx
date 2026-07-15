// datamind-scene.jsx — DataMind logo reveal scene (uses window.Easing/animate/useScene from animations-v2.jsx)
(function () {
  const { Easing, animate, clamp, useScene, React } = window;

  const NAVY = '#0a0e1a';
  const NAVY2 = '#0d1220';

  const DataMindConfigContext = React.createContext({ accent: '#3b82f6', showGrid: true, showOrbit: true });

  function lighten(hex) {
    const { r, g, b } = hexToRgb(hex);
    return rgbToHex(r + (255 - r) * 0.55, g + (255 - g) * 0.55, b + (255 - b) * 0.55);
  }
  function darken(hex) {
    const { r, g, b } = hexToRgb(hex);
    return rgbToHex(r * 0.55, g * 0.55, b * 0.6);
  }
  function hexToRgb(hex) {
    const n = parseInt(hex.replace('#', ''), 16);
    return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
  }
  function rgbToHex(r, g, b) {
    const c = (v) => Math.round(clamp(v, 0, 255)).toString(16).padStart(2, '0');
    return `#${c(r)}${c(g)}${c(b)}`;
  }

  function DataMindScene() {
    const { localTime } = useScene();
    const t = localTime;
    const cfg = React.useContext(DataMindConfigContext);
    const BLUE = cfg.accent;
    const BLUE_LIGHT = lighten(BLUE);
    const BLUE_DEEP = darken(BLUE);

    // ---- timings ----
    const badgeIn   = animate({ from: 0.6, to: 1, start: 0.05, end: 0.55, ease: Easing.easeOutBack });
    const badgeOp   = animate({ from: 0,   to: 1, start: 0.05, end: 0.35, ease: Easing.easeOutCubic });

    // three stacked "layers" diamonds — drop in from above with stagger, settle into the reference glyph
    const layerDefs = [
      { y: -15, start: 0.14, fill: BLUE_LIGHT, solid: true },
      { y: 3,   start: 0.30, fill: BLUE, solid: false },
      { y: 21,  start: 0.46, fill: BLUE_DEEP, solid: false },
    ];

    // ring pulses (two bursts) after assembly
    const pulses = [0.75, 1.55].map((start) => {
      const dur = 1.1;
      const local = clamp((t - start) / dur, 0, 1);
      const active = t >= start && t <= start + dur;
      const scale = 1 + Easing.easeOutCubic(local) * 0.9;
      const op = active ? (1 - Easing.easeInQuad(local)) * 0.55 : 0;
      return { scale, op };
    });

    // orbiting telemetry dot — continuous
    const orbitAngle = t * 1.3 + Math.PI * 0.2;
    const orbitR = 108;
    const ox = Math.cos(orbitAngle) * orbitR;
    const oy = Math.sin(orbitAngle) * orbitR * 0.62;

    // text reveal
    const textT = animate({ from: 0, to: 1, start: 0.95, end: 1.5, ease: Easing.easeOutCubic });
    const textY = 14 * (1 - textT(t));
    const textOp = textT(t);

    // subtle floating bob for the whole badge group once settled
    const bob = t > 0.6 ? Math.sin((t - 0.6) * 1.1) * 4 : 0;

    // background grid drift
    const gridShift = (t * 14) % 40;

    return (
      <div style={{
        width: '100%', height: '100%', position: 'relative', overflow: 'hidden',
        background: `radial-gradient(ellipse at 50% 42%, ${NAVY2} 0%, ${NAVY} 65%)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {/* faint dashboard grid */}
        {cfg.showGrid && (
          <div style={{
            position: 'absolute', inset: 0, opacity: 0.10,
            backgroundImage: `linear-gradient(${BLUE_LIGHT} 1px, transparent 1px), linear-gradient(90deg, ${BLUE_LIGHT} 1px, transparent 1px)`,
            backgroundSize: '40px 40px',
            backgroundPosition: `${gridShift}px ${gridShift}px`,
            maskImage: 'radial-gradient(ellipse at 50% 45%, black 30%, transparent 72%)',
            WebkitMaskImage: 'radial-gradient(ellipse at 50% 45%, black 30%, transparent 72%)',
          }} />
        )}

        {/* soft glow blob behind badge */}
        <div style={{
          position: 'absolute', width: 520, height: 520, borderRadius: '50%',
          background: `radial-gradient(circle, ${BLUE_DEEP}55 0%, transparent 70%)`,
          filter: 'blur(10px)',
          transform: `translateX(-190px) translateY(${bob * 0.5}px)`,
        }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 34, transform: `translateY(${bob * 0.3}px)` }}>

          {/* badge */}
          <div style={{
            position: 'relative', width: 132, height: 132,
            transform: `scale(${badgeIn(t)})`,
            opacity: badgeOp(t),
          }}>
            {/* pulses */}
            {pulses.map((p, i) => (
              <div key={i} style={{
                position: 'absolute', inset: 0, borderRadius: '50%',
                border: `2px solid ${BLUE_LIGHT}`,
                transform: `scale(${p.scale})`,
                opacity: p.op,
              }} />
            ))}

            {/* circular badge base */}
            <div style={{
              position: 'absolute', inset: 0, borderRadius: '50%',
              background: `radial-gradient(circle at 50% 45%, #141c2e 0%, ${NAVY} 75%)`,
              boxShadow: `0 0 40px ${BLUE}55, inset 0 0 0 1px #ffffff0f`,
            }} />

            {/* stacked layers glyph (matches reference icon) */}
            <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ position: 'relative', width: 60, height: 54 }}>
                {layerDefs.map((l, i) => {
                  const lt = clamp((t - l.start) / 0.45, 0, 1);
                  const e = Easing.easeOutBack(lt);
                  const dropFrom = -46;
                  const y = l.y + dropFrom * (1 - e);
                  const op = clamp((t - l.start) / 0.22, 0, 1);
                  const scale = 0.7 + 0.3 * clamp(e, 0, 1);
                  return (
                    <div key={i} style={{
                      position: 'absolute', left: '50%', top: '50%', width: 44, height: 44,
                      opacity: op,
                      transform: `translate(-50%, calc(-50% + ${y}px)) scale(${scale}) scaleY(0.42) rotate(45deg)`,
                      background: l.solid ? l.fill : 'transparent',
                      border: l.solid ? 'none' : `4px solid ${l.fill}`,
                      borderRadius: 6,
                      boxShadow: l.solid ? `0 0 14px ${l.fill}88` : 'none',
                    }} />
                  );
                })}
              </div>
            </div>

            {/* orbiting telemetry dot */}
            {cfg.showOrbit && (
              <div style={{
                position: 'absolute', left: '50%', top: '50%', width: 9, height: 9, borderRadius: '50%',
                background: BLUE_LIGHT,
                boxShadow: `0 0 10px 3px ${BLUE_LIGHT}99`,
                opacity: badgeOp(t),
                transform: `translate(calc(-50% + ${ox}px), calc(-50% + ${oy}px))`,
              }} />
            )}
          </div>

          {/* wordmark */}
          <div style={{
            fontFamily: "'Helvetica Neue', Helvetica, Arial, sans-serif",
            fontSize: 64, fontWeight: 700, letterSpacing: '-0.01em',
            color: '#f2f5fb',
            opacity: textOp,
            transform: `translateY(${textY}px)`,
          }}>
            Data<span style={{ color: BLUE_LIGHT }}>Mind</span>
          </div>
        </div>
      </div>
    );
  }

  window.DataMindScene = DataMindScene;
  window.DataMindConfigContext = DataMindConfigContext;
})();

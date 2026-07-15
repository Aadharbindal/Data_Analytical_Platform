const { useScene, interpolate, clamp, Easing } = window;

// ---------- helpers ----------
function ease(t) { return 1 - Math.pow(1 - clamp(t, 0, 1), 3); } // cubic out
function win(t, a, b) { if (b <= a) return t >= b ? 1 : 0; return clamp((t - a) / (b - a), 0, 1); }

const SIDEBAR_ITEMS = [
  { icon: 'grid', label: 'Dashboard', active: true },
  { icon: 'db', label: 'Datasets' },
  { icon: 'catalog', label: 'Data Catalog' },
  { icon: 'bars', label: 'Analytics' },
  { icon: 'bulb', label: 'Insights' },
  { icon: 'bolt', label: 'Recommendations' },
  { icon: 'branch', label: 'Rules' },
  { icon: 'shield', label: 'Confidence Center' },
  { icon: 'chat', label: 'AI Chat' },
];

function Icon({ name, size = 18, color = '#8891a8' }) {
  const s = size;
  const common = { width: s, height: s, viewBox: '0 0 24 24', fill: 'none', stroke: color, strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round' };
  switch (name) {
    case 'grid': return <svg {...common}><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></svg>;
    case 'db': return <svg {...common}><ellipse cx="12" cy="5" rx="8" ry="3" /><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5" /><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" /></svg>;
    case 'catalog': return <svg {...common}><circle cx="12" cy="5" r="2.2" /><circle cx="5" cy="18" r="2.2" /><circle cx="19" cy="18" r="2.2" /><path d="M12 7.2V13M12 13L6.3 16.4M12 13l5.7 3.4" /></svg>;
    case 'bars': return <svg {...common}><path d="M4 20V10M12 20V4M20 20v-7" /></svg>;
    case 'bulb': return <svg {...common}><path d="M9 18h6M10 21h4" /><path d="M12 3a6 6 0 0 0-3.6 10.8c.6.5 1 1.3 1 2.2h5.2c0-.9.4-1.7 1-2.2A6 6 0 0 0 12 3z" /></svg>;
    case 'bolt': return <svg {...common}><path d="M13 2 4 14h6l-1 8 9-12h-6l1-8z" /></svg>;
    case 'branch': return <svg {...common}><circle cx="6" cy="6" r="2.2" /><circle cx="6" cy="18" r="2.2" /><circle cx="18" cy="12" r="2.2" /><path d="M6 8.2V15.8M8 6.6c4.5 1 6 2.6 8 4.4" /></svg>;
    case 'shield': return <svg {...common}><path d="M12 3l7 3v6c0 4.4-3 7.7-7 9-4-1.3-7-4.6-7-9V6z" /></svg>;
    case 'chat': return <svg {...common}><path d="M4 5h16v11H8l-4 4z" /></svg>;
    case 'search': return <svg {...common}><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>;
    case 'bell': return <svg {...common}><path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6z" /><path d="M10 19a2 2 0 0 0 4 0" /></svg>;
    case 'moon': return <svg {...common}><path d="M20 14.5A8.5 8.5 0 1 1 9.5 4 7 7 0 0 0 20 14.5z" /></svg>;
    case 'chevron': return <svg {...common}><path d="M15 6l-6 6 6 6" /></svg>;
    case 'money': return <svg {...common} stroke="none" fill={color}><circle cx="12" cy="12" r="9" opacity="0.18" /><path stroke={color} fill="none" strokeWidth="2" d="M8 12h8M12 8v8" /></svg>;
    case 'users': return <svg {...common}><circle cx="9" cy="9" r="3" /><circle cx="17" cy="10" r="2.4" /><path d="M3.5 20c.5-3.5 3-5.5 5.5-5.5s5 2 5.5 5.5M14.5 20c.3-2.2 1.6-3.8 3-4.4" /></svg>;
    case 'card': return <svg {...common}><rect x="3" y="6" width="18" height="12" rx="2" /><path d="M3 10h18" /></svg>;
    case 'pulse': return <svg {...common}><path d="M3 12h4l2-7 4 14 2-9 2 2h4" /></svg>;
    case 'download': return <svg {...common}><path d="M12 4v11M8 11l4 4 4-4" /><path d="M4 19h16" /></svg>;
    case 'sparkle': return <svg {...common} fill={color} stroke="none"><path d="M12 2l1.8 5.6L19 9.4l-5.2 1.8L12 17l-1.8-5.8L5 9.4l5.2-1.8z" /></svg>;
    default: return null;
  }
}

const NAV_LOGO = (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
    <defs>
      <linearGradient id="logoGrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#6ea8ff" />
        <stop offset="1" stopColor="#3a6df0" />
      </linearGradient>
    </defs>
    <path d="M12 2 21 7 12 12 3 7z" fill="url(#logoGrad)" />
    <path d="M3 12l9 5 9-5" stroke="#6ea8ff" strokeWidth="1.6" fill="none" opacity="0.7" />
    <path d="M3 16.5l9 5 9-5" stroke="#3a6df0" strokeWidth="1.6" fill="none" opacity="0.4" />
  </svg>
);

const METRICS = [
  { icon: 'money', iconBg: '#3a2a63', label: ['Total Transaction', 'Amount'], to: 6.01, prefix: '₹', suffix: 'Cr', decimals: 2 },
  { icon: 'users', iconBg: '#22335c', label: ['Total Accounts'], to: 72, prefix: '', suffix: '', decimals: 0 },
  { icon: 'card', iconBg: '#173d33', label: ['Total Average', 'Transaction Value'], to: 12.5, prefix: '₹', suffix: 'K', decimals: 1 },
  { icon: 'pulse', iconBg: '#4a2418', label: ['Transaction', 'Completion Rate'], to: 91.6, prefix: '', suffix: '%', decimals: 1 },
];

const CHART_POINTS = [3600, 4550, 4300, 5550, 5250, 5100, 6050, 5750, 6250, 6000, 7200, 7900];
const CHART_FORECAST = [7900, 6900, 7550];

const AI_WORDS = ("An analysis of the uploaded dataset reveals a total Transaction Value of ₹6.01Cr, based on 4,802 transactions. This represents a notable increase of 24.1% compared to previous assessments. The comprehensive examination of the transactions provides valuable insights into the digital payments landscape.").split(' ');

function fmt(n, decimals) {
  return n.toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function MetricCard({ m, delay, t }) {
  const inT = win(t, delay, delay + 0.55);
  const e = ease(inT);
  const y = (1 - e) * 26;
  const op = e;
  const countT = win(t, delay + 0.15, delay + 1.15);
  const val = m.to * ease(countT);
  // idle glow breathing after settle
  const idle = t > delay + 2 ? (Math.sin((t - delay) * 1.4) + 1) / 2 : 0;
  return (
    <div style={{
      flex: 1, background: 'linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.015))',
      border: '1px solid rgba(255,255,255,0.08)', borderRadius: 20, padding: '26px 26px 24px',
      opacity: op, transform: `translateY(${y}px)`,
      boxShadow: `0 0 ${40 + idle * 30}px rgba(90,130,255,${0.05 + idle * 0.05}), inset 0 1px 0 rgba(255,255,255,0.04)`,
      position: 'relative', overflow: 'hidden',
    }}>
      <div style={{
        width: 44, height: 44, borderRadius: 13, background: m.iconBg, display: 'flex',
        alignItems: 'center', justifyContent: 'center', marginBottom: 22,
      }}>
        <Icon name={m.icon} size={20} color="#e9edf7" />
      </div>
      <div style={{ color: '#9aa3ba', fontSize: 17, fontWeight: 500, lineHeight: 1.35, marginBottom: 14, fontFamily: "'Sora', sans-serif" }}>
        {m.label.map((l, i) => <div key={i}>{l}</div>)}
      </div>
      <div style={{ color: '#f4f6fb', fontSize: 42, fontWeight: 700, letterSpacing: '-0.01em', fontFamily: "'Sora', sans-serif" }}>
        {m.prefix}{fmt(val, m.decimals)}{m.suffix}
      </div>
    </div>
  );
}

function Sidebar({ t }) {
  const e = ease(win(t, 0, 0.5));
  return (
    <div style={{
      width: 258, flexShrink: 0, background: '#0a0b10', borderRight: '1px solid rgba(255,255,255,0.06)',
      display: 'flex', flexDirection: 'column', padding: '26px 18px', opacity: e,
      transform: `translateX(${(1 - e) * -16}px)`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0 8px 28px' }}>
        {NAV_LOGO}
        <span style={{ color: '#fff', fontSize: 19, fontWeight: 700, fontFamily: "'Sora', sans-serif" }}>DataMind</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3, flex: 1 }}>
        {SIDEBAR_ITEMS.map((it, i) => {
          const rowE = ease(win(t, 0.15 + i * 0.035, 0.5 + i * 0.035));
          const pulse = it.active ? (Math.sin(t * 1.8) + 1) / 2 : 0;
          return (
            <div key={it.label} style={{
              display: 'flex', alignItems: 'center', gap: 13, padding: '11px 14px', borderRadius: 11,
              background: it.active ? `rgba(74,111,255,${0.16 + pulse * 0.05})` : 'transparent',
              opacity: rowE, transform: `translateX(${(1 - rowE) * -10}px)`,
              position: 'relative',
            }}>
              {it.active && <div style={{ position: 'absolute', left: -18, top: '20%', bottom: '20%', width: 3, borderRadius: 3, background: '#5c8dff' }} />}
              <Icon name={it.icon} size={18} color={it.active ? '#8fb0ff' : '#7d859c'} />
              <span style={{ fontSize: 15, fontWeight: it.active ? 600 : 500, color: it.active ? '#dbe6ff' : '#9aa1b5', fontFamily: "'Sora', sans-serif" }}>{it.label}</span>
            </div>
          );
        })}
      </div>
      <div style={{ marginTop: 'auto', borderTop: '1px solid rgba(255,255,255,0.07)', paddingTop: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '4px 8px' }}>
          <div style={{ width: 34, height: 34, borderRadius: '50%', background: 'linear-gradient(135deg,#4a6fe8,#7f6ae8)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: "'Sora', sans-serif" }}>A</div>
          <span style={{ color: '#e6e9f2', fontSize: 14.5, fontWeight: 600, fontFamily: "'Sora', sans-serif" }}>Aadhar Bindal</span>
        </div>
      </div>
    </div>
  );
}

function Topbar({ t }) {
  const e = ease(win(t, 0.05, 0.55));
  return (
    <div style={{
      height: 82, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 18, padding: '0 32px',
      borderBottom: '1px solid rgba(255,255,255,0.06)', opacity: e, transform: `translateY(${(1 - e) * -10}px)`,
    }}>
      <span style={{ color: '#f2f4fa', fontSize: 21, fontWeight: 700, fontFamily: "'Sora', sans-serif" }}>Global Analytics</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,0.045)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '9px 16px', color: '#b7bdcd', fontSize: 14.5, fontFamily: "'Sora', sans-serif" }}>
        digital_payments_LAST_FINAL....
        <Icon name="chevron" size={13} color="#8891a8" />
      </div>
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: '11px 18px', maxWidth: 520, marginLeft: 40 }}>
        <Icon name="search" size={16} color="#7d859c" />
        <span style={{ color: '#767f96', fontSize: 14.5, fontFamily: "'Sora', sans-serif" }}>Ask AI or search metrics...</span>
      </div>
      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 20 }}>
        <Icon name="bell" size={19} color="#a8afc2" />
        <Icon name="moon" size={19} color="#a8afc2" />
      </div>
    </div>
  );
}

function Chart({ t }) {
  const W = 900, H = 300;
  const all = [...CHART_POINTS, ...CHART_FORECAST];
  const max = 8200, min = 1800;
  const n = CHART_POINTS.length;
  const stepX = W / (n - 1 + CHART_FORECAST.length - 1);
  const toXY = (v, i) => [i * stepX, H - ((v - min) / (max - min)) * H];
  const mainPts = CHART_POINTS.map((v, i) => toXY(v, i));
  const forePts = CHART_FORECAST.map((v, i) => toXY(v, i + n - 1));

  function smoothPath(pts) {
    if (pts.length < 2) return '';
    let d = `M ${pts[0][0]},${pts[0][1]}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i]; const [x1, y1] = pts[i + 1];
      const mx = (x0 + x1) / 2;
      d += ` C ${mx},${y0} ${mx},${y1} ${x1},${y1}`;
    }
    return d;
  }

  const mainPath = smoothPath(mainPts);
  const forePath = smoothPath(forePts);
  const areaPath = `${mainPath} L ${mainPts[mainPts.length - 1][0]},${H} L 0,${H} Z`;

  const panelE = ease(win(t, 0.9, 1.4));
  const drawT = ease(win(t, 1.3, 4.2));
  const areaT = win(t, 3.0, 4.6);
  const foreT = ease(win(t, 4.0, 4.9));
  const dotPulse = t > 4.6 ? (Math.sin(t * 2.4) + 1) / 2 : 0;
  const lastPt = mainPts[mainPts.length - 1];

  return (
    <div style={{
      flex: 1.62, background: 'linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.015))',
      border: '1px solid rgba(255,255,255,0.08)', borderRadius: 20, padding: '28px 32px',
      opacity: panelE, transform: `translateY(${(1 - panelE) * 18}px)`, display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 18 }}>
        <span style={{ color: '#f2f4fa', fontSize: 20, fontWeight: 700, fontFamily: "'Sora', sans-serif" }}>Monthly Transaction Performance</span>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.09)', borderRadius: 9, padding: '8px 14px', color: '#d5d9e6', fontSize: 13.5, fontFamily: "'Sora', sans-serif" }}>
          Last 12 Months <Icon name="chevron" size={12} color="#8891a8" />
        </div>
      </div>
      <div style={{ flex: 1, position: 'relative' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 34, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', color: '#6b7488', fontSize: 13, fontFamily: "'Sora', sans-serif" }}>
          {['₹8000k', '₹6000k', '₹4000k', '₹2000k'].map(l => <div key={l}>{l}</div>)}
        </div>
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%" style={{ position: 'absolute', left: 56, right: 0, top: 0, bottom: 34, width: 'calc(100% - 56px)', height: 'calc(100% - 34px)' }} preserveAspectRatio="none">
          <defs>
            <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#4a86ff" stopOpacity="0.55" />
              <stop offset="1" stopColor="#4a86ff" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor="#5b8dff" />
              <stop offset="1" stopColor="#7fb0ff" />
            </linearGradient>
          </defs>
          {[0, 1, 2, 3].map(i => (
            <line key={i} x1="0" x2={W} y1={i * H / 3} y2={i * H / 3} stroke="rgba(255,255,255,0.06)" strokeDasharray="3 6" />
          ))}
          <path d={areaPath} fill="url(#areaGrad)" opacity={ease(areaT)} />
          <path d={mainPath} fill="none" stroke="url(#lineGrad)" strokeWidth="3.5" strokeLinecap="round"
            style={{ strokeDasharray: 1600, strokeDashoffset: 1600 * (1 - drawT) }} />
          <path d={forePath} fill="none" stroke="#8fb0ff" strokeWidth="3" strokeLinecap="round" strokeDasharray="2 9"
            opacity={foreT} />
          {drawT > 0.98 && (
            <circle cx={lastPt[0]} cy={lastPt[1]} r={6 + dotPulse * 4} fill="#8fb0ff" opacity={0.35 - dotPulse * 0.25} />
          )}
          {drawT > 0.98 && <circle cx={lastPt[0]} cy={lastPt[1]} r={5} fill="#dfe9ff" />}
        </svg>
      </div>
    </div>
  );
}

function AISummary({ t }) {
  const panelE = ease(win(t, 1.3, 1.9));
  const wordT = win(t, 2.1, 5.4);
  const shown = Math.floor(AI_WORDS.length * ease(wordT));
  const sparklePulse = (Math.sin(t * 2.2) + 1) / 2;
  return (
    <div style={{
      flex: 1, background: 'linear-gradient(160deg, rgba(90,120,255,0.16), rgba(60,50,110,0.10))',
      border: '1px solid rgba(120,150,255,0.22)', borderRadius: 20, padding: '28px 30px',
      opacity: panelE, transform: `translateY(${(1 - panelE) * 18}px)`, display: 'flex', flexDirection: 'column',
      boxShadow: `0 0 ${40 + sparklePulse * 20}px rgba(90,120,255,0.08)`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 20 }}>
        <div style={{ transform: `scale(${0.9 + sparklePulse * 0.25})` }}><Icon name="sparkle" size={17} color="#8fb0ff" /></div>
        <span style={{ color: '#a7c0ff', fontSize: 13.5, fontWeight: 700, letterSpacing: '0.06em', fontFamily: "'Sora', sans-serif" }}>AI EXECUTIVE SUMMARY</span>
      </div>
      <div style={{ color: '#dce2f2', fontSize: 18, lineHeight: 1.62, fontFamily: "'Manrope', sans-serif", flex: 1 }}>
        {AI_WORDS.slice(0, shown).join(' ')}
        {shown < AI_WORDS.length && shown > 0 && <span style={{ opacity: (Math.sin(t * 6) + 1) / 2, color: '#8fb0ff' }}>▍</span>}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 18, opacity: ease(win(t, 5.2, 5.7)), color: '#8fb0ff', fontSize: 14.5, fontWeight: 600, fontFamily: "'Sora', sans-serif" }}>
        <Icon name="download" size={15} color="#8fb0ff" /> Download Report
      </div>
    </div>
  );
}

function DashboardScene() {
  const { localTime, progress, dur } = useScene();
  const t = localTime;
  const fadeOut = 1 - win(t, dur - 0.55, dur);
  const fadeIn = win(t, 0, 0.32);
  const overlay = Math.max(1 - fadeIn, 1 - fadeOut);

  return (
    <div style={{
      width: 1920, height: 1080, background: 'radial-gradient(1200px 700px at 70% -10%, rgba(60,90,200,0.10), transparent), #07080c',
      display: 'flex', fontFamily: "'Sora', sans-serif", overflow: 'hidden', position: 'relative',
    }}>
      <Sidebar t={t} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Topbar t={t} />
        <div style={{ flex: 1, padding: '30px 34px', display: 'flex', flexDirection: 'column', gap: 22 }}>
          <div style={{ display: 'flex', gap: 22 }}>
            {METRICS.map((m, i) => <MetricCard key={m.label[0]} m={m} delay={0.5 + i * 0.12} t={t} />)}
          </div>
          <div style={{ display: 'flex', gap: 22, flex: 1 }}>
            <Chart t={t} />
            <AISummary t={t} />
          </div>
        </div>
      </div>
      <div style={{ position: 'absolute', inset: 0, background: '#07080c', opacity: overlay, pointerEvents: 'none' }} />
    </div>
  );
}

window.DashboardScene = DashboardScene;

function DashboardVideo() {
  const { SceneStage } = window;
  return (
    <SceneStage width={1920} height={1080} bg="#07080c" scenes={window.OM_SCENES} playback={window.OM_PLAYBACK}>
      {{ Dashboard: DashboardScene }}
    </SceneStage>
  );
}
window.DashboardVideo = DashboardVideo;

import React, { useMemo } from 'react';
import { useThemeMode } from '../../hooks/useThemeMode';

interface Props { showRain?: boolean; showBirds?: boolean; showWater?: boolean; }

/** پس‌زمینه زنده: آسمان + خورشید/ماه + ابر + باران + پرنده + آب */
export const LivingBackground: React.FC<Props> = ({
  showRain = true, showBirds = true, showWater = true }) => {
  const dark = useThemeMode() === 'dark';

  const drops = useMemo(() =>
    Array.from({ length: 34 }, (_, i) => ({
      left: (i * 97) % 100, delay: (i * 0.37) % 4, dur: 2.6 + ((i * 13) % 20) / 10 })), []);
  const birds = useMemo(() =>
    Array.from({ length: 3 }, (_, i) => ({
      top: 10 + i * 8, dur: 26 + i * 9, delay: i * 7, scale: 0.7 + i * 0.25 })), []);
  const stars = useMemo(() =>
    Array.from({ length: 40 }, (_, i) => ({
      left: (i * 61) % 100, top: (i * 37) % 55, s: 1 + (i % 3), d: (i * 0.53) % 3 })), []);

  return (
    <div aria-hidden style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
      <div className={dark ? 'sky-dark' : 'sky-light'} style={{ position: 'absolute', inset: 0 }} />

      {dark && stars.map((st, i) => (
        <span key={i} className="star" style={{ left: st.left + '%', top: st.top + '%', width: st.s, height: st.s, animationDelay: st.d + 's' }} />
      ))}

      <div className={dark ? 'moon' : 'sun'} />

      {/* تپه‌های خاکی */}
      <svg className="hill" viewBox="0 0 1440 220" preserveAspectRatio="none" style={{ height: 180 }}>
        <path d="M0,160 C240,60 480,200 720,120 C960,40 1200,180 1440,100 L1440,220 L0,220 Z"
          fill={dark ? '#2a2119' : '#d9ead3'} />
        <path d="M0,190 C300,110 600,220 900,150 C1150,95 1300,200 1440,150 L1440,220 L0,220 Z"
          fill={dark ? '#1e1a16' : '#c4ddb8'} opacity="0.9" />
      </svg>

      <div className="cloud" style={{ top: '10%', animationDuration: '80s' }} />
      <div className="cloud" style={{ top: '22%', animationDuration: '110s', animationDelay: '-30s', transform: 'scale(0.7)' }} />
      <div className="cloud" style={{ top: '5%', animationDuration: '95s', animationDelay: '-60s', transform: 'scale(0.85)' }} />

      {showRain && drops.map((d, i) => (
        <span key={i} className="raindrop" style={{ left: d.left + '%', animationDelay: d.delay + 's', animationDuration: d.dur + 's' }} />
      ))}

      {showBirds && birds.map((b, i) => (
        <svg key={i} className="bird" viewBox="0 0 100 40"
          style={{ top: b.top + '%', animationDuration: b.dur + 's', animationDelay: b.delay + 's', transform: `scale(${b.scale})` }}>
          <path d="M5,25 Q25,5 50,22 Q75,5 95,25" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round" />
        </svg>
      ))}

      {showWater && (
        <div className="water">
          <svg className="wave" viewBox="0 0 2880 120" preserveAspectRatio="none">
            <path d="M0,60 C240,100 480,20 720,60 C960,100 1200,20 1440,60 C1680,100 1920,20 2160,60 C2400,100 2640,20 2880,60 L2880,120 L0,120 Z"
              fill={dark ? 'rgba(30,58,90,0.8)' : 'rgba(59,130,246,0.35)'} />
          </svg>
          <svg className="wave w2" viewBox="0 0 2880 120" preserveAspectRatio="none">
            <path d="M0,70 C240,30 480,110 720,70 C960,30 1200,110 1440,70 C1680,30 1920,110 2160,70 C2400,30 2640,110 2880,70 L2880,120 L0,120 Z"
              fill={dark ? 'rgba(20,40,70,0.9)' : 'rgba(37,99,235,0.45)'} />
          </svg>
        </div>
      )}
    </div>
  );
};

import React from 'react';
import {AbsoluteFill, Img, interpolate, random, staticFile} from 'remotion';
import {ease, pop} from './anim';
import {parseAccent, Theme} from './theme';
import type {Scene, Word} from './types';

/* ------------------------------------------------------------ fondo papel */
export const Paper: React.FC<{theme: Theme; frame: number; grain?: boolean}> = ({theme, frame, grain = false}) => {
  const seed = Math.floor(frame / 2) % 6; // grano "vivo" a 15 fps
  return (
    <AbsoluteFill style={{background: theme.bg}}>
      <AbsoluteFill
        style={{background: `radial-gradient(120% 80% at 50% 35%, ${theme.bg} 0%, ${theme.bg} 45%, ${theme.bg2} 100%)`}}
      />
      {/* grano pre-renderizado (mucho más rápido que feTurbulence) */}
      {grain && <Img src={staticFile(`textures/grain${seed}.png`)} style={{position: "absolute", inset: 0, width: "100%", height: "100%", opacity: 0.16, mixBlendMode: "overlay"}} />}
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------ subtítulos (arriba, estilo kicker) */
export const Captions: React.FC<{words: Word[]; time: number; theme: Theme; scene?: Scene}> = ({words, time, theme, scene}) => {
  // Agrupa palabras en frases cortas (máx 6 palabras o corte por puntuación / pausa)
  const groups: Word[][] = [];
  let cur: Word[] = [];
  words.forEach((w, i) => {
    const prev = words[i - 1];
    const gap = prev ? w.start - prev.end : 0;
    if (cur.length && (cur.length >= 6 || gap > 0.35 || w.scene !== cur[0].scene || /[.!?¿¡:]$/.test(prev?.text ?? ''))) {
      groups.push(cur);
      cur = [];
    }
    cur.push(w);
  });
  if (cur.length) groups.push(cur);
  let g = groups.find((gr) => time >= gr[0].start - 0.15 && time <= gr[gr.length - 1].end + 0.25);
  if (!g) {
    // mantener el último grupo dicho mientras dure la escena
    const past = groups.filter((gr) => gr[0].start <= time && (!scene || gr[0].scene === words.find((w) => w.start >= scene.start)?.scene));
    g = past[past.length - 1];
  }
  const tag = scene?.tag;
  return (
    <div style={{position: 'absolute', left: 84, right: 84, top: 110}}>
      {tag && (
        <div style={{fontFamily: theme.mono, fontSize: 30, color: theme.muted, letterSpacing: 1, marginBottom: 22}}>
          // {tag}
        </div>
      )}
      <div style={{fontFamily: theme.body, fontWeight: 600, fontSize: 64, lineHeight: 1.12, color: theme.ink, letterSpacing: -1.2}}>
        {g?.map((w, i) => {
          const said = time >= w.start - 0.04;
          const k = ease(time, w.start - 0.06, w.start + 0.12);
          const style: React.CSSProperties = w.accent
            ? {fontFamily: theme.serif, fontStyle: 'italic', fontWeight: 400, fontSize: 74, color: said ? theme.accent : theme.faint, letterSpacing: 0}
            : {color: said ? theme.ink : theme.faint};
          return (
            <span key={i} style={{...style, display: 'inline-block', marginRight: 16, transform: `translateY(${(1 - k) * 6}px)`}}>
              {w.text}
            </span>
          );
        })}
      </div>
    </div>
  );
};

/* ------------------------------------------------------------ titular grande + badge */
export const Headline: React.FC<{scene: Scene; t: number; fps: number; theme: Theme; size?: number}> = ({scene, t, fps, theme, size = 132}) => {
  if (!scene.headline) return null;
  const parts = parseAccent(scene.headline);
  const at = scene.headlineTime;
  let idx = 0;
  const badgeP = pop(t, at + 0.18, fps, {damping: 10});
  return (
    <div style={{position: 'absolute', left: 70, right: 70, top: 470, display: 'flex', alignItems: 'flex-start', gap: 24}}>
      <div style={{flex: 1, fontFamily: theme.display, fontSize: size, lineHeight: 0.98, textTransform: 'uppercase', letterSpacing: -1}}>
        {parts.map((p, pi) =>
          p.text.split(/(\s+)/).map((w, wi) => {
            if (/^\s+$/.test(w)) return <span key={`${pi}-${wi}`}> </span>;
            const k = pop(t, at + idx++ * 0.06, fps, {damping: 14, stiffness: 200});
            return (
              <span
                key={`${pi}-${wi}`}
                style={{
                  display: 'inline-block',
                  color: p.accent ? theme.accent : theme.ink,
                  transform: `translateY(${(1 - k) * 60}px) scale(${0.85 + 0.15 * k})`,
                  opacity: Math.min(1, k * 1.5),
                  filter: `blur(${Math.max(0, (1 - k) * 8)}px)`,
                }}
              >
                {w}
              </span>
            );
          }),
        )}
      </div>
      {scene.badge !== undefined && scene.badge !== null && (
        <div
          style={{
            marginTop: 14,
            width: 88,
            height: 88,
            borderRadius: 18,
            background: theme.ink,
            color: '#fff',
            fontFamily: theme.display,
            fontSize: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `scale(${badgeP}) rotate(${(1 - badgeP) * -25}deg)`,
            boxShadow: '0 10px 24px rgba(0,0,0,.18)',
          }}
        >
          {scene.badge}
        </div>
      )}
    </div>
  );
};

/* ------------------------------------------------------------ sello rojo */
export const Stamp: React.FC<{text: string; t: number; at: number; fps: number; theme: Theme; x?: number; y?: number; rot?: number}> = ({
  text,
  t,
  at,
  fps,
  theme,
  x = 120,
  y = 1260,
  rot = -8,
}) => {
  if (t < at) return null;
  const k = pop(t, at, fps, {damping: 9, stiffness: 260});
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        transform: `rotate(${rot}deg) scale(${interpolate(k, [0, 1], [2.4, 1])})`,
        opacity: Math.min(1, k * 2),
        border: `6px solid ${theme.accent}`,
        color: theme.accent,
        padding: '6px 26px',
        borderRadius: 14,
        fontFamily: theme.display,
        fontSize: 64,
        letterSpacing: 1,
        textTransform: 'uppercase',
        background: 'rgba(255,255,255,.35)',
      }}
    >
      {text}
    </div>
  );
};

/* ------------------------------------------------------------ tarjeta base */
export const Card: React.FC<{theme: Theme; style?: React.CSSProperties; children: React.ReactNode}> = ({theme, style, children}) => (
  <div
    style={{
      background: theme.card,
      borderRadius: 26,
      boxShadow: '0 2px 0 rgba(0,0,0,.04), 0 18px 40px rgba(40,30,20,.14)',
      padding: 34,
      ...style,
    }}
  >
    {children}
  </div>
);

/* ------------------------------------------------------------ personaje (SVG, boca sincronizada a la voz) */
export const Character: React.FC<{
  theme: Theme;
  frame: number;
  fps: number;
  mouth: number;
  gesture: number; // 0..1 impulso de gesto al empezar escena
  side?: 'left' | 'right';
  enter: number;
}> = ({theme, frame, fps, mouth, gesture, side = 'right', enter}) => {
  const tsec = frame / fps;
  const bob = Math.sin(tsec * 2.2) * 6 + mouth * 4;
  const blinkPhase = (frame + 17) % 104;
  const blink = blinkPhase < 4 ? 1 - Math.abs(blinkPhase - 2) / 2 : 0;
  const armRot = -8 + Math.sin(tsec * 1.7) * 3 - gesture * 14;
  const headRot = Math.sin(tsec * 1.3) * 2.5 + mouth * 2 - gesture * 3;
  const mo = Math.max(0.08, mouth);
  const flip = side === 'left' ? -1 : 1;
  const y = (1 - enter) * 700;
  return (
    <svg
      viewBox="0 0 600 640"
      width={640}
      height={683}
      style={{position: 'absolute', bottom: -40, [side === 'right' ? 'right' : 'left']: -30, transform: `translateY(${y + bob}px) scaleX(${flip})`, overflow: 'visible'}}
    >
      <defs>
        <linearGradient id="shirt" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={theme.shirt} />
          <stop offset="1" stopColor={theme.shirt} stopOpacity="0.85" />
        </linearGradient>
        <radialGradient id="skin" cx="0.4" cy="0.35" r="0.8">
          <stop offset="0" stopColor="#FFE0C6" />
          <stop offset="1" stopColor={theme.skin} />
        </radialGradient>
      </defs>
      {/* sombra */}
      <ellipse cx="330" cy="640" rx="230" ry="26" fill="rgba(0,0,0,.08)" />
      {/* cuerpo */}
      <path d="M150 640 C150 470 210 420 330 420 C450 420 520 470 520 640 Z" fill="url(#shirt)" />
      <path d="M290 420 L330 470 L370 420" fill="none" stroke="#fff" strokeWidth="10" strokeLinecap="round" opacity=".9" />
      <path d="M330 470 L330 640" stroke="rgba(0,0,0,.15)" strokeWidth="4" />
      {/* brazo que señala (rota desde el hombro) */}
      <g transform={`rotate(${armRot} 205 470)`}>
        <path d="M205 470 C150 430 120 360 120 300" stroke={theme.shirt} strokeWidth="64" strokeLinecap="round" fill="none" />
        <path d="M205 470 C150 430 120 360 120 300" stroke="rgba(255,255,255,.12)" strokeWidth="8" fill="none" transform="translate(16,0)" />
        <g transform="translate(120 270)">
          <circle r="38" fill="url(#skin)" />
          <rect x="-12" y="-110" width="26" height="90" rx="13" fill="url(#skin)" />
          <circle cx="0" cy="-12" r="10" fill="rgba(0,0,0,.06)" />
        </g>
      </g>
      {/* cabeza */}
      <g transform={`rotate(${headRot} 330 400)`}>
        <rect x="300" y="360" width="60" height="70" rx="20" fill={theme.skin} />
        <ellipse cx="330" cy="285" rx="118" ry="128" fill="url(#skin)" />
        <ellipse cx="214" cy="300" rx="20" ry="30" fill={theme.skin} />
        <ellipse cx="446" cy="300" rx="20" ry="30" fill={theme.skin} />
        {/* pelo */}
        <path
          d="M208 270 C196 170 260 128 335 130 C420 132 470 180 455 270 C440 228 420 210 400 205 C370 222 300 226 260 205 C240 222 222 240 208 270 Z"
          fill={theme.hair}
        />
        <path d="M262 168 C300 150 340 152 372 160" stroke="rgba(255,255,255,.18)" strokeWidth="8" fill="none" strokeLinecap="round" />
        {/* cejas */}
        <path d={`M262 ${248 - gesture * 10} q24 -12 48 0`} stroke={theme.hair} strokeWidth="9" fill="none" strokeLinecap="round" />
        <path d={`M352 ${248 - gesture * 10} q24 -12 48 0`} stroke={theme.hair} strokeWidth="9" fill="none" strokeLinecap="round" />
        {/* ojos */}
        <ellipse cx="286" cy="290" rx="11" ry={13 * (1 - blink) + 1} fill={theme.hair} />
        <ellipse cx="376" cy="290" rx="11" ry={13 * (1 - blink) + 1} fill={theme.hair} />
        {/* gafas */}
        <rect x="244" y="258" width="84" height="66" rx="18" fill="rgba(255,255,255,.15)" stroke={theme.hair} strokeWidth="7" />
        <rect x="334" y="258" width="84" height="66" rx="18" fill="rgba(255,255,255,.15)" stroke={theme.hair} strokeWidth="7" />
        <path d="M328 286 h6" stroke={theme.hair} strokeWidth="7" />
        {/* nariz */}
        <path d="M330 312 q-8 18 6 22" stroke="rgba(150,80,50,.45)" strokeWidth="5" fill="none" strokeLinecap="round" />
        {/* boca: altura según la voz */}
        <path
          d={`M300 ${352} Q330 ${352 + 6 + mo * 44} 360 ${352} Q330 ${352 + mo * 10} 300 352 Z`}
          fill="#5B1E1E"
          stroke="#5B1E1E"
          strokeWidth="5"
          strokeLinejoin="round"
        />
        {mo > 0.35 && <ellipse cx="330" cy={356 + mo * 20} rx={12 * mo} ry={6 * mo} fill="#E07070" />}
        {/* mejillas */}
        <ellipse cx="258" cy="336" rx="20" ry="11" fill="#F08A7A" opacity=".35" />
        <ellipse cx="404" cy="336" rx="20" ry="11" fill="#F08A7A" opacity=".35" />
      </g>
    </svg>
  );
};

export const rnd = (s: string) => random(s);

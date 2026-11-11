import React from 'react';
import {interpolate} from 'remotion';
import {ease, pop} from '../anim';
import {Card} from '../components';
import {parseAccent} from '../theme';
import type {SceneCtx} from '../types';

const label = (it: any) => (typeof it === 'string' ? it : it.label ?? it.text ?? '');
const times = (ctx: SceneCtx) => ctx.scene.widget.itemTimes ?? [];
const Rich: React.FC<{text: string; ctx: SceneCtx}> = ({text, ctx}) => (
  <>
    {parseAccent(text).map((p, i) => (
      <span key={i} style={p.accent ? {color: ctx.theme.accent} : undefined}>
        {p.text}
      </span>
    ))}
  </>
);

/* -------------------------------------------- checklist */
const Checklist: React.FC<{ctx: SceneCtx}> = ({ctx}) => {
  const {t, fps, theme, scene} = ctx;
  const w = scene.widget;
  const items = w.items ?? [];
  const k0 = pop(t, 0.1, fps);
  return (
    <Card theme={theme} style={{width: w.width ?? 700, transform: `translateY(${(1 - k0) * 80}px) rotate(${w.rot ?? -1.5}deg)`, opacity: k0}}>
      {w.title && <div style={{fontFamily: theme.mono, fontSize: 26, color: theme.muted, marginBottom: 18}}>{w.title}</div>}
      {items.map((it: any, i: number) => {
        const at = times(ctx)[i] ?? 0;
        const k = pop(t, at, fps);
        const c = ease(t, at + 0.3, at + 0.55);
        return (
          <div key={i} style={{display: 'flex', alignItems: 'center', gap: 22, padding: '14px 0', opacity: interpolate(k, [0, 1], [0.25, 1]), transform: `translateX(${(1 - k) * -30}px)`}}>
            <div style={{width: 54, height: 54, borderRadius: 14, border: `4px solid ${c > 0 ? theme.accent : theme.faint}`, background: c > 0.2 ? theme.accent : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${1 + Math.sin(c * Math.PI) * 0.2})`}}>
              <svg width="34" height="34" viewBox="0 0 24 24">
                <path d="M4 12.5 L10 18 L20 6" fill="none" stroke="#fff" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="30" strokeDashoffset={30 * (1 - c)} />
              </svg>
            </div>
            <div style={{fontFamily: theme.display, fontSize: 52, textTransform: 'uppercase', color: theme.ink, lineHeight: 1}}>
              <Rich text={label(it)} ctx={ctx} />
            </div>
          </div>
        );
      })}
    </Card>
  );
};

/* -------------------------------------------- número grande */
const Stat: React.FC<{ctx: SceneCtx}> = ({ctx}) => {
  const {t, fps, theme, scene} = ctx;
  const w = scene.widget;
  const p = ease(t, 0.25, 1.45, 0, 1);
  const v = (w.from ?? 0) + (w.value - (w.from ?? 0)) * p;
  const dec = w.decimals ?? 0;
  const txt = v.toLocaleString('es-MX', {minimumFractionDigits: dec, maximumFractionDigits: dec});
  const k = pop(t, 0.1, fps);
  const end = pop(t, 1.45, fps, {damping: 8, stiffness: 250});
  const R = 250;
  const ringP = w.ring === false ? 0 : (w.ringValue ?? Math.min(1, w.value / (w.max ?? 100))) * p;
  return (
    <div style={{width: 940, display: 'flex', flexDirection: 'column', alignItems: 'center', transform: `scale(${k})`}}>
      <div style={{position: 'relative', width: R * 2 + 40, height: R * 2 + 40, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        {w.ring !== false && (
          <svg width={R * 2 + 40} height={R * 2 + 40} style={{position: 'absolute', transform: 'rotate(-90deg)'}}>
            <circle cx={R + 20} cy={R + 20} r={R} fill="none" stroke={theme.bg2} strokeWidth="30" />
            <circle cx={R + 20} cy={R + 20} r={R} fill="none" stroke={theme.accent} strokeWidth="30" strokeLinecap="round" strokeDasharray={2 * Math.PI * R} strokeDashoffset={2 * Math.PI * R * (1 - ringP)} />
          </svg>
        )}
        <div style={{textAlign: 'center', transform: `scale(${1 + (1 - end) * 0 + Math.max(0, end - 1) * 0.6})`}}>
          <div style={{fontFamily: theme.display, fontSize: w.fontSize ?? 168, color: theme.ink, lineHeight: 1}}>
            {w.prefix}
            {txt}
            <span style={{color: theme.accent}}>{w.suffix}</span>
          </div>
          {w.label && <div style={{fontFamily: theme.body, fontWeight: 600, fontSize: 40, color: theme.muted, marginTop: 6, maxWidth: 420}}>{w.label}</div>}
        </div>
      </div>
    </div>
  );
};

/* -------------------------------------------- donut */
const Donut: React.FC<{ctx: SceneCtx}> = ({ctx}) => {
  const {t, fps, theme, scene} = ctx;
  const w = scene.widget;
  const items = w.items ?? [];
  const total = items.reduce((s: number, it: any) => s + it.value, 0);
  const R = 170;
  const C = 2 * Math.PI * R;
  const colors = [theme.accent, theme.ink, theme.accent2, '#F2B33D', '#3BAA6E'];
  let acc = 0;
  const k0 = pop(t, 0.05, fps);
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 44, transform: `scale(${k0})`}}>
      <div style={{position: 'relative', width: 400, height: 400}}>
        <svg width="400" height="400" style={{transform: 'rotate(-90deg)'}}>
          <circle cx="200" cy="200" r={R} fill="none" stroke={theme.bg2} strokeWidth="64" />
          {items.map((it: any, i: number) => {
            const at = times(ctx)[i] ?? 0;
            const p = ease(t, at, at + 0.55);
            const frac = it.value / total;
            const off = acc;
            acc += frac;
            return (
              <circle key={i} cx="200" cy="200" r={R} fill="none" stroke={it.color ?? colors[i % colors.length]} strokeWidth={64 + 10 * Math.sin(p * Math.PI)} strokeDasharray={`${Math.max(0, C * frac * p - 4)} ${C}`} strokeDashoffset={-C * off} />
            );
          })}
        </svg>
        <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: theme.display, fontSize: 64, color: theme.ink}}>{w.center ?? ''}</div>
      </div>
      <div style={{display: 'flex', flexDirection: 'column', gap: 22}}>
        {items.map((it: any, i: number) => {
          const at = times(ctx)[i] ?? 0;
          const k = pop(t, at, fps);
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 18, opacity: k, transform: `translateX(${(1 - k) * 40}px)`}}>
              <div style={{width: 30, height: 30, borderRadius: 8, background: it.color ?? colors[i % colors.length]}} />
              <div>
                <div style={{fontFamily: theme.display, fontSize: 64, lineHeight: 1, color: theme.ink}}>{it.value}%</div>
                <div style={{fontFamily: theme.body, fontWeight: 600, fontSize: 30, color: theme.muted}}>{it.label}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

/* -------------------------------------------- barras */
const Bars: React.FC<{ctx: SceneCtx}> = ({ctx}) => {
  const {t, fps, theme, scene} = ctx;
  const w = scene.widget;
  const items = w.items ?? [];
  const max = Math.max(...items.map((i: any) => i.value));
  const k0 = pop(t, 0.05, fps);
  return (
    <Card theme={theme} style={{width: 820, height: 480, display: 'flex', alignItems: 'flex-end', gap: 26, padding: '40px 40px 30px', opacity: k0, transform: `translateY(${(1 - k0) * 60}px)`}}>
      {items.map((it: any, i: number) => {
        const at = times(ctx)[i] ?? 0;
        const p = pop(t, at, fps, {damping: 13});
        const h = (it.value / max) * 330 * p;
        const hi = it.highlight || i === items.length - 1;
        return (
          <div key={i} style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10}}>
            <div style={{fontFamily: theme.display, fontSize: 40, color: hi ? theme.accent : theme.ink, opacity: p}}>{it.display ?? it.value}</div>
            <div style={{width: '100%', height: h, borderRadius: 14, background: hi ? theme.accent : theme.ink}} />
            <div style={{fontFamily: theme.mono, fontSize: 24, color: theme.muted}}>{it.label}</div>
          </div>
        );
      })}
    </Card>
  );
};

/* -------------------------------------------- pasos numerados (grid) */
const Steps: React.FC<{ctx: SceneCtx}> = ({ctx}) => {
  const {t, fps, theme, scene} = ctx;
  const items = scene.widget.items ?? [];
  const cols = scene.widget.cols ?? 2;
  return (
    <div style={{display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: 22, width: 900}}>
      {items.map((it: any, i: number) => {
        const at = times(ctx)[i] ?? 0;
        const k = pop(t, at, fps);
        const done = typeof it === 'object' && it.done !== undefined ? t >= at + (it.done || 0.5) : false;
        return (
          <Card key={i} theme={theme} style={{padding: '22px 26px', display: 'flex', alignItems: 'center', gap: 20, transform: `scale(${k}) rotate(${(1 - k) * (i % 2 ? 8 : -8)}deg)`, opacity: Math.min(1, k * 2)}}>
            <div style={{width: 58, height: 58, borderRadius: 14, background: theme.ink, color: '#fff', fontFamily: theme.display, fontSize: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>{i + 1}</div>
            <div>
              <div style={{fontFamily: theme.body, fontWeight: 800, fontSize: 36, color: theme.ink, lineHeight: 1.05}}>
                <Rich text={label(it)} ctx={ctx} />
              </div>
              {it.sub && <div style={{fontFamily: theme.mono, fontSize: 22, color: theme.muted, marginTop: 4}}>// {it.sub}</div>}
            </div>
            {done && <div style={{marginLeft: 'auto', width: 40, height: 40, borderRadius: 20, background: theme.accent, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26, fontWeight: 800}}>✓</div>}
          </Card>
        );
      })}
    </div>
  );
};

/* -------------------------------------------- caja de texto que se escribe sola */
const Typing: React.FC<{ctx: SceneCtx}> = ({ctx}) => {
  const {t, fps, theme, scene} = ctx;
  const w = scene.widget;
  const text: string = w.text ?? '';
  const cps = w.cps ?? 22;
  const n = Math.max(0, Math.floor((t - 0.35) * cps));
  const shown = text.slice(0, n);
  const k = pop(t, 0.05, fps);
  const sendAt = 0.35 + text.length / cps + 0.25;
  const press = t > sendAt ? pop(t, sendAt, fps, {damping: 8}) : 0;
  const caret = Math.floor(t * 2.2) % 2 === 0;
  return (
    <Card theme={theme} style={{width: 860, minHeight: 230, position: 'relative', transform: `scale(${k})`, border: `3px solid ${theme.bg2}`}}>
      <div style={{fontFamily: theme.body, fontWeight: 500, fontSize: 46, color: theme.ink, lineHeight: 1.25, paddingRight: 80}}>
        {shown || <span style={{color: theme.faint}}>{w.placeholder ?? ''}</span>}
        <span style={{display: 'inline-block', width: 4, height: 50, marginLeft: 4, background: caret ? theme.ink : 'transparent', verticalAlign: 'middle'}} />
      </div>
      <div style={{position: 'absolute', right: 26, bottom: 26, width: 70, height: 70, borderRadius: 18, background: theme.accent, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 40, fontWeight: 800, transform: `scale(${1 - Math.sin(press * Math.PI) * 0.18})`}}>↑</div>
    </Card>
  );
};

/* -------------------------------------------- móvil con notificaciones */
const Phone: React.FC<{ctx: SceneCtx}> = ({ctx}) => {
  const {t, fps, theme, scene} = ctx;
  const w = scene.widget;
  const items = w.items ?? [];
  const k0 = pop(t, 0.05, fps, {damping: 14});
  return (
    <div style={{display: 'flex', gap: 34, alignItems: 'center'}}>
      <div style={{width: 470, height: 780, borderRadius: 66, background: '#111', padding: 14, transform: `translateY(${(1 - k0) * 200}px) rotate(${-4 + (1 - k0) * -10}deg)`, boxShadow: '0 30px 60px rgba(0,0,0,.3)'}}>
        <div style={{width: '100%', height: '100%', borderRadius: 48, overflow: 'hidden', background: w.screen ?? `linear-gradient(160deg, ${theme.accent2}, #0B1640)`, position: 'relative', padding: '70px 18px 18px'}}>
          <div style={{position: 'absolute', top: 16, left: '50%', marginLeft: -60, width: 120, height: 32, borderRadius: 16, background: '#000'}} />
          <div style={{fontFamily: theme.body, fontWeight: 700, color: '#fff', fontSize: 64, textAlign: 'center', marginBottom: 24, opacity: 0.95}}>{w.clock ?? '9:41'}</div>
          {items.map((it: any, i: number) => {
            const at = times(ctx)[i] ?? 0;
            const k = pop(t, at, fps);
            return (
              <div key={i} style={{background: 'rgba(255,255,255,.9)', borderRadius: 24, padding: '18px 18px', marginBottom: 12, display: 'flex', gap: 12, alignItems: 'center', transform: `translateY(${(1 - k) * -40}px) scale(${0.9 + 0.1 * k})`, opacity: k}}>
                <div style={{width: 54, height: 54, borderRadius: 14, background: it.color ?? theme.accent, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26}}>{it.icon ?? '•'}</div>
                <div style={{fontFamily: theme.body, fontSize: 28, color: '#111', lineHeight: 1.2}}>
                  <div style={{fontWeight: 800}}>{it.title ?? label(it)}</div>
                  {it.body && <div style={{fontWeight: 500, color: '#555'}}>{it.body}</div>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

/* -------------------------------------------- antes / después */
const Compare: React.FC<{ctx: SceneCtx}> = ({ctx}) => {
  const {t, fps, theme, scene} = ctx;
  const w = scene.widget;
  const [a, b] = w.items ?? [{}, {}];
  const ta = times(ctx)[0] ?? 0.1;
  const tb = times(ctx)[1] ?? 1;
  const ka = pop(t, ta, fps);
  const kb = pop(t, tb, fps);
  const arrow = ease(t, tb - 0.35, tb);
  const box = (it: any, k: number, good: boolean, rot: number) => (
    <Card theme={theme} style={{width: 380, minHeight: 330, transform: `scale(${k}) rotate(${rot}deg)`, opacity: Math.min(1, 2 * k), background: good ? theme.card : '#F4F1EC', position: 'relative'}}>
      <div style={{position: 'absolute', top: -26, left: 24, background: good ? theme.accent : theme.muted, color: '#fff', fontFamily: theme.display, fontSize: 34, padding: '4px 18px', borderRadius: 10}}>{it.tag ?? (good ? 'DESPUÉS' : 'ANTES')}</div>
      <div style={{fontFamily: theme.display, fontSize: 58, color: good ? theme.ink : theme.muted, marginTop: 20, lineHeight: 1, textDecoration: good ? 'none' : 'line-through', textDecorationColor: theme.accent}}>{it.title}</div>
      {(it.lines ?? []).map((l: string, i: number) => (
        <div key={i} style={{fontFamily: theme.body, fontWeight: 600, fontSize: 30, color: theme.muted, marginTop: 14}}>{l}</div>
      ))}
    </Card>
  );
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
      {box(a, ka, false, -3)}
      <svg width="120" height="80" viewBox="0 0 120 80">
        <path d="M10 50 Q60 0 105 40" fill="none" stroke={theme.accent} strokeWidth="7" strokeLinecap="round" strokeDasharray="130" strokeDashoffset={130 * (1 - arrow)} />
        <path d="M90 22 L106 41 L84 48" fill="none" stroke={theme.accent} strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" opacity={arrow > 0.9 ? 1 : 0} />
      </svg>
      {box(b, kb, true, 3)}
    </div>
  );
};

/* -------------------------------------------- chat */
const Chat: React.FC<{ctx: SceneCtx}> = ({ctx}) => {
  const {t, fps, theme, scene} = ctx;
  const items = scene.widget.items ?? [];
  return (
    <div style={{width: 900, display: 'flex', flexDirection: 'column', gap: 18}}>
      {items.map((it: any, i: number) => {
        const at = times(ctx)[i] ?? 0;
        const k = pop(t, at, fps);
        const me = it.from === 'me';
        return (
          <div key={i} style={{alignSelf: me ? 'flex-end' : 'flex-start', maxWidth: 760, background: me ? theme.accent : theme.card, color: me ? '#fff' : theme.ink, fontFamily: theme.body, fontWeight: 600, fontSize: 54, lineHeight: 1.2, padding: '20px 28px', borderRadius: 30, borderBottomRightRadius: me ? 8 : 30, borderBottomLeftRadius: me ? 30 : 8, boxShadow: '0 12px 30px rgba(0,0,0,.12)', transform: `scale(${k}) translateY(${(1 - k) * 30}px)`, transformOrigin: me ? 'right bottom' : 'left bottom', opacity: Math.min(1, k * 2)}}>
            {label(it)}
          </div>
        );
      })}
    </div>
  );
};

/* -------------------------------------------- emoji / icono gigante */
const Icon: React.FC<{ctx: SceneCtx}> = ({ctx}) => {
  const {t, fps, scene, theme} = ctx;
  const k = pop(t, 0.1, fps, {damping: 8});
  const float = Math.sin(t * 2.4) * 10;
  return (
    <div style={{width: 940, display: 'flex', justifyContent: 'center'}}>
      <div style={{fontSize: 300, transform: `translateY(${float}px) scale(${k}) rotate(${(1 - k) * -30}deg)`, filter: 'drop-shadow(0 30px 30px rgba(0,0,0,.18))'}}>{scene.widget.icon}</div>
      {scene.widget.caption && <div style={{position: 'absolute', top: 360, fontFamily: theme.display, fontSize: 60, color: theme.ink}}>{scene.widget.caption}</div>}
    </div>
  );
};

export const WIDGETS: Record<string, React.FC<{ctx: SceneCtx}>> = {
  checklist: Checklist,
  stat: Stat,
  donut: Donut,
  bars: Bars,
  steps: Steps,
  typing: Typing,
  phone: Phone,
  compare: Compare,
  chat: Chat,
  icon: Icon,
};

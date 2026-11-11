import React from 'react';
import {AbsoluteFill, Audio, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {ease} from './anim';
import {Captions, Character, Headline, Paper, Stamp} from './components';
import {mergeTheme} from './theme';
import type {SceneCtx, Timeline} from './types';
import {WIDGETS} from './widgets';

export const Reel: React.FC<{timeline: Timeline | null}> = ({timeline}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (!timeline) return <AbsoluteFill style={{background: '#111'}} />;
  const theme = mergeTheme(timeline.theme);
  const time = frame / fps;
  const scenes = timeline.scenes;
  const si = Math.max(0, scenes.findIndex((s, i) => time >= s.start && (i === scenes.length - 1 || time < scenes[i + 1].start)));
  const scene = scenes[si];
  const t = time - scene.start;
  const dur = scene.end - scene.start;
  const exit = ease(t, dur - 0.18, dur, 0, 1);
  const isLast = si === scenes.length - 1;
  const ctx: SceneCtx = {scene, t, frame, fps, theme, exit: isLast ? 0 : exit};

  // cámara: deriva lenta + punch-in cuando aparece el titular
  const drift = interpolate(t, [0, dur], [1, 1.035]);
  const punch = 1 + 0.025 * Math.exp(-Math.max(0, t - scene.headlineTime) * 6) * (t >= scene.headlineTime ? 1 : 0);
  const enter = ease(t, 0, 0.35);
  const W = WIDGETS[scene.widget?.type ?? ''];
  const w = scene.widget ?? {};

  const mouth = timeline.mouth[frame] ?? 0;
  const gesture = Math.exp(-Math.max(0, t - 0.05) * 3) * (t > 0 ? 1 : 0);
  const showChar = timeline.character && scene.character !== false;
  const charEnter = ease(time, 0, 0.6);

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Paper theme={theme} frame={frame} />
      <Audio src={staticFile(timeline.audio)} />
      <Captions words={timeline.words} time={time} theme={theme} scene={scene} />
      <AbsoluteFill
        style={{
          transform: `scale(${drift * punch * (1 - 0.06 * ctx.exit)}) translateY(${(1 - enter) * 40 - ctx.exit * 30}px)`,
          opacity: (0.2 + 0.8 * enter) * (1 - ctx.exit),
          filter: ctx.exit > 0 ? `blur(${ctx.exit * 10}px)` : undefined,
          transformOrigin: '50% 45%',
        }}
      >
        <Headline scene={scene} t={t} fps={fps} theme={theme} size={scene.headlineSize} />
        {W && (
          <div style={{position: 'absolute', left: 70, right: 70, top: w.top ?? 760, display: 'flex', justifyContent: w.align ?? 'flex-start'}}>
            <W ctx={ctx} />
          </div>
        )}
        {w.stamp && <Stamp text={w.stamp} t={t} at={w.stampTime ?? dur * 0.6} fps={fps} theme={theme} x={w.stampX} y={w.stampY} rot={w.stampRot} />}
      </AbsoluteFill>
      {showChar && (
        <Character theme={theme} frame={frame} fps={fps} mouth={mouth} gesture={gesture} side={scene.character === 'left' ? 'left' : 'right'} enter={charEnter} />
      )}
      {/* flash sutil en el corte */}
      {si > 0 && t < 0.12 && <AbsoluteFill style={{background: '#fff', opacity: 0.35 * (1 - t / 0.12)}} />}
    </AbsoluteFill>
  );
};

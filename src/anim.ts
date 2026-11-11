import {Easing, interpolate, spring} from 'remotion';

/** spring que arranca en el segundo `at` (tiempo local de escena). */
export const pop = (t: number, at: number, fps: number, cfg: {damping?: number; stiffness?: number; mass?: number} = {}) =>
  spring({frame: Math.round((t - at) * fps), fps, config: {damping: 12, stiffness: 170, mass: 0.7, ...cfg}});

export const ease = (t: number, a: number, b: number, from = 0, to = 1, e = Easing.bezier(0.22, 1, 0.36, 1)) =>
  interpolate(t, [a, b], [from, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

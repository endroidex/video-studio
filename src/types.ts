import type {Theme} from './theme';

export type Word = {text: string; start: number; end: number; accent: boolean; scene: number};

export type Widget = {
  type?: string;
  items?: any[];
  itemTimes?: number[];
  stamp?: string;
  stampTime?: number;
  [k: string]: any;
};

export type Scene = {
  tag?: string;
  headline?: string;
  badge?: string | number;
  start: number;
  end: number;
  voiceStart: number;
  headlineTime: number;
  widget: Widget;
  character?: boolean | 'left' | 'right';
  emotion?: string;
  [k: string]: any;
};

export type Timeline = {
  id: string;
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  theme: Partial<Theme>;
  character: boolean;
  scenes: Scene[];
  words: Word[];
  mouth: number[];
  audio: string;
  title: string;
};

export type SceneCtx = {
  scene: Scene;
  /** segundos desde el inicio de la escena */
  t: number;
  frame: number;
  fps: number;
  theme: Theme;
  /** 0..1 progreso de salida (últimos frames de la escena) */
  exit: number;
};

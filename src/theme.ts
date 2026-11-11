import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

const fonts: [string, string, string?, string?][] = [
  ['Anton', 'fonts/Anton.woff2'],
  ['Instrument Serif', 'fonts/InstrumentSerif-Italic.woff2', '400', 'italic'],
  ['Inter', 'fonts/Inter-400.woff2', '400'],
  ['Inter', 'fonts/Inter-500.woff2', '500'],
  ['Inter', 'fonts/Inter-600.woff2', '600'],
  ['Inter', 'fonts/Inter-700.woff2', '700'],
  ['Inter', 'fonts/Inter-800.woff2', '800'],
  ['JetBrains Mono', 'fonts/JetBrainsMono.woff2'],
];
for (const [family, url, weight, style] of fonts) {
  loadFont({family, url: staticFile(url), weight: weight ?? '400', style: style ?? 'normal'});
}

export type Theme = {
  bg: string;
  bg2: string;
  ink: string;
  muted: string;
  faint: string;
  accent: string;
  accent2: string;
  card: string;
  good: string;
  display: string;
  body: string;
  serif: string;
  mono: string;
  skin: string;
  hair: string;
  shirt: string;
};

export const defaultTheme: Theme = {
  bg: '#ECE8E1',
  bg2: '#E2DDD4',
  ink: '#16151A',
  muted: '#6E6A64',
  faint: '#BDB8AF',
  accent: '#E5483B',
  accent2: '#2F5BEA',
  card: '#FFFFFF',
  good: '#E5483B',
  display: 'Anton',
  body: 'Inter',
  serif: 'Instrument Serif',
  mono: 'JetBrains Mono',
  skin: '#F2C29B',
  hair: '#17171C',
  shirt: '#2050E0',
};

export const mergeTheme = (t?: Partial<Theme>): Theme => ({...defaultTheme, ...(t ?? {})});

/** Parte un texto con marcas *acento* en segmentos. */
export const parseAccent = (text: string) =>
  text.split(/(\*[^*]+\*)/g).filter(Boolean).map((s) => ({text: s.replace(/\*/g, ''), accent: s.startsWith('*')}));

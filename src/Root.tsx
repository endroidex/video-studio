import React from 'react';
import {CalculateMetadataFunction, Composition, staticFile} from 'remotion';
import {Reel} from './Reel';
import type {Timeline} from './types';
import './theme';

type Props = {project: string; timeline: Timeline | null};

const calc: CalculateMetadataFunction<Props> = async ({props}) => {
  const res = await fetch(staticFile(`projects/${props.project}/timeline.json`));
  const timeline = (await res.json()) as Timeline;
  return {
    durationInFrames: timeline.durationInFrames,
    fps: timeline.fps,
    width: timeline.width,
    height: timeline.height,
    props: {...props, timeline},
  };
};

export const Root: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    durationInFrames={300}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{project: 'demo', timeline: null} as Props}
    calculateMetadata={calc}
  />
);

import { AnimationCanvasWebView } from "./AnimationCanvasWebView";

type Props = {
  isPlaying: boolean;
  script?: any | null;
  currentTimeMs?: number;
  playbackRate?: number;
};

export function AnimationCanvasNative({
  isPlaying,
  script,
  currentTimeMs,
  playbackRate = 1,
}: Props) {
  return (
    <AnimationCanvasWebView
      isPlaying={isPlaying}
      script={script}
      currentTimeMs={currentTimeMs}
      playbackRate={playbackRate}
    />
  );
}

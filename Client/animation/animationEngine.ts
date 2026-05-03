import { easeInOutCubic } from "./core/easing";
import { detectDomain, renderUniversalScene, type ConceptDomain } from "./sceneRenderers";

const SCENE_TRANSITION_MS = 400;

export interface SceneActor {
  type: string;
  x?: number;
  y?: number;
  color?: string | null;
  size?: number;
  count?: number;
  animation?: string;
  angle?: number;
  length?: number;
  text?: string;
  fontSize?: number;
  timeline?: { at: number; action?: string; alpha?: number }[];
  [key: string]: any;
}

export interface Scene {
  id: string;
  startTime: number;
  duration: number;
  text: string;
  actors: SceneActor[];
  environment?: string;
  meta?: Record<string, any>;
}

export interface AnimationScript {
  title: string;
  duration: number;
  scenes: Scene[];
  concept?: string;
  /** Rule-engine: playback_speed, scene_transition_ms */
  meta?: Record<string, any>;
}

type Ctx = any;

export class AnimationEngine {
  private ctx: Ctx;
  private W: number;
  private H: number;
  private script: AnimationScript;
  private concept: string;
  private domain: ConceptDomain;
  private currentTime = 0;
  private isPlaying = false;
  private playbackRate = 1;
  private lastTS: number | null = null;
  private rafId: any = null;
  private postFrame?: () => void;
  private onSceneChange?: (idx: number, scene: Scene) => void;
  private onTimeUpdate?: (time: number) => void;
  private onComplete?: () => void;
  private lastSceneIndex = -1;

  constructor(
    ctx: Ctx,
    W: number,
    H: number,
    script: AnimationScript,
    concept = "",
    callbacks?: {
      onSceneChange?: (idx: number, scene: Scene) => void;
      onTimeUpdate?: (time: number) => void;
      onComplete?: () => void;
      postFrame?: () => void;
    },
  ) {
    this.ctx = ctx;
    this.W = W;
    this.H = H;
    this.script = script;
    this.concept = concept || script.concept || script.title || "";
    this.domain = detectDomain(this.concept, this.script.scenes);
    this.onSceneChange = callbacks?.onSceneChange;
    this.onTimeUpdate = callbacks?.onTimeUpdate;
    this.onComplete = callbacks?.onComplete;
    this.postFrame = callbacks?.postFrame;
    this.syncPlaybackFromScript();
  }

  private tickGeneration = 0;

  setScript(script: AnimationScript, concept = "") {
    this.pause(); // stop any running tick loop before replacing script
    this.script = script;
    this.concept = concept || script.concept || script.title || "";
    this.domain = detectDomain(this.concept, this.script.scenes);
    this.currentTime = 0;
    this.lastSceneIndex = -1;
    this.syncPlaybackFromScript();
  }

  setSize(W: number, H: number) {
    if (!Number.isFinite(W) || !Number.isFinite(H) || W <= 0 || H <= 0) return;
    this.W = W;
    this.H = H;
    this.draw();
  }

  play() {
    if (this.isPlaying) return;
    this.isPlaying = true;
    this.lastTS = null;
    this.tick();
  }

  pause() {
    this.isPlaying = false;
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  seek(ms: number) {
    this.currentTime = Math.max(0, Math.min(ms, this.script.duration || 0));
    this.renderFrame(this.currentTime);
    this.onTimeUpdate?.(this.currentTime);
  }

  seekToScene(idx: number) {
    const s = this.script.scenes[idx];
    if (s) this.seek(s.startTime);
  }

  reset() {
    this.pause();
    this.currentTime = 0;
    this.concept = this.script.concept || this.script.title || this.concept;
    this.domain = detectDomain(this.concept, this.script.scenes);
    this.lastSceneIndex = -1;
    this.renderFrame(0);
  }

  setPlaybackRate(rate: number) {
    if (!Number.isFinite(rate) || rate <= 0) return;
    this.playbackRate = rate;
  }

  dispose() {
    this.pause();
  }

  getCurrentTime() { return this.currentTime; }
  getDuration() { return this.script.duration; }
  getScenes() { return this.script.scenes; }
  getIsPlaying() { return this.isPlaying; }

  getCurrentSceneIndex() {
    const t = this.currentTime;
    for (let i = this.script.scenes.length - 1; i >= 0; i--) {
      if (t >= this.script.scenes[i].startTime) return i;
    }
    return 0;
  }

  private syncPlaybackFromScript() {
    const s = this.script as AnimationScript;
    const ps = Number(
      s.meta?.playback_speed ?? s.scenes?.[0]?.meta?.playback_speed,
    );
    if (Number.isFinite(ps) && ps > 0 && ps <= 4) {
      this.playbackRate = ps;
    } else {
      this.playbackRate = 1;
    }
  }

  /** Fade in at scene start / fade out before next scene — one clean beat at a time. */
  private sceneCompositeOpacity(
    sceneElapsed: number,
    sceneDuration: number,
    transitionMs: number,
  ): number {
    const tr = Math.max(100, Math.min(900, transitionMs));
    const dur = Math.max(800, sceneDuration || 6000);
    const aIn = Math.min(1, sceneElapsed / tr);
    const fadeStart = Math.max(0, dur - tr);
    const aOut = sceneElapsed <= fadeStart ? 1 : Math.max(0, (dur - sceneElapsed) / tr);
    return easeInOutCubic(Math.min(aIn, aOut));
  }

  private tick() {
    if (!this.isPlaying) return;
    this.rafId = requestAnimationFrame((ts: number) => {
      if (this.lastTS !== null) {
        this.currentTime = Math.min(
          this.currentTime + (ts - this.lastTS) * this.playbackRate,
          this.script.duration || 0,
        );
      }
      this.lastTS = ts;
      this.renderFrame(this.currentTime);
      this.onTimeUpdate?.(this.currentTime);
      if (this.currentTime >= (this.script.duration || 0)) {
        this.isPlaying = false;
        this.onComplete?.();
        return;
      }
      this.tick();
    });
  }

  renderFrame(timeMs: number) {
    const { ctx, W, H, script, domain } = this;
    const scenes = script.scenes || [];
    if (!scenes.length) {
      ctx.clearRect(0, 0, W, H);
      return;
    }

    let currentScene: Scene = scenes[0];
    let sceneIndex = 0;
    for (let i = scenes.length - 1; i >= 0; i--) {
      if (timeMs >= scenes[i].startTime) {
        currentScene = scenes[i];
        sceneIndex = i;
        break;
      }
    }

    const sceneElapsed = Math.max(0, timeMs - currentScene.startTime);
    if (sceneIndex !== this.lastSceneIndex) {
      this.lastSceneIndex = sceneIndex;
      this.onSceneChange?.(sceneIndex, currentScene);
    }
    ctx.clearRect(0, 0, W, H);
    const sceneDur =
      typeof currentScene.duration === "number" && currentScene.duration > 0
        ? currentScene.duration
        : 6000;
    const transitionMs = Number(
      currentScene.meta?.scene_transition_ms ??
        (this.script as AnimationScript).meta?.scene_transition_ms ??
        SCENE_TRANSITION_MS,
    );
    const blend = this.sceneCompositeOpacity(sceneElapsed, sceneDur, transitionMs);
    const seg = Number(currentScene.meta?.loop_segment_ms ?? 0);
    const visualElapsed =
      seg > 0 && seg <= sceneDur ? sceneElapsed % seg : sceneElapsed;
    renderUniversalScene(currentScene, domain, ctx, W, H, sceneElapsed, blend, visualElapsed);
    this.postFrame?.();
  }

  draw() {
    this.renderFrame(this.currentTime);
  }
}

export default AnimationEngine;

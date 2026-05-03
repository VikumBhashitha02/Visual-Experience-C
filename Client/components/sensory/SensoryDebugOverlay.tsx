import React from "react";
import { useSensoryStore } from "@/store/sensoryStore";

// ─── Debug flag ────────────────────────────────────────────────────────────────
// Set to `true` only when actively debugging the sensory cue pipeline.
// Must be `false` in all student-facing / production builds.
const DEBUG_MODE = false;

const MAX_VISIBLE = 5;

export function SensoryDebugOverlay() {
  const lastCues = useSensoryStore((s) => s.lastCues);

  // Always a no-op in production — returns null without any DOM nodes
  if (!DEBUG_MODE) return null;
  if (lastCues.length === 0) return null;

  // Developer-only: logged to console instead of shown on screen
  if (DEBUG_MODE) {
    lastCues.slice(0, MAX_VISIBLE).forEach((cue) => {
      console.log(
        `[SensoryDebug] ${cue.type} · ${Math.round(cue.timeMs)}ms | ${cue.patternOrText}`,
      );
    });
  }

  return null;
}

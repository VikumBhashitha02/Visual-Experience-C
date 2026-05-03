import React, { useEffect, useRef } from "react";
import { StyleSheet, View } from "react-native";
import { WebView } from "react-native-webview";

type Props = {
  isPlaying: boolean;
  script?: any | null;
  currentTimeMs?: number;
  playbackRate?: number;
};

const ANIM_JS = `
(function () {
  "use strict";
  var canvas = document.getElementById("c");
  var ctx = canvas.getContext("2d");
  var W = 800;
  var H = 600;
  var state = { script: null, playing: false, t: 0, lastTs: null, domain: "generic", rate: 1 };
  var TYPE_ALIAS = {
    water_drop: "waterdrop",
    droplet: "waterdrop",
    h2o: "waterdrop",
    carbon_dioxide: "co2",
    carbondioxide: "co2",
    o2: "oxygen",
    oxygen: "oxygen",
    glucose_molecule: "glucose",
    star: "sun",
    lightning: "bolt",
    energy: "bolt",
    tree: "plant",
    leaves: "leaf",
    roots: "root",
    battery_cell: "battery",
    lamp: "bulb",
    circuit: "wire",
    conductor: "wire",
    vibration: "wave",
    cell: "molecule"
  };
  var DEFAULT_POS = {
    sun: { x: 0.8, y: 0.14 },
    plant: { x: 0.24, y: 0.79 },
    root: { x: 0.24, y: 0.86 },
    cloud: { x: 0.52, y: 0.19 },
    waterdrop: { x: 0.18, y: 0.82 },
    water: { x: 0.18, y: 0.82 },
    co2: { x: 0.74, y: 0.31 },
    oxygen: { x: 0.66, y: 0.21 },
    glucose: { x: 0.55, y: 0.44 },
    battery: { x: 0.2, y: 0.5 },
    wire: { x: 0.5, y: 0.48 },
    switch: { x: 0.58, y: 0.32 },
    bulb: { x: 0.84, y: 0.32 },
    ear: { x: 0.82, y: 0.5 },
    wave: { x: 0.28, y: 0.5 },
    label: { x: 0.5, y: 0.16 }
  };
  var DOMAIN_ALLOWED = {
    photosynthesis: ["sun", "plant", "leaf", "root", "waterdrop", "water", "co2", "oxygen", "glucose", "arrow", "label", "line", "bolt", "cloud"],
    water_cycle: ["sun", "cloud", "waterdrop", "water", "arrow", "label", "line", "rock"],
    food_chain: ["plant", "animal", "arrow", "label", "line"],
    electric_circuit: ["battery", "wire", "switch", "bulb", "arrow", "label", "line", "bolt", "wave"],
    sound: ["wave", "ear", "arrow", "label", "line", "bolt"],
    heat_transfer: ["sun", "rock", "arrow", "label", "line", "bolt", "thermometer"],
    gravity: ["planet", "rock", "arrow", "label", "line"]
  };

  function clamp01(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
  function clamp(v, min, max) { return v < min ? min : v > max ? max : v; }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function easeOut(t) { var x = clamp01(t); return 1 - Math.pow(1 - x, 3); }
  function fadeIn(elapsed, delay, dur) { return easeOut((elapsed - (delay || 0)) / Math.max(1, dur || 500)); }
  function post(msg) { try { window.ReactNativeWebView && window.ReactNativeWebView.postMessage(JSON.stringify(msg)); } catch (_e) {} }

  function resizeCanvas() {
    var dpr = Math.max(1, window.devicePixelRatio || 1);
    var rect = canvas.getBoundingClientRect();
    W = Math.max(300, Math.round(rect.width || 800));
    H = Math.max(220, Math.round(rect.height || 600));
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function normalize(raw) {
    if (!raw || typeof raw !== "object") {
      return { title: "Untitled", duration: 6000, scenes: [{ id: "fallback", startTime: 0, duration: 6000, text: "Animation data is loading...", actors: [], environment: "minimal" }] };
    }
    var scenes = Array.isArray(raw.scenes) ? raw.scenes.slice() : [];
    var cursor = 0;
    scenes = scenes.map(function (s, i) {
      var sc = Object.assign({}, s || {});
      sc.id = String(sc.id || ("scene_" + i));
      sc.duration = Number(sc.duration) > 0 ? Number(sc.duration) : 6000;
      sc.startTime = Number(sc.startTime) >= 0 ? Number(sc.startTime) : cursor;
      sc.text = String(sc.text || "");
      sc.environment = String(sc.environment || "");
      sc.meta = sc.meta && typeof sc.meta === "object" ? sc.meta : {};
      sc.actors = Array.isArray(sc.actors) ? sc.actors.map(function (a) {
        var actor = Object.assign({}, a || {});
        actor.type = resolveType(actor.type, actor.text);
        actor.animation = String(actor.animation || "appear").toLowerCase().trim();
        actor.x = Number.isFinite(actor.x) ? Number(actor.x) : (typeof actor.x === "string" && actor.x.trim() ? Number(actor.x) : null);
        actor.y = Number.isFinite(actor.y) ? Number(actor.y) : (typeof actor.y === "string" && actor.y.trim() ? Number(actor.y) : null);
        actor.size = Number(actor.size) > 0 ? Number(actor.size) : 40;
        actor.timeline = Array.isArray(actor.timeline) ? actor.timeline.filter(function (step) { return step && Number.isFinite(step.at); }) : [];
        return actor;
      }) : [];
      cursor = sc.startTime + sc.duration;
      return sc;
    });
    if (!scenes.length) {
      scenes = [{ id: "fallback", startTime: 0, duration: 6000, text: String(raw.title || "Untitled"), actors: [], environment: "minimal" }];
      cursor = 6000;
    }
    scenes.sort(function (a, b) { return a.startTime - b.startTime; });
    var rebase = 0;
    scenes.forEach(function (sc) {
      if (!Number.isFinite(sc.startTime) || sc.startTime < rebase) sc.startTime = rebase;
      rebase = sc.startTime + sc.duration;
    });
    var computed = scenes.reduce(function (max, sc) { return Math.max(max, sc.startTime + sc.duration); }, 0);
    return {
      title: String(raw.title || "Untitled Animation"),
      concept: String(raw.concept || raw.title || ""),
      duration: Number(raw.duration) > 0 ? Math.max(Number(raw.duration), computed) : computed,
      scenes: scenes,
    };
  }

  function detectDomain(script) {
    if (!script) return "generic";
    var title = String(script.title || "").toLowerCase();
    var scenes = Array.isArray(script.scenes) ? script.scenes : [];
    var sceneText = scenes.map(function (s) { return String((s && s.text) || ""); }).join(" ").toLowerCase();
    var actorHints = scenes.map(function (s) {
      return Array.isArray(s && s.actors)
        ? s.actors.map(function (a) { return String((a && a.type) || ""); }).join(" ")
        : "";
    }).join(" ").toLowerCase();

    function contains(corpus, token) {
      var t = String(token || "").toLowerCase();
      if (!t) return false;
      if (t.indexOf(" ") >= 0) return corpus.indexOf(t) >= 0;
      var padded = (" " + corpus + " ").replace(/[^a-z0-9]+/gi, " ");
      return padded.indexOf(" " + t + " ") >= 0;
    }

    function score(signals) {
      var sum = 0;
      for (var i = 0; i < signals.length; i += 1) {
        var token = signals[i][0];
        var weight = signals[i][1];
        if (contains(sceneText, token)) sum += weight * 1.55;
        if (contains(title, token)) sum += weight * 1.05;
        if (contains(actorHints, token)) sum += weight * 0.5;
      }
      return sum;
    }

    var electricSignals = [["electric circuit", 4.2], ["circuit", 2.4], ["battery", 2.6], ["bulb", 2.6], ["switch", 2.4], ["wire", 2], ["current", 2], ["complete circuit", 3], ["incomplete circuit", 3]];
    var photoSignals = [["photosynthesis", 4], ["chlorophyll", 3.4], ["chloroplast", 3.2], ["glucose", 2.4], ["carbon dioxide", 2.2], ["co2", 1.8], ["plant food", 2.2], ["leaf", 1.2], ["plant", 1.3]];
    var waterSignals = [["water cycle", 4], ["evaporation", 2.8], ["condensation", 2.8], ["precipitation", 2.8], ["rain", 1.6], ["cloud", 1.4]];
    var soundSignals = [["sound", 2.6], ["vibration", 2.8], ["hearing", 2.2], ["ear", 2], ["wave", 1.6]];
    var heatSignals = [["heat transfer", 4], ["heat", 2.2], ["temperature", 2.2], ["conduction", 2.4], ["convection", 2.4], ["radiation", 2.2]];
    var gravitySignals = [["gravity", 4], ["fall", 2], ["weight", 2], ["pull", 1.8]];
    var foodSignals = [["food chain", 4], ["food web", 3.6], ["producer", 2], ["consumer", 2], ["herbivore", 2.2], ["carnivore", 2.2]];

    var scores = {
      electric_circuit: score(electricSignals),
      photosynthesis: score(photoSignals),
      water_cycle: score(waterSignals),
      sound: score(soundSignals),
      heat_transfer: score(heatSignals),
      gravity: score(gravitySignals),
      food_chain: score(foodSignals)
    };

    var electricHard = (contains(sceneText, "battery") || contains(title, "battery")) &&
      (contains(sceneText, "bulb") || contains(title, "bulb")) &&
      (contains(sceneText, "wire") || contains(sceneText, "switch") || contains(sceneText, "circuit"));
    var photoHard = (contains(sceneText, "photosynthesis") || contains(sceneText, "chlorophyll") || contains(sceneText, "chloroplast")) &&
      (contains(sceneText, "plant") || contains(sceneText, "leaf") || contains(actorHints, "plant") || contains(actorHints, "leaf"));
    if (electricHard) scores.electric_circuit += 7.5;
    if (photoHard) scores.photosynthesis += 6.5;
    if (electricHard) scores.photosynthesis -= 8.2;

    var best = "generic";
    var bestScore = 0;
    ["electric_circuit", "photosynthesis", "water_cycle", "food_chain", "sound", "heat_transfer", "gravity"].forEach(function (domain) {
      var s = scores[domain] || 0;
      if (s > bestScore + 0.2) {
        best = domain;
        bestScore = s;
      }
    });
    if (bestScore < 2.8) return "generic";
    return best;
  }

  function resolveType(type, text) {
    var raw = String(type || "label").toLowerCase().trim();
    var mapped = TYPE_ALIAS[raw] || raw;
    if (mapped !== "label") return mapped;
    var compact = String(text || "").toLowerCase().replace(/\\s+/g, "");
    if (/^(h2o|water)$/.test(compact)) return "waterdrop";
    if (/^(co2|carbondioxide)$/.test(compact)) return "co2";
    if (/^(o2|oxygen)$/.test(compact)) return "oxygen";
    if (/^(glucose|sugar|c6h)/.test(compact)) return "glucose";
    if (/battery|circuit|switch|wire|current/.test(compact)) return "battery";
    return mapped;
  }

  function axis(v, max, fallback) {
    if (!Number.isFinite(v)) return fallback;
    if (Math.abs(v) <= 1.2) return v * max;
    return v;
  }

  function hasToken(text) {
    var lower = String(text || "").toLowerCase();
    for (var i = 1; i < arguments.length; i += 1) {
      if (lower.indexOf(String(arguments[i])) >= 0) return true;
    }
    return false;
  }

  function semanticHint(text) {
    var lower = String(text || "").toLowerCase();
    if (hasToken(lower, "battery")) return "battery";
    if (hasToken(lower, "wire", "wires")) return "wire";
    if (hasToken(lower, "switch")) return "switch";
    if (hasToken(lower, "bulb", "lamp", "light bulb")) return "bulb";
    if (hasToken(lower, "current")) return "arrow";
    if (hasToken(lower, "co2", "carbon dioxide")) return "co2";
    if (hasToken(lower, "oxygen", "o2")) return "oxygen";
    if (hasToken(lower, "water", "h2o")) return "waterdrop";
    if (hasToken(lower, "glucose", "sugar")) return "glucose";
    if (hasToken(lower, "leaf")) return "leaf";
    if (hasToken(lower, "root")) return "root";
    return null;
  }

  function resolveSceneDomain(scene, baseDomain) {
    var probe = {
      title: String((scene && scene.text) || ""),
      scenes: [{ text: String((scene && scene.text) || ""), actors: Array.isArray(scene && scene.actors) ? scene.actors : [] }]
    };
    var sceneDomain = detectDomain(probe);
    if (sceneDomain !== "generic" && sceneDomain !== baseDomain) return sceneDomain;
    if (baseDomain === "generic" && sceneDomain !== "generic") return sceneDomain;
    return baseDomain;
  }

  function sanitizeActorsForDomain(domain, actors, text) {
    if (!Array.isArray(actors)) return [];
    var allowed = DOMAIN_ALLOWED[domain];
    var sceneHint = semanticHint(text);
    var out = [];
    actors.forEach(function (raw) {
      var actor = Object.assign({}, raw || {});
      var type = resolveType(actor.type, actor.text);
      var hinted = semanticHint(actor.text);
      var finalType = hinted || ((sceneHint && (type === "star" || type === "sun")) ? sceneHint : type);
      var ok = !allowed || allowed.indexOf(finalType) >= 0 || finalType === "label" || finalType === "arrow" || finalType === "line";
      if (!ok) return;
      if (domain === "electric_circuit" && ["sun", "plant", "leaf", "root", "glucose", "co2", "oxygen", "waterdrop", "water", "cloud"].indexOf(finalType) >= 0) {
        return;
      }
      actor.type = finalType;
      out.push(actor);
    });
    return out;
  }

  function ensureDomainEssentials(domain, actors, text) {
    if (domain !== "electric_circuit") return Array.isArray(actors) ? actors : [];
    var out = Array.isArray(actors) ? actors.slice() : [];
    var present = {};
    out.forEach(function (a) { present[resolveType(a && a.type, a && a.text)] = true; });
    var fallback = inferActors(domain, text);
    ["battery", "wire", "switch", "bulb"].forEach(function (need) {
      if (present[need]) return;
      var candidate = fallback.find(function (a) { return resolveType(a.type, a.text) === need; });
      if (candidate) {
        out.push(candidate);
        present[need] = true;
      }
    });
    if (hasToken(text, "label", "labels", "parts")) {
      var hasLabel = out.some(function (a) { return resolveType(a && a.type, a && a.text) === "label"; });
      if (!hasLabel) {
        out.push(
          { type: "label", text: "Battery", x: 0.2, y: 0.62, size: 14, color: "#F8FAFC" },
          { type: "label", text: "Switch", x: 0.58, y: 0.24, size: 14, color: "#F8FAFC" },
          { type: "label", text: "Bulb", x: 0.84, y: 0.24, size: 14, color: "#F8FAFC" },
          { type: "label", text: "Wires", x: 0.46, y: 0.22, size: 14, color: "#F8FAFC" }
        );
      }
    }
    return out;
  }

  function autoLayoutActors(rawActors) {
    var list = Array.isArray(rawActors) ? rawActors : [];
    var counters = {};
    var placed = list.map(function (raw) {
      var actor = Object.assign({}, raw || {});
      actor.type = resolveType(actor.type, actor.text);
      counters[actor.type] = (counters[actor.type] || 0) + 1;
      var idx = counters[actor.type] - 1;
      var slot = DEFAULT_POS[actor.type] || DEFAULT_POS.label;
      var spreadX = idx === 0 ? 0 : (idx % 2 === 0 ? 1 : -1) * (Math.floor(idx / 2) + 1) * 42;
      var spreadY = idx === 0 ? 0 : (idx % 2 === 0 ? 1 : -1) * (Math.floor(idx / 2) + 1) * 18;
      var x = axis(actor.x, W, slot.x * W + spreadX);
      var y = axis(actor.y, H, slot.y * H + spreadY);
      var size = Number(actor.size);
      if (!Number.isFinite(size) || size <= 0) size = 40;
      if (size <= 1.2) size = size * Math.min(W, H);
      actor.size = clamp(size, 12, Math.min(W, H) * 0.42);
      actor.x = clamp(x, actor.size * 0.28 + 12, W - actor.size * 0.28 - 12);
      actor.y = clamp(y, actor.size * 0.28 + 12, H - actor.size * 0.22 - 12);
      actor.__explicitPos = Number.isFinite(raw && raw.x) && Number.isFinite(raw && raw.y);
      return actor;
    });

    var plant = placed.find(function (a) { return a && a.type === "plant"; });
    if (plant) {
      var leafIndex = 0;
      var rootIndex = 0;
      placed.forEach(function (actor) {
        if (!actor || actor.__explicitPos) return;
        if (actor.type === "leaf") {
          var sideL = leafIndex % 2 === 0 ? -1 : 1;
          var ringL = Math.floor(leafIndex / 2);
          actor.x = plant.x + sideL * (26 + ringL * 16);
          actor.y = plant.y - (88 + ringL * 12);
          leafIndex += 1;
        } else if (actor.type === "root") {
          var sideR = rootIndex % 2 === 0 ? -1 : 1;
          var ringR = Math.floor(rootIndex / 2);
          actor.x = plant.x + sideR * (10 + ringR * 12);
          actor.y = Math.min(H * 0.9, plant.y + 66 + ringR * 9);
          rootIndex += 1;
        } else if (actor.type === "waterdrop" || actor.type === "water") {
          actor.x = plant.x - 72;
          actor.y = Math.min(H * 0.88, plant.y + 46);
        } else if (actor.type === "co2") {
          actor.x = Math.max(plant.x + 130, W * 0.62);
          actor.y = plant.y - 110;
        } else if (actor.type === "glucose") {
          actor.x = plant.x + 78;
          actor.y = plant.y - 94;
        } else if (actor.type === "oxygen") {
          actor.x = plant.x + 86;
          actor.y = plant.y - 160;
        }
        actor.x = clamp(actor.x, actor.size * 0.28 + 12, W - actor.size * 0.28 - 12);
        actor.y = clamp(actor.y, actor.size * 0.28 + 12, H - actor.size * 0.22 - 12);
      });
    }

    for (var pass = 0; pass < 2; pass += 1) {
      for (var i = 0; i < placed.length; i += 1) {
        for (var j = i + 1; j < placed.length; j += 1) {
          var a = placed[i];
          var b = placed[j];
          if (!a || !b) continue;
          var dx = b.x - a.x;
          var dy = b.y - a.y;
          var dist = Math.sqrt(dx * dx + dy * dy) || 0.0001;
          var aR = Math.max(12, (a.size || 40) * 0.42);
          var bR = Math.max(12, (b.size || 40) * 0.42);
          var minDist = aR + bR + 10;
          if (dist >= minDist) continue;
          var overlap = (minDist - dist) / minDist;
          var nx = dx / dist;
          var ny = dy / dist;
          var push = overlap * 16;
          a.x -= nx * push * 0.5;
          a.y -= ny * push * 0.5;
          b.x += nx * push * 0.5;
          b.y += ny * push * 0.5;
          a.x = clamp(a.x, a.size * 0.28 + 12, W - a.size * 0.28 - 12);
          a.y = clamp(a.y, a.size * 0.28 + 12, H - a.size * 0.22 - 12);
          b.x = clamp(b.x, b.size * 0.28 + 12, W - b.size * 0.28 - 12);
          b.y = clamp(b.y, b.size * 0.28 + 12, H - b.size * 0.22 - 12);
        }
      }
    }

    return placed;
  }

  function resolveCognitiveMode(scene) {
    var raw = String(
      (scene && scene.meta && (scene.meta.cognitiveState || scene.meta.cognitive_state || scene.meta.state)) || ""
    ).toUpperCase();
    if (raw === "OVERLOAD") return "OVERLOAD";
    if (raw === "LOW" || raw === "LOW_LOAD" || raw === "LOWLOAD") return "LOW_LOAD";
    return "OPTIMAL";
  }

  function simplifyActorsForOverload(actors) {
    if (!Array.isArray(actors) || actors.length <= 5) return actors || [];
    var priority = {
      plant: 10, sun: 9, star: 9, root: 8, leaf: 8, waterdrop: 7, water: 7, co2: 7, oxygen: 7, glucose: 8,
      battery: 10, wire: 8, switch: 8, bulb: 9, arrow: 6, label: 3
    };
    return actors.slice().sort(function (a, b) {
      var ta = String((a && a.type) || "").toLowerCase();
      var tb = String((b && b.type) || "").toLowerCase();
      return (priority[tb] || 4) - (priority[ta] || 4);
    }).slice(0, 5);
  }

  function sceneAt(timeMs) {
    if (!state.script || !state.script.scenes.length) return null;
    for (var i = state.script.scenes.length - 1; i >= 0; i--) {
      if (timeMs >= state.script.scenes[i].startTime) return state.script.scenes[i];
    }
    return state.script.scenes[0];
  }

  function isLabelOnly(actors) {
    if (!actors || !actors.length) return true;
    return actors.every(function (a) { return !a || String(a.type || "label").toLowerCase() === "label"; });
  }

  function inferActors(domain, text) {
    var lower = String(text || "").toLowerCase();
    if (domain === "photosynthesis") {
      var out = [
        { type: "sun", x: W * 0.8, y: H * 0.14, size: 50, animation: "rotate" },
        { type: "plant", x: W * 0.24, y: H * 0.79, size: 96, animation: "sway" },
        { type: "root", x: W * 0.24, y: H * 0.86, size: 58, animation: "idle" },
      ];
      if (hasToken(lower, "water", "h2o", "root")) out.push({ type: "waterdrop", x: W * 0.16, y: H * 0.82, size: 30, animation: "float" });
      if (hasToken(lower, "co2", "carbon dioxide", "air")) out.push({ type: "co2", x: W * 0.74, y: H * 0.3, size: 34, animation: "drift" });
      if (hasToken(lower, "glucose", "sugar", "food")) out.push({ type: "glucose", x: W * 0.56, y: H * 0.44, size: 34, animation: "pulse" });
      if (hasToken(lower, "oxygen", "o2")) out.push({ type: "oxygen", x: W * 0.64, y: H * 0.22, size: 30, animation: "float" });
      return out;
    }
    if (domain === "water_cycle") {
      return [
        { type: "sun", x: W * 0.8, y: H * 0.16, size: 46, animation: "rotate" },
        { type: "cloud", x: W * 0.52, y: H * 0.2, size: 54, animation: "float" },
        { type: "waterdrop", x: W * 0.36, y: H * 0.72, size: 30, animation: "bounce" },
        { type: "waterdrop", x: W * 0.54, y: H * 0.72, size: 28, animation: "bounce" },
      ];
    }
    if (domain === "electric_circuit") {
      var openSwitch = hasToken(lower, "open switch", "incomplete", "does not light", "bulb does not light", "off");
      var closedSwitch = hasToken(lower, "closed switch", "complete circuit", "current flows", "light up", "lights", "on");
      var switchClosed = closedSwitch || !openSwitch;
      return [
        { type: "battery", x: W * 0.2, y: H * 0.5, size: 48, animation: "pulse" },
        { type: "wire", x: W * 0.5, y: H * 0.48, length: W * 0.62, color: "#FACC15", animation: "idle" },
        { type: "switch", x: W * 0.58, y: H * 0.32, size: 38, closed: switchClosed, animation: "idle" },
        { type: "bulb", x: W * 0.84, y: H * 0.32, size: 36, animation: switchClosed ? "glow" : "idle" },
        { type: "arrow", x: W * 0.3, y: H * 0.32, angle: 0, length: switchClosed ? W * 0.24 : W * 0.08, color: "#FACC15", animation: "drift" },
      ];
    }
    return [
      { type: "label", x: W * 0.5, y: H * 0.46, text: text || "Science concept" },
      { type: "arrow", x: W * 0.34, y: H * 0.56, angle: 0, length: W * 0.32 },
    ];
  }

  function drawBackground(domain, t) {
    var top = "#B5D9FF";
    var bottom = "#ECF6FF";
    var ground = "#7C5A45";
    if (domain === "photosynthesis") { top = "#A8E6A1"; bottom = "#DFF7D8"; ground = "#795548"; }
    else if (domain === "water_cycle") { top = "#9EDBFF"; bottom = "#E2F5FF"; ground = "#8D6E63"; }
    else if (domain === "food_chain") { top = "#C9EFA5"; bottom = "#F4FCE8"; ground = "#7F5539"; }
    else if (domain === "electric_circuit") { top = "#1E3A8A"; bottom = "#111827"; ground = ""; }
    else if (domain === "sound") { top = "#CFE8FF"; bottom = "#EFF6FF"; ground = ""; }
    else if (domain === "heat_transfer") { top = "#FFD6A5"; bottom = "#FFEFD5"; ground = ""; }

    var sky = ctx.createLinearGradient(0, 0, 0, H * 0.75);
    sky.addColorStop(0, top);
    sky.addColorStop(1, bottom);
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, W, H);

    if (ground) {
      var soil = ctx.createLinearGradient(0, H * 0.68, 0, H);
      soil.addColorStop(0, ground);
      soil.addColorStop(1, "#4E342E");
      ctx.fillStyle = soil;
      ctx.fillRect(0, H * 0.68, W, H * 0.32);
      ctx.fillStyle = "#5DBB63";
      ctx.fillRect(0, H * 0.68, W, 20);
    }

    if (domain === "electric_circuit") {
      ctx.save();
      ctx.strokeStyle = "rgba(255,255,255,0.08)";
      ctx.lineWidth = 1;
      var offset = (t * 18) % 40;
      for (var gx = -40; gx <= W + 40; gx += 40) {
        ctx.beginPath(); ctx.moveTo(gx + offset, 0); ctx.lineTo(gx + offset, H); ctx.stroke();
      }
      for (var gy = -40; gy <= H + 40; gy += 40) {
        ctx.beginPath(); ctx.moveTo(0, gy + offset); ctx.lineTo(W, gy + offset); ctx.stroke();
      }
      ctx.restore();
      return;
    }

    drawCloud(W * 0.14 + Math.sin(t * 0.25) * 20, H * 0.1, 1, 0.78);
    drawCloud(W * 0.68 + Math.cos(t * 0.22) * 16, H * 0.12, 0.85, 0.68);
  }

  function drawCloud(cx, cy, scale, alpha) {
    var r = 20 * scale;
    ctx.save(); ctx.globalAlpha = alpha; ctx.fillStyle = "#FFFFFF";
    [[0, 0, r], [r * 0.95, -r * 0.3, r * 0.82], [r * 1.9, 0, r * 0.9], [-r * 0.82, -r * 0.2, r * 0.72]].forEach(function (p) {
      ctx.beginPath(); ctx.arc(cx + p[0], cy + p[1], p[2], 0, Math.PI * 2); ctx.fill();
    });
    ctx.restore();
  }

  function drawArrow(x, y, angle, length, color, thickness, alpha) {
    if (length <= 0 || alpha <= 0) return;
    var ex = x + Math.cos(angle) * length;
    var ey = y + Math.sin(angle) * length;
    var head = Math.max(8, (thickness || 3) * 3.6);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = color || "#1565C0";
    ctx.lineWidth = thickness || 3;
    ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(ex, ey); ctx.stroke();
    ctx.fillStyle = color || "#1565C0";
    ctx.beginPath();
    ctx.moveTo(ex - Math.cos(angle - 0.42) * head, ey - Math.sin(angle - 0.42) * head);
    ctx.lineTo(ex, ey);
    ctx.lineTo(ex - Math.cos(angle + 0.42) * head, ey - Math.sin(angle + 0.42) * head);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function drawWaterDrop(x, y, r, alpha, color) {
    var rad = Math.max(3, r);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = color || "#29B6F6";
    ctx.strokeStyle = "#0288D1";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(x, y - rad * 1.4);
    ctx.bezierCurveTo(x + rad, y - rad * 0.3, x + rad, y + rad * 0.7, x, y + rad);
    ctx.bezierCurveTo(x - rad, y + rad * 0.7, x - rad, y - rad * 0.3, x, y - rad * 1.4);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  function drawSun(x, y, radius, t, alpha) {
    ctx.save();
    ctx.globalAlpha = alpha;
    for (var i = 0; i < 12; i++) {
      var ang = (i / 12) * Math.PI * 2 + t * 0.7;
      var ray = radius * 0.42 + Math.sin(t * 2 + i) * radius * 0.08;
      ctx.strokeStyle = "rgba(255,213,79,0.9)";
      ctx.lineWidth = 3;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(x + Math.cos(ang) * (radius + 2), y + Math.sin(ang) * (radius + 2));
      ctx.lineTo(x + Math.cos(ang) * (radius + ray), y + Math.sin(ang) * (radius + ray));
      ctx.stroke();
    }
    var grad = ctx.createRadialGradient(x - radius * 0.25, y - radius * 0.25, 1, x, y, radius);
    grad.addColorStop(0, "#FFF9C4");
    grad.addColorStop(0.5, "#FFE066");
    grad.addColorStop(1, "#FF9800");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawPlant(x, y, t, alpha, scale) {
    var s = Math.max(0.25, scale || 1);
    var sway = Math.sin(t * 1.4) * 5;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.strokeStyle = "#6D4C41";
    ctx.lineWidth = 9;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.bezierCurveTo(sway, -38, sway * 0.8, -84, sway * 1.35, -132);
    ctx.stroke();
    [[sway * 0.45 - 8, -78, -0.55, false], [sway * 0.85 + 8, -98, 0.58, true]].forEach(function (leaf) {
      ctx.save();
      ctx.translate(leaf[0], leaf[1]);
      ctx.rotate(leaf[2]);
      if (leaf[3]) ctx.scale(-1, 1);
      ctx.fillStyle = "#4CAF50";
      ctx.beginPath();
      ctx.moveTo(-46, 0);
      ctx.bezierCurveTo(-22, -22, 0, -10, 0, 0);
      ctx.bezierCurveTo(0, 10, -22, 22, -46, 0);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    });
    ctx.restore();
  }

  function drawCO2(x, y, r, alpha) {
    var radius = Math.max(4, r);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = "#CFD8DC";
    ctx.strokeStyle = "#78909C";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#455A64";
    ctx.font = "bold " + Math.max(9, radius * 0.58) + "px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("CO2", x, y);
    ctx.restore();
  }

  function drawO2(x, y, r, alpha) {
    var radius = Math.max(4, r);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = "#D6F5DD";
    ctx.strokeStyle = "#2E7D32";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#2E7D32";
    ctx.font = "bold " + Math.max(8, radius * 0.72) + "px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("O2", x, y);
    ctx.restore();
  }

  function drawGlucose(x, y, r, alpha, t) {
    var radius = Math.max(6, r);
    var p = 1 + Math.sin(t * 1.8) * 0.06;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(x, y);
    ctx.scale(p, p);
    ctx.fillStyle = "#FB923C";
    ctx.strokeStyle = "#E65100";
    ctx.lineWidth = 2.3;
    ctx.beginPath();
    for (var i = 0; i < 6; i++) {
      var ang = (i / 6) * Math.PI * 2 - Math.PI / 6;
      var px = Math.cos(ang) * radius;
      var py = Math.sin(ang) * radius;
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  function drawBolt(x, y, size, alpha, color) {
    var s = Math.max(4, size);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = color || "#A855F7";
    ctx.beginPath();
    ctx.moveTo(x + s * 0.25, y - s);
    ctx.lineTo(x - s * 0.3, y + s * 0.08);
    ctx.lineTo(x + s * 0.08, y + s * 0.08);
    ctx.lineTo(x - s * 0.25, y + s);
    ctx.lineTo(x + s * 0.36, y - s * 0.04);
    ctx.lineTo(x - s * 0.04, y - s * 0.04);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function drawRock(x, y, r, alpha, color) {
    var radius = Math.max(6, r);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = color || "#795548";
    ctx.strokeStyle = "#5D4037";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x - radius, y + radius * 0.3);
    ctx.lineTo(x - radius * 0.55, y - radius);
    ctx.lineTo(x + radius * 0.34, y - radius * 0.82);
    ctx.lineTo(x + radius, y + radius * 0.05);
    ctx.lineTo(x + radius * 0.56, y + radius);
    ctx.lineTo(x - radius * 0.5, y + radius);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  function drawPlanet(x, y, r, alpha, color) {
    var radius = Math.max(8, r);
    ctx.save();
    ctx.globalAlpha = alpha;
    var grad = ctx.createRadialGradient(x - radius * 0.3, y - radius * 0.3, 1, x, y, radius);
    grad.addColorStop(0, "#9ED4FF");
    grad.addColorStop(0.7, color || "#42A5F5");
    grad.addColorStop(1, "#1565C0");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawLabel(text, x, y, alpha, color) {
    if (!text) return;
    var fs = 13;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.font = "600 " + fs + "px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    var w = Math.max(90, ctx.measureText(text).width + 24);
    var h = fs + 16;
    ctx.fillStyle = "rgba(255,255,255,0.94)";
    if (ctx.roundRect) {
      ctx.beginPath(); ctx.roundRect(x - w * 0.5, y - h * 0.5, w, h, h * 0.5); ctx.fill();
    } else {
      ctx.fillRect(x - w * 0.5, y - h * 0.5, w, h);
    }
    ctx.strokeStyle = "rgba(37,99,235,0.25)";
    ctx.lineWidth = 1.5;
    if (ctx.roundRect) {
      ctx.beginPath(); ctx.roundRect(x - w * 0.5, y - h * 0.5, w, h, h * 0.5); ctx.stroke();
    } else {
      ctx.strokeRect(x - w * 0.5, y - h * 0.5, w, h);
    }
    ctx.fillStyle = color || "#1E3A8A";
    ctx.fillText(text, x, y);
    ctx.restore();
  }

  function actorMotion(actor, t, index) {
    var anim = String(actor.animation || "idle").toLowerCase();
    var phase = index * 0.8;
    var dx = 0, dy = 0, scale = 1;
    if (anim === "sway" || anim === "float") { dx = Math.sin((t + phase) * 1.1) * 4.5; dy = Math.sin((t + phase) * 0.7) * 2.8; }
    else if (anim === "pulse" || anim === "glow") { scale = 1 + Math.sin((t + phase) * 1.6) * 0.06; }
    else if (anim === "bounce") { dy = -Math.abs(Math.sin((t + phase) * 2.8) * 10); }
    else if (anim === "drift") { dx = Math.sin((t + phase) * 0.72) * 8; dy = Math.sin((t + phase) * 0.5) * 5; }
    else { dy = Math.sin((t + phase) * 0.55) * 2; }
    return { dx: dx, dy: dy, scale: scale };
  }

  function drawActor(actor, alpha, t, index) {
    var m = actorMotion(actor, t, index);
    var x = actor.x + m.dx;
    var y = actor.y + m.dy;
    var size = (actor.size || 40) * m.scale;
    var type = actor.type;

    if (type === "sun") drawSun(x, y, size, t, alpha);
    else if (type === "plant" || type === "tree") drawPlant(x, y, t, alpha, size / 100);
    else if (type === "leaf") {
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.fillStyle = "#4CAF50";
      ctx.strokeStyle = "#2E7D32";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x - size * 0.5, y);
      ctx.bezierCurveTo(x - size * 0.2, y - size * 0.32, x + size * 0.2, y - size * 0.32, x + size * 0.5, y);
      ctx.bezierCurveTo(x + size * 0.2, y + size * 0.32, x - size * 0.2, y + size * 0.32, x - size * 0.5, y);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    }
    else if (type === "root") {
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = actor.color || "#6D4C41";
      ctx.lineWidth = 3.5;
      [[-40, 46], [-16, 56], [12, 58], [36, 46]].forEach(function (r) {
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + r[0], y + r[1]);
        ctx.stroke();
      });
      ctx.restore();
    }
    else if (type === "cloud") drawCloud(x, y, size / 24, alpha);
    else if (type === "waterdrop" || type === "water") drawWaterDrop(x, y, size * 0.5, alpha, actor.color || "#29B6F6");
    else if (type === "co2") drawCO2(x, y, size * 0.52, alpha);
    else if (type === "o2" || type === "oxygen") drawO2(x, y, size * 0.52, alpha);
    else if (type === "molecule") {
      var mType = String(actor.moleculeType || (actor.extra && actor.extra.moleculeType) || "").toLowerCase();
      if (mType.indexOf("co2") >= 0 || mType.indexOf("carbon") >= 0) drawCO2(x, y, size * 0.52, alpha);
      else if (mType.indexOf("oxygen") >= 0 || mType === "o2") drawO2(x, y, size * 0.52, alpha);
      else if (mType.indexOf("glucose") >= 0 || mType.indexOf("sugar") >= 0) drawGlucose(x, y, size * 0.56, alpha, t);
      else drawWaterDrop(x, y, size * 0.5, alpha, actor.color || "#29B6F6");
    }
    else if (type === "glucose") drawGlucose(x, y, size * 0.56, alpha, t);
    else if (type === "bolt" || type === "energy") drawBolt(x, y, size * 0.56, alpha, actor.color || "#A855F7");
    else if (type === "rock") drawRock(x, y, size * 0.52, alpha, actor.color || "#795548");
    else if (type === "planet" || type === "earth") drawPlanet(x, y, size * 0.56, alpha, actor.color || "#42A5F5");
    else if (type === "battery") {
      ctx.save();
      ctx.globalAlpha = alpha;
      var bw = Math.max(34, size * 1.2);
      var bh = bw * 0.54;
      var bx = x - bw * 0.5;
      var by = y - bh * 0.5;
      ctx.fillStyle = "#334155";
      if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 6); ctx.fill(); }
      else { ctx.fillRect(bx, by, bw, bh); }
      ctx.fillStyle = "#FACC15";
      if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(bx + bw * 0.1, by + bh * 0.2, bw * 0.56, bh * 0.6, 4); ctx.fill(); }
      else { ctx.fillRect(bx + bw * 0.1, by + bh * 0.2, bw * 0.56, bh * 0.6); }
      ctx.fillStyle = "#E2E8F0";
      ctx.fillRect(bx + bw + 2, by + bh * 0.32, 6, bh * 0.36);
      ctx.restore();
    }
    else if (type === "switch") {
      ctx.save();
      ctx.globalAlpha = alpha;
      var sw = Math.max(32, size);
      var sh = sw * 0.44;
      var sx = x - sw * 0.5;
      var sy = y - sh * 0.5;
      ctx.fillStyle = "rgba(226,232,240,0.8)";
      if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(sx, sy, sw, sh, sh * 0.5); ctx.fill(); }
      else { ctx.fillRect(sx, sy, sw, sh); }
      ctx.fillStyle = actor.closed === false ? "#94A3B8" : "#FACC15";
      ctx.beginPath();
      ctx.arc(x + (actor.closed === false ? -sw * 0.16 : sw * 0.16), y, sh * 0.34, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
    else if (type === "wire") {
      var w = Math.max(120, Number(actor.length) > 0 ? (Number(actor.length) <= 1.2 ? Number(actor.length) * Math.min(W, H) : Number(actor.length)) : W * 0.62);
      var h = Math.max(70, w * 0.44);
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = actor.color || "#FACC15";
      ctx.lineWidth = 3;
      if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(x - w * 0.5, y - h * 0.5, w, h, 18); ctx.stroke(); }
      else { ctx.strokeRect(x - w * 0.5, y - h * 0.5, w, h); }
      ctx.restore();
    }
    else if (type === "wave") {
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = actor.color || "#1D4ED8";
      ctx.lineWidth = 2;
      for (var wi = 0; wi < 3; wi++) {
        ctx.beginPath();
        ctx.arc(x, y, size * (0.45 + wi * 0.26), -0.7, 0.7);
        ctx.stroke();
      }
      ctx.restore();
    }
    else if (type === "arrow") {
      var rawLen = Number(actor.length);
      var len = Number.isFinite(rawLen) && rawLen > 0 ? rawLen : 120;
      if (len <= 1.2) len = len * Math.min(W, H);
      drawArrow(x, y, Number(actor.angle) || 0, len, actor.color || "#1565C0", actor.thickness || 3, alpha);
    }
    else drawLabel(String(actor.text || actor.type || "Concept"), x, y, alpha, actor.color || "#1E3A8A");
  }

  function drawActors(actors, elapsed, t) {
    var list = actors || [];
    list.forEach(function (actor, index) {
      var start = index * 180;
      var base = fadeIn(elapsed, start, 520);
      var alpha = base;
      if (Array.isArray(actor.timeline) && actor.timeline.length) {
        var tl = actor.timeline.filter(function (s) { return s && Number.isFinite(s.at); }).sort(function (a, b) { return a.at - b.at; });
        var current = null, next = null;
        for (var i = 0; i < tl.length; i++) {
          if (elapsed >= tl[i].at) { current = tl[i]; next = tl[i + 1] || null; } else { next = tl[i]; break; }
        }
        if (current && typeof current.alpha === "number") {
          if (next && typeof next.alpha === "number" && next.at > current.at) {
            var m = easeOut((elapsed - current.at) / (next.at - current.at));
            alpha = alpha * lerp(current.alpha, next.alpha, m);
          } else alpha = alpha * current.alpha;
        }
      }
      if (alpha > 0.005) drawActor(actor, alpha, t, index);
    });
  }

  function processSteps(domain, text) {
    if (domain === "photosynthesis") {
      var lower = String(text || "").toLowerCase();
      var includeWater = hasToken(lower, "water", "root", "h2o");
      var includeCo2 = hasToken(lower, "co2", "carbon dioxide", "air");
      var includeGlucose = hasToken(lower, "glucose", "food", "sugar");
      var includeOxygen = hasToken(lower, "oxygen", "o2", "release");
      var steps = [];
      var stepNum = 1;
      function pushStep(label, draw) {
        steps.push({ label: "Step " + (stepNum++) + ": " + label, draw: draw });
      }
      pushStep("Plant and Sun appear", function (p, t, s) { drawPlant(W * 0.26, H * 0.78, t, p * s, 0.6 + p * 0.4); drawSun(W * 0.8, H * 0.14, 48 * p, t, p * s); });
      pushStep("Light rays move to leaf", function (p, _t, s) { drawArrow(W * 0.7, H * 0.23, Math.PI - 0.55, W * 0.24 * p, "#F59E0B", 3, p * s); });
      if (includeWater) pushStep("Water moves upward", function (p, _t, s) { var y = lerp(H * 0.84, H * 0.46, easeOut(p)); drawWaterDrop(W * 0.26, y, 12, p * s, "#0288D1"); });
      if (includeCo2) pushStep("CO2 enters the leaf", function (p, _t, s) { var x = lerp(W * 0.76, W * 0.4, easeOut(p)); drawCO2(x, H * 0.3, 22, p * s); });
      pushStep("Energy conversion", function (p, _t, s) { drawBolt(W * 0.44, H * 0.4, 30 * p, p * s, "#8B5CF6"); });
      if (includeGlucose) pushStep("Glucose appears", function (p, t, s) { drawGlucose(W * 0.56, H * 0.44, 28 * p, p * s, t); });
      if (includeOxygen) pushStep("Oxygen exits plant", function (p, _t, s) { var x = lerp(W * 0.42, W * 0.68, easeOut(p)); var y = lerp(H * 0.38, H * 0.22, easeOut(p)); drawO2(x, y, 17, p * s); });
      return steps;
    }
    if (domain === "water_cycle") {
      return [
        { label: "Step 1: Sun heats water", draw: function (p, t, s) { drawSun(W * 0.78, H * 0.16, 44 * p, t, p * s); } },
        { label: "Step 2: Evaporation rises", draw: function (p, _t, s) { drawArrow(W * 0.44, H * 0.72, -Math.PI / 2, H * 0.28 * p, "#0288D1", 3, p * s); } },
        { label: "Step 3: Cloud forms", draw: function (p, _t, s) { drawCloud(W * 0.5, H * 0.2, 1.2 * p, p * s); } },
        { label: "Step 4: Rain falls", draw: function (p, _t, s) { for (var i = 0; i < 5; i++) { var x = W * 0.35 + i * W * 0.07; var y = lerp(H * 0.3, H * 0.72, easeOut(p)); drawWaterDrop(x, y, 10, p * s * (1 - i * 0.08), "#29B6F6"); } } },
        { label: "Step 5: Collection", draw: function (p, _t, s) { drawArrow(W * 0.2, H * 0.86, 0, W * 0.6 * p, "#0288D1", 3, p * s); } },
      ];
    }
    if (domain === "electric_circuit") {
      var lowerCircuit = String(text || "").toLowerCase();
      var openSwitchStep = hasToken(lowerCircuit, "open switch", "incomplete", "does not light", "off");
      var closedSwitchStep = hasToken(lowerCircuit, "closed switch", "complete circuit", "current flows", "light up", "on");
      var switchClosedStep = closedSwitchStep || !openSwitchStep;
      return [
        { label: "Step 1: Battery connects to wire loop", draw: function (p, _t, s) { drawArrow(W * 0.28, H * 0.32, 0, W * 0.18 * p, "#FACC15", 4, p * s); } },
        { label: "Step 2: Switch state is shown", draw: function (p, _t, s) { ctx.save(); ctx.globalAlpha = p * s; ctx.strokeStyle = "#CBD5E1"; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(W * 0.56, H * 0.32); ctx.lineTo(W * 0.62, switchClosedStep ? H * 0.32 : lerp(H * 0.26, H * 0.32, p)); ctx.stroke(); ctx.restore(); } },
        { label: switchClosedStep ? "Step 3: Current flows through circuit" : "Step 3: Current is blocked by open switch", draw: function (p, _t, s) { drawArrow(W * 0.3, H * 0.32, 0, (switchClosedStep ? W * 0.34 : W * 0.1) * p, "#FACC15", 4, p * s); } },
        { label: switchClosedStep ? "Step 4: Bulb lights up" : "Step 4: Bulb stays off", draw: function (p, t, s) { ctx.save(); ctx.globalAlpha = p * s; ctx.fillStyle = switchClosedStep ? ("rgba(250,204,21," + (0.18 + Math.max(0, Math.sin(t * 8)) * 0.38 * p) + ")") : "rgba(148,163,184,0.16)"; ctx.beginPath(); ctx.arc(W * 0.84, H * 0.32, 34, 0, Math.PI * 2); ctx.fill(); ctx.restore(); } },
      ];
    }
    if (domain === "sound") {
      return [
        { label: "Step 1: Source vibrates", draw: function (p, t, s) { var vib = Math.sin(t * 20) * 6 * p; ctx.save(); ctx.globalAlpha = p * s; ctx.strokeStyle = "#1D4ED8"; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(W * 0.2, H * 0.42 + vib); ctx.lineTo(W * 0.2, H * 0.58 - vib); ctx.stroke(); ctx.restore(); } },
        { label: "Step 2: Waves spread", draw: function (p, _t, s) { ctx.save(); ctx.globalAlpha = p * s; ctx.strokeStyle = "#1D4ED8"; ctx.lineWidth = 2; for (var i = 0; i < 4; i++) { var r = (i + 1) * (24 + p * 8); ctx.beginPath(); ctx.arc(W * 0.24, H * 0.5, r, -0.7, 0.7); ctx.stroke(); } ctx.restore(); } },
        { label: "Step 3: Waves reach ear", draw: function (p, _t, s) { drawArrow(W * 0.42, H * 0.5, 0, W * 0.28 * p, "#1D4ED8", 3, p * s); } },
        { label: "Step 4: Hearing signal", draw: function (p, _t, s) { drawBolt(W * 0.9, H * 0.46, 20 * p, p * s, "#2563EB"); } },
      ];
    }
    if (domain === "heat_transfer") {
      return [
        { label: "Step 1: Heat source", draw: function (p, t, s) { drawSun(W * 0.24, H * 0.5, 40 * p, t, p * s); } },
        { label: "Step 2: Heat transfer", draw: function (p, _t, s) { drawArrow(W * 0.34, H * 0.5, 0, W * 0.34 * p, "#EA580C", 4, p * s); } },
        { label: "Step 3: Effect on object", draw: function (p, _t, s) { drawRock(W * 0.78, H * 0.54, 24, p * s, "#9CA3AF"); drawBolt(W * 0.78, H * 0.46, 24 * p, p * s, "#EA580C"); } },
      ];
    }
    var short = String(text || "Science concept");
    if (short.length > 40) short = short.slice(0, 40) + "...";
    return [
      { label: short, draw: function (p, _t, s) { drawLabel("Key idea", W * 0.5, H * 0.46, p * s, "#1E3A8A"); } },
      { label: "Observe and explain", draw: function (p, _t, s) { drawArrow(W * 0.32, H * 0.56, 0, W * 0.36 * p, "#2563EB", 3, p * s); } },
    ];
  }

  function drawCaption(sceneText, stepLabel, elapsed) {
    var text = stepLabel || sceneText;
    if (!text) return;
    var alpha = fadeIn(elapsed, 80, 420);
    if (alpha <= 0.01) return;
    var barH = 46;
    var barY = H - barH - 10;
    var barX = W * 0.04;
    var barW = W * 0.92;
    ctx.save();
    ctx.globalAlpha = alpha;
    var grad = ctx.createLinearGradient(0, barY, 0, barY + barH);
    grad.addColorStop(0, "rgba(15,23,42,0.62)");
    grad.addColorStop(1, "rgba(2,6,23,0.9)");
    ctx.fillStyle = grad;
    if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(barX, barY, barW, barH, 12); ctx.fill(); }
    else { ctx.fillRect(barX, barY, barW, barH); }
    ctx.fillStyle = "#FFFFFF";
    ctx.font = "600 14px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    var maxW = barW - 36;
    var out = text;
    while (ctx.measureText(out).width > maxW && out.length > 12) out = out.slice(0, -4) + "...";
    ctx.fillText(out, barX + barW * 0.5, barY + barH * 0.5);
    ctx.restore();
  }

  function renderFrame() {
    if (!state.script) { ctx.clearRect(0, 0, W, H); return; }
    var scene = sceneAt(state.t);
    if (!scene) return;

    var elapsed = Math.max(0, state.t - scene.startTime);
    var time = elapsed * 0.001;
    var duration = scene.duration || 6000;
    var cognitiveMode = resolveCognitiveMode(scene);
    var overload = cognitiveMode === "OVERLOAD";
    var sceneDomain = resolveSceneDomain(scene, state.domain);

    ctx.clearRect(0, 0, W, H);
    drawBackground(sceneDomain, time);

    var actors = Array.isArray(scene.actors) ? scene.actors : [];
    actors = sanitizeActorsForDomain(sceneDomain, actors, scene.text || "");
    if (isLabelOnly(actors) || !actors.length) actors = inferActors(sceneDomain, scene.text);
    actors = ensureDomainEssentials(sceneDomain, actors, scene.text || "");
    if (overload) actors = simplifyActorsForOverload(actors);
    actors = actors.map(function (actor, index) {
      var a = Object.assign({}, actor || {});
      if (!Array.isArray(a.timeline) || !a.timeline.length) {
        var start = Math.min(index * 280, 1800);
        a.timeline = [{ at: start, alpha: 0 }, { at: start + (overload ? 760 : 600), alpha: 1 }];
      }
      return a;
    });
    actors = autoLayoutActors(actors);

    drawActors(actors, elapsed, time);

    var steps = processSteps(sceneDomain, scene.text || "");
    var windowMs = overload
      ? Math.max(1100, duration / Math.max(1, steps.length * 0.82))
      : Math.max(900, duration / (steps.length + 0.5));
    var idx = Math.min(steps.length - 1, Math.floor(elapsed / windowMs));
    var local = clamp01((elapsed - idx * windowMs) / (windowMs * (overload ? 0.72 : 0.78)));
    var stepStrength = isLabelOnly(scene.actors) ? 1 : (overload ? 0.84 : 0.68);
    for (var i = 0; i < idx; i++) {
      var linger = overload ? 0.32 : 0.68;
      steps[i].draw(1, time, stepStrength * linger);
    }
    steps[idx].draw(easeOut(local), time, stepStrength);
    drawCaption(scene.text || "", steps[idx].label, elapsed);
  }

  function tick(ts) {
    requestAnimationFrame(tick);
    if (state.playing && state.script && state.lastTs != null) {
      state.t = Math.min(state.t + (ts - state.lastTs) * state.rate, state.script.duration || 0);
      if (state.t >= (state.script.duration || 0)) {
        state.playing = false;
        post({ completed: true });
      }
    }
    state.lastTs = state.playing ? ts : null;
    renderFrame();
  }

  window.__anim = function (payload) {
    try {
      var msg = typeof payload === "string" ? JSON.parse(payload) : payload;
      if (!msg || typeof msg !== "object") return;
      if (msg.type === "init") {
        state.script = normalize(msg.script);
        state.domain = detectDomain(state.script);
        state.playing = !!msg.isPlaying;
        state.rate = Number(msg.rate) > 0 ? Number(msg.rate) : 1;
        state.t = Number.isFinite(msg.t) ? Math.max(0, Math.min(msg.t, state.script.duration || 0)) : 0;
        state.lastTs = null;
      } else if (msg.type === "play") {
        state.playing = !!msg.v;
        if (!state.playing) state.lastTs = null;
      } else if (msg.type === "rate") {
        state.rate = Number(msg.v) > 0 ? Number(msg.v) : 1;
      } else if (msg.type === "seek") {
        var max = state.script ? state.script.duration || 0 : 0;
        state.t = Math.max(0, Math.min(Number(msg.t) || 0, max));
      }
    } catch (err) {
      post({ debug: String(err && err.message ? err.message : err) });
    }
  };

  window.addEventListener("resize", resizeCanvas);
  resizeCanvas();
  requestAnimationFrame(tick);
  post({ ready: true });
})();\n`;

function makeHtml() {
  return `<!doctype html><html><head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no\" /><style>*{box-sizing:border-box;margin:0;padding:0}html,body{width:100%;height:100%;overflow:hidden;background:#0f172a}canvas{width:100%;height:100%;display:block;touch-action:none}</style></head><body><canvas id=\"c\"></canvas><script>${ANIM_JS}</script></body></html>`;
}

function inject(payload: object): string {
  return `(function(){if(typeof window.__anim==='function'){window.__anim(${JSON.stringify(
    JSON.stringify(payload),
  )});}})();true;`;
}

export function AnimationCanvasWebView({
  isPlaying,
  script,
  currentTimeMs,
  playbackRate = 1,
}: Props) {
  const webViewRef = useRef<WebView>(null);
  const readyRef = useRef(false);
  const prevTimeRef = useRef<number | undefined>(undefined);
  const htmlRef = useRef(makeHtml());

  const sendInit = (webView: WebView) => {
    webView.injectJavaScript(
      inject({
        type: "init",
        script,
        isPlaying,
        t: currentTimeMs ?? 0,
        rate: playbackRate,
      }),
    );
    readyRef.current = true;
  };

  useEffect(() => {
    if (!webViewRef.current || !script) return;
    sendInit(webViewRef.current);
  }, [script]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!webViewRef.current || !readyRef.current) return;
    webViewRef.current.injectJavaScript(inject({ type: "play", v: isPlaying }));
  }, [isPlaying]);

  useEffect(() => {
    if (!webViewRef.current || !readyRef.current) return;
    webViewRef.current.injectJavaScript(inject({ type: "rate", v: playbackRate }));
  }, [playbackRate]);

  useEffect(() => {
    if (!webViewRef.current || !readyRef.current || currentTimeMs == null) return;
    const previous = prevTimeRef.current;
    prevTimeRef.current = currentTimeMs;
    if (
      !isPlaying ||
      previous == null ||
      currentTimeMs < previous ||
      Math.abs(currentTimeMs - previous) > 300
    ) {
      webViewRef.current.injectJavaScript(inject({ type: "seek", t: currentTimeMs }));
    }
  }, [currentTimeMs, isPlaying]);

  return (
    <View style={styles.root}>
      <WebView
        ref={webViewRef}
        originWhitelist={["*"]}
        source={{ html: htmlRef.current }}
        style={styles.webview}
        scrollEnabled={false}
        bounces={false}
        javaScriptEnabled
        onLoadEnd={() => {
          if (script && webViewRef.current) sendInit(webViewRef.current);
        }}
        onMessage={(event) => {
          try {
            const payload = JSON.parse(event.nativeEvent.data ?? "{}");
            if (payload.ready && script && webViewRef.current) {
              sendInit(webViewRef.current);
            }
            if (__DEV__ && payload.debug) {
              console.log("[AnimationWebView]", payload.debug);
            }
          } catch {
            // no-op
          }
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    borderRadius: 20,
    overflow: "hidden",
    backgroundColor: "#0F172A",
  },
  webview: {
    flex: 1,
    backgroundColor: "transparent",
  },
});

declare let __DEV__: boolean;

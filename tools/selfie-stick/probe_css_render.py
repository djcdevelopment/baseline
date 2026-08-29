#!/usr/bin/env python3
"""R&D probe: can frozen world-save geometry become literal CSS 3-D?

This is deliberately not another architecture viewer.  It takes the already-proved
ZDO positions, deg_unity rotations, and prefab oriented-box geometry through one
browser-native vertical slice: one DOM group and six CSS faces per piece.  JavaScript
creates the DOM and moves the camera; CSS perspective and matrix3d do the projection.
There is no canvas, SVG, WebGL, Three.js, or network dependency.

The visual pilot is the largest physically connected component of cluster 1820.  If
that passes the mechanical browser gate, spatially coherent prefixes of cluster 182
are rendered until the first DOM/compositor edge.  All generated coordinates are
cluster-local; absolute world positions never enter the HTML.

Usage:
  python probe_css_render.py
  python probe_css_render.py --no-browser
  python probe_css_render.py --stress-tiers 1500,3000,5000
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
from collections import Counter
from pathlib import Path

import duckdb
import numpy as np

from reconstruct_cluster import BOX_CORNERS, FAMILY_COLORS, euler_matrix, load_geometry
from segment_buildings import segment
from verify_rotation import HYPOTHESES


HERE = Path(__file__).resolve().parent
ARCH = HERE / "out" / "era17" / "arch"
DEFAULT_CLUSTER_POINTS = Path(r"E:\omen\steward-era17-arch\cluster-zdos.parquet")
DEFAULT_BUILDING_GEOMETRY = Path(
    r"E:\omen\steward-era17-arch\building-geometry.parquet"
)
DEFAULT_OUT = HERE / "out" / "era17" / "css-render"
MIN_CSS_THICKNESS_M = 0.01


HTML_TEMPLATE = r'''<!doctype html>
<html lang="en" data-benchmark-done="false">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>World bytes → CSS 3-D</title>
<style>
  :root { color-scheme: dark; --slate:#101418; --panel:#181e23; --ink:#e7edf1;
    --muted:#92a0aa; --ochre:#d79a3b; --line:#34414a; }
  * { box-sizing:border-box; }
  html,body { width:100%; height:100%; margin:0; overflow:hidden; background:var(--slate);
    color:var(--ink); font:14px/1.35 system-ui,-apple-system,"Segoe UI",sans-serif; }
  body { display:grid; grid-template-columns:292px minmax(0,1fr); }
  aside { position:relative; z-index:10; padding:22px 20px; overflow:auto;
    background:linear-gradient(155deg,#1d2429,#12171b 72%); border-right:1px solid var(--line); }
  .eyebrow { color:var(--ochre); font:700 11px/1.2 ui-monospace,monospace;
    letter-spacing:.14em; text-transform:uppercase; }
  h1 { margin:8px 0 5px; font-size:23px; font-weight:590; letter-spacing:-.03em; }
  .sub { color:var(--muted); margin-bottom:18px; }
  .metric { display:grid; grid-template-columns:1fr auto; gap:4px 12px; padding:9px 0;
    border-top:1px solid var(--line); }
  .metric span { color:var(--muted); } .metric output { font-family:ui-monospace,monospace; }
  .section { margin-top:18px; }
  .label { display:block; margin-bottom:7px; color:var(--muted); font-size:11px;
    font-weight:700; letter-spacing:.1em; text-transform:uppercase; }
  .row { display:flex; flex-wrap:wrap; gap:6px; }
  button { appearance:none; border:1px solid #47545c; border-radius:3px; padding:6px 9px;
    background:#20282e; color:var(--ink); cursor:pointer; }
  button:hover,button[aria-pressed="true"] { border-color:var(--ochre); color:#ffd58d; }
  #families { display:grid; grid-template-columns:1fr 1fr; gap:5px 10px; }
  #families label { display:flex; min-width:0; align-items:center; gap:6px; color:#c6d0d6; }
  #families i { width:9px; height:9px; flex:0 0 auto; background:var(--swatch); }
  #families small { color:var(--muted); margin-left:auto; }
  #status { margin-top:17px; color:#aebac1; font:11px/1.45 ui-monospace,monospace; }
  main { position:relative; min-width:0; overflow:hidden; cursor:grab; perspective:1400px;
    perspective-origin:50% 47%; background:
      radial-gradient(circle at 50% 46%,rgba(91,116,128,.13),transparent 44%),
      linear-gradient(rgba(255,255,255,.022) 1px,transparent 1px),
      linear-gradient(90deg,rgba(255,255,255,.022) 1px,transparent 1px);
    background-size:auto,40px 40px,40px 40px; }
  main:active { cursor:grabbing; }
  #world { position:absolute; left:50%; top:50%; width:0; height:0;
    transform-style:preserve-3d; will-change:transform; }
  .piece { position:absolute; left:0; top:0; width:0; height:0;
    transform-style:preserve-3d; }
  .face { position:absolute; display:block; transform-style:preserve-3d;
    border:1px solid color-mix(in srgb,var(--piece-color),white 28%);
    backface-visibility:visible; }
  body[data-mode="wire"] .face { background:transparent; opacity:.7; }
  body[data-mode="solid"] .face {
    background:color-mix(in srgb,var(--piece-color) 30%,transparent); opacity:.82; }
  .floor-grid { position:absolute; left:50%; top:50%; width:900px; height:900px;
    transform-style:preserve-3d; transform:translate(-50%,-50%) rotateX(90deg) translateZ(-180px);
    background:linear-gradient(rgba(215,154,59,.11) 1px,transparent 1px),
      linear-gradient(90deg,rgba(215,154,59,.11) 1px,transparent 1px);
    background-size:40px 40px; border:1px solid rgba(215,154,59,.2); pointer-events:none; }
  #benchmarkReceipt { display:none; }
  .hint { position:absolute; right:15px; bottom:12px; color:#71808a; font:11px ui-monospace,monospace; }
  @media (max-width:780px) { body { grid-template-columns:220px minmax(0,1fr); }
    aside { padding:15px 13px; } #families { grid-template-columns:1fr; } }
</style>
</head>
<body data-mode="wire">
<aside>
  <div class="eyebrow">Buildings from bytes / CSS probe</div>
  <h1 id="title">World-save massing</h1>
  <div class="sub" id="subtitle"></div>
  <div class="metric"><span>pieces</span><output id="pieceCount">—</output></div>
  <div class="metric"><span>CSS faces</span><output id="faceCount">—</output></div>
  <div class="metric"><span>DOM nodes</span><output id="nodeCount">—</output></div>
  <div class="section"><span class="label">Surface</span><div class="row">
    <button type="button" data-mode="wire" aria-pressed="true">Wireframe</button>
    <button type="button" data-mode="solid" aria-pressed="false">Translucent solid</button>
  </div></div>
  <div class="section"><span class="label">Known views</span><div class="row">
    <button type="button" data-view="iso">Isometric</button>
    <button type="button" data-view="end-a">78.8° end</button>
    <button type="button" data-view="end-b">258.8° end</button>
  </div></div>
  <div class="section"><span class="label">Families</span><div id="families"></div></div>
  <div id="status">building DOM…</div>
</aside>
<main id="stage" aria-label="Interactive CSS 3-D reconstruction">
  <div id="world"><div class="floor-grid"></div></div>
  <div class="hint">drag to orbit · wheel to zoom</div>
</main>
<pre id="benchmarkReceipt">pending</pre>
<script id="geometry" type="application/json">__GEOMETRY__</script>
<script>
(() => {
  'use strict';
  const buildStarted = performance.now();
  const DATA = JSON.parse(document.getElementById('geometry').textContent);
  const UNIT = 10;
  const world = document.getElementById('world');
  const stage = document.getElementById('stage');
  const status = document.getElementById('status');
  const familyBox = document.getElementById('families');
  const familyCounts = new Map();
  let yaw = -35, pitch = -28, zoomFactor = 1, fitScale = 1;

  function cssMatrix(piece) {
    const r = piece.r, p = piece.p;
    const v = [r[0],r[3],r[6],0, r[1],r[4],r[7],0, r[2],r[5],r[8],0,
      p[0]*UNIT,p[1]*UNIT,p[2]*UNIT,1];
    return `matrix3d(${v.join(',')})`;
  }

  function addFace(group, width, height, transform, side) {
    const face = document.createElement('i');
    face.className = `face ${side}`;
    face.style.width = `${width * UNIT}px`;
    face.style.height = `${height * UNIT}px`;
    face.style.left = `${-width * UNIT / 2}px`;
    face.style.top = `${-height * UNIT / 2}px`;
    face.style.transform = transform;
    group.appendChild(face);
  }

  const fragment = document.createDocumentFragment();
  for (const piece of DATA.pieces) {
    const family = DATA.families[piece.f];
    const group = document.createElement('div');
    group.className = 'piece';
    group.dataset.family = family.name;
    group.style.setProperty('--piece-color', family.color);
    group.style.transform = cssMatrix(piece);
    const [x,y,z] = piece.s;
    addFace(group,x,y,`translateZ(${ z*UNIT/2}px)`,'front');
    addFace(group,x,y,`rotateY(180deg) translateZ(${z*UNIT/2}px)`,'back');
    addFace(group,z,y,`rotateY(90deg) translateZ(${ x*UNIT/2}px)`,'right');
    addFace(group,z,y,`rotateY(-90deg) translateZ(${x*UNIT/2}px)`,'left');
    addFace(group,x,z,`rotateX(90deg) translateZ(${ y*UNIT/2}px)`,'top');
    addFace(group,x,z,`rotateX(-90deg) translateZ(${y*UNIT/2}px)`,'bottom');
    fragment.appendChild(group);
    familyCounts.set(piece.f,(familyCounts.get(piece.f)||0)+1);
  }
  world.appendChild(fragment);

  for (const [index,count] of [...familyCounts].sort((a,b) => b[1]-a[1])) {
    const family = DATA.families[index];
    const label = document.createElement('label');
    const input = document.createElement('input');
    input.type = 'checkbox'; input.checked = true;
    input.addEventListener('change', () => {
      for (const node of document.querySelectorAll(`.piece[data-family="${CSS.escape(family.name)}"]`))
        node.style.display = input.checked ? '' : 'none';
    });
    const swatch = document.createElement('i');
    swatch.style.setProperty('--swatch',family.color);
    const name = document.createElement('span'); name.textContent = family.name;
    const total = document.createElement('small'); total.textContent = count;
    label.append(input,swatch,name,total); familyBox.appendChild(label);
  }

  document.getElementById('title').textContent = DATA.meta.label;
  document.getElementById('subtitle').textContent = `${DATA.meta.kind} · ${DATA.meta.dimensions_m.join(' × ')} m`;
  document.getElementById('pieceCount').textContent = DATA.pieces.length.toLocaleString();
  document.getElementById('faceCount').textContent = (DATA.pieces.length*6).toLocaleString();
  document.getElementById('nodeCount').textContent = document.getElementsByTagName('*').length.toLocaleString();

  function computeFit() {
    const available = Math.max(180,Math.min(stage.clientWidth,stage.clientHeight));
    fitScale = Math.min(2.5,Math.max(.04,available/(DATA.meta.radius_m*2*UNIT*1.12)));
  }
  function applyCamera() {
    world.style.transform = `rotateX(${pitch}deg) rotateY(${yaw}deg) scale(${fitScale*zoomFactor})`;
  }
  function setView(name) {
    const views = {iso:[-28,-35], 'end-a':[-10,78.8], 'end-b':[-10,258.8]};
    [pitch,yaw] = views[name] || views.iso; zoomFactor = 1; applyCamera();
  }
  function setMode(mode) {
    document.body.dataset.mode = mode === 'solid' ? 'solid' : 'wire';
    for (const button of document.querySelectorAll('[data-mode]'))
      button.setAttribute('aria-pressed',button.dataset.mode === document.body.dataset.mode);
  }
  for (const button of document.querySelectorAll('[data-view]'))
    button.addEventListener('click',() => setView(button.dataset.view));
  for (const button of document.querySelectorAll('[data-mode]'))
    button.addEventListener('click',() => setMode(button.dataset.mode));

  let dragging = false, lastX = 0, lastY = 0;
  stage.addEventListener('pointerdown',event => {
    dragging=true; lastX=event.clientX; lastY=event.clientY; stage.setPointerCapture(event.pointerId);
  });
  stage.addEventListener('pointermove',event => {
    if (!dragging) return;
    yaw += (event.clientX-lastX)*.35; pitch -= (event.clientY-lastY)*.25;
    pitch=Math.max(-88,Math.min(88,pitch)); lastX=event.clientX; lastY=event.clientY; applyCamera();
  });
  stage.addEventListener('pointerup',() => { dragging=false; });
  stage.addEventListener('wheel',event => {
    event.preventDefault(); zoomFactor*=Math.exp(-event.deltaY*.001); zoomFactor=Math.max(.2,Math.min(6,zoomFactor)); applyCamera();
  },{passive:false});
  window.addEventListener('resize',() => { computeFit(); applyCamera(); });

  const params = new URLSearchParams(location.search);
  computeFit(); setView(params.get('view') || 'iso'); setMode(params.get('mode') || 'wire');
  status.textContent = 'CSS scene ready';

  const frame = () => new Promise(resolve => requestAnimationFrame(resolve));
  const percentile = (values,p) => {
    const sorted=[...values].sort((a,b)=>a-b);
    return sorted[Math.max(0,Math.ceil(sorted.length*p)-1)];
  };
  async function benchmark() {
    await frame(); await frame();
    const ready = performance.now();
    const intervals=[]; let previous=ready;
    for (let i=0;i<DATA.meta.benchmark_frames;i++) {
      yaw += .7; applyCamera(); await frame();
      const now=performance.now(); if (i>=5) intervals.push(now-previous); previous=now;
    }
    const invalid = DATA.pieces.reduce((n,p) => n +
      [...p.p,...p.r,...p.s].filter(v => !Number.isFinite(v)).length,0);
    const receipt = {
      schema:'css-zdo-browser-benchmark/v1', status:invalid ? 'invalid_geometry' : 'ok',
      pieces:DATA.pieces.length, faces:DATA.pieces.length*6,
      dom_nodes:document.getElementsByTagName('*').length, invalid_numbers:invalid,
      startup_ms:+(ready-buildStarted).toFixed(2), samples:intervals.length,
      frame_p50_ms:+percentile(intervals,.5).toFixed(2),
      frame_p95_ms:+percentile(intervals,.95).toFixed(2),
      frame_max_ms:+Math.max(...intervals).toFixed(2),
      user_agent:navigator.userAgent
    };
    document.getElementById('benchmarkReceipt').textContent=JSON.stringify(receipt);
    document.documentElement.dataset.benchmarkDone='true'; window.__benchmarkReceipt=receipt;
    status.textContent=`${receipt.startup_ms} ms start · ${receipt.frame_p95_ms} ms p95 orbit`;
  }
  if (params.get('benchmark') === '1') benchmark();
})();
</script>
</body>
</html>
'''


NODE_CDP_POLL = r'''
const wsUrl = process.argv[1];
const timeoutMs = Number(process.argv[2]);
const deadline = Date.now() + timeoutMs;
let nextId = 1;
let pendingId = 0;
let finished = false;
const ws = new WebSocket(wsUrl);
function fail(message) {
  if (finished) return;
  finished = true;
  process.stderr.write(message + "\n");
  try { ws.close(); } catch (_) {}
  process.exitCode = 2;
}
function poll() {
  if (Date.now() >= deadline) return fail("benchmark receipt timed out");
  pendingId = nextId++;
  ws.send(JSON.stringify({id:pendingId,method:"Runtime.evaluate",params:{
    expression:"JSON.stringify(window.__benchmarkReceipt || null)",
    returnByValue:true
  }}));
}
ws.addEventListener("open", poll);
ws.addEventListener("error", () => fail("DevTools websocket error"));
ws.addEventListener("message", event => {
  const message = JSON.parse(event.data);
  if (message.id !== pendingId) return;
  const value = message.result && message.result.result && message.result.result.value;
  if (typeof value === "string" && value !== "null") {
    finished = true;
    process.stdout.write(value + "\n");
    ws.close();
    return;
  }
  setTimeout(poll,100);
});
'''


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cluster-points", type=Path, default=DEFAULT_CLUSTER_POINTS)
    ap.add_argument("--building-geometry", type=Path, default=DEFAULT_BUILDING_GEOMETRY)
    ap.add_argument("--piece-geometry", type=Path,
                    default=ARCH / "piece-geometry.json")
    ap.add_argument("--rotation-verify", type=Path,
                    default=ARCH / "rotation-verify.json")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--pilot-cluster", type=int, default=1820)
    ap.add_argument("--stress-cluster", type=int, default=182)
    ap.add_argument("--expected-pilot-pieces", type=int, default=847)
    ap.add_argument("--stress-tiers", default="1500,3000,5000,8000,12000,18000,all")
    ap.add_argument("--startup-limit-ms", type=float, default=5000.0)
    ap.add_argument("--frame-p95-limit-ms", type=float, default=50.0)
    ap.add_argument("--benchmark-frames", type=int, default=120)
    ap.add_argument("--browser", type=Path)
    ap.add_argument("--browser-timeout-s", type=float, default=45.0)
    ap.add_argument("--no-browser", action="store_true")
    return ap.parse_args()


def load_rotation_receipt(path):
    with path.open(encoding="utf-8") as fh:
        receipt = json.load(fh)
    if receipt.get("verdict") != "PASS":
        raise RuntimeError(f"rotation receipt is not PASS: {receipt.get('verdict')!r}")
    winner = receipt.get("winner")
    if winner not in HYPOTHESES:
        raise RuntimeError(f"unknown rotation winner: {winner!r}")
    return winner, HYPOTHESES[winner]


def load_cluster(con, cluster_id, cluster_points, building_geometry,
                 geom_by_name, to_rad, compose):
    raw_count, unique_count = con.execute("""
        SELECT count(*), count(DISTINCT zdo_index)
        FROM read_parquet(?) WHERE cluster_id = ?
        """, [str(cluster_points), cluster_id]).fetchone()
    if raw_count == 0:
        raise RuntimeError(f"cluster {cluster_id} has no frozen members")
    if raw_count != unique_count:
        raise RuntimeError(f"cluster {cluster_id} repeats zdo_index values")

    rows = con.execute("""
        SELECT c.zdo_index, c.prefab_name, c.x, c.y, c.z,
               b.has_rot, b.rot_x, b.rot_y, b.rot_z, c.creator_id,
               b.prefab_name, b.x, b.y, b.z
        FROM read_parquet(?) c
        JOIN read_parquet(?) b USING (zdo_index)
        WHERE c.cluster_id = ? ORDER BY c.zdo_index
        """, [str(cluster_points), str(building_geometry), cluster_id]).fetchall()
    if len(rows) != raw_count:
        raise RuntimeError(
            f"cluster {cluster_id} joined {len(rows)}/{raw_count} rotation rows")

    mismatches = sum(
        r[1] != r[10] or r[2] != r[11] or r[3] != r[12] or r[4] != r[13]
        for r in rows
    )
    if mismatches:
        raise RuntimeError(f"cluster {cluster_id} has {mismatches} join mismatches")

    missing = Counter()
    source_counts = Counter()
    zero_extent_rows = 0
    zero_extent_axes = 0
    pieces = []
    for row in rows:
        zdo_index, name, x, y, z, has_rot, rx, ry, rz, creator = row[:10]
        geom = geom_by_name.get(name)
        if not geom:
            missing[name] += 1
            continue
        extents = np.asarray(geom["extents"], dtype=float)
        if not np.all(np.isfinite(extents)) or np.any(extents < 0):
            raise RuntimeError(f"invalid extents for {name}: {extents}")
        if np.any(extents == 0):
            zero_extent_rows += 1
            zero_extent_axes += int(np.count_nonzero(extents == 0))
            # Planar prefab bounds (carpets are the common case) are meaningful,
            # but a zero-sized CSS rectangle cannot paint.  Give only the render
            # proxy a one-centimetre thickness; pose and source geometry stay exact.
            extents = np.maximum(extents, MIN_CSS_THICKNESS_M)
        rotation = (euler_matrix(rx, ry, rz, to_rad, compose)
                    if has_rot else np.eye(3))
        determinant = float(np.linalg.det(rotation))
        if not math.isclose(determinant, 1.0, abs_tol=1e-5):
            raise RuntimeError(f"rotation determinant {determinant} for {name}")
        pivot = np.asarray([x, y, z], dtype=float)
        center = pivot + rotation @ np.asarray(geom["center_offset"], dtype=float)
        source_counts[geom.get("source", "unknown")] += 1
        pieces.append({
            "zdo": int(zdo_index), "name": name, "family": geom["family"],
            "creator": creator, "pivot": pivot, "center": center, "R": rotation,
            "half": extents / 2.0, "extents": extents,
            "snaps": geom.get("snap_points") or [],
            "source": geom.get("source", "unknown"),
        })
    return pieces, {
        "cluster_id": cluster_id, "frozen_members": raw_count,
        "unique_zdo_indices": unique_count, "joined_rotation_rows": len(rows),
        "join_mismatches": mismatches, "geometry_rows": len(pieces),
        "missing_geometry_rows": sum(missing.values()),
        "missing_geometry_prefabs": dict(missing.most_common(10)),
        "geometry_sources": dict(sorted(source_counts.items())),
        "zero_extent_rows_thickened": zero_extent_rows,
        "zero_extent_axes_thickened": zero_extent_axes,
        "minimum_css_thickness_m": MIN_CSS_THICKNESS_M,
    }


def oriented_bounds(pieces):
    low = np.full(3, np.inf)
    high = np.full(3, -np.inf)
    for piece in pieces:
        corners = (BOX_CORNERS * piece["extents"]) @ piece["R"].T + piece["center"]
        low = np.minimum(low, corners.min(axis=0))
        high = np.maximum(high, corners.max(axis=0))
    return low, high


def encode_scene(pieces, label, kind, benchmark_frames):
    if not pieces:
        raise RuntimeError(f"cannot encode empty scene {label}")
    low, high = oriented_bounds(pieces)
    origin = (low + high) / 2.0
    dimensions = high - low
    family_names = sorted({p["family"] for p in pieces})
    family_index = {name: i for i, name in enumerate(family_names)}
    families = []
    for name in family_names:
        color = FAMILY_COLORS.get(name, FAMILY_COLORS["misc"])
        families.append({"name": name, "color": "#%02x%02x%02x" % color[:3]})

    encoded = []
    farthest = 0.0
    for piece in pieces:
        # reconstruct_cluster.py first mirrors X into glTF.  CSS then maps the
        # y-up RH model into x-right/y-down/z-toward compositor space with a
        # 180-degree X turn.  Their combined position conversion is -I.  For a
        # centered box the corresponding signed local-axis changes cancel, so
        # the verified proper rotation matrix itself remains valid.
        local_center = -(piece["center"] - origin)
        farthest = max(farthest, float(np.linalg.norm(local_center) +
                                      np.linalg.norm(piece["half"])))
        encoded.append({
            "f": family_index[piece["family"]],
            "p": [round(float(v), 4) for v in local_center],
            "r": [round(float(v), 7) for v in piece["R"].reshape(-1)],
            "s": [round(float(v), 4) for v in piece["extents"]],
        })

    numbers = [v for p in encoded for key in ("p", "r", "s") for v in p[key]]
    if not all(math.isfinite(v) for v in numbers):
        raise RuntimeError(f"non-finite CSS transform in {label}")
    return {
        "meta": {
            "schema": "css-zdo-scene/v1", "label": label, "kind": kind,
            "pieces": len(encoded),
            "dimensions_m": [round(float(v), 2) for v in dimensions],
            "radius_m": round(farthest, 3), "benchmark_frames": benchmark_frames,
            "coordinate_space": "cluster-local CSS; absolute origin withheld",
        },
        "families": families, "pieces": encoded,
    }


def write_scene(path, scene):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(scene, separators=(",", ":"), ensure_ascii=False)
    payload = payload.replace("<", "\\u003c")
    html = HTML_TEMPLATE.replace("__GEOMETRY__", payload)
    path.write_text(html, encoding="utf-8")
    if str(path.resolve().parent) in html:
        raise RuntimeError("local output path leaked into HTML")
    return {"path": str(path), "bytes": path.stat().st_size,
            "pieces": len(scene["pieces"]), "faces": len(scene["pieces"]) * 6}


def find_browser(explicit):
    if explicit:
        return explicit if explicit.is_file() else None
    candidates = []
    for env_name in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        root = os.environ.get(env_name)
        if not root:
            continue
        candidates.extend([
            Path(root) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ])
    return next((path for path in candidates if path.is_file()), None)


def browser_base(browser, profile):
    return [str(browser), "--headless=new", "--no-first-run", "--disable-default-apps",
            "--disable-extensions", "--disable-background-networking",
            "--disable-component-update", "--disable-sync", "--metrics-recording-only",
            "--mute-audio", "--hide-scrollbars", "--allow-file-access-from-files",
            "--run-all-compositor-stages-before-draw", "--disable-renderer-backgrounding",
            "--disable-background-timer-throttling", f"--user-data-dir={profile}"]


def run_benchmark(browser, html_path, timeout_s):
    started = time.perf_counter()
    node = shutil.which("node")
    if not node:
        return {"status": "node_not_found", "wall_ms": 0}
    with tempfile.TemporaryDirectory(
            prefix="css-zdo-browser-", ignore_cleanup_errors=True) as profile:
        url = html_path.resolve().as_uri() + "?benchmark=1"
        command = browser_base(browser, profile) + [
            "--remote-debugging-port=0", "--remote-allow-origins=*", url]
        browser_proc = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            active_port = Path(profile) / "DevToolsActivePort"
            startup_deadline = time.monotonic() + min(12.0, timeout_s / 2)
            while not active_port.is_file() and time.monotonic() < startup_deadline:
                if browser_proc.poll() is not None:
                    return {"status": "browser_error", "returncode": browser_proc.returncode,
                            "wall_ms": round((time.perf_counter() - started) * 1000, 2)}
                time.sleep(0.05)
            if not active_port.is_file():
                return {"status": "devtools_port_missing", "wall_ms": round(
                    (time.perf_counter() - started) * 1000, 2)}
            port = active_port.read_text(encoding="utf-8").splitlines()[0]
            targets = None
            while time.monotonic() < startup_deadline:
                try:
                    with urllib.request.urlopen(
                            f"http://127.0.0.1:{port}/json/list", timeout=1) as response:
                        targets = json.load(response)
                    break
                except OSError:
                    time.sleep(0.05)
            if not targets:
                return {"status": "devtools_target_missing", "wall_ms": round(
                    (time.perf_counter() - started) * 1000, 2)}
            target = next((item for item in targets if
                           item.get("type") == "page" and
                           html_path.name in item.get("url", "")), None)
            if not target:
                return {"status": "benchmark_page_missing", "wall_ms": round(
                    (time.perf_counter() - started) * 1000, 2)}
            remaining = max(1.0, timeout_s - (time.perf_counter() - started))
            poll = subprocess.run(
                [node, "-e", NODE_CDP_POLL, target["webSocketDebuggerUrl"],
                 str(int(remaining * 1000))],
                capture_output=True, text=True, timeout=remaining + 2,
                encoding="utf-8", errors="replace")
            if poll.returncode:
                return {"status": "receipt_missing", "wall_ms": round(
                    (time.perf_counter() - started) * 1000, 2),
                    "stderr_tail": poll.stderr[-1200:]}
            receipt = json.loads(poll.stdout.strip())
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            return {"status": "browser_timeout", "wall_ms": round(
                (time.perf_counter() - started) * 1000, 2), "error": str(exc)}
        finally:
            if browser_proc.poll() is None:
                browser_proc.terminate()
                try:
                    browser_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    browser_proc.kill()
                    browser_proc.wait(timeout=5)
    wall_ms = round((time.perf_counter() - started) * 1000, 2)
    receipt["wall_ms"] = wall_ms
    return receipt


def capture(browser, html_path, png_path, view, mode, timeout_s):
    png_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="css-zdo-capture-") as profile:
        url = html_path.resolve().as_uri() + f"?view={view}&mode={mode}"
        command = browser_base(browser, profile) + [
            "--window-size=1600,1000", "--force-device-scale-factor=1",
            "--virtual-time-budget=3500", f"--screenshot={png_path.resolve()}", url]
        try:
            proc = subprocess.run(command, capture_output=True, text=True,
                                  timeout=timeout_s, encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            return {"status": "browser_timeout", "path": str(png_path)}
    if proc.returncode or not png_path.is_file():
        return {"status": "capture_error", "returncode": proc.returncode,
                "path": str(png_path), "stderr_tail": proc.stderr[-1200:]}
    return {"status": "ok", "path": str(png_path), "bytes": png_path.stat().st_size,
            "view": view, "mode": mode}


def passes_gate(receipt, startup_limit, frame_limit):
    return (receipt.get("status") == "ok" and receipt.get("invalid_numbers") == 0
            and receipt.get("startup_ms", math.inf) <= startup_limit
            and receipt.get("frame_p95_ms", math.inf) <= frame_limit)


def parse_tiers(text, available):
    tiers = []
    for token in text.split(","):
        token = token.strip().lower()
        if not token:
            continue
        value = available if token == "all" else int(token)
        value = min(value, available)
        if value > 0 and value not in tiers:
            tiers.append(value)
    return tiers


def main():
    args = parse_args()
    winner, (to_rad, compose) = load_rotation_receipt(args.rotation_verify)
    geom_by_name = load_geometry(args.piece_geometry)
    con = duckdb.connect()
    pilot_all, pilot_join = load_cluster(
        con, args.pilot_cluster, args.cluster_points, args.building_geometry,
        geom_by_name, to_rad, compose)
    components = segment(pilot_all)
    pilot_indices = components[0]
    pilot = [pilot_all[i] for i in pilot_indices]
    if len(pilot) != args.expected_pilot_pieces:
        raise RuntimeError(
            f"pilot main component changed: {len(pilot)} != {args.expected_pilot_pieces}")

    stress_all, stress_join = load_cluster(
        con, args.stress_cluster, args.cluster_points, args.building_geometry,
        geom_by_name, to_rad, compose)
    stress_center = np.median(np.asarray([p["center"] for p in stress_all]), axis=0)
    stress_all.sort(key=lambda p: (float(np.linalg.norm(p["center"] - stress_center)),
                                   p["zdo"]))

    args.out.mkdir(parents=True, exist_ok=True)
    pilot_scene = encode_scene(
        pilot, f"Cluster {args.pilot_cluster}", "complete connected structure",
        args.benchmark_frames)
    pilot_html = args.out / "pilot-1820" / "index.html"
    pilot_artifact = write_scene(pilot_html, pilot_scene)
    browser = None if args.no_browser else find_browser(args.browser)

    report = {
        "schema": "css-zdo-rnd/v1", "rotation_verdict": "PASS",
        "rotation_decode": winner,
        "render_claim": "literal DOM faces + CSS perspective/matrix3d",
        "excluded_renderers": ["canvas", "SVG", "WebGL", "Three.js"],
        "privacy": "generated scenes contain cluster-local coordinates only",
        "pilot": {"join": pilot_join, "components": len(components),
                  "main_component_pieces": len(pilot), "artifact": pilot_artifact},
        "stress": {"join": stress_join, "ordering": "distance from median center, then zdo_index",
                   "available_geometry_pieces": len(stress_all), "tiers": []},
        "gate": {"startup_limit_ms": args.startup_limit_ms,
                 "frame_p95_limit_ms": args.frame_p95_limit_ms,
                 "benchmark_frames": args.benchmark_frames},
        "browser": str(browser) if browser else None, "captures": [],
        "uncertainties": [
            "oriented prefab boxes are massing proxies, not render meshes",
            "headless-browser timings characterize this workstation and browser build only",
            "synthetic world rotation does not reproduce every interactive workload",
            "translucent CSS faces do not model occlusion, lighting, terrain, or materials",
            "recognizability requires comparison with the existing GLB and photographs",
        ],
    }

    if not browser:
        report["pilot"]["benchmark"] = {"status": "browser_not_found"}
        report["edge"] = {"status": "BLOCKED", "reason": "headless browser unavailable"}
    else:
        pilot_benchmark = run_benchmark(browser, pilot_html, args.browser_timeout_s)
        report["pilot"]["benchmark"] = pilot_benchmark
        pilot_pass = passes_gate(
            pilot_benchmark, args.startup_limit_ms, args.frame_p95_limit_ms)
        report["pilot"]["mechanical_gate"] = "PASS" if pilot_pass else "FAIL"

        capture_specs = [
            ("isometric-wire.png", "iso", "wire"),
            ("end-078.8-solid.png", "end-a", "solid"),
            ("end-258.8-solid.png", "end-b", "solid"),
        ]
        for filename, view, mode in capture_specs:
            report["captures"].append(capture(
                browser, pilot_html, pilot_html.parent / filename,
                view, mode, args.browser_timeout_s))

        if not pilot_pass:
            report["edge"] = {
                "status": "FOUND", "at": "pilot",
                "pieces": len(pilot), "faces": len(pilot) * 6,
                "reason": "complete structure exceeded the mechanical browser gate",
            }
        else:
            last_pass = None
            for tier in parse_tiers(args.stress_tiers, len(stress_all)):
                selected = stress_all[:tier]
                scene = encode_scene(
                    selected, f"Cluster {args.stress_cluster} / {tier:,}",
                    "spatially coherent DOM stress sample", args.benchmark_frames)
                html_path = args.out / "stress-182" / f"{tier:05d}.html"
                artifact = write_scene(html_path, scene)
                benchmark = run_benchmark(browser, html_path, args.browser_timeout_s)
                passed = passes_gate(
                    benchmark, args.startup_limit_ms, args.frame_p95_limit_ms)
                item = {"pieces": tier, "artifact": artifact,
                        "benchmark": benchmark, "gate": "PASS" if passed else "FAIL"}
                report["stress"]["tiers"].append(item)
                print(f"stress {tier:>5}: {item['gate']} "
                      f"startup={benchmark.get('startup_ms')} "
                      f"p95={benchmark.get('frame_p95_ms')}", flush=True)
                if not passed:
                    report["edge"] = {
                        "status": "FOUND", "at": "stress",
                        "first_failing_pieces": tier, "faces": tier * 6,
                        "last_passing_pieces": last_pass,
                        "reason": "first configured tier exceeded the mechanical browser gate",
                    }
                    break
                last_pass = tier
            else:
                report["edge"] = {
                    "status": "NOT_REACHED", "sampled_through_pieces": last_pass,
                    "available_geometry_pieces": len(stress_all),
                    "reason": "all configured tiers passed",
                }

    result_path = args.out / "result.json"
    with result_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    print(f"pilot {len(pilot)} pieces / {len(pilot)*6} CSS faces", flush=True)
    print(f"stress source {stress_join['frozen_members']} frozen / "
          f"{len(stress_all)} with geometry", flush=True)
    print(f"edge: {report['edge']}", flush=True)
    print(f"wrote {result_path}", flush=True)


if __name__ == "__main__":
    main()

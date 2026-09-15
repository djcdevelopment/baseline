#!/usr/bin/env python3
"""The light table: the project's measuring instrument for photographs.

Ten minutes of blind pairwise judging by the eye produced more usable signal than three
vision-model runs and 601 automated frames (docs/evidence/2026-09-12-refine-loop-calibration).
So the page that did it is a tool, not a scratch file. Three steps, three receipts:

  build-pairs  rank-<era>.json (+ derivatives)      -> ab-pairs.json      steward-ab-pairs/v2
  page         ab-pairs.json  (+ derivatives)       -> light-table.html + pub/ + files.json
  harvest      ab-pairs.json  + verdict documents   -> pair-verdicts.json steward-pair-verdicts/v2
  merge        part verdict receipts                -> pair-verdicts.json steward-pair-verdicts/v2

A pair is two frames of one build shown blind, sides randomised by build key: the top two
survivors of rank_frames.py, or for a reshoot the old planned frame against the new one
(--against). A build with a single survivor is shown alone and judged keep / reshoot. Every
  verdict is written to a part-specific localStorage key as it is made.  The page exports a
  fingerprinted JSON document that it can import again, and harvest turns that document into
  the receipt frame_judge.replay_pairs scores rules against. A
cumulative file (--append) grows toward the ~150 decided pairs a fitted critic needs.

    python light_table.py build-pairs --rank R/rank-era1.json --derivatives R/derivatives --out R/ab-pairs.json
    python light_table.py page --pairs R/ab-pairs.json --derivatives R/derivatives --out R/light-table
    python light_table.py harvest --pairs R/ab-pairs.json --verdicts R/verdicts --out R/pair-verdicts.json \\
        --append docs/evidence/pair-verdicts-all.json
"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

PICKS = ("left", "right", "both", "neither", "keep", "reshoot")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value, compact=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, separators=(",", ":")) if compact else json.dumps(value, indent=1)
    path.write_text(text + ("" if compact else "\n"), encoding="utf-8")


def side_for(build_key):
    """Which frame goes on the left: deterministic, unguessable without the key."""
    return "a" if int(hashlib.sha256(build_key.encode()).hexdigest(), 16) % 2 == 0 else "b"


def frame_id(era, build_key, name):
    return f"{era}-{build_key[:12]}-{name.replace('~', '-')}"


def frame_record(era, build_key, frame):
    m = frame.get("metrics") or {}
    return {"name": frame["name"], "file": frame.get("file"), "id": frame_id(era, build_key, frame["name"]),
            "pose": frame.get("pose"), "score": m.get("score"), "live": m.get("liveTileShare"),
            "sky": m.get("skyFraction"), "luma": m.get("lumaMean"), "forecast": frame.get("forecast")}


# ---- build-pairs
def pairs_from_rank(ranking, against=None):
    """Top two survivors per build as a pair, a lone survivor as a single. With --against, each
    build's first survivor is paired against the same build's first survivor in the earlier
    ranking (the reshoot question: is the new planned frame better than the old one?)."""
    era = ranking["era"]; pairs, singles, skipped = [], [], []
    old = earlier_frames(against) if against is not None else {}
    for key, build in sorted(ranking["builds"].items()):
        kept = build.get("kept") or []
        if against is not None:
            previous = old.get(key)
            if not kept or not previous:
                skipped.append((key[:8], "no frame on one side")); continue
            a, b = previous, frame_record(era, key, kept[0])
            pairs.append({"build": key[:8], "buildKey": key, "mode": "pair", "a": a, "b": b, "left": side_for(key)})
        elif len(kept) >= 2:
            a, b = frame_record(era, key, kept[0]), frame_record(era, key, kept[1])
            pairs.append({"build": key[:8], "buildKey": key, "mode": "pair", "a": a, "b": b, "left": side_for(key)})
        elif len(kept) == 1:
            singles.append({"build": key[:8], "buildKey": key, "mode": "single", "a": frame_record(era, key, kept[0]), "left": "a"})
        else:
            skipped.append((key[:8], "no survivor; already on the reshoot list"))
    roles = ({"a": "the earlier planned frame", "b": "the replanned frame"} if against is not None
             else {"a": "first survivor", "b": "second survivor"})
    question = ("is the replanned frame a better photograph of this build than the earlier one?" if against is not None
                else "which of these two is the better photograph of this build?")
    return {"schema": "steward-ab-pairs/v2", "era": era, "sourceKey": ranking.get("sourceKey"),
            "run": ranking.get("run"), "roles": roles, "question": question, "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "counts": {"pairs": len(pairs), "singles": len(singles), "skipped": len(skipped)},
            "pairs": pairs + singles, "skipped": skipped}


def earlier_frames(document):
    """The frame to compare a reshoot against, per build key: the first survivor of an earlier
    rank receipt, or the planned (`a` / incumbent) frame of an earlier pairs file."""
    schema = document.get("schema")
    if schema == "steward-frame-rank/v1":
        era = document["era"]
        return {key: frame_record(era, key, build["kept"][0]) for key, build in document["builds"].items() if build.get("kept")}
    if schema in ("steward-ab-pairs/v1", "steward-ab-pairs/v2"):
        pairs = load_pairs_document(document)["pairs"]
        return {p["buildKey"]: {**p["a"], "id": p["a"].get("id")} for p in pairs}
    raise SystemExit(f"cannot take earlier frames from schema {schema}")


def load_pairs_document(document):
    if document.get("schema") == "steward-ab-pairs/v1":
        return upgrade_v1(document)
    return document


def upgrade_v1(document):
    """The 77-pair file of 2026-09-12 in the generic shape, so the same page and harvest read it."""
    pairs = []
    for p in document["pairs"]:
        pairs.append({"build": p["build"], "buildKey": p["buildKey"], "mode": "pair",
                      "a": {**p["incumbent"], "id": None}, "b": {**p["winner"], "id": None},
                      "left": "a" if p["left"] == "incumbent" else "b",
                      "context": {"path": p.get("path"), "climbed": p.get("climbed"), "rounds": p.get("rounds")}})
    return {**{k: v for k, v in document.items() if k != "pairs"}, "schema": "steward-ab-pairs/v2",
            "roles": {"a": "the planned pose", "b": "the pose the refine loop moved to"},
            "question": "which of these two is the better photograph of this build?", "pairs": pairs}


def load_pairs(path):
    document = read(path)
    if document.get("schema") == "steward-ab-pairs/v1":
        return upgrade_v1(document)
    if document.get("schema") != "steward-ab-pairs/v2":
        raise SystemExit(f"unsupported pairs schema: {document.get('schema')}")
    return document


# ---- page
def locate_image(frame, derivatives):
    """The 1600 px large derivative by id, else a webp beside the master's stem (the old layout)."""
    candidates = []
    if frame.get("id"):
        candidates.append(Path(derivatives) / "large" / (frame["id"] + ".webp"))
    if frame.get("file"):
        stem = Path(frame["file"]).stem
        candidates += [Path(derivatives) / (stem + ".webp"), Path(derivatives) / "large" / (stem + ".webp")]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise SystemExit(f"no image for {frame.get('id') or frame.get('file')} under {derivatives}")


def page_key(document):
    """A stable identity for one part, not merely its shared era title."""
    identity = {"era": document["era"], "run": document.get("run"),
                "buildKeys": [pair["buildKey"] for pair in document["pairs"]]}
    raw = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def render_page(document, derivatives, out):
    out = Path(out); pub = out / "pub"
    if pub.exists():
        shutil.rmtree(pub)
    pub.mkdir(parents=True)
    rows = []
    for n, p in enumerate(document["pairs"], 1):
        slots = {}
        for slot in ("a", "b"):
            if slot not in p:
                continue
            short = f"p{n:03d}{slot}.webp"
            shutil.copyfile(locate_image(p[slot], derivatives), pub / short)
            slots[slot] = short
        rows.append({"b": p["build"], "mode": p["mode"], "left": p["left"], "img": slots,
                     "a": {k: p["a"].get(k) for k in ("name", "score", "live", "sky", "luma")},
                     "bb": {k: p["b"].get(k) for k in ("name", "score", "live", "sky", "luma")} if "b" in p else None,
                     "ctx": p.get("context")})
    files = sorted(f for r in rows for f in r["img"].values())
    write(out / "files.json", {f: "pub/" + f for f in files}, compact=True)
    metadata = {"schema": "steward-light-table-local-verdicts/v1", "era": document["era"],
                "run": document.get("run"), "pageKey": page_key(document)}
    html = (TEMPLATE.replace("__TITLE__", f"{document['era']} light table")
                     .replace("__ROLES__", json.dumps(document.get("roles", {})))
                     .replace("__QUESTION__", json.dumps(document.get("question", "")))
                     .replace("__META__", json.dumps(metadata, separators=(",", ":")))
                     .replace("__PAIRS__", json.dumps(rows, separators=(",", ":"))))
    (out / "light-table.html").write_text(html, encoding="utf-8")
    return len(rows), len(files)


# ---- harvest
def chose(pick, left):
    if pick in ("both", "neither", "keep", "reshoot"):
        return pick
    if pick == "left":
        return left
    return "b" if left == "a" else "a"


def harvest(document, verdict_docs, judged_by=None, require_complete=False):
    by_build = {p["build"]: p for p in document["pairs"]}
    if require_complete and len(by_build) != len(document["pairs"]):
        raise SystemExit("pairs file contains duplicate short build identifiers")
    rows = []
    seen, invalid = set(), []
    for row in sorted(verdict_docs, key=lambda v: v.get("build", "")):
        p = by_build.get(row.get("build"))
        allowed = ("keep", "reshoot") if p and p["mode"] == "single" else ("left", "right", "both", "neither")
        if (p is None or row.get("pick") not in allowed
                or row.get("mode") not in (None, p["mode"])
                or row.get("left") not in (None, p["left"])
                or row.get("build") in seen):
            invalid.append(row.get("build"))
            continue
        seen.add(row["build"])
        verdict = chose(row["pick"], p["left"])
        record = {"build": p["build"], "buildKey": p["buildKey"], "mode": p["mode"], "chose": verdict, "pick": row["pick"],
                  "left": p["left"], "at": row.get("at"), "aFrame": p["a"], "bFrame": p.get("b"), "context": p.get("context")}
        # The 2026-09-12 naming, so frame_judge.replay_pairs and the calibration read this unchanged.
        roles = document.get("roles", {})
        if roles.get("a") == "the planned pose":
            classic = {"a": "incumbent", "b": "winner"}
            record.update({"chose": classic.get(verdict, verdict), "leftRole": classic[p["left"]],
                           "incumbent": p["a"]["name"], "fanPick": p["b"]["name"],
                           "incMetrics": {k: p["a"].get(k) for k in ("score", "live", "sky", "luma")},
                           "fanMetrics": {k: p["b"].get(k) for k in ("score", "live", "sky", "luma")}})
        else:
            record.update({"aMetrics": {k: p["a"].get(k) for k in ("score", "live", "sky", "luma")},
                           "bMetrics": {k: p["b"].get(k) for k in ("score", "live", "sky", "luma")} if p.get("b") else None})
        rows.append(record)
    if require_complete:
        missing = sorted(set(by_build) - seen)
        if invalid or missing:
            raise SystemExit(f"incomplete verdict set: {len(invalid)} invalid/duplicate, "
                             f"{len(missing)} missing; first invalid={invalid[:1]}, missing={missing[:1]}")
    return {"schema": "steward-pair-verdicts/v2", "era": document["era"], "sourceKey": document.get("sourceKey"),
            "run": document.get("run"), "roles": document.get("roles"), "question": document.get("question"),
            "judgedBy": judged_by, "harvestedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "counts": dict(collections.Counter(r["chose"] for r in rows)), "verdicts": rows}


def read_verdict_docs(path):
    path = Path(path)
    docs = []
    if path.is_file():
        loaded = read(path)
        docs = loaded if isinstance(loaded, list) else list((loaded.get("verdicts") or loaded).values()) if isinstance(loaded, dict) else []
    else:
        for file in sorted(path.rglob("*.json")):
            try:
                loaded = read(file)
                if isinstance(loaded, dict) and isinstance(loaded.get("verdicts"), dict):
                    docs.extend(loaded["verdicts"].values())
                else:
                    docs.append(loaded)
            except ValueError:
                continue
    return [d for d in docs if isinstance(d, dict) and d.get("build")]


def append_cumulative(path, receipt):
    path = Path(path)
    total = read(path) if path.exists() else {"schema": "steward-pair-verdicts-cumulative/v1", "runs": [], "verdicts": []}
    if total.get("schema") != "steward-pair-verdicts-cumulative/v1":
        raise SystemExit(f"unsupported cumulative verdict schema: {total.get('schema')}")
    tag = f"{receipt['era']}:{receipt.get('run') or receipt['harvestedAt']}"
    run = next((row for row in total["runs"] if row["tag"] == tag), None)
    if run is None:
        run = {"tag": tag, "era": receipt["era"], "roles": receipt.get("roles"), "counts": {}}
        total["runs"].append(run)
    elif run.get("era") != receipt.get("era") or run.get("roles") != receipt.get("roles"):
        raise SystemExit(f"cumulative run identity changed for {tag}")
    existing = {}
    for verdict in (row for row in total["verdicts"] if row.get("runTag") == tag):
        key = verdict.get("buildKey")
        if not key or key in existing:
            raise SystemExit(f"cumulative run has duplicate or missing build key: {tag}")
        existing[key] = verdict
    incoming = set()
    for verdict in receipt["verdicts"]:
        key = verdict.get("buildKey")
        if not key or key in incoming:
            raise SystemExit(f"receipt has duplicate or missing build key: {tag}")
        incoming.add(key)
        prior = existing.get(key)
        if prior is not None:
            if {k: v for k, v in prior.items() if k != "runTag"} != verdict:
                raise SystemExit(f"verdict conflicts with cumulative evidence: {tag} {key}")
            continue
        total["verdicts"].append({**verdict, "runTag": tag})
    run_verdicts = [row for row in total["verdicts"] if row.get("runTag") == tag]
    run["counts"] = dict(collections.Counter(row["chose"] for row in run_verdicts))
    decided = sum(1 for v in total["verdicts"] if v["chose"] in ("a", "b", "incumbent", "winner"))
    total["decidedPairs"] = decided
    write(path, total)
    return total


def merge_receipts(paths):
    """Join disjoint part receipts for one run, retaining hashes of every input."""
    paths = [Path(path) for path in paths]
    if not paths:
        raise SystemExit("at least one part receipt is required")
    documents = [read(path) for path in paths]
    first = documents[0]
    if first.get("schema") != "steward-pair-verdicts/v2":
        raise SystemExit(f"unsupported part receipt schema: {first.get('schema')}")
    identity_fields = ("era", "sourceKey", "run", "roles", "question", "judgedBy")
    identity = {key: first.get(key) for key in identity_fields}
    verdicts, seen, parts = [], set(), []
    for path, document in zip(paths, documents):
        if document.get("schema") != "steward-pair-verdicts/v2":
            raise SystemExit(f"unsupported part receipt schema: {document.get('schema')}")
        actual = {key: document.get(key) for key in identity_fields}
        if actual != identity:
            raise SystemExit(f"part receipt belongs to another run: {path}")
        for verdict in document.get("verdicts", []):
            key = verdict.get("buildKey")
            if not key or key in seen:
                raise SystemExit(f"duplicate or missing build key across part receipts: {key}")
            seen.add(key); verdicts.append(verdict)
        parts.append({"path": str(path.resolve()),
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "verdicts": len(document.get("verdicts", []))})
    return {"schema": "steward-pair-verdicts/v2", **identity,
            "harvestedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "counts": dict(collections.Counter(row["chose"] for row in verdicts)),
            "parts": parts, "verdicts": sorted(verdicts, key=lambda row: row["buildKey"])}


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* A light table, not a webpage: one ground, committed, so prints are compared against
   the same neutral in every viewer's theme. Every colour is painted explicitly. */
:root { --ground:#14161a; --panel:#1c1f25; --line:#2b3038; --line-2:#3a414c; --ink:#e6e3dd; --muted:#8b9099;
        --amber:#c8792e; --amber-d:#7a4a1c; --slate:#5d7f8c; --bad:#8c5d5d;
        --display:"Barlow Condensed","Helvetica Neue",Arial,sans-serif; --mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,monospace; }
* { box-sizing:border-box; } html,body { height:100%; }
body { margin:0; background:var(--ground); color:var(--ink); font-family:var(--mono); font-size:13px; display:flex; flex-direction:column; overflow:hidden; }
button { font:inherit; color:inherit; background:none; border:none; cursor:pointer; }
:focus-visible { outline:2px solid var(--amber); outline-offset:2px; }
.rail { flex:0 0 auto; display:flex; align-items:center; gap:18px; padding:0 16px; background:var(--panel); border-bottom:1px solid var(--line); }
.rail.top { height:46px; } .rail.bottom { height:62px; border-bottom:none; border-top:1px solid var(--line); }
.mark { font-family:var(--display); font-size:15px; font-weight:600; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); white-space:nowrap; }
.mark b { color:var(--amber); font-weight:600; }
.build { font-size:12px; letter-spacing:.08em; color:var(--muted); } .build strong { color:var(--ink); font-weight:500; }
.spacer { flex:1 1 auto; } .count { font-variant-numeric:tabular-nums; color:var(--muted); white-space:nowrap; } .count b { color:var(--ink); font-weight:500; }
.bar { width:180px; height:3px; background:var(--line); position:relative; } .bar i { position:absolute; inset:0 auto 0 0; background:var(--amber); width:0; transition:width .18s; }
main { flex:1 1 auto; display:grid; grid-template-columns:1fr 1fr; grid-template-rows:minmax(0,1fr); gap:2px; min-width:0; min-height:0; overflow:hidden; transition:opacity .12s; }
main.single { grid-template-columns:1fr; } main.fade { opacity:.25; }
.frame { position:relative; background:var(--panel); min-height:0; overflow:hidden; display:flex; align-items:center; justify-content:center; border:2px solid transparent; transition:border-color .12s; }
.frame img { width:100%; height:100%; min-width:0; min-height:0; object-fit:contain; display:block; }
.frame:hover { border-color:var(--line-2); } .frame.pick { border-color:var(--amber); } .frame[hidden] { display:none; }
.frame .tag { position:absolute; top:10px; left:12px; font-family:var(--display); font-size:26px; font-weight:600; line-height:1; letter-spacing:.06em; color:var(--ink); opacity:.55; text-shadow:0 1px 6px rgba(0,0,0,.8); pointer-events:none; }
.frame .role { position:absolute; bottom:0; left:0; right:0; padding:7px 12px; background:rgba(20,22,26,.92); border-top:1px solid var(--line); font-size:11px; letter-spacing:.04em; display:none; gap:14px; flex-wrap:wrap; align-items:baseline; }
body.revealed .frame .role { display:flex; }
.role .who { font-family:var(--display); font-size:13px; letter-spacing:.14em; text-transform:uppercase; font-weight:600; color:var(--amber); }
.role b { color:var(--ink); font-weight:500; }
.keys { display:flex; gap:8px; } .keys button { padding:8px 14px; border:1px solid var(--line-2); border-radius:3px; letter-spacing:.06em; }
.keys button:hover { border-color:var(--amber); } .keys kbd { color:var(--muted); font-family:var(--mono); margin-left:6px; }
.keys button.bad { border-color:var(--bad); } .keys button.good { border-color:var(--slate); }
#save { color:var(--muted); } #save.warn { color:var(--bad); }
#tally { display:none; padding:40px; max-width:820px; margin:0 auto; overflow:auto; }
body.done main, body.done .rail.bottom { display:none; } body.done #tally { display:block; }
#tally h1 { font-family:var(--display); font-weight:600; letter-spacing:.06em; font-size:32px; margin:0 0 12px; }
#tally table { border-collapse:collapse; margin:18px 0; } #tally td,#tally th { padding:6px 14px; border-bottom:1px solid var(--line); text-align:left; }
#tally .note { color:var(--muted); }
</style>
</head>
<body>
<div class="rail top">
  <span class="mark"><b>light table</b> · __TITLE__</span>
  <span class="build">build <strong id="bid"></strong> <span id="mode"></span></span>
  <div class="keys"><button id="export">export</button><button id="import">import</button></div>
  <input id="importFile" type="file" accept="application/json,.json" hidden>
  <span class="spacer"></span>
  <span class="count"><b id="n">0</b> / <span id="tot">0</span></span>
  <span class="bar"><i id="fill"></i></span>
  <span id="save"></span>
</div>
<main id="stage">
  <div class="frame" id="fL"><span class="tag">A</span><img id="imL" alt=""><div class="role" id="roL"></div></div>
  <div class="frame" id="fR"><span class="tag">B</span><img id="imR" alt=""><div class="role" id="roR"></div></div>
</main>
<div id="tally"></div>
<div class="rail bottom">
  <div class="keys" id="pairKeys">
    <button data-pick="left">A is better<kbd>←</kbd></button>
    <button data-pick="right">B is better<kbd>→</kbd></button>
    <button data-pick="both" class="good">both worth publishing<kbd>↑</kbd></button>
    <button data-pick="neither" class="bad">neither<kbd>↓</kbd></button>
  </div>
  <div class="keys" id="singleKeys" hidden>
    <button data-pick="keep" class="good">keep<kbd>↑</kbd></button>
    <button data-pick="reshoot" class="bad">reshoot<kbd>↓</kbd></button>
  </div>
  <span class="spacer"></span>
  <div class="keys"><button id="reveal">reveal<kbd>space</kbd></button><button id="undo">undo<kbd>u</kbd></button></div>
</div>
<script>
const PAIRS = __PAIRS__;
const ROLES = __ROLES__;
const QUESTION = __QUESTION__;
const META = __META__;
const STORAGE_KEY = `lt-verdicts:v1:${META.era}:${META.run || "none"}:${META.pageKey}`;
const $ = (id) => document.getElementById(id);
let i = 0, verdicts = {}, lastKey = null;
function saveLocal() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(verdicts)); $("save").textContent = "saved locally"; }
  catch (e) { $("save").textContent = "local save failed"; $("save").className = "warn"; }
}
const num = (v, d = 3) => (v === null || v === undefined) ? "—" : Number(v).toFixed(d);
function roleHtml(slot, m) {
  if (!m) return "";
  return `<span class="who">${ROLES[slot] || slot}</span><span>${m.name}</span><span>score <b>${num(m.score, 6)}</b></span>` +
         `<span>live <b>${num(m.live, 2)}</b></span><span>sky <b>${num(m.sky, 3)}</b></span><span>luma <b>${num(m.luma, 2)}</b></span>`;
}
function render() {
  if (i >= PAIRS.length) return finish();
  const p = PAIRS[i];
  document.body.classList.remove("revealed", "done");
  $("fL").classList.remove("pick"); $("fR").classList.remove("pick");
  const single = p.mode === "single";
  $("stage").classList.toggle("single", single);
  $("fR").hidden = single; $("pairKeys").hidden = single; $("singleKeys").hidden = !single;
  $("mode").textContent = single ? "· single frame" : "";
  const leftSlot = p.left, rightSlot = p.left === "a" ? "b" : "a";
  $("imL").src = "pub/" + p.img[leftSlot];
  $("roL").innerHTML = roleHtml(leftSlot, leftSlot === "a" ? p.a : p.bb);
  if (!single) { $("imR").src = "pub/" + p.img[rightSlot]; $("roR").innerHTML = roleHtml(rightSlot, rightSlot === "a" ? p.a : p.bb); }
  $("bid").textContent = p.b;
  const n = Object.keys(verdicts).length;
  $("n").textContent = n; $("tot").textContent = PAIRS.length;
  $("fill").style.width = (100 * n / PAIRS.length) + "%";
  $("undo").disabled = !lastKey;
  const cur = verdicts[p.b];
  if (cur) { document.body.classList.add("revealed"); const el = {left: "fL", right: "fR", keep: "fL"}[cur.pick]; if (el) $(el).classList.add("pick"); }
}
async function record(pick) {
  const p = PAIRS[i];
  const allowed = p.mode === "single" ? ["keep", "reshoot"] : ["left", "right", "both", "neither"];
  if (!allowed.includes(pick)) return;
  const row = {build: p.b, pick, left: p.left, mode: p.mode, at: new Date().toISOString()};
  verdicts[p.b] = row; lastKey = p.b;
  saveLocal();
  $("stage").classList.add("fade");
  setTimeout(() => { i = nextUnjudged(i + 1); $("stage").classList.remove("fade"); render(); }, 120);
}
function nextUnjudged(from) {
  for (let k = from; k < PAIRS.length; k++) if (!verdicts[PAIRS[k].b]) return k;
  for (let k = 0; k < from && k < PAIRS.length; k++) if (!verdicts[PAIRS[k].b]) return k;
  return PAIRS.length;
}
function finish() {
  document.body.classList.add("done");
  const rows = Object.values(verdicts);
  $("n").textContent = rows.length; $("tot").textContent = PAIRS.length;
  $("fill").style.width = (100 * rows.length / PAIRS.length) + "%";
  const count = (test) => rows.filter(test).length;
  const chose = (r) => (r.pick === "left" ? r.left : r.pick === "right" ? (r.left === "a" ? "b" : "a") : r.pick);
  $("tally").innerHTML = `<h1>${rows.length} verdicts in</h1><p>${QUESTION}</p>
    <table><thead><tr><th>verdict</th><th>n</th></tr></thead><tbody>
      <tr><td>${ROLES.a || "A"}</td><td>${count(r => chose(r) === "a")}</td></tr>
      <tr><td>${ROLES.b || "B"}</td><td>${count(r => chose(r) === "b")}</td></tr>
      <tr><td>both worth publishing</td><td>${count(r => r.pick === "both")}</td></tr>
      <tr><td>neither</td><td>${count(r => r.pick === "neither")}</td></tr>
      <tr><td>keep (single)</td><td>${count(r => r.pick === "keep")}</td></tr>
      <tr><td>reshoot (single)</td><td>${count(r => r.pick === "reshoot")}</td></tr>
    </tbody></table>
    <p class="note">Every verdict is saved locally as it is made. Export the JSON before closing this part;
       the harvest step turns it into the receipt the rules are scored against. <em>Neither</em> and
       <em>reshoot</em> rows name the builds the planner has to answer for.</p>`;
}
document.querySelectorAll("[data-pick]").forEach(b => b.addEventListener("click", () => record(b.dataset.pick)));
$("fL").addEventListener("click", () => record(PAIRS[i] && PAIRS[i].mode === "single" ? "keep" : "left"));
$("fR").addEventListener("click", () => record("right"));
$("reveal").addEventListener("click", () => document.body.classList.toggle("revealed"));
$("undo").addEventListener("click", () => {
  if (!lastKey) return; const k = lastKey; delete verdicts[k]; lastKey = null;
  saveLocal();
  i = PAIRS.findIndex(p => p.b === k); document.body.classList.remove("done"); render();
});
addEventListener("keydown", (e) => {
  if (document.body.classList.contains("done")) return;
  const single = PAIRS[i] && PAIRS[i].mode === "single";
  const map = single ? {ArrowUp: "keep", ArrowDown: "reshoot", e: "keep", x: "reshoot"}
                     : {ArrowLeft: "left", ArrowRight: "right", ArrowUp: "both", ArrowDown: "neither", a: "left", d: "right", e: "both", x: "neither"};
  const pick = map[e.key];
  if (pick) { e.preventDefault(); record(pick); return; }
  if (e.key === " ") { e.preventDefault(); document.body.classList.toggle("revealed"); }
  if (e.key === "u") { e.preventDefault(); $("undo").click(); }
});
function validRows(rows) {
  if (!rows || typeof rows !== "object" || Array.isArray(rows)) return false;
  const pairs = Object.fromEntries(PAIRS.map(p => [p.b, p]));
  return Object.entries(rows).every(([key, row]) => {
    const p = pairs[key], allowed = p && (p.mode === "single" ? ["keep", "reshoot"] : ["left", "right", "both", "neither"]);
    return p && row && row.build === key && row.mode === p.mode && row.left === p.left && allowed.includes(row.pick);
  });
}
$("export").addEventListener("click", () => {
  const payload = {...META, exportedAt: new Date().toISOString(), verdicts};
  const blob = new Blob([JSON.stringify(payload, null, 2) + "\\n"], {type: "application/json"});
  const link = document.createElement("a"); link.href = URL.createObjectURL(blob);
  link.download = `verdicts-${META.era}-${META.run || "run"}-${META.pageKey.slice(0, 12)}.json`;
  link.click(); URL.revokeObjectURL(link.href);
});
$("import").addEventListener("click", () => $("importFile").click());
$("importFile").addEventListener("change", async (event) => {
  const file = event.target.files[0]; if (!file) return;
  try {
    const payload = JSON.parse(await file.text());
    if (payload.schema !== META.schema || payload.era !== META.era || payload.run !== META.run
        || payload.pageKey !== META.pageKey || !validRows(payload.verdicts)) throw new Error("wrong page or invalid verdicts");
    verdicts = payload.verdicts; lastKey = null; saveLocal(); i = nextUnjudged(0); render();
  } catch (e) { $("save").textContent = "import refused: " + e.message; $("save").className = "warn"; }
  event.target.value = "";
});
try { const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); if (validRows(saved)) verdicts = saved; } catch (e) {}
i = nextUnjudged(0); render();
$("save").textContent = "saved locally";
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build-pairs", help="pairs from a rank_frames receipt (top two per build), or old-vs-new with --against")
    b.add_argument("--rank", type=Path, required=True); b.add_argument("--against", type=Path, help="an earlier rank-<era>.json to pair against")
    b.add_argument("--run", help="a name for this session, kept in every receipt"); b.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("page", help="publishable light-table.html + pub/ from a pairs file")
    p.add_argument("--pairs", type=Path, required=True); p.add_argument("--derivatives", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    h = sub.add_parser("harvest", help="verdict documents -> pair-verdicts receipt")
    h.add_argument("--pairs", type=Path, required=True); h.add_argument("--verdicts", type=Path, required=True)
    h.add_argument("--out", type=Path, required=True); h.add_argument("--append", type=Path, help="cumulative pair-verdicts file to grow")
    h.add_argument("--judged-by", default=None)
    h.add_argument("--require-complete", action="store_true",
                   help="reject missing, duplicate, foreign, or malformed verdict rows")
    m = sub.add_parser("merge", help="join disjoint part verdict receipts for one run")
    m.add_argument("--receipts", type=Path, nargs="+", required=True)
    m.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build-pairs":
        ranking = read(args.rank)
        if ranking.get("schema") != "steward-frame-rank/v1":
            raise SystemExit(f"unsupported rank schema: {ranking.get('schema')}")
        if args.run:
            ranking["run"] = args.run
        document = pairs_from_rank(ranking, read(args.against) if args.against else None)
        write(args.out, document)
        c = document["counts"]; print(f"{c['pairs']} pairs, {c['singles']} singles, {c['skipped']} skipped -> {args.out}")
    elif args.command == "page":
        document = load_pairs(args.pairs)
        pairs, files = render_page(document, args.derivatives, args.out)
        print(f"wrote {args.out / 'light-table.html'} for {pairs} pairs, {files} images; publish with files.json as the files map")
    elif args.command == "harvest":
        document = load_pairs(args.pairs)
        if args.require_complete and args.verdicts.is_file():
            envelope = read(args.verdicts)
            if envelope.get("schema") == "steward-light-table-local-verdicts/v1":
                expected = {"era": document["era"], "run": document.get("run"),
                            "pageKey": page_key(document)}
                actual = {key: envelope.get(key) for key in expected}
                if actual != expected:
                    raise SystemExit(f"verdict export belongs to another page: {actual} != {expected}")
        receipt = harvest(document, read_verdict_docs(args.verdicts), args.judged_by,
                          require_complete=args.require_complete)
        write(args.out, receipt)
        print(f"{len(receipt['verdicts'])} verdicts: {receipt['counts']} -> {args.out}")
        if args.append:
            total = append_cumulative(args.append, receipt)
            print(f"cumulative: {len(total['verdicts'])} verdicts, {total.get('decidedPairs')} decided pairs across {len(total['runs'])} run(s)")
    else:
        receipt = merge_receipts(args.receipts)
        write(args.out, receipt)
        print(f"merged {len(args.receipts)} part(s), {len(receipt['verdicts'])} verdicts: "
              f"{receipt['counts']} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

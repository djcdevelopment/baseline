"""Build an explorer page from an explicitly supplied component-atlas artifact.

Embeds the atlas JSON inline (minified) so the page is fully self-contained —
works from file://, a Discord-shared file, or GitHub Pages with no fetch/CORS.
The caller supplies both input and output paths; this script never reaches into a
sibling repository or assumes a checkout layout.
"""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--atlas", required=True, type=Path,
                    help="verified valheim-component-atlas.json artifact")
parser.add_argument("--output", required=True, type=Path,
                    help="destination HTML path")
args = parser.parse_args()
if not args.atlas.is_file():
    parser.error(f"atlas artifact does not exist: {args.atlas}")

atlas = json.loads(args.atlas.read_text(encoding="utf-8"))
# Trim per-component Source (repeated 336x) — the page shows the top-level one.
for c in atlas["Components"]:
    c.pop("Source", None)
data = json.dumps(atlas, separators=(",", ":"))

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Valheim Component Atlas — explorer</title>
<style>
  :root {
    color-scheme: light;
    --page:#f9f9f7; --surface:#fcfcfb; --card:#ffffff; --ink:#0b0b0b; --ink-2:#52514e;
    --muted:#898781; --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,0.10);
    --s1:#2a78d6; --s2:#eb6834;
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) {
      color-scheme: dark;
      --page:#0d0d0d; --surface:#1a1a19; --card:#222220; --ink:#ffffff; --ink-2:#c3c2b7;
      --muted:#898781; --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10);
      --s1:#3987e5; --s2:#d95926;
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --page:#0d0d0d; --surface:#1a1a19; --card:#222220; --ink:#ffffff; --ink-2:#c3c2b7;
    --muted:#898781; --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10);
    --s1:#3987e5; --s2:#d95926;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--page); color:var(--ink);
         font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; }
  .wrap { max-width:1080px; margin:0 auto; padding:24px 20px 60px; }
  h1 { font-size:24px; margin:0 0 2px; }
  .sub { color:var(--ink-2); font-size:13.5px; }
  .prov { font-size:12px; color:var(--muted); margin-top:4px; }
  .tiles { display:flex; gap:12px; margin:16px 0; flex-wrap:wrap; }
  .tile { background:var(--surface); border:1px solid var(--border); border-radius:10px;
          padding:10px 16px; min-width:120px; }
  .tile .n { font-size:26px; font-weight:650; }
  .tile .l { font-size:12px; color:var(--ink-2); }
  .bar { display:flex; gap:8px; margin:14px 0 12px; flex-wrap:wrap; }
  .bar input {
    flex:1; min-width:220px; background:var(--surface); border:1px solid var(--border);
    border-radius:8px; padding:8px 12px; font:inherit; color:var(--ink);
  }
  .bar button {
    background:var(--surface); border:1px solid var(--border); border-radius:8px;
    padding:8px 14px; font:inherit; color:var(--ink-2); cursor:pointer;
  }
  .bar button.on { color:var(--s1); border-color:var(--s1); font-weight:600; }
  .cols { display:grid; grid-template-columns:280px 1fr; gap:14px; }
  @media (max-width:760px) { .cols { grid-template-columns:1fr; } }
  .list { background:var(--surface); border:1px solid var(--border); border-radius:10px;
          max-height:70vh; overflow-y:auto; }
  .list .item { padding:7px 12px; border-bottom:1px solid var(--grid); cursor:pointer;
                display:flex; justify-content:space-between; gap:8px; }
  .list .item:hover { background:var(--card); }
  .list .item.on { border-left:3px solid var(--s1); padding-left:9px; background:var(--card); }
  .list .item .nm { font-family:Consolas,monospace; font-size:13px; }
  .list .item .ct { color:var(--muted); font-size:12px; white-space:nowrap; }
  .detail { background:var(--surface); border:1px solid var(--border); border-radius:10px;
            padding:16px 18px; max-height:70vh; overflow-y:auto; }
  .detail h2 { font-family:Consolas,monospace; font-size:19px; margin:0 0 2px; }
  .chainline { font-family:Consolas,monospace; font-size:12.5px; color:var(--ink-2); margin:2px 0 10px; }
  .badges { margin:6px 0 12px; }
  .badge { display:inline-block; font-size:11.5px; border:1px solid var(--border);
           border-radius:999px; padding:1px 9px; margin:2px 4px 2px 0; color:var(--ink-2); }
  .badge.b1 { border-color:var(--s1); color:var(--s1); }
  .badge.b2 { border-color:var(--s2); color:var(--s2); }
  table { border-collapse:collapse; width:100%; font-size:13px; margin:6px 0 14px; }
  th { text-align:left; color:var(--muted); font-weight:500; font-size:11.5px;
       border-bottom:1px solid var(--grid); padding:3px 10px 3px 0; }
  td { border-bottom:1px solid var(--grid); padding:4px 10px 4px 0; vertical-align:top; }
  td.k { font-family:Consolas,monospace; white-space:nowrap; }
  td.t { color:var(--muted); white-space:nowrap; }
  td.d { color:var(--ink-2); }
  h3 { font-size:13px; margin:14px 0 4px; color:var(--ink); }
  .empty { color:var(--muted); padding:30px; text-align:center; }
  .hint { font-size:12px; color:var(--muted); margin-top:10px; }
  a { color:var(--s1); }
  .rw { font-variant-numeric:tabular-nums; }
  .rw .r { color:var(--s1); } .rw .w { color:var(--s2); }
  footer { margin-top:20px; font-size:12px; color:var(--muted); }
</style>
</head>
<body>
<div class="wrap">
  <h1>Valheim component atlas</h1>
  <div class="sub">Every component, tunable field, synced ZDO key, and instance RPC in <span style="font-family:Consolas,monospace">assembly_valheim.dll</span> — searchable.</div>
  <div class="prov" id="prov"></div>

  <div class="tiles">
    <div class="tile"><div class="n" id="nComp"></div><div class="l">components</div></div>
    <div class="tile"><div class="n" id="nFields"></div><div class="l">tunable fields</div></div>
    <div class="tile"><div class="n" style="color:var(--s1)" id="nZdo"></div><div class="l">synced ZDO keys</div></div>
    <div class="tile"><div class="n" style="color:var(--s2)" id="nRpc"></div><div class="l">instance RPC names</div></div>
  </div>

  <div class="bar">
    <input id="q" type="search" placeholder="Search components, fields, ZDO keys, RPCs… (e.g. m_health, fuel, MonsterAI)">
    <button id="mComp" class="on">Components</button>
    <button id="mZdo">ZDO keys</button>
    <button id="mRpc">RPCs</button>
  </div>

  <div class="cols">
    <div class="list" id="list"></div>
    <div class="detail" id="detail"><div class="empty">Select an entry — or search. Field hits search the whole atlas, so “m_health” finds every component that has one.</div></div>
  </div>

  <div class="hint">Extracted facts only — nothing here is hand-written. Descriptions live in the reviewed
    <a href="https://github.com/djcdevelopment/comfy-quest/blob/main/tools/component-packets/README.md">field dictionaries</a>; lessons at the <a href="index.html">guide home</a>.</div>
  <footer id="foot"></footer>
</div>

<script id="atlas-data" type="application/json">__ATLAS__</script>
<script>
(function () {
  const A = JSON.parse(document.getElementById('atlas-data').textContent);
  const comps = A.Components, byName = {};
  comps.forEach(c => byName[c.Component] = c);
  const totalFields = comps.reduce((s, c) => s + c.TunableFields.filter(f => f.DeclaredBy === c.Component).length, 0);
  document.getElementById('prov').textContent = 'Source: ' + A.Source + ' — regenerate with the component-packets --all sweep after game patches.';
  document.getElementById('nComp').textContent = A.ComponentCount;
  document.getElementById('nFields').textContent = totalFields.toLocaleString();
  document.getElementById('nZdo').textContent = A.ZdoKeyCount;
  document.getElementById('nRpc').textContent = A.RpcCount;
  document.getElementById('foot').textContent = 'Generated by build_explorer.py from valheim-component-atlas.json.';

  const list = document.getElementById('list'), detail = document.getElementById('detail'), q = document.getElementById('q');
  let mode = 'comp', selected = null;
  const btns = { comp: document.getElementById('mComp'), zdo: document.getElementById('mZdo'), rpc: document.getElementById('mRpc') };
  Object.entries(btns).forEach(([m, b]) => b.onclick = () => { mode = m; selected = null; Object.values(btns).forEach(x => x.classList.remove('on')); b.classList.add('on'); render(); });
  q.oninput = () => { render(); };

  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
  function item(name, count, onclick, on) {
    const d = document.createElement('div');
    d.className = 'item' + (on ? ' on' : '');
    d.innerHTML = '<span class="nm">' + esc(name) + '</span><span class="ct">' + count + '</span>';
    d.onclick = onclick; return d;
  }

  function render() {
    const needle = q.value.trim().toLowerCase();
    list.innerHTML = '';
    if (mode === 'comp') {
      const hits = comps.filter(c =>
        !needle || c.Component.toLowerCase().includes(needle) ||
        c.TunableFields.some(f => f.Name.toLowerCase().includes(needle)) ||
        c.ZdoFields.some(z => z.Key.toLowerCase().includes(needle)) ||
        c.InstanceRpcs.some(r => r.Name.toLowerCase().includes(needle)));
      hits.forEach(c => list.appendChild(item(c.Component,
        c.TunableFields.length + ' f · ' + new Set(c.ZdoFields.map(z => z.Key)).size + ' zdo',
        () => { selected = c.Component; render(); showComp(c); }, selected === c.Component)));
      if (!hits.length) list.innerHTML = '<div class="empty">no matches</div>';
    } else if (mode === 'zdo') {
      const keys = Object.keys(A.ZdoKeyIndex).filter(k => !needle || k.toLowerCase().includes(needle) ||
        A.ZdoKeyIndex[k].Readers.concat(A.ZdoKeyIndex[k].Writers).some(x => x.toLowerCase().includes(needle)));
      keys.sort((a, b) => touch(b) - touch(a));
      keys.forEach(k => { const e = A.ZdoKeyIndex[k];
        list.appendChild(item(k, e.Readers.length + 'r/' + e.Writers.length + 'w',
          () => { selected = k; render(); showZdo(k); }, selected === k)); });
      if (!keys.length) list.innerHTML = '<div class="empty">no matches</div>';
    } else {
      const names = Object.keys(A.RpcIndex).filter(k => !needle || k.toLowerCase().includes(needle) ||
        A.RpcIndex[k].some(x => x.toLowerCase().includes(needle)));
      names.forEach(k => list.appendChild(item(k, A.RpcIndex[k].length + '×',
        () => { selected = k; render(); showRpc(k); }, selected === k)));
      if (!names.length) list.innerHTML = '<div class="empty">no matches</div>';
    }
  }
  function touch(k) { const e = A.ZdoKeyIndex[k]; return e.Readers.length + e.Writers.length; }

  function compLink(name) {
    return '<a href="#" onclick="return _open(\'' + name + '\')" style="font-family:Consolas,monospace">' + esc(name) + '</a>';
  }
  window._open = function (name) {
    const c = byName[name];
    if (c) { mode = 'comp'; selected = name; Object.values(btns).forEach(x => x.classList.remove('on')); btns.comp.classList.add('on'); render(); showComp(c); }
    return false;
  };

  function showComp(c) {
    const chain = c.InheritanceChain.map(x => x.split('.').pop()).join(' : ');
    const zdoAgg = {};
    c.ZdoFields.forEach(z => { (zdoAgg[z.Key] = zdoAgg[z.Key] || { r: [], w: [], t: z.ValueType })[z.Access === 'write' ? 'w' : 'r'].push(z.Method); });
    let h = '<h2>' + esc(c.Component) + '</h2><div class="chainline">' + esc(chain) + '</div><div class="badges">';
    c.Interfaces.forEach(i => h += '<span class="badge b1">' + esc(i) + '</span>');
    c.LifecycleMethods.forEach(l => h += '<span class="badge">' + esc(l) + '</span>');
    c.InstanceRpcs.forEach(r => h += '<span class="badge b2">' + esc(r.Name) + '</span>');
    h += '</div>';
    const keys = Object.keys(zdoAgg);
    if (keys.length) {
      h += '<h3>Synced ZDO fields (' + keys.length + ')</h3><table><tr><th>key</th><th>type</th><th>read by</th><th>written by</th></tr>';
      keys.forEach(k => { const e = zdoAgg[k];
        h += '<tr><td class="k">' + esc(k) + '</td><td class="t">' + esc(e.t) + '</td><td class="d">' + esc(e.r.join(', ') || '—') + '</td><td class="d">' + esc(e.w.join(', ') || '—') + '</td></tr>'; });
      h += '</table>';
    }
    h += '<h3>Tunable fields (' + c.TunableFields.length + ')</h3><table><tr><th>field</th><th>type</th><th>declared by</th></tr>';
    c.TunableFields.forEach(f => h += '<tr><td class="k">' + esc(f.Name) + '</td><td class="t">' + esc(f.Type) +
      '</td><td class="t">' + (f.DeclaredBy === c.Component ? esc(f.DeclaredBy) : compLink(f.DeclaredBy)) + '</td></tr>');
    h += '</table>';
    detail.innerHTML = h;
  }
  function showZdo(k) {
    const e = A.ZdoKeyIndex[k];
    let h = '<h2>' + esc(k) + '</h2><div class="chainline">ZDO key · ' + esc(e.ValueType) +
      ' · <span class="rw"><span class="r">' + e.Readers.length + ' readers</span> / <span class="w">' + e.Writers.length + ' writers</span></span></div>';
    h += '<h3>Written by</h3>' + refList(e.Writers) + '<h3>Read by</h3>' + refList(e.Readers);
    detail.innerHTML = h;
  }
  function refList(arr) {
    if (!arr.length) return '<div class="chainline">—</div>';
    return '<table><tr><th>component</th><th>method</th></tr>' + arr.map(x => {
      const [c, m] = x.split('.');
      return '<tr><td>' + compLink(c) + '</td><td class="k">' + esc(m || '') + '</td></tr>';
    }).join('') + '</table>';
  }
  function showRpc(k) {
    detail.innerHTML = '<h2>' + esc(k) + '</h2><div class="chainline">instance RPC · registered by ' + A.RpcIndex[k].length +
      ' component(s)</div><table><tr><th>component</th></tr>' +
      A.RpcIndex[k].map(c => '<tr><td>' + compLink(c) + '</td></tr>').join('') + '</table>';
  }
  render();
})();
</script>
</body>
</html>
"""

out = args.output
out.write_text(TEMPLATE.replace("__ATLAS__", data.replace("</", "<\\/")), encoding="utf-8")
print(f"{out}: {out.stat().st_size // 1024} KB")

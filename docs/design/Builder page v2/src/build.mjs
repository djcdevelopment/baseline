// Stamp the Builder page v2 artboards from one component template.
// Run from the "Builder page v2" folder:  node src/build.mjs
// The kinship tree's SVG is pre-rendered here (a template loop inside <svg> is
// foster-parented by the HTML parser), so it is the same drawing on every artboard.
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, '..');
const tpl = readFileSync(join(here, 'profile.dc.template.html'), 'utf8');

// Same data the component uses for its node overlay: name, shared pieces, first era, last era, lane x.
const bandY = { 12: 64, 11: 136, 10: 208, 8: 280, 7: 352 };
const raw = [
  ['Loanati', 564, 7, 7, 550], ['Builder e103f2a3', 201, 7, 7, 410], ['Toinin', 157, 10, 10, 620], ['Atlas', 144, 7, 7, 340],
  ['Yoni', 79, 10, 10, 690], ['Ibocain', 49, 10, 7, 270], ['Bernie', 48, 12, 7, 760], ['Heimlich', 41, 8, 8, 200],
  ['Tanagor', 38, 10, 10, 830], ['Vivicat', 13, 12, 12, 130], ['Vigor', 13, 10, 8, 900], ['Builder 17a1605b', 13, 10, 10, 60],
];
const treeSvg = () => {
  const bands = [12, 11, 10, 8, 7].map(e =>
    `<line x1="24" x2="936" y1="${bandY[e]}" y2="${bandY[e]}" stroke="#2f353e" stroke-width="1"></line>` +
    `<text x="26" y="${bandY[e] - 8}" fill="#a08e7a" font-family="JetBrains Mono, monospace" font-size="10" letter-spacing="1.2">ERA ${e}</text>`).join('');
  const branches = raw.map(([name, pieces, first, last, x]) => {
    const y = bandY[first], y2 = bandY[last];
    const w = Math.max(2, Math.min(8, 2 * Math.log10(pieces + 1))).toFixed(1);
    const op = name === 'Loanati' ? '1' : '0.72';
    let s = `<path d="M480,${y - 44} C480,${y - 4} ${x},${y - 40} ${x},${y}" fill="none" stroke="url(#kin-ember)" stroke-width="${w}" stroke-linecap="round" opacity="${op}"></path>`;
    if (y2 !== y) s += `<line x1="${x}" x2="${x}" y1="${y}" y2="${y2}" stroke="url(#kin-ember)" stroke-width="${w}" stroke-linecap="round" opacity="${op}"></line>`;
    return s;
  }).join('');
  return `<svg viewBox="0 0 960 428" style="display:block;width:100%;height:auto;" role="img" aria-label="Kinship tree">` +
    `<defs><linearGradient id="kin-ember" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="428"><stop offset="0" stop-color="#f59e0b"></stop><stop offset="1" stop-color="#d97707"></stop></linearGradient></defs>` +
    bands + `<line x1="480" x2="480" y1="64" y2="352" stroke="url(#kin-ember)" stroke-width="8" stroke-linecap="round"></line>` + branches + `</svg>`;
};

const props = ({ pair = false, row = false, w, h }) => ({
  pairDetails: { editor: 'boolean', default: pair, tsType: 'boolean', section: 'State' },
  expandRow:   { editor: 'boolean', default: row,  tsType: 'boolean', section: 'State' },
  $preview:    { width: w, height: h },
});

const boards = [
  { file: 'Main',        title: 'Builder page v2 · 1160',            w: 1160, h: 3620, x: 0,    y: 0,    p: {} },
  { file: 'PairDetails', title: 'Pair details open · one row expanded', w: 1160, h: 4200, x: 1280, y: 0,    p: { pair: true, row: true } },
  { file: 'Mobile',      title: 'Mobile · 390',                        w: 390,  h: 5200, x: 2560, y: 0,    p: {} },
];

const svg = treeSvg();
for (const b of boards) {
  const json = JSON.stringify(props({ ...b.p, w: b.w, h: b.h }));
  if (/['&<>]/.test(json)) throw new Error('data-props needs escaping: ' + json);
  writeFileSync(join(out, `${b.file}.dc.html`), tpl.replace('__TREE_SVG__', svg).replace('__PROPS__', json));
}

const canvas = {
  artboards: [
    ...boards.map(b => ({ file: `${b.file}.dc.html`, title: b.title, x: b.x, y: b.y, w: b.w, h: b.h, is_interactive: true })),
    { file: 'Before.dc.html', title: 'Today (grey-box, same scale)', x: 3070, y: 0, w: 1160, h: 4200, is_interactive: false },
  ],
  annotations: [
    { id: 'v2-story', x: 0, y: -360, w: 620, text:
      'BUILDER PAGE v2 — one story, the weeds on demand\n' +
      'This is Tugcow. Here is what they built. Here is who they built beside. Everything else is there if you go looking.\n\n' +
      '1 HERO — portrait, name, one line. The TIER / FIRST ERA / LATEST ERA labels go; the counters (the MySpace wink) stay.\n' +
      '2 THE WORK — the builder\'s best photograph from each photographed album (the first frame is already the best one), 4-up. Today the photos are the fourth thing inside each album card, a screen and a half down.\n' +
      '3 WHO THEY BUILT BESIDE — the kinship tree, on the page. The Top 8 is its caption, not a second card. Pick a branch or a chip: the pair opens below.\n' +
      '4 THE PAIR — photo, one line, the shared-builds ledger. Laurels, hearth, affinity, the facts and the tiles wait under Details.\n' +
      '5 ALBUMS BY ERA — one row per build; the disclaimer said once; contributors and the four claim buttons on expand. Newest era open, older eras folded.\n' +
      '6 NOTES — the three status lines and the manifest, together, at the bottom.\n' +
      '7 WHERE TO GO NEXT — the five figures, unchanged.' },
    { id: 'v2-labels', x: 1280, y: -240, w: 520, text:
      'THE LABEL RULE\nAn eyebrow only where a bare value is ambiguous. "Major Architect", "eras 7–12", "39 build albums", "34 %" and "1,908" carry their own meaning. The one label row that earns its place is the ledger head over the album rows (Build · Pieces · Share · Photos).' },
    { id: 'v2-cannot-show', x: 2560, y: -300, w: 440, text:
      'WHAT THE MOCK CANNOT SHOW\n• The tree is drawn from the real thread + directory data (12 closest branches; 8 under 720 px; horizontal scroll on a phone, centred on the trunk).\n• Node click ↔ chip press ↔ pair view are one state.\n• Counts are live (39 / 7,386 / 28, 34 co-builders, 7 photographed).\n• "I built this" opens the existing claim sheet; "Request…" stays inert until a built claim; "Copy this build payload" is how a claim travels — all unchanged by design.\n• Photos are placeholders here.' },
    { id: 'v2-before', x: 3070, y: -200, w: 440, text:
      'TODAY, AT THE SAME SCALE\nHero with labelled facts → three orphan sentences → Top 8 card → the full pair view (eleven sub-sections) → six album cards for era 12 alone, each repeating the disclaimer, the contributor list and four buttons → four more eras → figures. About 4,200 px for Tugcow before the fold reaches a photograph.' },
  ],
  launch: { view: 'canvas' },
};
writeFileSync(join(out, 'canvas.json'), JSON.stringify(canvas, null, 2) + '\n');
console.log('wrote', boards.map(b => b.file + '.dc.html').join(', '), '+ canvas.json (Before.dc.html is hand-written)');

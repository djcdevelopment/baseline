// Stamp the five Gallery Menu v3 artboards + canvas.json from one component template.
// Run from the v3/ folder:  node src/build.mjs
// Every artboard is the same component; only the tweak defaults and the frame differ,
// so the states can't drift apart while Derek reviews them side by side.
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, '..');
const tpl = readFileSync(join(here, 'menu.dc.template.html'), 'utf8');

const props = ({ drawer = false, era = false, sort = false, chips = true, w, h }) => ({
  drawerOpen: { editor: 'boolean', default: drawer, tsType: 'boolean', section: 'State' },
  eraMenu:    { editor: 'boolean', default: era,    tsType: 'boolean', section: 'State' },
  sortMenu:   { editor: 'boolean', default: sort,   tsType: 'boolean', section: 'State' },
  seedChips:  { editor: 'boolean', default: chips,  tsType: 'boolean', section: 'State' },
  placesShown:{ editor: 'range', default: 8, min: 4, max: 16, step: 2, unit: 'rows', tsType: 'number', section: 'Filters' },
  $preview:   { width: w, height: h },
});

const boards = [
  { file: 'Main',         title: 'Desktop · 1440 · two filters on',  w: 1440, h: 900, x: 0,    y: 0,    p: { chips: true } },
  { file: 'Drawer',       title: 'Desktop · drawer open',            w: 1440, h: 900, x: 1560, y: 0,    p: { drawer: true } },
  { file: 'Menus',        title: 'Desktop · era + sort menus',       w: 1440, h: 520, x: 0,    y: 1040, p: { era: true, sort: true, chips: false } },
  { file: 'Mobile',       title: 'Mobile · 390',                     w: 390,  h: 844, x: 1560, y: 1040, p: { chips: true } },
  { file: 'MobileDrawer', title: 'Mobile · drawer open',             w: 390,  h: 844, x: 2050, y: 1040, p: { drawer: true } },
];

for (const b of boards) {
  const json = JSON.stringify(props({ ...b.p, w: b.w, h: b.h }));
  if (/['&<>]/.test(json)) throw new Error('data-props needs escaping: ' + json);
  writeFileSync(join(out, `${b.file}.dc.html`), tpl.replace('__PROPS__', json));
}

const canvas = {
  artboards: boards.map(b => ({ file: `${b.file}.dc.html`, title: b.title, x: b.x, y: b.y, w: b.w, h: b.h, is_interactive: true })),
  annotations: [
    { id: 'v3-what-changed', x: 0, y: -330, w: 640, text:
      'GALLERY MENU v3 — what changed from v2\n' +
      '1. Re-tokened onto the Chronicler system the live viewer already ships (Bodoni Moda / Plus Jakarta Sans / JetBrains Mono; #0e141c surface, #ffc174 primary, #f59e0b flame; 4 px chips, 6 px buttons). v2\'s Playfair/Archivo and #e8a33d were placeholder drift.\n' +
      '2. Era is navigation, not a filter: header dropdown only (real links to the sibling era folders, current marked, "Builders across eras" last). The ERA chip row leaves the drawer.\n' +
      '3. Header nav keeps CHRONICLES · BUILDERS in the front door\'s mono uppercase — Builders is the photo → creators path.\n' +
      '4. Sort lives in the sticky header row; the subline carries only the count.\n' +
      '5. Places are two lists — Areas and Builds — not one; see the note beside the drawer.\n' +
      '6. Fog is a toggle ("Include fog-hidden frames"), not a facet chip: it widens the set.\n' +
      '7. Page size moves into the bottom pager (50 · 100 · 200).\n' +
      'Tiles are unchanged from the live page and are placeholders here.' },
    { id: 'v3-places', x: 1560, y: -200, w: 440, text:
      'AREAS + BUILDS\nTwo things in the data: an area is a 2 km neighbourhood ("near X", deep link #area=), a build is one structure (#build=). Build names collide without their piece count (two Sky Islands, two Tree Forts), so the count stays as small right-hand meta instead of being stripped. 8 rows each + "Show all N"; the search box narrows both; a selected row is always visible.' },
    { id: 'v3-live', x: 0, y: 1680, w: 640, text:
      'WHAT THE MOCK CANNOT SHOW (implementation spec)\n• Counts are live-narrowing: each option counts the rows that match the OTHER facets; zero-count options dim (40 %) and never disappear.\n• Header chips: weather · and kind · carry a light prefix because "Clear" and "build" are ambiguous alone; places show the name.\n• Footer button follows the sort: "Show N builds" under every build (one frame per build), "Show N photographs" otherwise. Clear all = today\'s goHome(): back to the front door, showcase sort.\n• Keyboard: focus lands in search on open (× on mobile) and returns to Filters on close; Esc order = lightbox › open menu › non-empty search (clears) › drawer; menus close on outside click or pick.\n• Sample figures in the mock (41 builds / 312 photographs / 412 setups) are illustrative.' },
    { id: 'v3-mobile', x: 2500, y: 1040, w: 360, text:
      'MOBILE ≤ 640 px\nChip strip hidden — the Filters badge carries the count. Sort is icon-only, ERA shows the name only, BUILDERS hides (it stays in the era menu), CHRONICLES is the emblem alone. Drawer is min(400 px, 92 vw); the grid drops to two columns. Real media queries, so resize the frame to test.' },
  ],
  launch: { view: 'canvas' },
};
writeFileSync(join(out, 'canvas.json'), JSON.stringify(canvas, null, 2) + '\n');
console.log('wrote', boards.map(b => b.file + '.dc.html').join(', '), 'and canvas.json');

#!/usr/bin/env python3
"""Offline terrain height for shot planning: ground_y(x, z) with no game running.

The selfie-stick planners keep needing one number the ZDO index cannot give
them: the ground. A stance is chosen, a bearing is chosen, and then the only
way to know whether the sight line dies into a hillside 80 m out was to fly
the route in game. This module answers it from disk, in milliseconds, from a
file Valheim already wrote.

Source: the game's own minimap height cache
-------------------------------------------
Valheim writes ``<World>_heightTexCache`` beside the save (worlds_local), a
2048x2048 RGBA PNG. The encoding was reverse-engineered the reliable way --
not by guessing at the bytes but by decompiling ``Minimap`` out of
``assembly_valheim.dll`` (ilspycmd) and reading the writer and the reader:

  GenerateWorldMap:            v = clamp(int(height * 127.5), 0, 65025)
                               R = v >> 8;  G = v & 0xFF;  B = 0;  A = 255
  TryLoadMinimapTextureData:   height = ((R << 8) + G) / 127.5

So the R and G bytes are one big-endian 16-bit fixed-point height in ABSOLUTE
world metres at 1/127.5 m resolution, range 0..510 m. The height sampled is
``WorldGenerator.GetBiomeHeight`` -- pristine world-gen terrain. Sea level is
y = 30 (the shader draws water wherever height < 30, see GetMaskColor).

Two caveats fall straight out of the writer:

  * ``clamp(.., 0, ..)``: world-gen heights below y=0 are stored as 0. Deep
    ocean floor here reads 0.0 and means "0 or below". Irrelevant for shot
    planning; fatal if you ever try to use this for bathymetry.
  * It is WORLD-GEN terrain. Player terraforming (hoe, pickaxe) lives in
    ``_TerrainCompiler`` ZDOs in the .db and is NOT in this cache. Residuals
    against 824 placed-structure anchors put the median gap at ~2.9 m with
    IQR ~3.1 m, so for pre-clearing sight lines the cache is the terrain;
    expect metre-scale lies exactly where builders dug.

Georeferencing -- measured, and NOT what scan_channels.py uses
--------------------------------------------------------------
The mapping below was fixed by sweeping pixel size, row direction and
sub-pixel offset against 824 compact in-world build clusters (frozen
``out/era17/clusters.json``, piece min_y as ground truth):

    col = (x - 6) / 12 + 1024          # +x -> +col (east right)
    row = 1023 - (z - 6) / 12          # +z -> -row (north UP the PNG)

    ps=12, +z up:   corr(ground, min_y) = +0.94,  residual IQR 3.1 m
    ps=10, +z down (scan_channels' georef):  corr = +0.01  -- noise

which is exactly ``Minimap.GenerateWorldMap``'s loop (m_pixelSize = 12, the
half-texel ``+ m_pixelSize/2`` included) with the texture row order inverted
between Unity and the PNG on disk.

LOUD DISAGREEMENT, on purpose: scan_channels.py maps the SIBLING file
(mapTexCache) with 10 m/px and +z DOWN, and reads 0x333333 as Ocean. The
game writes both textures in the same loop with the same pixel size, so both
files share THIS grid. Decompiled GetPixelColor says Ocean is WHITE
(255,255,255) -- as are Mountain and DeepNorth, which is why "white = water"
also needs care -- and the 0x333333 pixels sit on ground averaging y=38, dry
land (it is a dark land-biome colour, most plausibly Mistlands). The
scan_channels numbers that depend on its ocean mask (sea_at_m / sea_run_m)
inherit that error; its canopy geometry does not. Fixing that scanner is a
separate change -- this module only refuses to copy the mistake. Evidence:
``out/era17/terrain-validation.md``.

Layer 2 (optional): player terrain edits from the world .db
------------------------------------------------------------
The cache is pristine world-gen; the hoe and the pickaxe live in
``_TerrainCompiler`` ZDOs in the .db, one per touched 64 m zone, each holding
per-vertex height deltas on the zone's 65x65 one-metre grid (gzip-packed
``TCData``; format read out of TerrainComp.Save/Load, applied deltas clamped
to +-8 m of base exactly as TerrainComp.ApplyToHeightmap does). The extractor
walks the .db's packed ZDO stream (format from ZDOMan.Load + ZDO.Load,
data version 37; ``_TerrainCompiler`` prefab hash -367065113 and ``TCData``
key hash 1305470367 both verified against the steward DuckDB) and freezes
every modified vertex into a small .npz:

  python terrain.py --extract-edits <frozen ComfyEra17_backup_auto-*.db> \
      --edits-out out/era17/terrain-edits.npz

NEVER point it at the live ComfyEra17.db -- a capture may be running; use a
frozen ``_backup_auto-*`` sibling. With ``--edits`` the module then answers
from cache + edit delta and SAYS SO: every CLI row carries a layer column
(``base`` vs ``edited``), because the two layers have different failure
modes -- the cache is smooth-but-everywhere, the edits are exact-but-sparse,
and their sum inherits the cache's 12 m interpolation error wherever the
builder did not touch.

Usage
-----
  # heights at points
  python terrain.py --probe -5758.8,-1547.9 0,0

  # height profile along a segment (what sight-line pre-clearing wants)
  python terrain.py --profile -6258.8,-1547.9 -5258.8,-1547.9 --steps 100

  # same, rendered as a PNG cross-section
  python terrain.py --profile -6258.8,-1547.9 -5258.8,-1547.9 --steps 200 \
      --png out/era17/terrain-profile.png

As a library:

  from terrain import TerrainGrid
  t = TerrainGrid.load()            # ComfyEra17 from the default worlds dir
  t.ground_y(x, z)                  # float metres, bilinear, sea level 30.0
  t.is_water(x, z)                  # ground below sea level
"""
import argparse
import math
import os
import re
import sys

# Minimap.GenerateWorldMap constants, verified against this world's cache.
PIXEL_SIZE_M = 12.0          # m_pixelSize on the 2048 texture (NOT the 10 of scan_channels)
TEXTURE_SIZE = 2048          # m_textureSize
HEIGHT_SCALE = 127.5         # metres * 127.5 -> stored 16-bit value
SEA_LEVEL_Y = 30.0           # ZoneSystem water level; the map shader's water threshold
DEFAULT_WORLD = "ComfyEra17"
DEFAULT_WORLDS_DIR = os.path.expandvars(
    r"%USERPROFILE%\AppData\LocalLow\IronGate\Valheim\worlds_local")

# Layer 2 constants. Both hashes are GetStableHashCode values; the prefab one
# is cross-checked against the steward DuckDB's zdo table, the key one against
# a reimplementation of the algorithm that reproduces the prefab hash exactly.
TERRAIN_COMPILER_HASH = -367065113   # "_TerrainCompiler"
TCDATA_HASH = 1305470367             # "TCData"
ZONE_HALF_M = 32                     # heightmap vertex (0,0) sits at zone centre - 32
ZONE_VERTS = 65                      # 65x65 vertices per zone, 1 m apart
EDIT_CLAMP_M = 8.0                   # ApplyToHeightmap clamps deltas to base +- 8


class TerrainGrid:
    """World-gen terrain heights for one world, decoded from its heightTexCache.

    The grid is read once into a float32 array (16 MB) and sampled with
    bilinear interpolation, clamped at the raster edge -- the same wrap mode
    (TextureWrapMode.Clamp) the game gives the live texture. Points beyond
    the +-12.3 km the raster covers therefore return the edge value, which
    beyond the 10.5 km world edge is 0.0 anyway.
    """

    def __init__(self, heights, world, path):
        self.h = heights            # (2048, 2048) float32, world metres
        self.world = world
        self.path = path
        self.source = "worldgen-cache"   # which layer answered; see module docstring
        self.edits = None                # optional TerrainEdits layer

    @classmethod
    def load(cls, world=DEFAULT_WORLD, worlds_dir=DEFAULT_WORLDS_DIR, path=None):
        try:
            import numpy as np
            from PIL import Image
        except ImportError:
            sys.exit("terrain.py needs numpy and Pillow")
        if path is None:
            path = os.path.join(worlds_dir, f"{world}_heightTexCache")
        if not os.path.exists(path):
            sys.exit(f"no height cache at {path}\n"
                     f"       Valheim writes it beside the save; open the world once if it is missing.")
        arr = np.asarray(Image.open(path))
        if arr.shape[:2] != (TEXTURE_SIZE, TEXTURE_SIZE) or arr.shape[2] < 2:
            sys.exit(f"unexpected height cache shape {arr.shape} at {path} "
                     f"(expected {TEXTURE_SIZE}x{TEXTURE_SIZE} RGBA)")
        # height = ((R << 8) + G) / 127.5  -- Minimap.TryLoadMinimapTextureData
        h = ((arr[..., 0].astype("uint16") << 8) | arr[..., 1]).astype("float32")
        h /= HEIGHT_SCALE
        return cls(h, world, path)

    # -- coordinate transform ------------------------------------------------
    # Inverse of GenerateWorldMap's  wx = (j - 1024) * 12 + 6  (and wy/rows),
    # with the PNG row order inverted relative to the Unity texture: north up.
    @staticmethod
    def world_to_pixel(x, z):
        """(x, z) world metres -> (row_f, col_f) fractional PIL pixel coords."""
        col = (x - PIXEL_SIZE_M / 2.0) / PIXEL_SIZE_M + TEXTURE_SIZE / 2
        row = (TEXTURE_SIZE / 2 - 1) - (z - PIXEL_SIZE_M / 2.0) / PIXEL_SIZE_M
        return row, col

    def ground_y(self, x, z):
        """World-gen terrain height in world metres at (x, z). Bilinear."""
        row, col = self.world_to_pixel(x, z)
        n = TEXTURE_SIZE - 1
        # Clamp keeps the sample inside the raster; fractions then interpolate
        # toward the edge texel, matching TextureWrapMode.Clamp.
        r0 = min(max(int(math.floor(row)), 0), n - 1)
        c0 = min(max(int(math.floor(col)), 0), n - 1)
        fr = min(max(row - r0, 0.0), 1.0)
        fc = min(max(col - c0, 0.0), 1.0)
        h = self.h
        return float(h[r0, c0] * (1 - fr) * (1 - fc)
                     + h[r0, c0 + 1] * (1 - fr) * fc
                     + h[r0 + 1, c0] * fr * (1 - fc)
                     + h[r0 + 1, c0 + 1] * fr * fc)

    def ground_y_detail(self, x, z):
        """(ground_y, layer) -- layer is "base" or "edited".

        "edited" means at least one of the four surrounding 1 m edit vertices
        carries a player terraforming delta; the height is then cache + the
        bilinear delta. Planners that care about provenance read this; the
        plain ground_y() stays a bare float for the common case.
        """
        base = self.ground_y(x, z)
        if self.edits is not None:
            d = self.edits.delta(x, z)
            if d != 0.0:
                return base + d, "edited"
        return base, "base"

    def is_water(self, x, z):
        """True where ground (edits included, if loaded) sits below sea level."""
        return self.ground_y_detail(x, z)[0] < SEA_LEVEL_Y

    def profile(self, x1, z1, x2, z2, steps):
        """[(dist_m, x, z, ground_y, layer)] at steps+1 points along the segment."""
        length = math.hypot(x2 - x1, z2 - z1)
        out = []
        for i in range(steps + 1):
            t = i / steps
            x, z = x1 + (x2 - x1) * t, z1 + (z2 - z1) * t
            y, layer = self.ground_y_detail(x, z)
            out.append((length * t, x, z, y, layer))
        return out


class TerrainEdits:
    """Layer 2: player terraforming deltas, frozen out of a .db snapshot.

    Sparse by nature -- a few hundred thousand touched vertices against the
    354 million points of the 1 m world grid -- so it is held as a dict from
    packed (x, z) integer vertex to delta metres, and sampled bilinearly with
    untouched vertices contributing 0. The npz on disk is three flat arrays
    (vx, vz int16; delta float32) because that is greppable, diffable in size,
    and free of pickle.
    """

    def __init__(self, deltas, path, meta=""):
        self._d = deltas
        self.path = path
        self.meta = meta

    @classmethod
    def load(cls, path):
        import numpy as np
        z = np.load(path)
        vx = z["vx"].astype(np.int64)
        vz = z["vz"].astype(np.int64)
        dv = z["delta"].astype(np.float64)
        deltas = dict(zip(((vx + 32768) << 17) + (vz + 32768), dv))
        return cls(deltas, path, meta=str(z.get("meta", "")))

    def delta(self, x, z):
        """Bilinear player-edit delta at (x, z); 0.0 where nobody dug."""
        x0, z0 = math.floor(x), math.floor(z)
        fx, fz = x - x0, z - z0
        g = self._d.get
        k = ((x0 + 32768) << 17) + (z0 + 32768)
        d00 = g(k, 0.0)
        d10 = g(k + (1 << 17), 0.0)
        d01 = g(k + 1, 0.0)
        d11 = g(k + (1 << 17) + 1, 0.0)
        return (d00 * (1 - fx) * (1 - fz) + d10 * fx * (1 - fz)
                + d01 * (1 - fx) * fz + d11 * fx * fz)


def extract_edits(db_path, out_path):
    """Walk a FROZEN .db snapshot and freeze every terraformed vertex to npz.

    This is a sequential decode of the packed ZDO stream -- there is no index
    to seek by, so every one of the ~9M ZDOs is walked and everything except
    ``_TerrainCompiler``'s ``TCData`` byte arrays is skipped by size. The
    stream layout is ZDOMan.Load/ZDO.Load (data version >= 33: two-byte
    high-bit count encoding); the TCData payload layout is TerrainComp.Load
    behind a gzip (Utils.Compress). Refuses the live .db by name on purpose:
    the capture rigs may be holding it open mid-save.
    """
    import gzip
    import struct
    import numpy as np

    base = os.path.basename(db_path).lower()
    if base in (DEFAULT_WORLD.lower() + ".db", DEFAULT_WORLD.lower() + ".db.old"):
        sys.exit(f"refusing the live save {db_path}; use a frozen *_backup_auto-*.db sibling")

    with open(db_path, "rb") as fh:
        buf = fh.read()
    u16 = struct.Struct("<H").unpack_from
    i32 = struct.Struct("<i").unpack_from
    f32x2 = struct.Struct("<ff").unpack_from

    version, = i32(buf, 0)
    o = 4
    if version >= 4:
        o += 8                               # netTime double
    o += 8 + 4                               # sessionID + nextUid
    count, = i32(buf, o)
    o += 4
    if version < 31:
        sys.exit(f"data version {version}: pre-31 per-ZDO format not implemented "
                 f"(this world saves at 37)")
    print(f"  {db_path}: data version {version}, {count} zdos")

    deltas = {}
    tc = 0
    for n in range(count):
        flags, = u16(buf, o)
        o += 2
        po = o + 4                           # position floats, after the sector
        o += 4 + 12
        prefab, = i32(buf, o)
        o += 4
        if flags & 0x1000:
            o += 12                          # rotation
        low = flags & 0xFF
        if not low:
            continue
        if low & 0x01:                       # connection: byte type + int hash
            o += 5
        for bit, size in ((0x02, 8), (0x04, 16), (0x08, 20), (0x10, 8), (0x20, 12)):
            if low & bit:                    # fixed-size typed dicts
                cnt = buf[o]
                o += 1
                if cnt & 0x80:
                    cnt = ((cnt & 0x7F) << 8) | buf[o]
                    o += 1
                o += cnt * size
        if low & 0x40:                       # strings: hash + 7-bit-length str
            cnt = buf[o]
            o += 1
            if cnt & 0x80:
                cnt = ((cnt & 0x7F) << 8) | buf[o]
                o += 1
            for _ in range(cnt):
                o += 4
                sl, shift = 0, 0
                while True:
                    b = buf[o]
                    o += 1
                    sl |= (b & 0x7F) << shift
                    if not b & 0x80:
                        break
                    shift += 7
                o += sl
        if low & 0x80:                       # byte arrays: the whole point
            cnt = buf[o]
            o += 1
            if cnt & 0x80:
                cnt = ((cnt & 0x7F) << 8) | buf[o]
                o += 1
            for _ in range(cnt):
                kh, = i32(buf, o)
                bl, = i32(buf, o + 4)
                o += 8
                if prefab == TERRAIN_COMPILER_HASH and kh == TCDATA_HASH:
                    zx, zz = struct.unpack_from("<f", buf, po)[0], \
                             struct.unpack_from("<f", buf, po + 8)[0]
                    _apply_tcdata(gzip.decompress(buf[o:o + bl]),
                                  zx, zz, deltas, f32x2)
                    tc += 1
                o += bl
        if n % 1000000 == 0 and n:
            print(f"    ...{n} zdos, {tc} compilers, {len(deltas)} vertices")

    print(f"  {tc} terrain compilers -> {len(deltas)} modified vertices")
    keys = np.fromiter(deltas.keys(), dtype=np.int64, count=len(deltas))
    vx = ((keys >> 17) - 32768).astype(np.int16)
    vz = ((keys & 0x1FFFF) - 32768).astype(np.int16)
    dv = np.fromiter(deltas.values(), dtype=np.float32, count=len(deltas))
    np.savez_compressed(out_path, vx=vx, vz=vz, delta=dv,
                        meta=f"from {os.path.basename(db_path)} data_version={version}")
    print(f"  {out_path}")


def _apply_tcdata(raw, zone_x, zone_z, deltas, f32x2):
    """One decompressed TCData blob -> per-vertex deltas into the shared dict.

    Vertex k on the 65x65 grid is (row i = k // 65) along +z, (col j = k % 65)
    along +x, spanning zone centre +- 32 m -- TerrainComp.ApplyToHeightmap's
    ``i * (width+1) + j`` with Heightmap's x-inner ordering. Neighbouring
    zones share border vertices; last writer wins, which is harmless because
    the game clamps both to the same base.
    """
    import struct
    n, = struct.unpack_from("<i", raw, 24)   # after ver, ops, lastOp vec3+radius
    o = 28
    if n != ZONE_VERTS * ZONE_VERTS:
        return                               # not a standard 64 m zone; skip
    bx = int(zone_x) - ZONE_HALF_M
    bz = int(zone_z) - ZONE_HALF_M
    for k in range(n):
        if raw[o]:
            lvl, sm = f32x2(raw, o + 1)
            o += 9
            d = lvl + sm
            if d > EDIT_CLAMP_M:
                d = EDIT_CLAMP_M
            elif d < -EDIT_CLAMP_M:
                d = -EDIT_CLAMP_M
            if d:
                key = ((bx + (k % ZONE_VERTS) + 32768) << 17) \
                    + (bz + (k // ZONE_VERTS) + 32768)
                deltas[key] = d
        else:
            o += 1


def render_profile_png(samples, out_path, title=""):
    """A cross-section a human can eyeball: ground filled, sea level ruled.

    Deliberately PIL-only -- the repo's dependency posture is numpy+Pillow, and
    a terrain silhouette does not need an axes library to be legible.
    """
    from PIL import Image, ImageDraw
    W, H = 1200, 400
    ml, mr, mt, mb = 60, 20, 28, 34
    dists = [s[0] for s in samples]
    ys = [s[3] for s in samples]
    y_lo = min(0.0, min(ys))
    y_hi = max(max(ys), SEA_LEVEL_Y) + 8.0
    im = Image.new("RGB", (W, H), (250, 250, 248))
    dr = ImageDraw.Draw(im)

    def px(d, y):
        fx = ml + (W - ml - mr) * (d / dists[-1] if dists[-1] else 0.0)
        fy = mt + (H - mt - mb) * (1.0 - (y - y_lo) / (y_hi - y_lo))
        return fx, fy

    # water band up to sea level, then the ground silhouette over it
    sx0, sy = px(0, SEA_LEVEL_Y)[0], px(0, SEA_LEVEL_Y)[1]
    dr.rectangle([sx0, sy, px(dists[-1], 0)[0], px(0, y_lo)[1]], fill=(205, 222, 235))
    poly = [px(s[0], s[3]) for s in samples]
    poly += [px(dists[-1], y_lo), px(0, y_lo)]
    dr.polygon(poly, fill=(150, 137, 120))
    dr.line([px(s[0], s[3]) for s in samples], fill=(80, 70, 58), width=2)
    dr.line([px(0, SEA_LEVEL_Y), px(dists[-1], SEA_LEVEL_Y)], fill=(60, 110, 160), width=1)
    dr.text((ml + 4, sy - 14), f"sea level y={SEA_LEVEL_Y:g}", fill=(60, 110, 160))
    # simple elevation rules every 25 m
    y = math.ceil(y_lo / 25.0) * 25.0
    while y <= y_hi:
        fx, fy = px(0, y)
        dr.line([(ml - 4, fy), (ml, fy)], fill=(120, 120, 120))
        dr.text((6, fy - 6), f"{y:g} m", fill=(120, 120, 120))
        y += 25.0
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        d = dists[-1] * frac
        fx, fy = px(d, y_lo)
        dr.text((fx - 14, H - mb + 6), f"{d:.0f} m", fill=(120, 120, 120))
    if title:
        dr.text((ml, 8), title, fill=(60, 60, 60))
    im.save(out_path)
    return out_path


def parse_xz(s):
    try:
        x, z = s.split(",")
        return float(x), float(z)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected X,Z -- got {s!r}")


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    # Half this world has negative coordinates, so "--probe -5758.8,-1547.9"
    # must parse. argparse's stock negative-number matcher rejects the comma
    # and then reads the coordinate as an unknown option; widen it.
    p._negative_number_matcher = re.compile(r"^-\d+[\d.,-]*$")
    p.add_argument("--world", default=DEFAULT_WORLD)
    p.add_argument("--worlds-dir", default=DEFAULT_WORLDS_DIR)
    p.add_argument("--cache", default=None,
                   help="explicit path to a *_heightTexCache (overrides --world)")
    p.add_argument("--probe", type=parse_xz, nargs="+", metavar="X,Z",
                   help="print ground_y at each point")
    p.add_argument("--profile", type=parse_xz, nargs=2, metavar=("X1,Z1", "X2,Z2"),
                   help="height profile along the segment")
    p.add_argument("--steps", type=int, default=64,
                   help="samples along --profile (default 64)")
    p.add_argument("--png", default=None,
                   help="with --profile: also render the cross-section here")
    p.add_argument("--edits", default=None, metavar="NPZ",
                   help="load a player-edits layer extracted by --extract-edits")
    p.add_argument("--extract-edits", default=None, metavar="DB",
                   help="walk a FROZEN *_backup_auto-*.db and freeze terraforming "
                        "deltas to --edits-out (never the live .db)")
    p.add_argument("--edits-out", default=None, metavar="NPZ",
                   help="where --extract-edits writes its layer")
    args = p.parse_args()

    if args.extract_edits:
        if not args.edits_out:
            p.error("--extract-edits needs --edits-out")
        extract_edits(args.extract_edits, args.edits_out)
        if not args.probe and not args.profile:
            return
    elif not args.probe and not args.profile:
        p.error("nothing to do: pass --probe, --profile or --extract-edits")

    t = TerrainGrid.load(args.world, args.worlds_dir, args.cache)
    if args.edits:
        t.edits = TerrainEdits.load(args.edits)
        t.source = "worldgen-cache+edits"

    if args.probe:
        print(f"# {t.world}  source={t.source}  sea_level_y={SEA_LEVEL_Y:g}")
        print("x\tz\tground_y\twater\tlayer")
        for x, z in args.probe:
            y, layer = t.ground_y_detail(x, z)
            print(f"{x:.1f}\t{z:.1f}\t{y:.2f}\t"
                  f"{'WATER' if y < SEA_LEVEL_Y else 'land'}\t{layer}")

    if args.profile:
        (x1, z1), (x2, z2) = args.profile
        samples = t.profile(x1, z1, x2, z2, args.steps)
        print(f"# {t.world}  profile ({x1:g},{z1:g}) -> ({x2:g},{z2:g})  "
              f"length={samples[-1][0]:.1f} m  source={t.source}")
        print("dist_m\tx\tz\tground_y\twater\tlayer")
        for d, x, z, y, layer in samples:
            print(f"{d:.1f}\t{x:.1f}\t{z:.1f}\t{y:.2f}\t"
                  f"{'WATER' if y < SEA_LEVEL_Y else 'land'}\t{layer}")
        if args.png:
            path = render_profile_png(
                samples, args.png,
                title=f"{t.world}  ({x1:g},{z1:g}) -> ({x2:g},{z2:g})")
            print(f"# wrote {path}", file=sys.stderr)


if __name__ == "__main__":
    main()

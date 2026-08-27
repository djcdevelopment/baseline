import contextlib
import importlib.util
import io
import json
import math
import os
import pathlib
import sys
import tempfile
import unittest

import duckdb
from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "scan_clusters", ROOT / "tools" / "selfie-stick" / "scan_clusters.py"
)
SCAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCAN)
BUILD_SPEC = importlib.util.spec_from_file_location(
    "build_valheim_index", ROOT / "tools" / "selfie-stick" / "build_valheim_index.py"
)
BUILD = importlib.util.module_from_spec(BUILD_SPEC)
BUILD_SPEC.loader.exec_module(BUILD)
PLAN_SPEC = importlib.util.spec_from_file_location(
    "plan_shots", ROOT / "tools" / "selfie-stick" / "plan_shots.py"
)
PLAN = importlib.util.module_from_spec(PLAN_SPEC)
PLAN_SPEC.loader.exec_module(PLAN)
SELFIE_DIR = str(ROOT / "tools" / "selfie-stick")
if SELFIE_DIR not in sys.path:
    sys.path.insert(0, SELFIE_DIR)          # scan_features imports scan_clusters
FEAT_SPEC = importlib.util.spec_from_file_location(
    "scan_features", ROOT / "tools" / "selfie-stick" / "scan_features.py"
)
FEAT = importlib.util.module_from_spec(FEAT_SPEC)
FEAT_SPEC.loader.exec_module(FEAT)
OVER_SPEC = importlib.util.spec_from_file_location(
    "check_overlay", ROOT / "tools" / "selfie-stick" / "check_overlay.py"
)
OVER = importlib.util.module_from_spec(OVER_SPEC)
OVER_SPEC.loader.exec_module(OVER)
PICK_SPEC = importlib.util.spec_from_file_location(
    "pick_targets", ROOT / "tools" / "selfie-stick" / "pick_targets.py"
)
PICK = importlib.util.module_from_spec(PICK_SPEC)
PICK_SPEC.loader.exec_module(PICK)
INTERIOR_SPEC = importlib.util.spec_from_file_location(
    "plan_interiors", ROOT / "tools" / "selfie-stick" / "plan_interiors.py"
)
INTERIOR = importlib.util.module_from_spec(INTERIOR_SPEC)
INTERIOR_SPEC.loader.exec_module(INTERIOR)
NIGHT_SPEC = importlib.util.spec_from_file_location(
    "plan_nightsky", ROOT / "tools" / "selfie-stick" / "plan_nightsky.py"
)
NIGHT = importlib.util.module_from_spec(NIGHT_SPEC)
NIGHT_SPEC.loader.exec_module(NIGHT)
CHAN_SPEC = importlib.util.spec_from_file_location(
    "plan_channel", ROOT / "tools" / "selfie-stick" / "plan_channel.py"
)
CHAN = importlib.util.module_from_spec(CHAN_SPEC)
CHAN_SPEC.loader.exec_module(CHAN)


def _cluster(cid, creator, x=0.0, z=0.0, score=10.0, size_y=20.0, **extra):
    c = {"cluster_id": cid, "top_creator_id": creator, "center_x": x, "center_z": z,
         "score": score, "size_y": size_y, "size_x": 30.0, "size_z": 30.0,
         "min_y": 10.0, "max_y": 10.0 + size_y, "pieces": 500, "region": "in-world",
         "diagonal_m": 50.0, "rank": cid, "sky": False}
    c.update(extra)
    return c


def _corpus(tmp, clusters, shot_ids):
    cpath = pathlib.Path(tmp) / "clusters.json"
    ipath = pathlib.Path(tmp) / "index.json"
    cpath.write_text(json.dumps({"world": "T", "clusters": clusters}), encoding="utf-8")
    ipath.write_text(json.dumps({"images": [{"cluster_id": i} for i in shot_ids]}),
                     encoding="utf-8")
    return str(cpath), str(ipath)


def _run(module, argv):
    """Run a script's main() under a given argv, returning what it put on stdout."""
    out = io.StringIO()
    old = sys.argv
    sys.argv = argv
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            module.main()
    finally:
        sys.argv = old
    return out.getvalue()


class SnapshotSelectionTests(unittest.TestCase):
    def setUp(self):
        self.db = duckdb.connect(":memory:")
        self.db.execute(
            """
            CREATE TABLE world_snapshot(
              snapshot_id BIGINT, source_path TEXT, parsed_at TEXT,
              world_id TEXT, world_name TEXT
            )
            """
        )
        self.db.executemany(
            "INSERT INTO world_snapshot VALUES (?, ?, ?, ?, ?)",
            [
                (1, "Era16.db", "old", "ComfyEra16", "Comfy Era 16"),
                (2, "Era17-a.db", "newer", "ComfyEra17", "Comfy Era 17"),
                (3, "Era17-b.db", "newest", "ComfyEra17", "Comfy Era 17"),
            ],
        )

    def tearDown(self):
        self.db.close()

    def test_world_id_selects_newest_snapshot(self):
        row = SCAN.select_snapshot(self.db, world_id="ComfyEra17")
        self.assertEqual(3, row[0])

    def test_snapshot_id_is_exact(self):
        row = SCAN.select_snapshot(self.db, snapshot_id=2)
        self.assertEqual("Era17-a.db", row[1])

    def test_multi_snapshot_cache_requires_selection(self):
        with self.assertRaisesRegex(ValueError, "pass --world-id or --snapshot-id"):
            SCAN.select_snapshot(self.db)

    def test_legacy_single_snapshot_remains_supported(self):
        legacy = duckdb.connect(":memory:")
        try:
            legacy.execute("CREATE TABLE world_snapshot(source_path TEXT, parsed_at TEXT)")
            legacy.execute("INSERT INTO world_snapshot VALUES ('Legacy.db', 'old')")
            row = SCAN.select_snapshot(legacy)
            self.assertIsNone(row[0])
            self.assertEqual("Legacy.db", row[1])
        finally:
            legacy.close()


class GalleryImageTests(unittest.TestCase):
    def test_ui_and_detail_crops_are_applied_before_resize(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = pathlib.Path(temp_dir) / "source.png"
            destination = pathlib.Path(temp_dir) / "detail.webp"
            Image.new("RGB", (100, 80), "navy").save(source)

            BUILD.make_thumb(
                source,
                destination,
                px=100,
                crop_right_ui_px=20,
                detail_crop_fraction=0.25,
            )

            with Image.open(destination) as rendered:
                self.assertEqual((40, 40), rendered.size)

    def test_ui_crop_cannot_remove_the_whole_image(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = pathlib.Path(temp_dir) / "source.png"
            Image.new("RGB", (10, 10), "navy").save(source)
            with self.assertRaisesRegex(ValueError, "wider than the source"):
                BUILD.make_thumb(source, pathlib.Path(temp_dir) / "bad.webp", crop_right_ui_px=10)


class AreaAssignmentTests(unittest.TestCase):
    """Neighbourhoods on a 2 km grid, and the promise that they ship no location."""

    @staticmethod
    def cluster(cid, x, z, pieces=100):
        return {"cluster_id": cid, "center_x": x, "center_z": z, "pieces": pieces}

    def test_same_cell_shares_an_area(self):
        areas = BUILD.assign_areas(
            [self.cluster(1, 10, 10), self.cluster(2, 1990, 1990)], {})
        self.assertEqual(areas[1][0], areas[2][0])

    def test_neighbouring_cells_are_separate_areas(self):
        areas = BUILD.assign_areas(
            [self.cluster(1, 1990, 10), self.cluster(2, 2010, 10)], {})
        self.assertNotEqual(areas[1][0], areas[2][0])

    def test_negative_coordinates_land_in_their_own_cell(self):
        areas = BUILD.assign_areas(
            [self.cluster(1, -10, -10), self.cluster(2, 10, 10)], {})
        self.assertNotEqual(areas[1][0], areas[2][0])

    def test_ids_are_a_sequence_ordered_by_mass_not_a_grid_reference(self):
        """The id must not encode the cell, because a cell is a coordinate.

        This is the assertion that keeps area_id out of scrub_index.py's DROP
        list: ids are 1..N ordered by piece mass, so they say which area is
        biggest and nothing whatsoever about where it is.
        """
        clusters = [self.cluster(1, -8000, 4000, pieces=10),
                    self.cluster(2, 6000, -2000, pieces=900),
                    self.cluster(3, 0, 0, pieces=100)]
        areas = BUILD.assign_areas(clusters, {})
        self.assertEqual([1, 2, 3], sorted(a for a, _ in areas.values()))
        self.assertEqual(1, areas[2][0])          # heaviest area is id 1
        self.assertEqual(3, areas[1][0])          # lightest is last

    def test_label_prefers_a_named_build_over_a_bigger_nameless_one(self):
        """An area named after a build nobody photographed is worse than a number.

        Only photographed structures get names, and the biggest build in a cell
        is usually not one of them.
        """
        clusters = [self.cluster(1, 10, 10, pieces=9000),
                    self.cluster(2, 20, 20, pieces=5)]
        self.assertEqual("near Black Tower",
                         BUILD.assign_areas(clusters, {"2": "Black Tower"})[1][1])

    def test_label_falls_back_to_the_area_number(self):
        areas = BUILD.assign_areas([self.cluster(1, 10, 10)], {})
        self.assertEqual("area 1", areas[1][1])

    def test_area_fields_are_absent_for_an_unknown_cluster(self):
        self.assertEqual({}, BUILD.area_fields({}, {"cluster_id": 99}))


class TargetSelectionTests(unittest.TestCase):
    """Targeting optimises coverage, because nothing predicts quality.

    Measured over 268 builds with three or more scored frames, every structural
    attribute correlates with photo quality at |r| <= 0.25 and most are negative
    -- the ranking score itself sits at -0.136. So the selector's job is who and
    where the gallery covers, not which build will photograph best.
    """

    def test_creator_tier_takes_one_build_each_and_skips_the_represented(self):
        clusters = [_cluster(1, 100, score=9), _cluster(2, 100, score=8),
                    _cluster(3, 200, score=7), _cluster(4, 300, score=6)]
        with tempfile.TemporaryDirectory() as tmp:
            c, i = _corpus(tmp, clusters, shot_ids=[3])      # creator 200 covered
            ids = _run(PICK, ["pick_targets.py", "--clusters", c, "--index", i,
                              "--strategy", "creators", "--count", "10"]).strip()
        picked = sorted(int(x) for x in ids.split(","))
        self.assertEqual([1, 4], picked)                     # best of 100, plus 300
        self.assertNotIn(2, picked)                          # creator 100 once only

    def test_never_returns_an_already_photographed_cluster(self):
        clusters = [_cluster(n, 100 + n) for n in range(1, 6)]
        with tempfile.TemporaryDirectory() as tmp:
            c, i = _corpus(tmp, clusters, shot_ids=[1, 2, 3])
            ids = _run(PICK, ["pick_targets.py", "--clusters", c, "--index", i,
                              "--count", "10"]).strip()
        self.assertEqual([4, 5], sorted(int(x) for x in ids.split(",")))

    def test_cell_tier_reaches_a_2km_cell_with_no_photograph(self):
        clusters = [_cluster(1, 100, x=0, z=0), _cluster(2, 100, x=50, z=50),
                    _cluster(3, 100, x=9000, z=9000)]
        with tempfile.TemporaryDirectory() as tmp:
            c, i = _corpus(tmp, clusters, shot_ids=[1])
            ids = _run(PICK, ["pick_targets.py", "--clusters", c, "--index", i,
                              "--strategy", "cells", "--count", "10"]).strip()
        picked = [int(x) for x in ids.split(",")]
        self.assertIn(3, picked)          # its cell holds nothing yet
        self.assertNotIn(2, picked)       # shares a cell with the photographed 1

    def test_sky_and_chained_clusters_are_never_offered(self):
        clusters = [_cluster(1, 100), _cluster(2, 200, sky=True),
                    _cluster(3, 300, size_y=2297.1)]
        with tempfile.TemporaryDirectory() as tmp:
            c, i = _corpus(tmp, clusters, shot_ids=[])
            ids = _run(PICK, ["pick_targets.py", "--clusters", c, "--index", i,
                              "--count", "10"]).strip()
        self.assertEqual([1], [int(x) for x in ids.split(",")])


class BrokenClusterGuardTests(unittest.TestCase):
    """A 2 km column is not a structure, and --include-ids must not force one.

    Era 17's cluster 2 measures 2,297 m tall with a 5,195 m diagonal: union-find
    chained a sky platform to ground builds through a vertical column, and the
    planner would aim a camera at a centroid in open air. The tallest real build
    measured is 177.9 m, so the 300 m threshold carries a 1.7x margin.
    """

    def _plan(self, tmp, clusters, extra=()):
        cpath = pathlib.Path(tmp) / "clusters.json"
        cpath.write_text(json.dumps({"world": "T", "clusters": clusters}), encoding="utf-8")
        out = pathlib.Path(tmp) / "plan.json"
        _run(PLAN, ["plan_shots.py", "--clusters", str(cpath), "--out", str(out),
                    "--region", "in-world"] + list(extra))
        return json.loads(out.read_text(encoding="utf-8"))

    def test_a_chained_column_is_dropped_and_a_tall_build_is_kept(self):
        clusters = [_cluster(1, 100, size_y=177.9), _cluster(2, 200, size_y=2297.1)]
        with tempfile.TemporaryDirectory() as tmp:
            plan = self._plan(tmp, clusters)
        self.assertEqual({1}, {s["cluster_id"] for s in plan["plan"]})

    def test_include_ids_cannot_force_one_through(self):
        """Placed before the include step this guard passed --include-ids "2,68"
        straight past it and planned fifteen shots of two vertical chains."""
        clusters = [_cluster(1, 100), _cluster(2, 200, size_y=2297.1)]
        with tempfile.TemporaryDirectory() as tmp:
            plan = self._plan(tmp, clusters,
                              ["--skip", "100000", "--include-ids", "1,2"])
        self.assertEqual({1}, {s["cluster_id"] for s in plan["plan"]})

    def test_fixed_elevation_overrides_the_tilt_by_shape_rule(self):
        """A floating platform wants the camera aimed down; elevation_for levels
        off on anything tall, which is right on the ground and wrong at y=5000."""
        tall = [_cluster(1, 100, size_y=40.0)]
        with tempfile.TemporaryDirectory() as tmp:
            shaped = self._plan(tmp, tall, ["--elevation", "65"])
            fixed = self._plan(tmp, tall, ["--elevation", "65", "--fixed-elevation"])
        self.assertLess(shaped["plan"][0]["elevation_deg"], 65.0)
        self.assertEqual(65.0, fixed["plan"][0]["elevation_deg"])

    def test_time_of_day_moves_the_orbits_and_leaves_dawn_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self._plan(tmp, [_cluster(1, 100)], ["--time-of-day", "0.9"])
        by_slot = {s["shot"]: s["time_of_day"] for s in plan["plan"]}
        self.assertEqual(0.9, by_slot["orbit1"])
        self.assertEqual(0.9, by_slot["orbit4"])
        self.assertEqual(PLAN.GOLDEN_AM, by_slot["dawn"])


if __name__ == "__main__":
    unittest.main()


class SeatVocabularyTests(unittest.TestCase):
    """Every sit-able prefab in Valheim 0.221.12, not every craftable one.

    The vocabulary was first written from the build menu, so the three seats that
    are world props rather than recipes were missing -- the prefab dump marks them
    piece:false. They are wearNTear:true, players place them from the prefab table,
    and 7,453 of them in Era 17 carry a creator id. Deleting them again because
    they do not start with "piece_" is the regression this guards.
    """

    PROP_SEATS = ("dvergrprops_chair", "dvergrprops_stool", "mountainkit_chair")

    def test_prop_seats_are_in_the_vocabulary(self):
        for name in self.PROP_SEATS:
            self.assertIn(name, FEAT.SEATS, f"{name} is sit-able and player-placed")

    def test_every_throne_is_present(self):
        thrones = [n for n in FEAT.SEATS if "throne" in n]
        self.assertCountEqual(
            thrones,
            ["piece_throne01", "piece_throne02",
             "piece_blackmarble_throne", "piece_bone_throne"])

    def test_a_throne_outranks_a_chair_which_outranks_a_stool(self):
        self.assertGreater(FEAT.SEATS["piece_throne01"], FEAT.SEATS["dvergrprops_chair"])
        self.assertGreater(FEAT.SEATS["dvergrprops_chair"], FEAT.SEATS["dvergrprops_stool"])

    def test_the_scan_only_ever_reads_placed_pieces(self):
        """The prop seats also exist in their thousands inside generated dungeons.
        Those rows are UNKNOWN/INTERIOR; only the BUILDING filter keeps them out."""
        source = io.open(
            ROOT / "tools" / "selfie-stick" / "scan_features.py", encoding="utf-8"
        ).read()
        self.assertIn("category = 'BUILDING'", source)
        self.assertIn("category='BUILDING'", source)


class LightVocabularyTests(unittest.TestCase):
    """Every deliberate light source, not every craftable one.

    The vocabulary was four exact names plus a ("piece_brazier",
    "piece_groundtorch") prefix tuple -- and the prefix half counted nothing.
    expand_pattern_sets() used it only to keep torches out of the wall set;
    feature_rows() emitted FIRES_EXACT alone. So 80,010 placed torches and
    braziers in Era 17 matched a pattern and were then discarded, and the whole
    vocabulary reached 6.5% of the world's 173,541 lights. A night pass targets
    on this count, so the miss is the difference between finding the builds
    someone lit on purpose and finding the builds with a cooking fire.
    """

    MOST_PLACED = ("piece_groundtorch_wood", "piece_groundtorch_mist",
                   "piece_groundtorch_green", "piece_dvergr_lantern",
                   "dvergrprops_lantern_standing", "piece_Lavalantern",
                   "MountainKit_brazier", "Candle_resin",
                   "piece_FairylightGarland", "CastleKit_groundtorch")

    def test_the_most_placed_lights_are_in_the_vocabulary(self):
        for name in self.MOST_PLACED:
            self.assertIn(name, FEAT.LIGHTS, f"{name} lights a build after dark")

    def test_the_old_prefix_names_now_actually_emit_rows(self):
        """The regression that motivated this: matched by a pattern, counted by
        nothing. Every prefix name must reach the lookup table as a fire row."""
        rows = FEAT.feature_rows((set(), set(), set(), set()))
        fires = {name for name, kind, _w in rows if kind == "fire"}
        for name in FEAT.LIGHTS:
            self.assertIn(name, fires)
        self.assertTrue(
            any(n.startswith("piece_groundtorch") for n in fires),
            "ground torches are the most-placed light in the world")

    def test_unlit_variants_are_never_lights(self):
        """A sweep for "torch" matches these, and they emit nothing."""
        for name in ("CastleKit_groundtorch_unlit",
                     "CastleKit_metal_groundtorch_unlit"):
            self.assertNotIn(name, FEAT.LIGHTS)

    def test_creature_effects_and_crafting_glow_are_never_lights(self):
        """DvergerMageFire is a creature effect; a forge's glow is incidental and
        counting it would track workshop density rather than lighting design."""
        for name in ("DvergerMageFire", "forge", "blackforge", "smelter",
                     "charcoal_kiln", "piece_oven", "blastfurnace",
                     "dverger_demister_broken", "crystal_wall_1x1"):
            self.assertNotIn(name, FEAT.LIGHTS)

    def test_an_open_flame_outweighs_a_torch_which_outweighs_a_candle(self):
        self.assertGreater(FEAT.LIGHTS["hearth"], FEAT.LIGHTS["piece_groundtorch_wood"])
        self.assertGreater(FEAT.LIGHTS["piece_groundtorch_wood"], FEAT.LIGHTS["Candle_resin"])

    def test_lights_are_excluded_from_the_pattern_sets(self):
        """piece_walltorch contains "wall" and is not a wall; the fixed set has
        to shadow the pattern sweep or every torch becomes masonry."""
        _doors, _roofs, _floors, walls = FEAT.expand_pattern_sets(
            ["piece_walltorch", "wood_wall_log", "piece_groundtorch_wood"])
        self.assertIn("wood_wall_log", walls)
        self.assertNotIn("piece_walltorch", walls)

    def test_the_feature_join_itself_reads_placed_pieces_only(self):
        """The pre-existing BUILDING assertion passed against the *count*
        queries while the feature join had no category filter at all -- so a
        build whose padded box touched a Dvergr tower inherited its lights."""
        source = io.open(
            ROOT / "tools" / "selfie-stick" / "scan_features.py", encoding="utf-8"
        ).read()
        join = source.split("JOIN feature_name f ON f.name = z.prefab_name", 1)[1]
        self.assertIn("category = 'BUILDING'", join.split(".fetchall()", 1)[0])


class CelestialArcTests(unittest.TestCase):
    """The sky's geometry, pinned to the measurement that produced it.

    comfyproof_sky walked EnvMan's directional light through 41 times of day and
    the closed form reproduces every lit sample to 0.001 degrees. These fixtures
    are lifted straight out of that dump, so if anyone "simplifies" the arc the
    test fails against the game rather than against an opinion.
    """

    # (time, azimuth, altitude, is the light warm i.e. the sun)
    DUMP = [
        (0.000, 180.0, 45.0, False), (0.100, 225.8, 34.9, False),
        (0.200, 257.1, 12.6, False), (0.300, 102.9, 12.6, True),
        (0.400, 134.2, 34.9, True), (0.500, 180.0, 45.0, True),
        (0.640, 239.7, 26.8, True), (0.700, 257.1, 12.6, True),
        (0.800, 102.9, 12.6, False), (0.900, 134.2, 34.9, False),
        (0.975, 167.4, 44.3, False),
    ]

    def test_the_arc_reproduces_the_dump(self):
        for t, az, alt, warm in self.DUMP:
            rise = NIGHT.SUN_RISE_T if warm else NIGHT.MOON_RISE_T
            got_az, got_alt = NIGHT.body_direction(t, rise)
            self.assertAlmostEqual(got_az, az, delta=0.1, msg=f"azimuth at t={t}")
            self.assertAlmostEqual(got_alt, alt, delta=0.1, msg=f"altitude at t={t}")

    def test_both_bodies_rise_east_and_set_west(self):
        rise_az, rise_alt = NIGHT.body_direction(NIGHT.MOON_RISE_T)
        self.assertAlmostEqual(rise_az, 90.0, delta=0.1)
        self.assertAlmostEqual(rise_alt, 0.0, delta=0.1)
        # A hair before the handover: at exactly rise+0.5 this body has set and
        # the other one is rising, which is what the dump shows at t=0.25 (az 90,
        # altitude 0, intensity 0).
        set_az, set_alt = NIGHT.body_direction(NIGHT.MOON_RISE_T + 0.4999)
        self.assertAlmostEqual(set_az, 270.0, delta=0.1)
        self.assertAlmostEqual(set_alt, 0.0, delta=0.1)

    def test_neither_body_ever_gets_higher_than_45_degrees(self):
        """Which is why the roofline constraint bites at all: a body that went
        overhead could never share a frame with the roof you are standing on."""
        peak = max(NIGHT.body_direction(t / 200.0)[1] for t in range(201))
        self.assertAlmostEqual(peak, 45.0, delta=0.01)

    def test_the_sun_at_golden_hour_agrees_with_the_frames(self):
        """Independent check: regressing sky-strip luminance on camera yaw over
        seven capture runs pooled to 235 +/- 25 degrees for t=0.64."""
        az, _alt = NIGHT.body_direction(0.64, NIGHT.SUN_RISE_T)
        self.assertLess(abs(az - 235.0), 25.0)

    def test_night_is_the_moon_half_of_the_day(self):
        for t in (0.75, 0.8, 0.9, 0.99, 0.0, 0.1, 0.25):
            self.assertTrue(NIGHT.is_night(t), t)
        for t in (0.26, 0.32, 0.5, 0.64, 0.71, 0.74):
            self.assertFalse(NIGHT.is_night(t), t)


class NightSkyPlanTests(unittest.TestCase):
    """The rooftop plan, checked against the geometry it claims to satisfy."""

    def _rooftops(self, reach=None, platforms=None):
        reach = reach or {str(b): 12.0 for b in range(0, 360, 30)}
        extra = {"platforms_detail": platforms} if platforms else {}
        return {"world": "T", "structures": [dict(extra, **{
            "cluster_id": 7, "lights": 300, "light_pieces": 100, "pieces": 5000,
            "height_m": 30.0, "region": "in-world", "above_base_m": 22.0,
            "stance": {"x": 100.0, "y": 60.0, "z": 200.0},
            "exposure": 8, "exposure_of": 16, "platforms": 3, "reach_m": reach,
        })]}

    def _run(self, tmp, extra=(), reach=None, platforms=None):
        roof = os.path.join(tmp, "rooftops.json")
        clusters = os.path.join(tmp, "clusters.json")
        out = os.path.join(tmp, "nightsky.json")
        with io.open(roof, "w", encoding="utf-8") as fh:
            json.dump(self._rooftops(reach, platforms), fh)
        with io.open(clusters, "w", encoding="utf-8") as fh:
            json.dump({"clusters": [_cluster(7, 1)]}, fh)
        argv = ["plan_nightsky.py", "--rooftops", roof, "--clusters", clusters,
                "--names", os.path.join(tmp, "none.json"), "--out", out] + list(extra)
        old = sys.argv
        sys.argv = argv
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                NIGHT.main()
        finally:
            sys.argv = old
        with io.open(out, encoding="utf-8") as fh:
            return json.load(fh), os.path.splitext(out)[0] + ".tsv"

    def test_every_camera_looks_up(self):
        """The one thing that separates this from every other planner here."""
        with tempfile.TemporaryDirectory() as tmp:
            doc, _tsv = self._run(tmp)
            self.assertTrue(doc["plan"])
            for shot in doc["plan"]:
                self.assertLess(shot["pitch_deg"], 0.0, shot["shot"])

    def test_the_roofline_stays_in_the_bottom_of_the_frame(self):
        """elevation + atan(h_eye / reach) is where the parapet lands below the
        optical axis, and past half the vertical FOV it has left the picture --
        which is the sky-platform frame that medians 4.69."""
        with tempfile.TemporaryDirectory() as tmp:
            doc, _tsv = self._run(tmp)
            h = doc["settings"]["h_eye_m"]
            half = doc["settings"]["fov_v_deg"] / 2.0
            for shot in doc["plan"]:
                below = shot["elevation_deg"] + math.degrees(
                    math.atan(h / shot["reach_m"]))
                self.assertLessEqual(below, half + 1e-6, shot["shot"])

    def test_the_aim_point_reproduces_the_planned_angles(self):
        """The mod recomputes yaw/pitch from `aim` if occlusion recovery fires.
        If that recomputation disagrees with the plan, a rescued frame is a
        different photograph than the one that was designed."""
        with tempfile.TemporaryDirectory() as tmp:
            doc, _tsv = self._run(tmp)
            for shot in doc["plan"]:
                lens, aim = shot["lens"], shot["aim"]
                dx = aim["x"] - lens["x"]
                dy = aim["y"] - lens["y"]
                dz = aim["z"] - lens["z"]
                n = math.sqrt(dx * dx + dy * dy + dz * dz)
                yaw = math.degrees(math.atan2(dx, dz)) % 360.0
                pitch = -math.degrees(math.asin(dy / n))
                self.assertAlmostEqual(n, doc["settings"]["aim_distance_m"], delta=0.3)
                self.assertAlmostEqual(
                    (yaw - shot["yaw_deg"] + 180) % 360 - 180, 0.0, delta=0.5)
                self.assertAlmostEqual(pitch, shot["pitch_deg"], delta=0.5)

    def test_repeats_are_distinct_variants(self):
        """Cloud position is a re-roll, so the plan shoots the same stance more
        than once -- but the index supersedes on (cluster, variant, environment,
        time). Repeats sharing a name would retire each other instead of joining,
        which is exactly how 150 golden frames were quietly replaced."""
        with tempfile.TemporaryDirectory() as tmp:
            doc, _tsv = self._run(tmp, ["--repeats", "3"])
            keys = [(s["cluster_id"], s["shot"], s["environment"], s["time_of_day"])
                    for s in doc["plan"]]
            self.assertEqual(len(keys), len(set(keys)))
            self.assertGreaterEqual(len(keys), 3)

    def test_the_mod_can_parse_every_row_as_a_rooftop_shot(self):
        with tempfile.TemporaryDirectory() as tmp:
            _doc, tsv = self._run(tmp)
            ok, bad = INTERIOR.validate_tsv(tsv, mode="rooftop")
            self.assertGreater(ok, 0)
            self.assertEqual(bad, 0)

    def test_daylight_is_refused_rather_than_planned(self):
        """There is nothing to point at: the sun is the lit body from 0.25 to
        0.75, and this composition is the moon and the star field."""
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                self._run(tmp, ["--times", "0.64"])

    def test_a_tight_roof_is_stepped_back_from(self):
        """The stance is the highest flat block, which on a big build is often a
        turret whose edge is a few metres away -- close enough that the roofline
        lands near the bottom edge as a sliver instead of a near layer. Backing
        along the reverse bearing buys forward roof."""
        tight = {str(b): 8.0 for b in range(0, 360, 30)}
        with tempfile.TemporaryDirectory() as tmp:
            doc, _tsv = self._run(tmp, reach=tight)
            self.assertTrue(doc["plan"])
            for shot in doc["plan"]:
                self.assertGreater(shot["step_back_m"], 0.0)
                self.assertGreater(shot["reach_m"], 8.0)

    def test_a_roof_too_small_for_the_tilt_is_refused_not_shipped(self):
        """At t=0.90 the moon is 34.9 degrees up, so the axis is steep, and a 4 m
        rooftop cannot keep the parapet inside the bottom of the frame even after
        stepping back as far as the roof allows. The
        answer is no frame, not a frame with no near layer in it -- that is the
        sky-platform shot, and it medians 4.69 against a gallery median of 5.47."""
        cramped = {str(b): 4.0 for b in range(0, 360, 30)}
        with tempfile.TemporaryDirectory() as tmp:
            doc, _tsv = self._run(tmp, reach=cramped)
            self.assertEqual(doc["plan"], [])

    def test_the_same_roof_works_once_the_moon_is_lower(self):
        """Which makes it a scheduling problem rather than a dead end."""
        cramped = {str(b): 4.0 for b in range(0, 360, 30)}
        with tempfile.TemporaryDirectory() as tmp:
            doc, _tsv = self._run(tmp, ["--times", "0.83"], reach=cramped)
            self.assertTrue(doc["plan"])
            for shot in doc["plan"]:
                self.assertLess(shot["pitch_deg"], 0.0)

    def test_a_stance_under_its_own_masonry_is_refused(self):
        """The failure the first capture run actually had. All 16 frames came
        back clearance="planned" and occluded=false and not one had sky in it:
        four of them are a photograph of cluster 182's own lattice. The mod's
        raycast masks terrain, static_solid and Default, and player pieces are on
        the piece layer, so for a camera standing inside its own build that check
        is blind. This one is computed from the world's positions instead."""
        roofed = [{"stance": {"x": 100.0, "y": 60.0, "z": 200.0},
                   "reach_m": {str(b): 12.0 for b in range(0, 360, 30)},
                   "skyline_deg": {str(b): 40.0 for b in range(0, 360, 30)}}]
        with tempfile.TemporaryDirectory() as tmp:
            doc, _tsv = self._run(tmp, platforms=roofed)
            self.assertEqual(doc["plan"], [])

    def test_an_open_stance_on_the_same_build_is_still_taken(self):
        """A build is only dropped when EVERY candidate stance is boxed in --
        the highest flat block is not reliably the one with sky over it, so the
        scan offers several and the planner picks."""
        blocked = {"stance": {"x": 100.0, "y": 66.0, "z": 200.0},
                   "reach_m": {str(b): 12.0 for b in range(0, 360, 30)},
                   "skyline_deg": {str(b): 40.0 for b in range(0, 360, 30)}}
        open_one = {"stance": {"x": 130.0, "y": 60.0, "z": 200.0},
                    "reach_m": {str(b): 12.0 for b in range(0, 360, 30)},
                    "skyline_deg": {str(b): 0.0 for b in range(0, 360, 30)}}
        with tempfile.TemporaryDirectory() as tmp:
            doc, _tsv = self._run(tmp, platforms=[blocked, open_one])
            self.assertTrue(doc["plan"])
            for shot in doc["plan"]:
                self.assertEqual(shot["platform"], 1)
                self.assertEqual(shot["camera"]["y"], 60.0)

    def test_the_gallery_gives_these_frames_their_own_perspective(self):
        """The aesthetic head prefers a landscape to a room by 0.45 and marks
        dark frames down on principle, and the gallery ranks within perspective.
        Without a bucket of their own every night frame sinks by construction."""
        self.assertEqual(BUILD.perspective_of("moon1"), "rooftop")
        self.assertEqual(BUILD.perspective_of("moon2_r3"), "rooftop")
        self.assertEqual(BUILD.perspective_of("orbit1"), "drone")
        self.assertEqual(BUILD.perspective_of("seat_night"), "seated")


class OverlayDetectionTests(unittest.TestCase):
    """A mod drawing on the frames is found by what it does not do: change.

    Written against the run that shipped the ComfyQuest bar. The check must not
    know where a bar lives -- the next mod to draw one will put it somewhere else.
    """

    W, H = 320, 240

    def _run_dir(self, tmp, overlay_rows=None):
        import numpy as np
        d = pathlib.Path(tmp) / "run"
        d.mkdir()
        rng = np.random.default_rng(7)
        for i in range(8):
            # Coarse blocks, not per-pixel noise: the check downsamples 8x, and
            # white noise averages to a constant under that, which would make an
            # empty frame look as frozen as a HUD. Real frames carry structure at
            # every scale, so the fixture has to as well.
            coarse = rng.integers(0, 255, (self.H // 8, self.W // 8), dtype=np.uint8)
            frame = np.kron(coarse, np.ones((8, 8), dtype=np.uint8))
            if overlay_rows:
                lo, hi = overlay_rows
                frame[lo:hi, 40:280] = 200          # same pixels in every frame
            Image.fromarray(frame, mode="L").save(d / f"{i:02d}.png")
        return str(d)

    def _check(self, directory, **kw):
        argv = ["check_overlay.py", "--run", directory, "--sample", "8"]
        for k, v in kw.items():
            argv += [f"--{k.replace('_', '-')}", str(v)]
        out = io.StringIO()
        old, sys.argv = sys.argv, argv
        try:
            with contextlib.redirect_stdout(out):
                code = OVER.main()
        finally:
            sys.argv = old
        return code, out.getvalue()

    def test_noise_alone_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, text = self._check(self._run_dir(tmp))
        self.assertEqual(code, 0, text)
        self.assertIn("Clean", text)

    def test_a_static_band_fails_and_is_located(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, text = self._check(self._run_dir(tmp, overlay_rows=(24, 40)))
        self.assertEqual(code, 1, text)
        self.assertIn("static horizontal band", text)
        # located within one downsampled row of the truth, never hard-coded
        self.assertRegex(text, r"y (16|24)-(40|48)")

    def test_the_band_is_found_wherever_it_is_drawn(self):
        """The bar sat at the top. Nothing about the method depends on that."""
        with tempfile.TemporaryDirectory() as tmp:
            code, text = self._check(self._run_dir(tmp, overlay_rows=(180, 196)))
        self.assertEqual(code, 1, text)
        self.assertRegex(text, r"y 1[78]\d-(19|20)\d")

    def test_tolerance_can_forgive_a_small_static_feature(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = self._check(self._run_dir(tmp, overlay_rows=(24, 40)),
                                  tolerance=50.0)
        self.assertEqual(code, 0)


class DuplicateFrameTests(unittest.TestCase):
    """The dawn and weather slots re-use the hero camera and change only the
    light. Ask for a plan already shot at that light and they collapse onto an
    orbit, and the game takes the same photograph twice. The 2026-08-24 sky
    re-shoot lost 14 of 70 frames -- 20%, on every single structure -- that way.
    """

    def _plan(self, tmp, extra):
        clusters = [_cluster(i, creator=i, x=i * 400.0, z=0.0, score=100 - i,
                             size_x=30.0, size_z=18.0) for i in (1, 2, 3)]
        cpath = pathlib.Path(tmp) / "c.json"
        cpath.write_text(json.dumps({"world": "T", "clusters": clusters}),
                         encoding="utf-8")
        out = pathlib.Path(tmp) / "p.json"
        text = _run(PLAN, ["plan_shots.py", "--clusters", str(cpath),
                           "--out", str(out)] + extra)
        return json.loads(out.read_text(encoding="utf-8")), text

    def test_the_default_plan_still_takes_six_frames_each(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan, _ = self._plan(tmp, [])
        self.assertEqual(plan["shots"], 18)
        self.assertEqual(len(plan["plan"]), 18)

    def test_shooting_at_dawn_drops_the_dawn_retake(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan, text = self._plan(tmp, ["--time-of-day", "0.32", "--alt-shots", "0"])
        self.assertEqual(plan["shots"], 12, "four orbits each, no fifth duplicate")
        self.assertNotIn("dawn", {s["shot"] for s in plan["plan"]})

    def test_the_drop_is_reported_and_says_what_it_matched(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, text = self._plan(tmp, ["--time-of-day", "0.32", "--alt-shots", "0"])
        self.assertIn("dropped 3 duplicate frame(s)", text)
        self.assertRegex(text, r"dawn was identical to orbit\d on 3 structure")

    def test_every_frame_in_a_plan_is_a_different_photograph(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan, _ = self._plan(tmp, ["--time-of-day", "0.32"])
        keys = [(s["camera"]["x"], s["camera"]["y"], s["camera"]["z"],
                 s["yaw_deg"], s["pitch_deg"], s["environment"], s["time_of_day"])
                for s in plan["plan"]]
        self.assertEqual(len(keys), len(set(keys)))

    def test_a_weather_slot_at_a_different_sky_survives(self):
        """Only identical frames go. The alt slot is still doing work when it
        actually changes something."""
        with tempfile.TemporaryDirectory() as tmp:
            plan, _ = self._plan(tmp, ["--time-of-day", "0.32",
                                       "--alt-environment", "Misty"])
        self.assertIn("weather", {s["shot"] for s in plan["plan"]})


class SupersedeTests(unittest.TestCase):
    """A newer frame replaces an older one only when it is the same photograph.

    The slot names orbit1..4 mean "the four bearings", not "the four bearings at
    one time of day", so every re-shoot reuses them. Keying supersede on
    (cluster, variant) alone made a deliberate 0.71 re-shoot of 30 builds retire
    their 0.64 originals -- 150 frames, silently, and the best thirty at that.

    These call build_valheim_index.supersede_key itself; a local copy of the rule
    would pass whatever the index builder actually did.
    """

    @staticmethod
    def _row(cid, variant, ts, env="Clear", tod=0.64, fires=False, flash=None):
        return {"source": "orbit", "cluster_id": cid, "variant": variant,
                "ts": ts, "environment": env, "time_of_day": tod,
                "fires": fires, "flash_bearing_deg": flash}

    @classmethod
    def _collapse(cls, rows):
        best = {}
        for r in rows:
            key = BUILD.supersede_key(r)
            if key not in best or r["ts"] > best[key]["ts"]:
                best[key] = r
        return [r for r in rows if best.get(BUILD.supersede_key(r)) is r]

    def test_the_key_carries_the_light(self):
        self.assertEqual(
            BUILD.supersede_key(self._row(7, "orbit2", 1, env="Misty", tod=0.66)),
            (7, "orbit2", "Misty", 0.66, False, None))

    def test_holding_the_fires_makes_a_different_photograph(self):
        """The A/B depends on this. Re-shooting a plan with --fires reuses every
        variant name at the same environment and the same time, so if the held
        frames superseded the unheld ones the comparison they were taken to make
        would be deleted on the way into the gallery."""
        keep = self._collapse([self._row(1, "orbit1", 100, fires=False),
                               self._row(1, "orbit1", 200, fires=True)])
        self.assertEqual(len(keep), 2)

    def test_a_flash_lit_frame_is_a_different_photograph(self):
        keep = self._collapse([self._row(1, "storm", 100, fires=True),
                               self._row(1, "storm", 200, fires=True, flash=-35.0)])
        self.assertEqual(len(keep), 2)

    def test_a_row_from_before_the_light_columns_still_keys(self):
        """Every receipt written before this existed has no fires field at all,
        and the whole 4,536-receipt back catalogue has to keep collapsing the
        way it did."""
        old = {"source": "orbit", "cluster_id": 3, "variant": "orbit1",
               "ts": 1, "environment": "Clear", "time_of_day": 0.64}
        self.assertEqual(BUILD.supersede_key(old),
                         (3, "orbit1", "Clear", 0.64, False, None))

    def test_a_retake_in_the_same_light_supersedes(self):
        keep = self._collapse([self._row(1, "orbit1", 100),
                               self._row(1, "orbit1", 200)])
        self.assertEqual(len(keep), 1)
        self.assertEqual(keep[0]["ts"], 200, "the newer capture wins")

    def test_the_same_angle_in_different_light_is_a_different_photograph(self):
        keep = self._collapse([self._row(1, "orbit1", 100, tod=0.64),
                               self._row(1, "orbit1", 200, tod=0.71)])
        self.assertEqual(len(keep), 2)

    def test_a_different_sky_also_survives(self):
        keep = self._collapse([self._row(1, "orbit1", 100, env="Clear"),
                               self._row(1, "orbit1", 200, env="Misty")])
        self.assertEqual(len(keep), 2)

    def test_different_builds_never_collide(self):
        keep = self._collapse([self._row(1, "orbit1", 100),
                               self._row(2, "orbit1", 200)])
        self.assertEqual(len(keep), 2)


class ChannelPlanTests(unittest.TestCase):
    """Down the channel, moon off-axis, stars in the top sixth-to-third.

    The rule these guard is Derek's: aiming AT the moon composes the moon, which
    is the least interesting thing a night frame can do. The moon is a lamp.
    """

    def _channels(self, bearings=None):
        if bearings is None:
            bearings = {}
            for b in range(0, 360, 15):
                bearings[str(b)] = {"first_tree_m": 900.0, "trees_near": 0,
                                    "sea_at_m": None, "sea_run_m": 0.0,
                                    "canopy_deg": -4.0}
        return {"world": "T", "settings": {}, "structures": [{
            "cluster_id": 7, "lights": 300, "reach_m": {str(b): 12.0 for b in range(0, 360, 30)},
            "stance": {"x": 100.0, "y": 60.0, "z": 200.0},
            "tall_trees_in_range": 500, "bearings": bearings,
        }]}

    def _run(self, tmp, extra=(), bearings=None):
        chan = os.path.join(tmp, "channels.json")
        clusters = os.path.join(tmp, "clusters.json")
        out = os.path.join(tmp, "channel.json")
        with io.open(chan, "w", encoding="utf-8") as fh:
            json.dump(self._channels(bearings), fh)
        with io.open(clusters, "w", encoding="utf-8") as fh:
            json.dump({"clusters": [_cluster(7, 1)]}, fh)
        argv = ["plan_channel.py", "--channels", chan, "--clusters", clusters,
                "--names", os.path.join(tmp, "none.json"), "--out", out] + list(extra)
        old = sys.argv
        sys.argv = argv
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                CHAN.main()
        finally:
            sys.argv = old
        with io.open(out, encoding="utf-8") as fh:
            return json.load(fh), os.path.splitext(out)[0] + ".tsv"

    def test_no_shot_ever_points_at_the_moon(self):
        """The refusal that gives this planner its reason to exist."""
        with tempfile.TemporaryDirectory() as tmp:
            doc, _ = self._run(tmp)
            self.assertTrue(doc["plan"])
            for shot in doc["plan"]:
                self.assertGreaterEqual(shot["moon_offset_deg"],
                                        doc["settings"]["min_moon_offset_deg"])

    def test_the_moon_is_never_behind_the_camera_either(self):
        """Frontal moonlight is as flat as pointing at it."""
        with tempfile.TemporaryDirectory() as tmp:
            doc, _ = self._run(tmp)
            for shot in doc["plan"]:
                self.assertLessEqual(shot["moon_offset_deg"],
                                     doc["settings"]["max_moon_offset_deg"])

    def test_the_skyline_lands_where_the_sky_band_asks(self):
        """v = tan(delta)/tan(fov_v/2); the skyline must sit at 1 - 2*band."""
        with tempfile.TemporaryDirectory() as tmp:
            doc, _ = self._run(tmp, extra=["--sky-band", "0.2"])
            want_v = 1.0 - 2.0 * 0.2
            for shot in doc["plan"]:
                delta = shot["skyline_deg"] - shot["elevation_deg"]
                v = (math.tan(math.radians(delta))
                     / math.tan(math.radians(CHAN.FOV_V / 2.0)))
                # elevation_deg is stored rounded to 2 dp for the TSV: 0.005 deg, about
                # 1e-4 of frame height. Assert what the file promises.
                self.assertAlmostEqual(v, want_v, places=3)

    def test_a_sixth_of_sky_tilts_further_down_than_a_third(self):
        """More ground in frame means a lower axis, not a different subject."""
        with tempfile.TemporaryDirectory() as tmp:
            sixth, _ = self._run(tmp, extra=["--sky-band", "0.167"])
        with tempfile.TemporaryDirectory() as tmp:
            third, _ = self._run(tmp, extra=["--sky-band", "0.333"])
        self.assertGreater(sixth["plan"][0]["pitch_deg"], third["plan"][0]["pitch_deg"])

    def test_a_canopy_above_the_lens_is_refused_not_shot(self):
        """The measurement that a gap distance cannot make."""
        walled = {}
        for b in range(0, 360, 15):
            walled[str(b)] = {"first_tree_m": 40.0, "trees_near": 30,
                              "sea_at_m": None, "sea_run_m": 0.0,
                              "canopy_deg": 18.0}
        with tempfile.TemporaryDirectory() as tmp:
            doc, _ = self._run(tmp, bearings=walled)
            self.assertEqual(doc["plan"], [])

    def test_open_water_outranks_bare_distance(self):
        """Depth through variance is the objective; water is the strongest cue."""
        mixed = {}
        for b in range(0, 360, 15):
            mixed[str(b)] = {"first_tree_m": 1200.0, "trees_near": 0,
                             "sea_at_m": None, "sea_run_m": 0.0, "canopy_deg": -4.0}
        mixed["90"] = {"first_tree_m": 400.0, "trees_near": 0,
                       "sea_at_m": 300.0, "sea_run_m": 800.0, "canopy_deg": -4.0}
        with tempfile.TemporaryDirectory() as tmp:
            doc, _ = self._run(tmp, extra=["--times", "0.0", "--shots", "1"],
                               bearings=mixed)
            self.assertTrue(doc["plan"])
            self.assertEqual(doc["plan"][0]["yaw_deg"], 90.0)

    def test_every_frame_is_a_different_photograph(self):
        """The index supersedes on (cluster, variant, environment, time)."""
        with tempfile.TemporaryDirectory() as tmp:
            doc, _ = self._run(tmp)
            keys = {(s["cluster_id"], s["shot"], s["environment"], s["time_of_day"])
                    for s in doc["plan"]}
            self.assertEqual(len(keys), len(doc["plan"]))

    def test_the_aim_point_reproduces_the_planned_angles(self):
        """If FindClearView fires, LookAngles(lens, aim) must recover yaw/pitch."""
        with tempfile.TemporaryDirectory() as tmp:
            doc, _ = self._run(tmp)
            for shot in doc["plan"]:
                dx = shot["aim"]["x"] - shot["lens"]["x"]
                dy = shot["aim"]["y"] - shot["lens"]["y"]
                dz = shot["aim"]["z"] - shot["lens"]["z"]
                yaw = math.degrees(math.atan2(dx, dz)) % 360.0
                pitch = -math.degrees(math.asin(dy / math.sqrt(dx*dx + dy*dy + dz*dz)))
                # aim is stored to 1 dp; over a 25 m sight line that is 0.05 m, so
                # 0.115 deg. The mod needs this only to reproduce framing if
                # recovery fires, and 0.2 deg is well inside that.
                self.assertAlmostEqual(yaw, shot["yaw_deg"], delta=0.2)
                self.assertAlmostEqual(pitch, shot["pitch_deg"], delta=0.2)

    def test_daylight_is_refused_rather_than_planned(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                self._run(tmp, extra=["--times", "0.5"])

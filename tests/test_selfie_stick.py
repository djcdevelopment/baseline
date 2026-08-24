import contextlib
import importlib.util
import io
import json
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
PICK_SPEC = importlib.util.spec_from_file_location(
    "pick_targets", ROOT / "tools" / "selfie-stick" / "pick_targets.py"
)
PICK = importlib.util.module_from_spec(PICK_SPEC)
PICK_SPEC.loader.exec_module(PICK)


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

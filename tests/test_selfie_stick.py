import importlib.util
import pathlib
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


if __name__ == "__main__":
    unittest.main()

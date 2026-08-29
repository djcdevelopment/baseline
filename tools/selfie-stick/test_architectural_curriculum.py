#!/usr/bin/env python3
"""Focused deterministic contract tests for the architectural curriculum probe."""

from __future__ import annotations

import base64
import hashlib
import http.server
import json
import shutil
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path

import habs_harvester as harvester
import probe_architectural_constraint_envelope as envelope
import probe_architectural_curriculum as curriculum
import probe_architectural_css_fit_v3 as css_v3
import probe_habs_ocr_audit as ocr_audit


class ArchitecturalCurriculumTests(unittest.TestCase):
    def test_architectural_build_capsule_is_deterministic_and_cross_checked(self):
        head = json.loads((envelope.DEFAULT_OUT / "HEAD.json").read_text(encoding="utf-8"))
        revision = envelope.DEFAULT_OUT / "revisions" / head["revision"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = envelope.write_capsule(revision, root / "first.zip")
            second = envelope.write_capsule(revision, root / "second.zip")
            first_bytes = first.read_bytes()
            self.assertEqual(first_bytes, second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(
                    archive.namelist(),
                    sorted([
                        "capsule.json", "solved-building.graph.json",
                        "constraint-model.json", "interpretation-receipt.json",
                        "compilation-receipt.json", "pieces.json",
                        "architectural-candidate.capture.json", "prefab-geometry.json",
                    ]),
                )
                capsule = json.loads(archive.read("capsule.json"))
                self.assertEqual(capsule["schema"], envelope.CAPSULE_SCHEMA)
                self.assertEqual(capsule["piece_count"], 40)
                self.assertEqual(
                    capsule["prefab_counts"],
                    {"wood_floor": 16, "wood_roof_45": 8, "woodwall": 16},
                )
                self.assertEqual(
                    capsule["compiled_pieces_sha256"],
                    hashlib.sha256(archive.read("pieces.json")).hexdigest(),
                )
                for name, pin in capsule["members"].items():
                    payload = archive.read(name)
                    self.assertEqual(pin["bytes"], len(payload))
                    self.assertEqual(pin["sha256"], hashlib.sha256(payload).hexdigest())

            broken = root / "broken-revision"
            (broken / "tn0304").mkdir(parents=True)
            shutil.copy2(revision / "identity.json", broken / "identity.json")
            for source in (revision / "tn0304").glob("*.json"):
                shutil.copy2(source, broken / "tn0304" / source.name)
            compilation_path = broken / "tn0304" / "compilation-receipt.json"
            compilation = json.loads(compilation_path.read_text(encoding="utf-8"))
            compilation["prefab_counts"]["wood_floor"] = 15
            compilation_path.write_text(json.dumps(compilation), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "prefab counts disagree"):
                envelope.write_capsule(broken, root / "broken.zip")

    def test_relational_envelope_scar_contract(self):
        with self.subTest("confidence-weighted compromise preserves observations"):
            observations = [
                {"id": "a", "value": 4.00, "confidence": 0.9},
                {"id": "b", "value": 4.08, "confidence": 0.8},
            ]
            before = [dict(item) for item in observations]
            solved = envelope.weighted_compromise(observations, 0.10)
            self.assertEqual(solved["status"], "PASS")
            self.assertEqual(observations, before)

        with self.subTest("explicit conflict beyond residual bound is held"):
            conflict = envelope.weighted_compromise([
                {"id": "a", "value": 4.00, "confidence": 1.0},
                {"id": "b", "value": 4.25, "confidence": 1.0},
            ], 0.10)
            self.assertEqual(conflict["status"], "HELD_CONFLICT")
            self.assertGreater(conflict["maximum_residual"], 0.10)

        with self.subTest("relative elevation agrees after view-only translation"):
            registration = envelope.solve_view_translation(
                [3.050325, 3.111332, 6.738643],
                [2.2225, 2.2225, 5.8166],
                0.10,
            )
            self.assertEqual(registration["status"], "PASS")
            self.assertFalse(registration["changes_source_observation"])

        with self.subTest("historical prose cannot become a floor datum"):
            disposition = envelope.narrative_datum_disposition({
                "id": "history", "type": "first_floor", "value_m": None,
                "normalized": "ORIGINALLY A TWO-STORY BUILDING",
            })
            self.assertEqual(disposition["status"], "REJECTED_NARRATIVE_NOT_GEOMETRIC")
            self.assertFalse(disposition["changes_level_count"])

    def test_dimension_parser_handles_metric_and_feet_inches(self):
        self.assertAlmostEqual(curriculum.parse_dimension("12'-6 1/2\""), 3.8227, places=4)
        self.assertAlmostEqual(curriculum.parse_dimension("7.25 metres"), 7.25)
        self.assertIsNone(curriculum.parse_dimension("2'-6 1/4°"))
        self.assertIsNone(curriculum.parse_dimension("12'-"))
        self.assertIsNone(curriculum.parse_dimension("1:48 MOLDING"))
        self.assertIsNone(curriculum.parse_dimension("1:48 METERS"))
        self.assertIsNone(curriculum.parse_dimension("3 DEC. METRIC 1M"))
        self.assertIsNone(curriculum.parse_dimension("METRIC FT 4M"))
        self.assertIsNone(curriculum.parse_dimension(
            "ELEVATION OF MANTEL, SEE SHEET NO.6 M."))
        self.assertIsNone(curriculum.parse_dimension("SCALE 3/8\" = 1'-0\""))
        self.assertIsNone(curriculum.parse_dimension("WOOD POST 1-6'"))
        self.assertIsNone(curriculum.parse_dimension("7 2x4 1'×8"))
        self.assertIsNone(curriculum.parse_dimension("2'ND FLOOR DOORS"))
        self.assertIsNone(curriculum.parse_dimension("3'.61/2\""))
        self.assertAlmostEqual(curriculum.parse_dimension("width 12'"), 3.6576)
        self.assertIsNone(curriculum.parse_dimension("not a dimension"))

    def test_ocr_authority_can_match_adjacent_tokens(self):
        tokens = [
            {"text": "12'-", "confidence": 0.91},
            {"text": "6 1/2\"", "confidence": 0.88},
        ]
        self.assertTrue(curriculum.token_matches("12'-6 1/2\"", tokens))
        self.assertFalse(curriculum.token_matches("19'-0\"", tokens))

    def test_audit_joins_split_dimensions_and_holds_corrupt_notation(self):
        tokens = [
            {"text": "12'-", "confidence": 0.91, "region": [0.0, 0.0, 0.1, 0.1]},
            {"text": "6 1/2\"", "confidence": 0.88, "region": [0.1, 0.0, 0.2, 0.1]},
            {"text": "2'-6 1/4°", "confidence": 0.84, "region": [0.2, 0.0, 0.3, 0.1]},
        ]
        accepted, suspicious = ocr_audit.dimension_signals(tokens)
        self.assertEqual(len(accepted), 1)
        self.assertAlmostEqual(accepted[0]["value_m"], 3.8227, places=4)
        self.assertEqual([item["text"] for item in suspicious], ["2'-6 1/4°"])

    def test_audit_holds_scale_legends_and_material_sizes_by_spatial_context(self):
        tokens = [
            {"text": "METRIC", "confidence": 0.95, "region": [0.10, 0.10, 0.18, 0.12]},
            {"text": "1M", "confidence": 0.90, "region": [0.20, 0.10, 0.23, 0.12]},
            {"text": "2x4", "confidence": 0.92, "region": [0.40, 0.20, 0.44, 0.22]},
            {"text": "1'×8", "confidence": 0.88, "region": [0.45, 0.20, 0.50, 0.22]},
        ]
        accepted, suspicious = ocr_audit.dimension_signals(tokens)
        self.assertEqual(accepted, [])
        self.assertEqual(
            {item["reason"] for item in suspicious},
            {"scale-legend-context", "material-size-context"},
        )

    def test_audit_does_not_greedily_join_leading_labels(self):
        tokens = [
            {"text": "BATHROOM", "confidence": 0.99, "region": [0.10, 0.10, 0.20, 0.12]},
            {"text": "UNIT 16A", "confidence": 0.98, "region": [0.50, 0.10, 0.60, 0.12]},
            {"text": "7'-10 3/4\"", "confidence": 0.94,
             "region": [0.80, 0.10, 0.85, 0.12]},
        ]
        accepted, _ = ocr_audit.dimension_signals(tokens)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["token_count"], 1)
        self.assertEqual(accepted[0]["region"], tokens[2]["region"])

    def test_audit_does_not_complete_scale_fragment_with_author_credit(self):
        tokens = [
            {"text": "SCALE", "confidence": 0.99, "region": [0.80, 0.10, 0.86, 0.12]},
            {"text": "1'-", "confidence": 0.91, "region": [0.88, 0.10, 0.92, 0.12]},
            {"text": "K.C. MCCAETER, DEL.", "confidence": 0.96,
             "region": [0.10, 0.12, 0.25, 0.14]},
        ]
        accepted, suspicious = ocr_audit.dimension_signals(tokens)
        self.assertEqual(accepted, [])
        self.assertTrue(suspicious)

    def test_regression_selects_lesson_free_control(self):
        baseline = {
            "route": {"approved": "G1_METRIC_GRAPH", "G1_METRIC_GRAPH": True,
                      "gates": [{"id": "scale-spread", "status": "PASS"}]},
            "unresolved_assertions": 1,
        }
        cumulative = {
            "route": {"approved": "A0_TRIAGED", "A0_TRIAGED": True,
                      "gates": [{"id": "scale-spread", "status": "FAIL"}]},
            "unresolved_assertions": 2,
        }
        result = curriculum.compare_candidates(baseline, cumulative)
        self.assertEqual(result["selected"], "baseline")
        self.assertIn("scale-spread", result["regressions"])
        self.assertIn("promotion-level", result["regressions"])

    def test_cluster_order_is_input_order_independent(self):
        records = [{"id": item} for item in ("aa", "bb", "cc", "dd", "ee", "ff")]
        features = {
            "aa": {"area": 20, "height": 2.5, "floors": 1},
            "bb": {"area": 25, "height": 2.8, "floors": 1},
            "cc": {"area": 45, "height": 3.0, "floors": 1},
            "dd": {"area": 55, "height": 5.8, "floors": 2},
            "ee": {"area": 95, "height": 6.2, "floors": 2},
            "ff": {"area": 140, "height": 8.8, "floors": 3},
        }
        charter = {"curriculum": {"minimum_clusters": 3, "maximum_clusters": 3}}
        first = curriculum.build_curriculum(records, features, charter)
        second = curriculum.build_curriculum(list(reversed(records)), features, charter)
        self.assertEqual(first, second)
        self.assertEqual(set(first[1]), set(features))

    def test_generic_compiler_keeps_physical_xyz_and_budget_receipt(self):
        graph = {
            "dimensions": {"width_m": 6.0, "depth_m": 8.0, "floor_count": 1,
                           "mean_height_m": 2.8, "ridge_height_m": 4.2},
            "openings": [{"id": "door-1", "kind": "door", "wall": "south", "u": 0.5}],
        }
        pieces, receipt = curriculum.compile_generic(graph, 256)
        self.assertTrue(pieces)
        self.assertTrue(all(len(piece["position"]) == 3 for piece in pieces))
        self.assertEqual(receipt["physical_scale"], 1.0)
        self.assertFalse(receipt["nonuniform_scale"])
        self.assertTrue(receipt["within_budget"])

    def test_acquisition_plan_requires_http_content_length(self):
        with self.assertRaises(harvester.AcquisitionBudgetError):
            harvester.required_http_bytes({}, "https://example.invalid/sheet.tif")

    def test_acquisition_budget_rejects_each_scope(self):
        cases = (
            {"sheet_bytes": 11, "building_bytes": 11, "total_bytes": 11},
            {"sheet_bytes": 5, "building_bytes": 21, "total_bytes": 21},
            {"sheet_bytes": 5, "building_bytes": 15, "total_bytes": 31},
        )
        for values in cases:
            with self.subTest(values=values), self.assertRaises(
                harvester.AcquisitionBudgetError
            ):
                harvester.check_planned_budget(
                    loc_id="control",
                    sheet_limit=10,
                    building_limit=20,
                    total_limit=30,
                    **values,
                )

    def test_frozen_download_accepts_exact_size_and_removes_drifted_partial(self):
        payload = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
            "YAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        )

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_HEAD(self):
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Content-Type", "image/png")
                self.end_headers()

            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Content-Type", "image/png")
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, _format, *_args):
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = harvester.LocClient("test", 5.0, 0, 0.0)
            url = f"http://127.0.0.1:{server.server_port}/sheet.png"
            with tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "sheet.png"
                tracker = {
                    "sheet_limit": len(payload),
                    "building_limit": len(payload),
                    "total_limit": len(payload),
                    "building_bytes": 0,
                    "total_bytes": 0,
                }
                record, disposition = harvester.download_file(
                    client,
                    url,
                    target,
                    None,
                    None,
                    planned_bytes=len(payload),
                    budget=tracker,
                )
                self.assertEqual(disposition, "downloaded")
                self.assertEqual(record["bytes"], len(payload))
                self.assertEqual(tracker["total_bytes"], len(payload))

                drifted = Path(directory) / "drifted.png"
                with self.assertRaises(harvester.AcquisitionBudgetError):
                    harvester.download_file(
                        client,
                        url,
                        drifted,
                        None,
                        None,
                        planned_bytes=len(payload) - 1,
                        budget={
                            "sheet_limit": len(payload),
                            "building_limit": len(payload),
                            "total_limit": len(payload),
                            "building_bytes": 0,
                            "total_bytes": 0,
                        },
                    )
                self.assertFalse(drifted.exists())
                self.assertFalse(Path(str(drifted) + ".part").exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_registration_is_unique_or_held_without_input_order_effect(self):
        passing = {"different_sheets": True, "plan_independently_calibrated": True,
                   "vertical_independently_calibrated": True,
                   "exact_section_marker": True, "compatible_metric_span": True,
                   "matching_floor_or_grade_origin": True, "cut_line_axis": True}
        failed = {**passing, "exact_section_marker": False}
        unique = [
            {"id": "b", "status": "CANDIDATE", "gates": failed},
            {"id": "a", "status": "CANDIDATE", "gates": passing},
        ]
        rows, registration = css_v3.resolve_registration_candidates(unique)
        self.assertEqual(registration["candidate_id"], "a")
        self.assertEqual([row["id"] for row in rows], ["a", "b"])
        ambiguous = [
            {"id": "a", "status": "CANDIDATE", "gates": dict(passing)},
            {"id": "c", "status": "CANDIDATE", "gates": dict(passing)},
        ]
        first = css_v3.resolve_registration_candidates(ambiguous)
        second = css_v3.resolve_registration_candidates(list(reversed(ambiguous)))
        self.assertEqual(first, second)
        self.assertEqual(first[1]["status"], "HELD_AMBIGUOUS")
        self.assertTrue(all(row["status"] == "HELD_AMBIGUOUS" for row in first[0]))

    def test_cut_line_requires_paired_markers_and_real_segment_provenance(self):
        endpoints = [
            {"marker": "W", "center_px": [20, 10], "confidence": .9,
             "crop_px": [10, 0, 30, 20], "ocr_engine": "RapidOCR/3.9.2-recognizer",
             "source_sha256": "a" * 64},
            {"marker": "W", "center_px": [20, 90], "confidence": .8,
             "crop_px": [10, 80, 30, 100], "ocr_engine": "RapidOCR/3.9.2-recognizer",
             "source_sha256": "a" * 64},
        ]
        segments = [
            {"id": "top", "pixels": [10, 10, 30, 10], "length_px": 20,
             "detector": "OpenCV.HoughLinesP", "source_sha256": "a" * 64},
            {"id": "bottom", "pixels": [10, 90, 30, 90], "length_px": 20,
             "detector": "OpenCV.HoughLinesP", "source_sha256": "a" * 64},
        ]
        passing = css_v3.cut_line_contract("plan", "W", endpoints, segments, [100, 100])
        self.assertEqual((passing["status"], passing["axis"]), ("PASS", "z"))
        segments[1] = {**segments[1], "source_sha256": None}
        failed = css_v3.cut_line_contract("plan", "W", endpoints, segments, [100, 100])
        self.assertEqual(failed["status"], "FAIL")
        self.assertIn("two-source-pinned-endpoint-segments-required", failed["reasons"])


if __name__ == "__main__":
    unittest.main()

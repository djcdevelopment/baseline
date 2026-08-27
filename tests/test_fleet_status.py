import copy
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from tools.fleet import render_status


ROOT = Path(__file__).resolve().parents[1]
INTENT_PATH = ROOT / "fleet" / "intent.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "fleet_status" / "github.json"
NOW = dt.datetime(2026, 8, 19, 12, 0, tzinfo=dt.timezone.utc)


class FleetStatusTests(unittest.TestCase):
    def setUp(self):
        self.intent_data = json.loads(INTENT_PATH.read_text(encoding="utf-8"))
        self.fixture_data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def collect(self, *, intent=None, fixture=None, now=NOW):
        checked = render_status.validate_intent(
            copy.deepcopy(intent or self.intent_data), today=now.date()
        )
        client = render_status.FixtureClient(copy.deepcopy(fixture or self.fixture_data))
        return render_status.collect_status(checked, client, now=now)

    def test_offline_projection_has_three_tables_and_current_head_ci(self):
        model = self.collect()
        rows = {row["id"]: row for row in model["repositories"]}
        seams = {row["id"]: row for row in model["seams"]}

        self.assertEqual(6, len(rows))
        self.assertEqual(6, len(seams))
        self.assertEqual("PASS", rows["comfy-quest"]["ci_state"])
        self.assertEqual("FAIL", rows["lumberjacks-platform"]["ci_state"])
        self.assertEqual("ATTENTION", model["overall"])
        self.assertEqual("PINNED_BEHIND", seams["quest-release-platform"]["state"])
        self.assertEqual("PINNED_BEHIND", seams["platform-baseline-corpus"]["state"])
        self.assertEqual("PINNED_DIFFERENT", seams["quest-contracts-platform"]["state"])
        self.assertEqual("CURRENT", seams["transport-contracts-networksense"]["state"])

        page = render_status.render_html(model)
        markdown = render_status.render_markdown(model)
        self.assertEqual(3, page.count("<table>"))
        self.assertEqual(1, markdown.count("## Fleet now"))
        self.assertEqual(1, markdown.count("## Where we are going"))
        self.assertEqual(1, markdown.count("## Integration seams"))

    def test_old_green_run_cannot_make_current_head_green(self):
        fixture = copy.deepcopy(self.fixture_data)
        fixture["repositories"]["djcdevelopment/comfy-quest"]["workflows"]["ci.yml"][0][
            "head_sha"
        ] = "1" * 40
        fixture["repositories"]["djcdevelopment/comfy-quest"]["workflows"]["ci.yml"][0][
            "conclusion"
        ] = "success"

        model = self.collect(fixture=fixture)
        quest = next(row for row in model["repositories"] if row["id"] == "comfy-quest")
        self.assertEqual("UNVERIFIED", quest["ci_state"])
        self.assertIn(
            {"scope": "comfy-quest", "code": "NO_CI_FOR_HEAD"}, model["warnings"]
        )

    def test_in_progress_current_run_is_running_without_false_failure(self):
        fixture = copy.deepcopy(self.fixture_data)
        run = fixture["repositories"]["djcdevelopment/lumberjacks-platform"]["workflows"][
            "ci.yml"
        ][0]
        run["status"] = "in_progress"
        run["conclusion"] = None

        model = self.collect(fixture=fixture)
        platform = next(
            row for row in model["repositories"] if row["id"] == "lumberjacks-platform"
        )
        self.assertEqual("RUNNING", platform["ci_state"])
        self.assertNotIn(
            {"scope": "lumberjacks-platform", "code": "CI_FAILED"}, model["warnings"]
        )

    def test_intent_warns_after_thirty_days_not_at_thirty(self):
        at_limit = copy.deepcopy(self.intent_data)
        at_limit["repositories"][0]["intent_as_of"] = "2026-07-20"
        model = self.collect(intent=at_limit)
        self.assertEqual("CURRENT", model["repositories"][0]["intent_state"])

        over_limit = copy.deepcopy(self.intent_data)
        over_limit["repositories"][0]["intent_as_of"] = "2026-07-19"
        model = self.collect(intent=over_limit)
        self.assertEqual("STALE", model["repositories"][0]["intent_state"])
        self.assertIn({"scope": "baseline", "code": "STALE_INTENT"}, model["warnings"])

    def test_remote_failure_renders_unknown_instead_of_suppressing_page(self):
        fixture = copy.deepcopy(self.fixture_data)
        fixture["repositories"]["djcdevelopment/comfy-quest"] = {
            "error": "API_UNAVAILABLE"
        }

        model = self.collect(fixture=fixture)
        quest = next(row for row in model["repositories"] if row["id"] == "comfy-quest")
        self.assertEqual("UNKNOWN", quest["ci_state"])
        self.assertTrue(model["degraded"])
        self.assertIn("UNKNOWN", render_status.render_html(model))
        self.assertIn(
            {"scope": "comfy-quest", "code": "REPOSITORY_API_UNAVAILABLE"},
            model["warnings"],
        )

    def test_malformed_remote_commit_renders_unknown_instead_of_crashing(self):
        fixture = copy.deepcopy(self.fixture_data)
        fixture["repositories"]["djcdevelopment/comfy-quest"]["commit"].pop("sha")

        model = self.collect(fixture=fixture)
        quest = next(row for row in model["repositories"] if row["id"] == "comfy-quest")
        self.assertEqual("UNKNOWN", quest["ci_state"])
        self.assertIn(
            {"scope": "comfy-quest", "code": "REPOSITORY_MALFORMED_RESPONSE"},
            model["warnings"],
        )

    def test_private_repository_metadata_never_enters_public_outputs(self):
        model = self.collect()
        rendered = "\n".join(
            (
                render_status.render_html(model),
                render_status.render_markdown(model),
                json.dumps(model, sort_keys=True),
            )
        )
        self.assertNotIn("PRIVATE-SUBJECT-MUST-NOT-LEAK", rendered)
        self.assertNotIn("djcdevelopment/isolate", rendered)
        self.assertNotIn("372a48ebb0db", rendered)
        self.assertNotIn("31617179947", rendered)
        isolate = next(row for row in model["repositories"] if row["id"] == "isolate")
        self.assertEqual(
            {
                "id",
                "name",
                "purpose",
                "current_focus",
                "next_outcome",
                "done_when",
                "blocker",
                "claim_state",
                "intent_as_of",
                "intent_age_days",
                "intent_state",
                "ci_state",
                "visibility",
                "private_detail",
            },
            set(isolate),
        )

    def test_non_exact_package_constraint_turns_the_seam_red(self):
        fixture = copy.deepcopy(self.fixture_data)
        fixture["repositories"]["djcdevelopment/networksense"]["files"][
            "eng/dependencies.interim.props"
        ] = (
            "<Project><PropertyGroup>"
            "<ComfyQuestContractsVersion>[0.1.0,0.3.0)</ComfyQuestContractsVersion>"
            "<ComfyTransportContractsVersion>0.1.0-local</ComfyTransportContractsVersion>"
            "</PropertyGroup></Project>"
        )

        model = self.collect(fixture=fixture)
        seam = next(
            row for row in model["seams"] if row["id"] == "quest-contracts-networksense"
        )
        self.assertEqual("BROKEN", seam["state"])
        self.assertTrue(model["degraded"])

    def test_non_exact_producer_version_turns_the_seam_red(self):
        fixture = copy.deepcopy(self.fixture_data)
        fixture["repositories"]["djcdevelopment/comfy-quest"]["files"][
            "network/mod/ComfyQuestContracts/ComfyQuestContracts.csproj"
        ] = "<Project><PropertyGroup><Version>$(Version)</Version></PropertyGroup></Project>"

        model = self.collect(fixture=fixture)
        seam = next(
            row for row in model["seams"] if row["id"] == "quest-contracts-platform"
        )
        self.assertEqual("BROKEN", seam["state"])
        self.assertTrue(model["degraded"])

    def test_divergent_revision_is_not_reported_as_intentionally_behind(self):
        fixture = copy.deepcopy(self.fixture_data)
        key = (
            "a7043648fe171152f71c5af743a2b81a9f8eef02"
            "...0fd6db103ee20691880e4c9fa9fd962f86ef4dd3"
        )
        fixture["repositories"]["djcdevelopment/comfy-quest"]["compares"][key] = "diverged"

        model = self.collect(fixture=fixture)
        seam = next(row for row in model["seams"] if row["id"] == "quest-release-platform")
        self.assertEqual("DIVERGED", seam["state"])
        self.assertTrue(model["degraded"])

    def test_public_text_is_escaped_and_private_shaped_values_are_rejected(self):
        escaped = copy.deepcopy(self.intent_data)
        escaped["repositories"][0]["current_focus"] = "Explain <script>alert(1)</script> safely."
        model = self.collect(intent=escaped)
        page = render_status.render_html(model)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)

        unsafe = copy.deepcopy(self.intent_data)
        unsafe["repositories"][0]["next_outcome"] = (
            "Publish the operator view at https://private.example.ts.net/status"
        )
        with self.assertRaises(render_status.ConfigError):
            render_status.validate_intent(unsafe, today=NOW.date())

    def test_invalid_schema_duplicate_ids_and_future_dates_fail_closed(self):
        wrong_schema = copy.deepcopy(self.intent_data)
        wrong_schema["schema"] = "baseline-fleet-intent/v2"
        with self.assertRaises(render_status.ConfigError):
            render_status.validate_intent(wrong_schema, today=NOW.date())

        duplicate = copy.deepcopy(self.intent_data)
        duplicate["repositories"][1]["id"] = "baseline"
        with self.assertRaises(render_status.ConfigError):
            render_status.validate_intent(duplicate, today=NOW.date())

        future = copy.deepcopy(self.intent_data)
        future["repositories"][0]["intent_as_of"] = "2026-08-20"
        with self.assertRaises(render_status.ConfigError):
            render_status.validate_intent(future, today=NOW.date())

    def test_frozen_fixture_render_is_byte_deterministic(self):
        model = self.collect()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_path = Path(first)
            second_path = Path(second)
            render_status.write_outputs(model, first_path)
            render_status.write_outputs(model, second_path)
            for name in ("index.html", "status.md", "status.json"):
                self.assertEqual(
                    (first_path / name).read_bytes(), (second_path / name).read_bytes()
                )


if __name__ == "__main__":
    unittest.main()

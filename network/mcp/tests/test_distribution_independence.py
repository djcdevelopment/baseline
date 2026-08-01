"""Architecture regression: the project MCP must run from this repository alone.

The privacy scanner (tools/workbench/Test-WorkbenchZipPrivacy.ps1) gates what goes
*into* a published zip. It cannot prove project independence, because the coupling
that matters is usually not in a zip at all — on 2026-08-01 the launcher
network/mcp/etc/start-comfy-gateway.cmd had a second interpreter rung pointing at
the operator's private venv. It named no private system, shipped in no bundle, and
would have passed every content rule. What caught it was asking a different
question: does anything in the distributable surface reach outside the checkout?

That is this test. It scans the files a contributor actually receives and runs —
not the whole repository. Internal evidence, retros, audits, and roadmap provenance
are allowed to name and describe private infrastructure, and deliberately are not
scanned here.

Note what is NOT forbidden: the words HEARTH and Mechnet. They are not secrets, and
they are valid in provenance, boundary documentation, and any sentence that
distinguishes this project-owned gateway from a general-purpose one. The rules below
match concrete private *configuration* — paths, endpoints, and interpreters — which
is what creates a dependency a contributor cannot satisfy.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# The distributable project-MCP / toolkit surface: what a contributor clones, builds,
# reads, and runs. Directories are walked; files are taken as-is.
DISTRIBUTION_SCOPE: tuple[str, ...] = (
    "network/mcp",
    "network/mod/ComfyNetworkSense/README.md",
    "Lumberjacks/docs/workbench/tools",
)

# Runtime state, caches, and build output are not authored surface.
EXCLUDED_PARTS = frozenset({"var", "__pycache__", ".pytest_cache", "bin", "obj"})

SCANNED_SUFFIXES = frozenset({
    ".md", ".txt", ".json", ".jsonl", ".yml", ".yaml", ".py", ".cs", ".cmd",
    ".bat", ".ps1", ".psm1", ".sh", ".cfg", ".config", ".html", ".js", ".mjs",
    ".toml", ".ini", "",  # "" covers Dockerfile and friends
})

# This module lives inside the scope it scans, and that is deliberate: a checker
# exempt from its own rules is a hole in the rule. So the two literals that would
# otherwise match are assembled from fragments — the file genuinely contains no
# complete forbidden string, rather than being excused for containing one.
_PRIVATE_VENV = r"\.venv" + "-omen"
_PRIVATE_WORKER = "fleet-" + "worker-node"

FORBIDDEN = (
    (
        "private operator repository path",
        re.compile(r"C:\\work\\commandcenter", re.IGNORECASE),
    ),
    (
        "private virtual environment",
        re.compile(_PRIVATE_VENV, re.IGNORECASE),
    ),
    (
        "private fleet worker layout",
        re.compile(_PRIVATE_WORKER, re.IGNORECASE),
    ),
    (
        "private HEARTH gateway endpoint",
        re.compile(r"(?:127\.0\.0\.1|localhost):8710\b", re.IGNORECASE),
    ),
    (
        "user-profile absolute path",
        # Placeholder forms a doc may legitimately use — C:\Users\<you>\ or
        # C:\Users\%USERNAME%\ — fall outside the name class and do not match.
        re.compile(r"C:\\Users\\[A-Za-z0-9._-]+\\", re.IGNORECASE),
    ),
)


def _iter_scope_files():
    for entry in DISTRIBUTION_SCOPE:
        target = REPO_ROOT / entry
        if target.is_file():
            yield target
            continue
        if not target.is_dir():
            raise AssertionError(f"distribution scope entry does not exist: {entry}")
        for path in sorted(target.rglob("*")):
            if not path.is_file():
                continue
            if EXCLUDED_PARTS.intersection(path.relative_to(target).parts):
                continue
            if path.suffix.lower() not in SCANNED_SUFFIXES:
                continue
            yield path


class DistributionIndependenceTest(unittest.TestCase):
    def test_scope_is_non_empty(self) -> None:
        """A silently-empty scan would make every assertion below vacuously true."""
        files = list(_iter_scope_files())
        self.assertGreater(len(files), 10, "distribution scope resolved to almost nothing")

    def test_no_private_environment_references(self) -> None:
        findings: list[str] = []
        for path in _iter_scope_files():
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            relative = path.relative_to(REPO_ROOT).as_posix()
            for line_number, line in enumerate(text.splitlines(), start=1):
                for label, pattern in FORBIDDEN:
                    match = pattern.search(line)
                    if match:
                        findings.append(
                            f"{relative}:{line_number}: {label} -> {match.group(0)}"
                        )
        self.assertEqual(
            findings,
            [],
            "distributable project-MCP surface references private operator "
            "infrastructure:\n  " + "\n  ".join(findings),
        )

    def test_launcher_has_no_machine_specific_interpreter_rung(self) -> None:
        """The specific defect, asserted directly.

        The general scan above would catch the old fallback by its path, but this
        pins the *shape* of the fix: exactly two interpreter sources, the explicit
        environment variable and PATH.
        """
        launcher = REPO_ROOT / "network/mcp/etc/start-comfy-gateway.cmd"
        text = launcher.read_text(encoding="utf-8")
        self.assertIn("COMFY_GATEWAY_PYTHON", text)
        self.assertNotIn("COMFY_GATEWAY_PYTHON_FALLBACK", text)
        assignments = re.findall(
            r'set\s+"?COMFY_GATEWAY_PYTHON_EXE=([^"\r\n]+)"?', text
        )
        self.assertEqual(
            assignments,
            ["%COMFY_GATEWAY_PYTHON%", "python"],
            "launcher interpreter precedence must be exactly: explicit env var, then PATH",
        )

    def test_dependencies_are_declared_in_a_file(self) -> None:
        """Prose alone is not a reproducible dependency declaration."""
        requirements = REPO_ROOT / "network/mcp/requirements.txt"
        self.assertTrue(requirements.is_file(), "network/mcp/requirements.txt is missing")
        declared = requirements.read_text(encoding="utf-8")
        self.assertRegex(declared, r"(?m)^mcp==")

        dockerfile = (REPO_ROOT / "network/mcp/Dockerfile").read_text(encoding="utf-8")
        self.assertIn("requirements.txt", dockerfile)
        self.assertNotIn(
            'pip install --no-cache-dir "mcp==',
            dockerfile,
            "the image must install from requirements.txt, not a second inline pin",
        )


if __name__ == "__main__":
    unittest.main()

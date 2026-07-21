import re
from pathlib import Path
from urllib.parse import unquote
import unittest


ROOT = Path(__file__).resolve().parents[1]


def _entrypoints():
    """Discover orientation docs instead of hardcoding them.

    The list used to be literal, which meant every directory removed from the repo
    turned this test red for a reason that had nothing to do with broken links --
    the 2026-07 prune took out five of the nine named files at once. Discovery keeps
    the test about link integrity and lets the repo's shape change underneath it.
    Scope stays deliberately shallow: the root README plus one README per top-level
    directory, not every README in the tree (Lumberjacks/ alone has dozens, and they
    are that subtree's concern).
    """
    found = [ROOT / "README.md"]
    for child in sorted(ROOT.iterdir()):
        if child.name.startswith(".") or not child.is_dir():
            continue
        readme = child / "README.md"
        if readme.is_file():
            found.append(readme)
    return [p for p in found if p.is_file()]


ENTRYPOINTS = _entrypoints()
LINK = re.compile(r"!?\[[^]]*\]\(([^)]+)\)")


class EntrypointLinkTests(unittest.TestCase):
    def test_local_links_resolve(self):
        missing = []
        for document in ENTRYPOINTS:
            for raw_target in LINK.findall(document.read_text(encoding="utf-8")):
                target = raw_target.split("#", 1)[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (document.parent / unquote(target)).resolve()
                if not resolved.exists():
                    missing.append(f"{document.relative_to(ROOT)} -> {target}")
        self.assertEqual([], missing, "Missing local links:\n" + "\n".join(missing))


if __name__ == "__main__":
    unittest.main()

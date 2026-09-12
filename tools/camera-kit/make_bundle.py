#!/usr/bin/env python3
"""Zip the kit into one release bundle with a manifest, the companion-bootstrap shape.

    python make_bundle.py --out <dir> [--release camera-kit-YYYYMMDD]

Produces `<release>.zip` (runner, shot lists, mods with their NOTICE and SHA256SUMS,
README) and `<release>.json` (schema_version 1: package file, SHA-256, size, entrypoint,
the plugin hashes, the game builds the kit was proven on). Publishing the two files as
a GitHub release is a separate, operator-run step; this only builds them.
"""
import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["README.md", "Invoke-EraCapture.ps1", "capture_kit.py", "make_shots.py",
         "mods/NOTICE.md", "mods/SHA256SUMS", "mods/ComfyCameraProof.dll", "mods/BetterServerPortals.dll"]
PROVEN_ON = ["25185596", "25253764"]   # Valheim 1.0.7 (AM4, Linux) and 1.0.12 (OMEN, Windows)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--release", default="camera-kit-" + time.strftime("%Y%m%d"))
    args = p.parse_args()
    files = [HERE / f for f in FILES] + sorted((HERE / "shots").glob("shots-*.tsv"))
    missing = [str(f) for f in files if not f.exists()]
    if missing:
        raise SystemExit("missing from the kit: " + ", ".join(missing))
    sums = {line.split()[1].lstrip("*"): line.split()[0]
            for line in (HERE / "mods" / "SHA256SUMS").read_text(encoding="utf-8").splitlines() if line.strip()}
    for name, digest in sums.items():
        actual = sha256(HERE / "mods" / name)
        if actual != digest:
            raise SystemExit(f"mods/{name} is {actual[:12]}…, SHA256SUMS says {digest[:12]}…")
    args.out.mkdir(parents=True, exist_ok=True)
    package = args.out / f"{args.release}.zip"
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f"camera-kit/{f.relative_to(HERE).as_posix()}")
    manifest = {
        "schema_version": 1,
        "release": args.release,
        "package_file": package.name,
        "package_sha256": sha256(package),
        "package_size_bytes": package.stat().st_size,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "entrypoint": "camera-kit/Invoke-EraCapture.ps1",
        "plugins": {name: {"sha256": digest, "bytes": (HERE / "mods" / name).stat().st_size} for name, digest in sums.items()},
        "shot_lists": [f.name for f in files if f.suffix == ".tsv"],
        "proven_on_game_builds": PROVEN_ON,
    }
    (args.out / f"{args.release}.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{package} ({manifest['package_size_bytes']:,} B, {manifest['package_sha256'][:12]}…) + {args.release}.json")


if __name__ == "__main__":
    main()

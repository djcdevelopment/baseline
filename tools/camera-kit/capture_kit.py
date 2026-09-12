#!/usr/bin/env python3
"""Shoot a list of camera poses in a Valheim world on your own machine, with receipts.

This is the community half of the era-archive photography: the same two plugins the
archive uses (ComfyCameraProof, which reads a shot list and takes 4K stills unattended,
and BetterServerPortals, which keeps a big old world's portals from stalling the load),
the same shot-list format, the same receipts. Point it at your Valheim install, a world
you have copied into worlds_local, a character, and a shot list; it parks whatever
plugins you normally run, drops in exactly these two, launches the game directly (never
through Steam, so a queued update cannot move the game under you), waits for the frames,
and puts everything back.

    python capture_kit.py --game-root "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Valheim" ^
        --world ComfyEra11 --character MyViking --shots shots-era11.tsv --out out\\era11

Standard library only. Windows first; Linux works with --game-root pointing at a client
that has BepInEx's start_game_bepinex.sh (the Unity Linux player reads its prefs from
unity3d/unknown/unknown when -screen-* flags are present -- see the archive's notes).

Shot list: tab-separated, one row per frame, `#` lines ignored:
  cluster_id  shot  cam_x  cam_y  cam_z  yaw  pitch  env  time  aim_x  aim_y  aim_z  label  mode  fires  flash
cam_* is where the player's feet are put (the lens rides ~1.7 m above); yaw is degrees
clockwise from +Z, pitch positive looks down; env is a Valheim environment name (Clear);
time is 0..1 of the day. The gallery's own lists are in this format, so a run here
reproduces the archive's frames.
"""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

HEADER = "# cluster_id\tshot\tcam_x\tcam_y\tcam_z\tyaw\tpitch\tenv\ttime\taim_x\taim_y\taim_z\tlabel\tmode\tfires\tflash\n"
PLUGINS = ("ComfyCameraProof.dll", "BetterServerPortals.dll")
CONTROL = ("shotplan.tsv", "shotplan-receipts.jsonl", "orbit-request.json")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def png_ok(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
        fh.seek(-12, 2)
        tail = fh.read(12)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or tail != b"\0\0\0\0IEND\xaeB`\x82":
        return None
    return list(struct.unpack(">II", head[16:24]))


def save_dir():
    if platform.system() == "Windows":
        return Path(os.environ["USERPROFILE"]) / "AppData" / "LocalLow" / "IronGate" / "Valheim"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "unity3d" / "IronGate" / "Valheim"


def read_rows(path):
    rows = []
    for raw in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip("\r\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 12:
            raise SystemExit(f"shot list row has {len(fields)} columns, needs at least 12: {line[:80]}")
        int(fields[0]); [float(fields[i]) for i in (2, 3, 4, 5, 6, 8, 9, 10, 11)]
        rows.append(fields)
    if not rows:
        raise SystemExit("the shot list has no rows")
    return rows


def game_build(game_root):
    manifest = game_root.parent.parent / "appmanifest_892970.acf"
    if manifest.exists():
        m = re.search(r'"buildid"\s*"(\d+)"', manifest.read_text(encoding="utf-8", errors="replace"))
        if m:
            return m.group(1)
    return None


def read_receipts(path, wanted):
    found = {}
    if not path.exists():
        return found
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = (row.get("cluster_id"), row.get("shot"))
        if key in wanted:
            found[key] = row
    return found


def find_character(name, characters):
    """The character's own file: characters_local first, then the Steam Cloud folder Steam keeps
    on disk (userdata/<id>/892970/remote/characters). Read only; the run plays a copy."""
    local = characters / f"{name}.fch"
    if local.exists():
        return local
    roots = []
    if platform.system() == "Windows":
        for env in ("ProgramFiles(x86)", "ProgramFiles"):
            base = os.environ.get(env)
            if base:
                roots.append(Path(base) / "Steam" / "userdata")
    else:
        roots += [Path.home() / ".steam" / "steam" / "userdata", Path.home() / ".local" / "share" / "Steam" / "userdata"]
    for root in roots:
        for candidate in sorted(root.glob(f"*/892970/remote/characters/{name}.fch")) if root.exists() else []:
            return candidate
    return None


def place_file(source, target, what):
    """Copy a world/character file in, refusing to replace a different file of the same name."""
    if target.exists():
        if sha256(target) == sha256(source):
            return "present"
        raise SystemExit(f"{what} already exists with different contents: {target}\n"
                         f"Move it aside yourself; this tool never overwrites a save.")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return "copied"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--game-root", type=Path, required=True, help="folder with valheim.exe (or valheim.x86_64) and BepInEx/")
    p.add_argument("--world", required=True, help="world name as the game shows it (the .db/.fwl stem)")
    p.add_argument("--world-db", type=Path, help="copy this .db into worlds_local first (optional if already there)")
    p.add_argument("--world-fwl", type=Path, help="copy this .fwl into worlds_local first")
    p.add_argument("--character", required=True, help="character name (an existing .fch in characters_local, or see --character-file)")
    p.add_argument("--character-file", type=Path, help="copy this .fch into characters_local first")
    p.add_argument("--shots", type=Path, required=True, help="tab-separated shot list")
    p.add_argument("--out", type=Path, required=True, help="where frames and receipts go")
    p.add_argument("--mods", type=Path, default=Path(__file__).resolve().parent / "mods",
                   help="folder holding ComfyCameraProof.dll and BetterServerPortals.dll")
    p.add_argument("--width", type=int, default=3840)
    p.add_argument("--height", type=int, default=2160)
    p.add_argument("--timeout-minutes", type=float, default=0, help="0 = 5 min + 1 min per shot")
    p.add_argument("--keep-window", action="store_true", help="show the game window normally instead of minimised")
    args = p.parse_args()

    game = args.game_root.resolve()
    exe = game / ("valheim.exe" if platform.system() == "Windows" else "start_game_bepinex.sh")
    if not exe.exists():
        raise SystemExit(f"not a Valheim install with BepInEx: {exe} missing")
    if not (game / "BepInEx" / "core").is_dir():
        raise SystemExit("BepInEx is not installed in this game folder (install BepInExPack Valheim from Thunderstore first)")
    if platform.system() == "Windows" and subprocess.run(["tasklist", "/FI", "IMAGENAME eq steam.exe"], capture_output=True, text=True).stdout.count("steam.exe") == 0:
        raise SystemExit("Steam must be running (the game needs steam_api); start Steam, then rerun")
    mods = {name: args.mods / name for name in PLUGINS}
    for name, path in mods.items():
        if not path.exists():
            raise SystemExit(f"missing plugin {path}; put the released DLLs in {args.mods}")

    rows = read_rows(args.shots)
    wanted = {(int(r[0]), r[1]) for r in rows}
    saves = save_dir()
    worlds, characters = saves / "worlds_local", saves / "characters_local"
    placed = {}
    if args.world_db:
        placed["db"] = place_file(args.world_db, worlds / f"{args.world}.db", "world .db")
    if args.world_fwl:
        placed["fwl"] = place_file(args.world_fwl, worlds / f"{args.world}.fwl", "world .fwl")
    for ext in (".db", ".fwl"):
        if not (worlds / f"{args.world}{ext}").exists():
            raise SystemExit(f"world file missing: {worlds / (args.world + ext)} (pass --world-db/--world-fwl or copy it there)")
    # The game plays a throwaway copy of the character, never the original. Valheim lists
    # Steam Cloud and local characters together and, when both hold the same file name, plays
    # the cloud one -- and saves it back, with the last camera as the logout point. A distinct
    # file stem (<name>-kit) keeps the run on a local copy the plugin picks by that stem, and the
    # copy is removed afterwards, so nothing of yours is written to.
    seed = f"{args.character}-kit"
    seed_file = characters / f"{seed}.fch"
    source = args.character_file or find_character(args.character, characters)
    if source is None:
        raise SystemExit(f"no character named {args.character!r} in {characters} or the Steam Cloud folder; pass --character-file")
    if seed_file.exists():
        seed_file.unlink()
    characters.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, seed_file)
    placed["character"] = {"from": str(source), "sha256": sha256(source), "playedAs": seed}

    cfg = game / "BepInEx" / "config"
    plugins = game / "BepInEx" / "plugins"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    parked = game / "BepInEx" / f"plugins.kit-parked-{stamp}"
    backups = {}
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    process = None
    try:
        if plugins.exists():
            plugins.rename(parked)
        plugins.mkdir()
        for name, path in mods.items():
            shutil.copy2(path, plugins / name)
        cfg.mkdir(parents=True, exist_ok=True)
        for name in CONTROL:
            src = cfg / name
            if src.exists():
                backups[name] = src.read_bytes()
        (cfg / "shotplan.tsv").write_text(HEADER + "".join("\t".join(r) + "\n" for r in rows), encoding="utf-8")
        (cfg / "shotplan-receipts.jsonl").write_text("", encoding="utf-8")
        (cfg / "orbit-request.json").write_text(json.dumps({"world": args.world, "character": seed,
                                                            "quit_when_done": True}, indent=2), encoding="utf-8")
        captures = cfg / "comfy-orbit-captures"
        before = {p.name for p in captures.iterdir()} if captures.exists() else set()

        command = [str(exe), "-console", "-screen-fullscreen", "0", "-screen-width", str(args.width),
                   "-screen-height", str(args.height), "-monitor", "1"]
        creation = 0
        startup = None
        if platform.system() == "Windows" and not args.keep_window:
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 6  # SW_MINIMIZE
        log = (out / "stdout.log").open("wb")
        process = subprocess.Popen(command, cwd=game, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                   startupinfo=startup, creationflags=creation)
        timeout = args.timeout_minutes * 60 if args.timeout_minutes else 300 + 60 * len(rows)
        t0 = time.monotonic()
        print(f"launched {exe.name} pid {process.pid}; {len(rows)} shot(s); world load takes ~3 min, then ~10 s per frame")
        last = 0
        while process.poll() is None:
            n = len(read_receipts(cfg / "shotplan-receipts.jsonl", wanted))
            if n != last:
                print(f"  {n}/{len(rows)} receipts")
                last = n
            if time.monotonic() - t0 > timeout:
                print("timeout; stopping the game")
                process.terminate()
                try:
                    process.wait(120)
                except subprocess.TimeoutExpired:
                    process.kill()
                break
            time.sleep(5)
        log.close()
        receipts = read_receipts(cfg / "shotplan-receipts.jsonl", wanted)
        frames = []
        for key, row in receipts.items():
            if row.get("skipped") or not row.get("file"):
                frames.append({"cluster_id": key[0], "shot": key[1], "skipped": row.get("skipped", "no file")})
                continue
            src = captures / row["run"] / row["file"]
            dims = png_ok(src) if src.exists() else None
            if dims is None:
                frames.append({"cluster_id": key[0], "shot": key[1], "skipped": "frame incomplete"})
                continue
            dest = out / row["run"] / row["file"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            frames.append({"cluster_id": key[0], "shot": key[1], "file": dest.relative_to(out).as_posix(),
                           "bytes": dest.stat().st_size, "sha256": sha256(dest), "dimensions": dims, "receipt": row})
        for name in ("shotplan-receipts.jsonl",):
            if (cfg / name).exists():
                shutil.copy2(cfg / name, out / "receipts.jsonl")
        if (game / "BepInEx" / "LogOutput.log").exists():
            shutil.copy2(game / "BepInEx" / "LogOutput.log", out / "BepInEx.log")
        kept = sum(1 for f in frames if "file" in f)
        json.dump({"schema": "camera-kit-run/v1", "startedAt": started, "endedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "gameRoot": str(game), "gameBuild": game_build(game), "world": args.world, "character": args.character,
                   "resolution": [args.width, args.height], "placed": placed,
                   "plugins": {name: {"bytes": path.stat().st_size, "sha256": sha256(path)} for name, path in mods.items()},
                   "shots": len(rows), "frames": kept, "exitCode": process.returncode, "results": frames},
                  (out / "receipt.json").open("w", encoding="utf-8"), indent=2)
        print(f"{kept}/{len(rows)} frame(s) in {out}; receipt.json written")
        return 0 if kept == len(rows) else 1
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
        for name, data in backups.items():
            (cfg / name).write_bytes(data)
        for name in CONTROL:
            if name not in backups and (cfg / name).exists():
                (cfg / name).unlink()
        for leftover in seed_file.parent.glob(seed_file.name + "*"):   # the copy and the .old the game writes beside it
            leftover.unlink()
        if parked.exists():
            if plugins.exists():
                shutil.rmtree(plugins)
            parked.rename(plugins)
        print("your plugins and config are back as they were")


if __name__ == "__main__":
    sys.exit(main())

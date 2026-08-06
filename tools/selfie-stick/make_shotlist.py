#!/usr/bin/env python3
"""Turn clusters.json into a paste-ready console shot list.

No web app, no MCP, no mailbox. You alt-tab, copy a line, paste it into the
Valheim F5 console, and you are standing above the build.

Usage:
  python make_shotlist.py [--clusters PATH] [--out PATH]
                          [--in-world N] [--outland N]
"""
import argparse
import json
import os

HEADER = """\
================================================================================
 ERA 16 SHOT LIST  —  {count} builds
================================================================================

SETUP (once per session, in the F5 console)

    devcommands
    fly
    comfyproof_hideplayer on

  'fly' lets you reframe after each jump. 'hideplayer' keeps your character out
  of the shot — that one is the mod, vanilla has no equivalent.

HOTKEYS — the whole loop, one hand, no typing

    RIGHT ARROW   next build in the list (wraps around at the end)
    LEFT ARROW    previous build
    UP ARROW      capture this framing in 4 moods, hands off
    DOWN ARROW    write a status file

  These stand down automatically while the console or chat has focus, so
  up/down still scroll console history when you are typing.

  Rebind in BepInEx/config/com.comfy.camera-proof.cfg. Avoid F7 —
  ComfyControlSurface binds it for quest submit.

  Typed equivalents, if you prefer: next / prev / shot <n>


WEATHER AND TIME (change any time, applies instantly)

    comfyproof_env Clear          comfyproof_time 0.25   (morning)
    comfyproof_env Misty          comfyproof_time 0.50   (noon)
    comfyproof_env Rain           comfyproof_time 0.72   (sunset)
    comfyproof_env ThunderStorm   comfyproof_time 0.90   (night)
    comfyproof_env noforce        comfyproof_time off    (back to normal)

    comfyproof_envs   writes the full list of environment names to
                      BepInEx/config/comfy-camera-proof-envs.json

CAPTURING

    UP ARROW            frame it yourself, then press once. Hides you and the
                        HUD, then shoots 24 frames from one setup:
                          12 x clear, swept 0.33 -> 0.77 (dense at golden hour)
                           4 x misty, 4 x rain, 3 x storm
                        ~3 minutes hands-off. Go get a coffee.

    capture quick       4 frames if you are in a hurry
    capture weather     12 frames, weather-weighted
    F12                 Steam screenshot, if you have the overlay on

    Output: BepInEx/config/comfy-manual-captures/<timestamp>/
    Filenames sort in shooting order: a_clear_t33 ... d_storm_t66

    Every time value sits inside the band that measurably produces a usable
    frame. The old presets shot 0.25 and 0.90, which came back too dark 88% and
    97% of the time — half of every session was wasted. Those are gone.

    Video, if you want it: Win+Alt+R (Windows Game Bar) or OBS. Nothing in the
    mod records — screenshots are the fast path.

HOW TO READ AN ENTRY

    The teleport y is already set above the build so you arrive looking down at
    it. 'back' is roughly how far to pull the camera to fit the whole thing.
    High sign counts mean lore and detail worth reading; high portal counts
    mean a hub someone else visits.

    If the mod is not loaded, vanilla works too — 'goto <x> <z>' lands you at
    ground level and you fly up from there.

================================================================================
"""


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--clusters", default=os.path.join(here, "out", "clusters.json"))
    p.add_argument("--out", default=os.path.join(here, "out", "shotlist.txt"))
    p.add_argument("--in-world", type=int, default=40, help="how many in-world builds")
    p.add_argument("--outland", type=int, default=15, help="how many build-plot entries")
    return p.parse_args()


def describe(c):
    """One line of 'what am I looking at' from the landmark counts."""
    bits = []
    if c["size_y"] >= 80:
        bits.append("very tall")
    elif c["size_y"] >= 50:
        bits.append("tall")
    if c["footprint_m2"] >= 50000:
        bits.append("sprawling")
    if c["portals"] >= 30:
        bits.append("major hub")
    elif c["portals"] >= 10:
        bits.append("hub")
    if c["signs"] >= 500:
        bits.append("heavily signed")
    if c["distinct_creators"] >= 10:
        bits.append(f"{c['distinct_creators']} builders")
    elif c["distinct_creators"] == 1:
        bits.append("solo build")
    if c["item_stands"] >= 200:
        bits.append("big display collection")
    if c["sky"]:
        bits.append("SKY BUILD")
    return ", ".join(bits) or "dense build"


def block(n, c):
    head = (f"[{n:>2}]  {c['pieces']:>6,} pieces | {c['size_y']:>3.0f} m tall | "
            f"back ~{c['suggested_standoff_m']:.0f} m")
    detail = (f"      {describe(c)}\n"
              f"      portals {c['portals']}  beds {c['beds']}  signs {c['signs']}  "
              f"containers {c['containers']}")
    cmd = f"      comfyproof_tp {c['center_x']:.0f} {c['suggested_camera_y']:.0f} {c['center_z']:.0f}"
    vanilla = f"      (vanilla: goto {c['center_x']:.0f} {c['center_z']:.0f})"
    return "\n".join([head, detail, "", cmd, vanilla, ""])


def main():
    args = parse_args()
    with open(args.clusters, encoding="utf-8") as fh:
        doc = json.load(fh)

    inworld = [c for c in doc["clusters"] if c["region"] == "in-world"][: args.in_world]
    outland = [c for c in doc["clusters"] if c["region"] == "outland"][: args.outland]

    parts = [HEADER.format(count=len(inworld) + len(outland))]

    parts.append("\nTHE MAP — ranked by how well they should photograph\n")
    parts.append("-" * 80 + "\n")
    for i, c in enumerate(inworld, start=1):
        parts.append(block(i, c))

    if outland:
        parts.append("\n" + "=" * 80)
        parts.append("THE BUILD PLOTS — outside the world radius, on a 576 m grid")
        parts.append("=" * 80)
        parts.append("""
These sit past the playable map edge, in what looks like an instanced plot
area — templated lots, heavily signed, real people sleeping in them. Showcase
builds often live here. Worth a look before you decide they are not the story.
""")
        for i, c in enumerate(outland, start=1):
            parts.append(block(i, c))

    text = "\n".join(parts)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)

    print(f"wrote {len(inworld)} in-world + {len(outland)} plot entries -> {args.out}")


if __name__ == "__main__":
    main()

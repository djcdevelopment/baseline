# Camera kit — shoot the era archive's frames on your own machine

The gallery's 4K photographs are taken by a small BepInEx plugin that reads a list of camera
poses, places the camera, waits for the world to settle, and takes a screenshot with a receipt
saying exactly where the lens was and what it aimed at. Nothing about that needs our hardware.
This kit is the same plugins, the same shot lists and the same receipts, packaged so anyone
with Valheim and one of the end-of-era worlds can run it.

## What you need

1. **Valheim on Steam** (1.0.x), plus **BepInExPack Valheim** from Thunderstore installed into the
   game folder (`BepInEx\core` must exist).
2. **An era world.** The end-of-era saves were released by the community itself on the server's
   Discord — download the `.db` and `.fwl` pair for the era you want and either copy them into
   `%USERPROFILE%\AppData\LocalLow\IronGate\Valheim\worlds_local\` or pass them with `-WorldDb`
   / `-WorldFwl` (the kit copies them in and refuses to overwrite a different file of the same name).
3. **A character** — any of yours, by name. The kit finds it in `characters_local` or in the
   Steam Cloud folder Steam keeps on disk, or takes `-CharacterFile`, and plays a **copy** named
   `<name>-kit` (the game would otherwise pick the cloud copy of a same-named character and save
   the last camera back into it). The copy is deleted after the run; your character is never
   written to. It is made invulnerable and hidden for the shots.
4. **The two plugins** in `mods\`: `ComfyCameraProof.dll` (MIT, source in
   `github.com/djcdevelopment/comfy` under `handoffs/valheim-camera-proof`) and
   `BetterServerPortals.dll` 1.9.0 (GPL-3, built from `redseiko/ComfyMods` commit `a2b4680`
   against the 1.0 client; see `mods/NOTICE.md` for the pin and the build recipe). Check them
   against `mods/SHA256SUMS` before running.
5. **Python 3** on the PATH, and **Steam running** (the game needs `steam_api`; the kit never
   launches through Steam, it starts `valheim.exe` directly).

## Run

```powershell
.\Invoke-EraCapture.ps1 -World ComfyEra11 -Character MyViking -Shots .\shots\shots-era11.tsv -Out .\out\era11
```

Expect ~3 minutes for the world to load (these worlds hold ~7 million objects) and ~10 s per
frame after that. Frames land in `out\era11\<run>\NNNN_<shot>.png` with `receipt.json` (game
build, plugin hashes, every frame's SHA-256 and its capture receipt). Your own plugins and the
three control files are parked before the run and put back afterwards, even if the run fails.

At 3840×2160 the frame is the window size; on a smaller display use `-Width 1920 -Height 1080`
— the receipts record what you shot at. Proof of the round trip: run on a Windows PC with the
Steam client build 25253764 (1.0.12), three rows of `shots-era11.tsv` came back with the lens,
yaw and pitch equal to the archive's own receipts to the centimetre (`receipt.json` in
`docs/evidence/2026-09-12-camera-kit-omen/`).

## Shot lists

`shots\shots-<era>.tsv` are the archive's own lists: the pose the photography loop judged best
for each build (see the gallery's "refined" caption). The format is one tab-separated row per
frame:

```
# cluster_id  shot  cam_x  cam_y  cam_z  yaw  pitch  env  time  aim_x  aim_y  aim_z  label  mode  fires  flash
```

`cam_*` is where the player's feet go (the lens rides about 1.7 m above), `yaw` is degrees
clockwise from +Z, `pitch` positive looks down, `env` is a Valheim environment (`Clear`),
`time` is the fraction of the in-game day (0.64 = mid-afternoon). You can write your own rows
— the gallery's "open the 3D scene at this camera" link shows a photograph's pose, and the
world viewer's "Request this shot" produces rows in exactly this format.

## What is not here

No world files (they are on the Discord), no gallery pipeline (derivatives, indexes, the
site), no scoring. This is the photograph and its receipt, on your machine.

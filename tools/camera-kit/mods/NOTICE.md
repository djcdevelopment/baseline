# Plugins in this kit

| file | version | license | source |
|---|---|---|---|
| `ComfyCameraProof.dll` | 0.2.5 (feed mode, 1.0 cloth skip, intro skip, `pose`/`runclips`, plays the local character copy by file stem) | MIT | `github.com/djcdevelopment/comfy`, `handoffs/valheim-camera-proof/Plugin.cs`, commit `655ede1`; built with `dotnet build -c Release` against the Valheim 1.0 client (build 25253764) and BepInEx 5.4.23.3; runs on 25185596 too (it reaches the game by reflection) |
| `BetterServerPortals.dll` | 1.9.0 | GPL-3.0 | `github.com/redseiko/ComfyMods`, commit `a2b4680`, `BetterServerPortals/`; not on Thunderstore for 1.0 at the time of this kit. Built against publicized Valheim 1.0 client assemblies: publicize `assembly_valheim.dll`/`assembly_utils.dll` with Mono.Cecil (or BepInEx.AssemblyPublicizer), lay them out as `<G>/valheim_server_Data/Managed/publicized_assemblies/`, then `dotnet build -p:GamePath=<G>` |

BetterServerPortals is redistributed here under the GPL-3.0 with this notice and the exact
commit it was built from; the full source is at the repository above. ComfyCameraProof's
1.7.0 Thunderstore predecessor does not load a 1.0 world (`MissingFieldException` in
`ZDOMan.Load`); use the 1.9.0 build in this kit.

Verify before running:

    certutil -hashfile mods\ComfyCameraProof.dll SHA256
    certutil -hashfile mods\BetterServerPortals.dll SHA256

against `SHA256SUMS` beside this file.

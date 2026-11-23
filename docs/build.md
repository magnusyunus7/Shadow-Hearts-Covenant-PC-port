# Build notes (Windows, MSVC)

Tested on a Ryzen 7 5800H with 8 GB RAM and Visual Studio 2022 (Developer PowerShell).
Folder names follow the original setup (`C:\shc`); adjust as you like.

## 0. Prerequisites

* Python 3 with `pip install rabbitizer`
* Visual Studio 2022 with the C++ workload, CMake, and Git
* Your own dump of disc 1 (`SLUS_210.41`); check it against Redump

## 1. Extract the disc

Extract the ISO with 7-Zip to `C:\shc\extracted\disc1`.

## 2. Prepare ELFs

```powershell
cd C:\shc\work
python ..\repo\scripts\main2elf.py C:\shc\extracted\disc1\SLUS_210.41 MAIN.elf
foreach ($n in "OPENING","FIELD","BATTLE") {
  python ..\repo\scripts\ovl2elf.py C:\shc\extracted\disc1\$n.BIN $n.elf
}
```

The configs in `config/` already contain the constructor and overlay entry points
(`addctors.py` / `ovlentries.py` output). Rerun those scripts only if you regenerate the configs.

## 3. PS2Recomp with the patch

```powershell
git clone https://github.com/ran-j/PS2Recomp.git C:\shc\port
cd C:\shc\port
git checkout e563698
git apply ..\repo\patches\ps2recomp-e563698-shadow-hearts.patch
```

Configure and build the tools (`ps2_analyzer`, `ps2_recomp`).

## 4. Recompile

Edit `input`/`output` in each config to your paths, then:

```powershell
ps2_recomp config\main.toml                      # main executable  -> ps2xRuntime/src/runner
ps2_recomp config\main_overlay_entries.toml      # same + 231 extra entries -> separate folder
ps2_recomp config\overlays\OPENING.toml          # likewise FIELD, BATTLE
```

Put the main output (the `sub_*`/`entry_*` files, `register_functions.cpp` and the two headers) in
`ps2xRuntime/src/runner` and `ps2xRuntime/include` as PS2Recomp expects.

Overlay banks:

```powershell
python scripts\ovlbank.py out_OPENING OPENING C:\shc\extracted\disc1\OPENING.BIN C:\shc\port\ps2xRuntime\src\runner
python scripts\ovlbank.py out_FIELD   FIELD   C:\shc\extracted\disc1\FIELD.BIN   C:\shc\port\ps2xRuntime\src\runner
python scripts\ovlbank.py out_BATTLE  BATTLE  C:\shc\extracted\disc1\BATTLE.BIN  C:\shc\port\ps2xRuntime\src\runner
```

`ZMAIN` bank: from the extra-entries output, take only the function files that differ from the
main output. Put them in a folder together with `ps2_recompiled_functions.h` and a
`register_functions.cpp` filtered to those functions, then run:

```powershell
python scripts\ovlbank.py <that folder> ZMAIN - C:\shc\port\ps2xRuntime\src\runner
```

## 5. Build the runner

```powershell
cmake -S . -B out/dbg -G "Visual Studio 17 2022" -A x64 -DCMAKE_UNITY_BUILD=ON -DCMAKE_UNITY_BUILD_BATCH_SIZE=8
cmake --build out/dbg --config Debug -- /m:1
```

Use a Debug build: Release (`/fp:fast` + LTO) needed more than 8 GB and over 40 minutes to link.
The largest generated function is 6.4 MB; `scripts/deopt_huge.py` turns optimisation off for files
over 1 MB if you build optimised.

## 6. Run

```powershell
$env:PS2X_CD_IMAGE = "C:\shc\iso\Shadow Hearts - Covenant (USA) (Disc 1).iso"
$env:PS2X_SIFDIAG = "1"     # optional diagnostics
.\out\dbg\ps2xRuntime\Debug\ps2EntryRunner.exe C:\shc\extracted\disc1\SLUS_210.41 > run.log 2>&1
```

F1 toggles the debug panel.

Diagnostics: `PS2X_DUMPRAM=<file>` with `PS2X_DUMPTICK=<n>` writes the 32 MB EE RAM at tick n.
The dump contains game data, so never commit it.

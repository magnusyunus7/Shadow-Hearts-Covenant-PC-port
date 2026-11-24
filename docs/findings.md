# Findings

Facts below were checked against the disc, a disassembly or a running build unless marked
*(assumption)*. Addresses are for the USA release (`SLUS_210.41`).

## Executable layout

| Range | Content |
|---|---|
| `0x200000–0x416F80` | code (`.text`) |
| `0x416F80–0x437300` | data |
| `0x437300–0x437E80` | static-constructor code (34 constructors; table at `0x437E80`) |
| `0x437E80–0x43FC00` | data |
| `0x43FC00–0x45EA80` | bss |
| `0x429CE8` | kernel-patch island (touches `0x8007xxxx`), left as data on purpose |

`main2elf.py` re-sections the ELF this way. Without it the analyzer decodes data as code
(about 3,000 bogus errors). Three constructors (`0x437450`, `0x4376C0`, `0x437990`) are leaf functions that
get merged unless listed as entry points (`addctors.py`).

## Overlays (Metrowerks "MWo3")

* `FIELD.BIN` (id 1), `BATTLE.BIN` (id 2) and `OPENING.BIN` (id 3) all load at `0x45EA80`.
* 0x40-byte header: magic, id, load address, text size, data size, bss size, ctor start/end, name.
* **The whole file, header included, is loaded at the load address.** Code starts at `0x45EAC0`.
  (Verified by comparing OPENING.BIN with a RAM dump; the main code calls `0x45EB60` = file offset 0xE0.)
* BATTLE has 3 static constructors whose code sits inside the "data" part, between the first
  constructor and the constructor table (`0x6E7C80–0x6E83B0`).
* Loader: `mwOverlayInit` at `0x3C58B0`, called from `0x23A010`.
* The runtime picks the right recompiled overlay by reading the header (magic + id) in guest RAM
  (`ps2_overlay_banks.h`).
* 231 main-executable functions are called **only from overlays**, so the analyzer merged them into
  their predecessors. They are recompiled separately as the always-on `ZMAIN` bank
  (`config/main_extra_entries.txt`).

## Disc / file system

* `PKFINFO.TBL` + `*.PKB`: names are base-40 (alphabet `.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_`,
  decoder at `0x22A360`). Directory entries have bit 31 set in word 3, and offsets are ×16 relative to the parent.
  4,437 files + 42 directories; sizes validated.
* The game resolves files with `sceCdLayerSearchFile` (`0x215860`) and then reads raw sectors, so the
  runtime must return real ISO9660 LSNs (`PS2X_CD_IMAGE`).
* Streaming goes through Nautilus `FIO.IRX` on the IOP (command channel 1). The EE side queues
  requests at `0x44A428`, and the queue is serviced by the FIO task (vtable `0x437F78`, update `0x22AA10`).

## IOP / SIF

* `sceSifSendCmd` passes arguments 5 and 6 in `t0`/`t1` (EE EABI); the IOP side uses the stack (O32).
* Module lookup protocol (IOPUTY "sifc"): IOPUTY = cmd 0, FIO = 1, SDRV = 2.
* FIO.IRX needs `SetAlarm`/`iSetAlarm` (thbase 35–38) and `sceSifSetDmaIntr` (sifman 32).

## Recompilation gaps

* Small functions placed right after another function's `jr ra` (plus `nop` padding) and reached
  only through pointers get merged into the previous function, so they have no entry point
  (example: `0x24C930`, `0x24CFE0`). Scanning for non-entry code that follows a `jr ra` delay slot
  found 175 such addresses; all are entry points now.

## EE kernel behaviour the game depends on

* **Timer 3** must free-run at the H-blank rate. The game reads it in 18 places and never sets it up
  (the kernel normally does).
* **Timer 0** (INTC 9) drives the task system: the handler at `0x4080E0` walks timer lists
  (`0x43FE90/94/98`) and calls `iWakeupThread` for type-2 entries.
* **A thread switch must not happen in the middle of an interrupt handler.** The handler wakes a
  thread and *then* unlinks its timer node. Switching early let the thread re-arm the node, which
  the handler then deleted, leaving the thread asleep forever.
* `di`/`ei` critical sections (`0x213520`/`0x213568`) must be respected when delivering interrupts.

## Graphics

* `sceGsSetDefDispEnv` (`0x200508`) stores **PMODE = 0x66** and SMODE2 = 1/2/3 in the env. A stub
  that leaves them zero switches the display off (the pink screen).
* The game flips between framebuffers 0 and 140 (PSMCT24), 640×448. In-engine 3D scenes use
  512×448 buffers at FBP 0 and 112.
* 3D models go through VU1. The microprogram transforms vertices with the object matrix it loads from
  VU1 data rows 19–22 (projection in rows 14–17). The EE uploads the object matrix each frame with a
  DMA `REF` tag whose VIF code is `UNPACK V4-32, 4 qwords, row 19` (built at `0x257318`), from a
  double-buffered slot at object `+0xB0`/`+0xF0` selected by the frame-parity byte at `0x43FC30`.
* `0x24A530` computes that matrix as camera matrix (`*(gp-0x7B44)+0x280`) × bone matrix, with VU0
  macro instructions. Bone matrices are built by `0x240E80`, starting from an identity matrix made
  from `vf0` with `VMR32`. **VU0 `vf0` must read (0, 0, 0, 1) on every thread**; with zero the whole
  chain is zero and nothing is drawn.

## Movies

* libmpeg in "IPU ring" mode: callbacks registered at `0x3CD66C…`. Type 1 (`sceMpegCbNodata`,
  `0x3CCDD0`) sends up to 100 KB per call to DMA channel 4 (toIPU) with a single `refe` tag.
* The stream is raw MPEG-2 video (starts with `000001B3`), 640×448.

## Sound

* SDRV_IOP.IRX command handler `0xAE0`, timer callback `0x8DE4C`. EE sound interpreter `0x3B5130`.
* A timed wait in sound init (`0x3B5420`) polls Timer 3 (see above).

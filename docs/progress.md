# Progress log

## Milestone 1: first picture (2026-11-23)

Boot reaches the disclaimer screen and the title logo. Fixes, in the order they were needed:

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | ~3,000 analyzer errors | data decoded as code | `main2elf.py` re-sectioning |
| 2 | pink screen, stuck at `0x437300` | static constructors never run | `.text.init` section + `addctors.py` |
| 3 | stuck at `0x3B9000` | EE→IOP SIF commands not delivered; handler `gp` = 0 | SIF command path in runtime + IOP |
| 4 | IOPUTY lookup returned -1 | guest command table not written through | write-through in IOP RPC |
| 5 | "no configured CD image" | — | `PS2X_CD_IMAGE` |
| 6 | endless RPC bind | `sceCdLayerSearchFile` | game override |
| 7 | hang at `0x3ED5B0` | t0/t1 args, IOP alarms, real LSNs, `sceSifSetDmaIntr` | runtime + IOP |
| 8 | hang at `0x3B66F8` | Timer 3 not running | free-running Timer 3 |
| 9 | hang at `0x23ABB4` | thread switch inside the Timer 0 handler | defer preemption until handler returns |
| 10 | jump to `0x45EB60` | overlays not recompiled | overlay banks |
| 11 | jump to `0x2179B0` | main functions called only from overlays | `ZMAIN` bank |
| 12 | movie thread waits forever | `sceMpegCbNodata` never called; DMA ch4 ignored | IPU-ring feed to FFmpeg |
| 13 | livelock in Timer 0 handler | time-slice yield inside interrupt context | no yield while in a handler |
| 14 | — | interrupts delivered during `di` | gate interrupt delivery on Status.EIE |
| 15 | pink screen with rendering running | PMODE = 0 | correct `sceGsSetDefDispEnv` |

## Verified on Windows (run9, 2026-11-23)

* MSVC Debug build with the runtime patch and the ZMAIN bank boots on the playtester's machine and shows an image in place of the pink screen.
* PMODE=0x66 and SMODE2=1 are set. The game draws into two alternating buffers (FBP 0 and 140), and both memory-card ports return "no save directory" (-4) as expected for a fresh card.
* The frame rate is very low: about 2 `[frame:upload]` lines per 120 runtime ticks. The Debug build (`/Od`, runtime checks) is the main suspect. This has not been measured yet.

## Milestone 2: full speed into the first 3D scene (2026-11-24)

Release build on the playtester's machine: New Game, skip the movie, and the first in-engine 3D
room renders. Fixes, in the order they were needed:

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 16 | jump to `0x3DA1B0` after the movie skip | 12 more main functions reached only from overlays | added to the `ZMAIN` bank |
| 17 | Release build: `C1002` out of heap, then `C4653` | multi-MB generated functions in unity batches; PCH built with `/O2` | files over 1 MB build alone, `/Od /Ob0`, no PCH (`CMakeLists.txt`) |
| 18 | after New Game the game ran ~13x slower than on Linux | per-function trace log flushed two lines to disk on **every** recompiled call (97% of game-thread time, 3.3 GB log) | trace is opt-in: `PS2X_FNTRACE=1` |
| 19 | white screen after skipping the movie | function at `0x24C930` sits right after another one's `jr ra` + padding; the analyzer merged it, so it had no entry | entry added; a scan of the whole executable found **175** such spots, all added (`config/main_overlay_entries.toml`) |
| 20 | 3D scene black, game otherwise running | VU0 `vf0` was zero on every thread the game creates (`StartThread` reset the context to all zeros). Game code builds identity matrices from `vf0` with `VMR32`, so all bone matrices, and with them every model matrix, came out zero | `vf0` = (0, 0, 0, 1) for new threads (`EeScheduler.cpp`) |

How fix 20 was found (each step verified):

1. GS snapshot: both framebuffers fully black; only degenerate sprites drawn.
2. GIF capture: every VU1-generated vertex had XYZ = 0 and the ADC (no-draw) bit set; colours and
   texture coordinates were normal.
3. VU1 data memory: the object matrix (rows 19–22) was all zero; the projection rows were fine.
4. The EE uploads that matrix (`UNPACK V4-32`, 4 qwords, row 19) from a double-buffered slot in the
   model object; both copies were zero.
5. Host watchpoint on the object: `0x24A530` writes it every frame as camera × bone matrix; the
   camera matrix was fine, the bone matrices zero.
6. Watchpoint on a bone entry: `0x240E80` writes zeros; it starts from an identity matrix built
   from `vf0`, which was zero on that thread.

Also verified:

* Speed: Release build about 15–20 fps on the playtester's machine (Debug was ~1 fps).
* The black screen after New Game is a movie; START pauses it and **triangle** (V key) skips it.
* Rejected hypothesis: Windows timer granularity. Timed scheduler waits were not the bottleneck
  (the trace log was); the experiment was removed.

## Next

* Opening/story movies: frames decode but are not displayed.
* Title screen colours (white/yellow backgrounds, texture fragments).
* Check the 3D scene against real hardware (it looks dark), then walk around the first area.
* Controller test on the playtester's machine; audio output from SDRV.
* Performance: huge functions compiled `/Od`, unresolved jump tables.

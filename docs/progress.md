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

## Milestone 3: title menu and the first story cutscene (2026-11-25)

The title screen and its menu draw correctly, New Game reaches the first story cutscene, and its
room renders completely and stays on screen. Fixes, in the order they were found:

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 21 | movie pixels written over the second display buffer | `sceMpegGetPicture` wrote a whole frame regardless of the buffer size the game passed | write at most `mbCount` × 1024 bytes (`MPEG.cpp`) |
| 22 | jumps into the heap (`0x75F418`, `0x989730`) | a recursive function paused at its own self-call by a scheduler checkpoint was treated as finished, so the caller skipped ahead | only treat the call as finished if no checkpoint fired inside it (`ps2_runtime.cpp`) |
| 23 | 3D black again in some scenes | `vf0` was only fixed for new threads; interrupt handlers and other invocations still saw zero | `vf0` = (0, 0, 0, 1) before every dispatch (`EeScheduler.cpp`) |
| 24 | VU1 matrices overwritten | an `UNPACK` split across two DMA transfers was dropped and the rest of its data parsed as VIF codes | carry an incomplete VIF command into the next transfer (`ps2_vif1_interpreter.cpp`) |
| 25 | title menu missing, speckled textures | a GIF IMAGE transfer continued in the next `DIRECT` was resynchronised from raw VIF words | continue the image inside the next `DIRECT` payload |
| 26 | cutscene room blinking on and off; her hands missing | the DMA chain walker stopped after **4096 tags**; this room sends about 4100 per frame, so the tail (room objects and the final `STCYCL 1/1`) was dropped, which also scrambled the next frame's matrices | no practical limit (2^20, only a loop guard) (`ps2_memory.cpp`) |
| 27 | black diagonal over half the screen; broken subtitles | the game splits a GIF tag and its data across two `DIRECT` commands; the GS parser started afresh on each, so the fade sprite turned into a giant triangle | hold an unfinished PATH2 tag and join it with the next `DIRECT` |
| 28 | flicker on the black screen before the MIDWAY logo | upstream presenter showed the back buffer whenever the displayed one was all black | heuristic off by default (`PS2X_BLACK_FALLBACK=1` restores it) |

How fix 26 was found (each step from logs or snapshots):

1. Per-frame triangle counts: about 1,320 (character only) most of the time, about 2,200 for
   bursts of 10 frames every ~2 s.
2. Same VU1 program, same number of calls, same per-object parameter blocks, nearly the same VIF1
   byte count on good and bad frames: the game sent the room every frame.
3. A check for unexpected writes to the matrix rows found `UNPACK`s running with `CYCLE = 0103`
   (skipping write) where the game had set `0101`: the command resetting it had never arrived.
4. The per-frame DMA log stopped at exactly 4,101 segments: the 4,096-tag cap.

Also changed: the presenter reads the display registers and copies VRAM under the same lock, so a
flip cannot land between the two (`PS2X_PRESENT_LOCKED=0` for the old behaviour).

Rejected hypotheses (tested and reverted): the game drawing into the displayed buffer (swaps were
always correct), per-thread VU0 registers (sharing them changed nothing), the 65,536-cycle VU1
budget (never reached).

## Milestone 4: character animation in the first room (2026-11-27)

The Windows Release playtest reached the end of the room cutscene and continued after
skipping the following scene. The playtester reported better character models and
movement and did not notice the previous character flicker. Hair motion still looks wrong.

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 29 | Characters collapse or flicker in the first room | The packed animation decoder uses EE `PREVH`. The recompiler reversed all eight halfwords, which let stale upper-register data replace the packed footer. | Reverse the four halfwords in each 64-bit half independently in `mmi_translation_helpers.cpp`. |

A saved RAM capture showed a local bone translation near `(-24.64, -128.04, -228.38)` in a
bad sample. After the fix the watched samples stayed near the expected pose, around
`(-0.9, -3.8, -6.4)`, apart from explicit identity writes. The Release runner and
recompiler built successfully. A fresh recompile emitted the corrected instruction,
and an offline check passed 1,000 lane patterns plus a packed animation sample.

Before the animation fix, performance profiles measured about 5 frame uploads per second
in the heaviest room stretch and about 13 in lighter sections. VU1 dominated the slow
stretches. The source patch includes the VU1 scheduling and arithmetic optimizations used
in those runs.

## Milestone 5: story movies around the first room (2026-11-27)

Windows Release playback now works for the previously black movie before the room
and the “1915” movie afterward. The playtester continued beyond both scenes. The run
log recorded decoded 512×448 frames from both movie handles.

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 30 | Black movie before the first room and a stalled “1915” subtitle after it | `sceMpegCreate` left three status words in reused MPEG work RAM. A nonzero word at offset zero made guest `sceMpegIsEnd` report end-of-stream before the first picture. | Clear the guest status words when creating a movie. |

The Release build passed a regression check using the stale work-buffer values from
the capture. The issue and the fix were verified on the same Windows setup.

## Milestone 6: faster VU1 execution in a busy cutscene (2026-11-27)

As the camera tilted from the sky into the scenery, the matching busy stretch drew
about 8,500 primitives and ran about 1,130 VU1 programs per display flip. VU1
accounted for about 72% of game-thread samples during the slowdown.

The interpreter now reuses cached instruction pairs directly and selects the
retirement schedule once per program run. The same 96 captured VU1 programs
produced identical GIF packets and final state in replay. The median replay
time fell from 1.20 s to 1.09 s across eight paired measurements. All 40 VU1 tests
passed with the retirement optimization enabled and disabled.

In one matched Windows Release comparison, the median display upload rate rose
from 4.59 to 5.28 per second. The cutscene played through and the most demanding
section remains slow.

## Milestone 7: correct hair rotation in the first room (2026-11-27)

The hair pose routine computed its normalization input in $f3. The recompiler
translated the EE SQRT.S instruction using fs, so that instruction took the
root of $f0, which still held 1.0. SQRT.S reads ft on the EE. The translator
and the four affected runner files were corrected.

An offline replay rebuilt the pose from each of three captures. The old code
stretched a hair bone axis to 2.40 times its unit length in the worst capture.
After the fix, the tested axes were within 0.02% of unit length in all three
captures. All eight floating-point tests passed, and the Windows Release
playtester confirmed that the hair looks right in the room cutscene.

## Next

* Play past the camera pan into the first controllable area and verify the first battle.
* Improve performance in busy scenes. Use the captured camera pan to check further
  changes to VU1 instruction execution.
* Check the delay before the title screen accepts input.
* Verify audio beyond the narration, controller input, and memory-card use.
* Address remaining oversized generated functions and unresolved jump tables.

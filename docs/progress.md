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

## Next

* Confirm the opening movie frames reach the screen.
* Controller input (PADMAN/SIO2MAN path).
* Audio output from SDRV.
* Performance (Release build, huge functions with unresolved jump tables).

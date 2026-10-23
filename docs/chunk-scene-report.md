# P4a: separately authored 256px scene

2026-10-23 · [Detailed Chinese report](chunk-scene-report.zh-CN.md) · [Run/rebuild](../demos/chunk-scene/README.md) · [Measurements](measurements/chunk-scene.json).

Four independently runnable 128px local drawing files form the Canalworks crossing. Contract commit `7506d55` precedes the art and freezes the palette, light, ownership, canal/bridge dimensions and global material phase. Each file receives the contract, not finished artwork. Shared helpers create local patterns/props, never a complete scene. This is one author's separate chunks, not multiple independent agents or blind review.

![Native 256px scene at nearest-neighbor 2×](../demos/chunk-scene/assets/preview.png)

The existing assembler covers all 65,536 pixels with exact copy placement, no gaps/overlaps and four seams. File-based assembly exactly matches the builder, including reversed order. Isolated sources containing only one chunk, the helper, contract and runtime reproduce each first PNG exactly. No whole-scene crop or post-assembly retouch supplies the art; cropped outputs are review views.

Actual native, 2×, grayscale, eight coordinate-labeled seam views and the center junction were reviewed. Water/bridge/plank/slab phase continues across both boundaries; north/south rails leave the east/west deck clear. 1,140 pixel assertions check material roles and fixed anchors, including repeat checks; they are not an aesthetic coverage score. A first checker falsely rejected six valid water highlights; its overly strict condition was corrected without changing the art/contract. No critical visual break required repainting, so visual revision rounds are zero.

A depot-flag variant changes exactly 84 pixels inside global `[210,11,16,9]`, zero outside; the other three PNGs retain byte hashes. Its JSON rerenders exactly and a parameterized full build matches the independent edit/reassembly. The command rehearsal uses Unicode/space paths: 14 commands, zero unexpected failures, three expected refusals (overwrite, injected pixel shift, invalid ownership placement). An additional same-palette slab-phase error is caught by a test.

Local portable checks pass 94 source tests, 43 stable images, fixture/study integrity, 77 isolated ZIP cases and reproducible packaging. Five new tests check local isolation, ownership/contracts, drift, scoped edits and output/error behavior; they were rerun after the final batch flag option. Frozen Skill bytes are unchanged at 222,984 bytes/91 files, SHA-256 `b680e73c966eb6557ed94bfc2e843dd4fca2c74c8aaf5f279caa2eeece6f308d`. No official-validator rerun is needed for the identical P2-validated package. Core APIs, mod resources, published rc.2, sealed rc.3 and installed stable v1.1.1 are retained.

This controlled layout does not establish complex terrain/large cross-chunk buildings, multi-model style convergence, navigation/collision, game acceptance, general aesthetic gains or native 512px capability. Source bytes and scripted command time are not measured creative time or model tokens.

The plan has four main stages: P1 external follow-ups remain pending; P2/P3 are complete; the current checkpoint is P4a 256px. Next is P4b's native-512 usefulness/requirements gate. Only proceed when a larger original scene adds practical value; otherwise consolidate the proven workflows into the next candidate and apply the existing external/stable release gate. Do not call a 256px upscale a native-512 result.

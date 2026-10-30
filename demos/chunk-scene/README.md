# Independently authored 256px chunk example

Four separate 128×128 drawings form the Canalworks crossing. This is one author using a frozen shared palette, lighting and edge contract, **not** independent agents or blind aesthetic review. No finished scene is supplied to a chunk, no complete background is rendered and cut into tiles, and no painting occurs after assembly. Crops in the output are review views only.

From a checkout with the repository Python/Pillow requirements:

```sh
python tools/build_chunk_scene.py --out-dir output/canal
python tools/build_chunk_scene.py --check-chunks output/canal/chunks
python src/pixel_art.py assemble --project output/canal/project.json --out output/canal-file-assembly.png --report output/canal-file-assembly.json
```

The builder refreshes PNG/spec/layout/manifest together. Existing outputs require explicit `--force`. It re-renders all four small chunks for convenience; it does not claim incremental caching. For a color variant, use `--out-dir output/canal-blue --flag 73A5AA`. The manifest records that parameter. Each chunk also runs by itself, from any working directory, without the other three sources or finished PNGs:

```sh
python demos/chunk-scene/chunk_ne.py --out-dir output/one-chunk --flag 73A5AA
```

Keep changed chunks in a separate candidate project, then reassemble and run `verify`. A manual change to a PNG/spec does not update an old full-build manifest; regenerate it or keep the edited project separate. The documented flag trial changes 84 pixels inside global `[210,11,16,9]` and zero elsewhere. The source and artifact mapping is:

| Source | Owned global rectangle | Content |
|---|---|---|
| `chunk_nw.py` | 0,0,128,128 | Workshop, pump, left upper bridge/water |
| `chunk_ne.py` | 128,0,128,128 | Depot, boat, right upper bridge/water |
| `chunk_sw.py` | 0,128,128,128 | Timber yard, left lower bridge/water |
| `chunk_se.py` | 128,128,128,128 | Warehouse, crane, right lower bridge/water |

`contract.json` was frozen before drawing. `chunk_common.py` provides local primitives, repeating material patterns and small props; it never returns a full scene. Each `chunks/name.json` is independently renderable JSON v1, with its PNG and layout. `project.json` uses exact non-overlapping `copy` placements. `manifest.json` records source/contract/artifact hashes.

The 40px canal and 56×32 bridge cross the center. The 24px deck connects the two paved approaches; rails are north/south. Stone slabs and planks use shared pattern origins, so the textures line up across chunk boundaries. `edges.json` checks material roles and frozen anchors, `assembly.json` checks geometry. These do not establish semantic or aesthetic quality; inspect `scene.png`, `preview.png`, `grayscale.png`, `seams.png` and `center.png` yourself.

[Direction and acceptance brief (Chinese)](BRIEF.zh-CN.md) · [Detailed results](../../docs/chunk-scene-report.zh-CN.md) · [English results](../../docs/chunk-scene-report.md).

This repository example uses the existing Python/Pillow tools; it is not included in the standalone Skill ZIP. Its checks cover offline assembly and seams. Test game integration, collision/navigation and larger or multi-agent projects separately. Code/art are MIT.

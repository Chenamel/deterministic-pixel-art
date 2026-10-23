# Separately drawn chunks

Use for artwork too awkward to edit as one object. First choose native logical size from the actual display and required forms; splitting is an editing technique, not evidence that a larger canvas improves quality. A larger asset needs new native detail, not an enlarged smaller PNG.

## Agree before drawing

Record canvas size, each owned `[x,y,width,height]`, palette roles, light direction, pixel scale and the shapes crossing each boundary. Use exclusive right/bottom bounds. Give every final pixel one owner. If working with context padding, record its crop explicitly in the assembly project.

Define connectors in global coordinates: road/water widths, contour crossings, wall height, rail positions and texture origin/period. Local drawing uses `global = owner origin + local`; repeating a texture from zero in every block introduces phase jumps when block width is not a multiple of its period. Shared helpers should draw primitives/materials, not conceal a finished whole scene that is later cut apart.

Choose boundaries that leave manageable work, while keeping a global composition sketch. Avoid separately outlining both sides of a shared object. Each source produces its own editable spec and PNG before assembly. Name blocks and freeze the agreement before expanding details; a contract change must reach all affected sources.

## Runnable small example

```text
python <skill>/scripts/recipes/chunk_pair.py --out-dir baseline
python <skill>/scripts/recipes/chunk_pair.py --out-dir candidate --flag 73A5AA
python <skill>/scripts/pixel_art.py verify --image candidate/asset.png --compare baseline/asset.png --allow-region 51 5 6 4
```

This original 64x32 bridge has two separately drawn 32x32 owners. `chunk_left.py` and `chunk_right.py` read only their local drawing and shared `_chunk_contract.py`/`_common.py`; neither reads the other source or a completed image. The six-pixel plank period intentionally does not divide the block width. `chunk_pair.py` assembles only after both PNGs exist in memory; it does not retouch the merge.

Outputs include local JSON/PNG/layout/preview, `contract.json`, `project.json`, merged PNG/layout/preview, assembly facts and a seam view. The top-level PNG is assembled; there is no top-level editable spec. Edit the short owner source or its local JSON. When copying these recipes, keep their shared helpers and the Skill runtime available as described in [recipes.md](recipes.md).

To rebuild only one owner in an existing **candidate**, explicitly replace its outputs, then create a fresh merged image:

```text
python <skill>/scripts/recipes/chunk_right.py --out-dir candidate/right --flag C47763 --force
python <skill>/scripts/pixel_art.py assemble --project candidate/project.json --out candidate/reassembled.png --report candidate/reassembled-report.json --seams candidate/reassembled-seams.png
python <skill>/scripts/pixel_art.py verify --image candidate/reassembled.png --compare baseline/asset.png --allow-region 51 5 6 4
```

`candidate/asset.png`, its preview and `layout.json` remain the previous merge: do not present them as refreshed. Use the new `reassembled*` outputs; `inspect`/`review` can read this non-atlas PNG without metadata. A fresh complete `chunk_pair.py` build refreshes all outputs together. Never reuse a content-bound sidecar from an older image.

## Check geometry, then meaning

`assemble` checks bounds, intended overlap and required rectangular coverage. `copy` preserves raw RGBA; `over` composites intentionally layered components. Neither proves contour, material, lighting or navigation continuity. See [workflows.md](workflows.md) for crops and output limits.

View the whole composition at 1:1, integer enlargement and grayscale, then labeled seam strips and junctions. Some seam sheets omit segments: inspect all critical undisplayed crossings separately. Check path width, silhouette, material phase, shadows and repeated borders. A valid seam can change color; forcing equal adjacent pixels is not a continuity test. Use independent coordinate anchors for declared crossings, rather than checking a pattern by calling its own generator.

After a small edit, retain untouched owner PNGs and verify the assembled allowed-change region or mask, including hidden RGBA. At most two targeted seam corrections normally suffice; retain unresolved candidates and the exact remaining issue instead of scaling up. This example teaches the workflow; it is not an independent-agent test, a general visual-quality score or native512 validation.

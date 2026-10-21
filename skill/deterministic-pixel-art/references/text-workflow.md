# Text-only inspection and exact PNG editing

Use this when images cannot be viewed or an existing PNG needs a precise edit.
Statistics expose pixels; they do not identify objects or judge beauty. Preserve
the brief and use visual review when available.

## Short path

```text
python <skill>/scripts/pixel_art.py inspect --image icon.png --grid
python <skill>/scripts/pixel_art.py import --image icon.png --out editable.json
python <skill>/scripts/pixel_art.py render --spec editable.json --out candidate.png
python <skill>/scripts/pixel_art.py inspect --image candidate.png --compare icon.png --grid
```

Edit the generated grid/rectangles between import and render. For a small change,
read only the relevant region and check its neighbors; no mandatory silhouettes,
context file or full contact sheet is needed. Output to a separate candidate.

For larger images, use `--region X Y W H`; for named atlases, use `--metadata
layout.json --cell NAME`. `--region` and `--cell` are mutually exclusive. A grid
requires at most 64×64 pixels and 62 exact colors. It is never silently reduced.
`--out report.json` saves the bounded report instead of printing it; overwriting
requires `--force`. `--compare previous.png` requires equal source dimensions.

## Interpret the report

All new analysis rectangles are global `[x,y,width,height]`. Grid row/column
indices are local to `grid.origin`. A centroid averages visible pixel centers
`(x+.5,y+.5)`; it is not optical weight. Empty foreground has null bbox, margins
and centroid. Margins describe the selected scope.

Geometry uses alpha > 0. Opaque panels therefore occupy the whole canvas unless
the user explicitly supplies `{"analysis":{"exclude_colors":["C6C6C6"]}}` in
context. Exclusions match exact RGBA and affect foreground statistics only;
they do not remove source pixels or alter raw alpha facts.

`facts` includes occupancy, bbox, margins, centroid, visible-color frequencies,
alpha histogram and partial-alpha coordinates, mirror differences, 4/8-neighbor
components, and exact/visible hashes. X symmetry compares left/right pairs; Y
compares top/bottom. Each mirrored pair is counted once; an odd center line is
excluded. Silhouette and color differences are separate: asymmetric lighting
does not necessarily imply an asymmetric shape.

Default caps: 32 color entries, 16 largest components for each neighborhood,
64 partial-alpha coordinates. Full counts and omitted counts remain available.
Cells have their own global-coordinate facts; use `--cell` to avoid reading all
cells. Colors sort by frequency then RGBA; component ties sort by bounding box.
Alpha facts include all scope pixels even when a foreground color is excluded.

Comparison separates raw RGBA changes from visible changes. RGB under alpha=0
is ignored only by the visible comparison/hash. Existing `review.comparison.bbox`
retains its legacy `[left,top,right,bottom]` convention; new analysis uses xywh.
Neither changed pixels nor a clean report prove the candidate is better.

## Exact import boundaries

`import --image input.png --out editable.json [--region X Y W H]` accepts static
PNG with at most 8-bit channels, including indexed transparency. The API
`image_to_spec(image, region=None)` operates on already-decoded 8-bit Pillow
images, not original PNG encoding. Animation and high-bit-depth modes are rejected.

Up to 62 RGBA values produce a sorted palette and grid. More colors produce
horizontal exact-color rect runs in JSON v1. There is no quantization, smoothing,
layer reconstruction or inferred object naming. Hidden RGB under zero alpha is
preserved. The specification is limited to 4 MiB; crop an individual asset when
the complete image would exceed that limit. Pixel equality means decoded RGBA,
not original PNG bytes, color profiles, palette indices or original layer structure.

## Reuse layout

`render --metadata layout.json` retains the existing size/mode/atlas fields and
adds `version:1` and `rgba_sha256`. Review/inspect accept that file directly.
`render --embed-metadata` optionally embeds the same deterministic record in
`pixelart:layout`; PNGs without the flag retain the existing encoding behavior.
No complete spec, timestamp or machine path is embedded.

Embedded, sidecar and context layouts must agree. Pixel digests include dimensions
and all decoded RGBA, including hidden RGB; stale records are rejected. Legacy
sidecars are accepted and listed as unverified. A digest cannot prove a cell named
"hover" actually depicts the intended hover state. Keep the editable spec and
consumer's state contract separately; imported pixels do not recover them.

Python APIs: `inspect_image(image, context=None, *, region=None, cell=None,
grid=False, comparison=None, metadata=None)` and `image_to_spec(image, *,
region=None)` return JSON-serializable mappings and perform no file writes.

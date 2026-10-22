# Exact edits and larger component projects

Read only the needed section. Inherit accepted style, dimensions and names. Coordinates/extents are integer `[x,y,width,height]` with exclusive right/bottom bounds.

## Named PNG editing

```text
python <skill>/scripts/pixel_art.py import --image atlas.png --metadata layout.json --out editable.json
python <skill>/scripts/pixel_art.py replace-cell --spec editable.json --cell transfer --replacement transfer.json --out candidate.json --image-out candidate.png --metadata candidate-layout.json
python <skill>/scripts/pixel_art.py verify --image candidate.png --compare atlas.png --allow-region 32 0 16 16
```

The replacement is a grid/draw spec with the original cell size. Import with current metadata checks dimensions and the image digest, retaining names, order, positions, rows and unused pixels. Legacy layouts without a digest provide structural checks only; they cannot verify content association or state-name meaning. `--region` and named metadata import are mutually exclusive. Without metadata, import keeps its flat grid/row-run behavior. Layers/original objects are not reconstructed. Keep fresh metadata; never delete the digest to reuse a stale layout.

Imported atlases explicitly use `assembly:"copy"` to preserve partial alpha and hidden RGB. Old atlas/blit defaults stay source-over. Optional `cells[].at`, `rows` and a `base` preserve sparse layouts. Do not switch assembly mode merely to hide a mismatch. The combined imported spec has the existing 4 MiB limit.

Try `assets/workflows/atlas-before.png`, `atlas-before-layout.json` and `atlas-replacement.json`; transfer occupies `[32,0,16,16]`. `atlas-final.json` independently rerenders the result. Directly edit the selected grid when simpler than a replacement file.

## Prove a precise edit boundary

`verify` compares all decoded RGBA, including RGB under alpha zero. Repeat `--allow-region X Y W H` for multiple rectangles. `--allow-mask allowed.png` accepts nonzero L/1 intensity or RGBA/LA alpha; RGB-only masks are rejected. Regions/mask combine by union. Mask size must match. A hollow border needs a hollow mask, not its enclosing rectangle.

Exit codes: 0 valid boundary; 1 outside changes; 2 input/output error. `--out verification.json` saves counts, outside xywh bbox, up to 64 coordinates and omitted count. This does not judge appearance or state meaning. `validate` still checks image contracts.

## Native artwork and assembly

Start with overall composition, silhouette, palette, lighting and pixel scale. Split UI by components and scenes by objects/layers; sprites share a complete silhouette before local detail. Enlarging a smaller PNG does not establish native detail. `assets/workflows/sprite-128.json` is an original native 128x128 asymmetric courier.

Assembly uses a separate PNG project. JSON v1 rendering stays embedded data without file includes:

```json
{
  "version":1, "size":[256,256], "require_coverage":true,
  "parts":[
    {"name":"nw", "image":"tiles/nw.png", "at":[0,0], "mode":"copy"},
    {"name":"ne", "image":"tiles/ne.png", "at":[128,0], "mode":"copy"},
    {"name":"sw", "image":"tiles/sw.png", "at":[0,128], "mode":"copy"},
    {"name":"se", "image":"tiles/se.png", "at":[128,128], "mode":"copy"}
  ]
}
```

```text
python <skill>/scripts/pixel_art.py assemble --project <skill>/assets/workflows/scene-tiles.json --out scene.png --report assembly.json --seams seams.png --preview scene-2x.png
```

`scene-components.json` assembles editable terrain, mill, bridge and decoration PNGs. Matching component JSON remains editable: rerender changed components before assembling. `scene-control.json` is the whole-scene embedded-spec control. `scene-tiles.json` is a crop/reassemble control, not evidence that independent agents painted seamless chunks.

Each part declares `mode:"copy"` (raw RGBA replacement) or `"over"` (source-over once). Later layers explicitly set `allow_overlap:true` when intended. `crop:[x,y,w,h]` selects the owned interior of a context-padded source. Placement is never resized/clipped; padding is not silently discarded.

PNG paths are relative to the project directory and must stay within it after symlink resolution. Sources are static at-most-8-bit PNGs. Limits: 256 parts, existing canvas limits, 67,108,864 decoded source pixels. `require_coverage:true` checks rectangular coverage, including transparent pixels. Missing sources, invalid crops, undeclared overlaps, out-of-bounds placement and required gaps fail before writing.

Reports retain up to 256 adjacent-edge crops plus omitted counts. `--seams` displays up to 32 labeled 64px segments at nearest 4x, with omitted counts. Inspect undisplayed critical seams separately. Adjacent colors need not match: connectors, contours, lighting and material continuity need contextual visual review. Give each final tile pixel one owner to avoid repeated outlines/alpha.

Python `assemble(project,sources)` takes a filename-to-Pillow-image mapping and returns `(image,report)` without I/O. `replace_cell(spec,name,replacement)` and `verify_edit(image,comparison,regions=None,mask=None)` also perform no writes.

## Environment and output recovery

Use compatible installed Pillow when offline. Exact reproduction pins Pillow 12.3.0; supported 10.4–12.x can fill some polygons differently. Record the actual version. Frozen imported grid/row-run specs retain accepted pixels; keep editable geometry too.

Prefer a task-local venv. If the mount rejects venv symlinks, create it on a local temporary filesystem, or run `python -m pip install --target ./deps -r <skill>/requirements.txt` in a fresh task-local directory and add that directory to the task process's `PYTHONPATH`. Confirm `PIL.__version__` and `PIL.__file__` with the actual CLI interpreter; do not replace global packages.

Default publication stages artifacts and uses exclusive hard links for new targets. If rejected, choose a local output directory or explicitly use `--portable-output`. This exclusively creates NEW files, which readers may observe while writing. Existing outputs still require `--force`; forced writes use the existing atomic replacement path. Cooperating writers reserve outputs; ordinary errors attempt rollback and report remaining outputs/errors. No mode promises a crash-safe multi-file transaction.

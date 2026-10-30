# Exact edits and larger component projects

Read only the needed section. Inherit accepted style, dimensions and names. Coordinates/extents are integer `[x,y,width,height]` with exclusive right/bottom bounds.

## Named PNG editing

```text
python <skill>/scripts/pixel_art.py import --image atlas.png --metadata layout.json --out editable.json
python <skill>/scripts/pixel_art.py import --image atlas.png --metadata layout.json --cell transfer --out transfer.json
python <skill>/scripts/pixel_art.py replace-cell --spec editable.json --cell transfer --replacement transfer.json --out candidate.json --image-out candidate.png --metadata candidate-layout.json
python <skill>/scripts/pixel_art.py verify --image candidate.png --compare atlas.png --allow-region 32 0 16 16
```

Edit `transfer.json` between import and replacement. `import --cell` exports only that cell as a grid/draw spec at local origin `[0,0]`; it validates the full source layout/digest first. Sidecar, embedded or in-memory named layouts are accepted; absent or unknown names fail. `--region` and `--cell` are mutually exclusive. The replacement has the original cell size, with exact RGBA including hidden RGB.

Import with current metadata and no `--cell` retains the complete atlas: names, order, positions, rows and unused pixels. Legacy layouts without a digest provide structural checks only; they cannot verify content association or state-name meaning. `--region` and named metadata import remain mutually exclusive. Without metadata or `--cell`, import keeps its flat grid/row-run behavior. Layers/original objects are not reconstructed. Keep fresh metadata; never delete the digest to reuse a stale layout.

Imported atlases explicitly use `assembly:"copy"` to preserve partial alpha and hidden RGB. Old atlas/blit defaults stay source-over. Optional `cells[].at`, `rows` and a `base` preserve sparse layouts. Do not switch assembly mode merely to hide a mismatch. The combined imported spec has the existing 4 MiB limit.

Try `assets/workflows/atlas-before.png`, `atlas-before-layout.json` and `atlas-replacement.json`; transfer occupies `[32,0,16,16]`. `atlas-final.json` independently rerenders the result. Directly edit the selected grid when simpler than a replacement file.

`replace-cell --image-out ... --metadata ...` writes the complete atlas block and a fresh `rgba_sha256`. A standalone cell render correctly has no atlas block; that does not describe the metadata produced by atlas replacement. No manual sidecar construction is needed.

## Candidates without overwriting evidence

When exploring variants, give each a directory such as `candidates/v01/` containing its spec, PNG, fresh layout and optional review. Use `v02/` for another candidate; keep paths meaningful rather than repeatedly occupying a shared `final.*`. After selecting a result, write the delivery paths. This is a useful convention, not a requirement to produce alternatives for every small edit.

A later revision can use another candidate directory, or an explicit `--force` rebuild when replacement is authorized. If the task requires revision history, preserve each reviewed version's spec, PNG, fresh layout and generator source together before a rebuild; editing one shared generator later does not retain its earlier source. Deleting occupied outputs to render again loses the same evidence as replacing them. A refusal is not a reason to add `--force` automatically. Do not select a visually weaker version just because it was written to a path called `final`. The renderer does not track revision history or mark a version as approved based on its filename.

## Prove a precise edit boundary

`verify` compares all decoded RGBA, including RGB under alpha zero. Repeat `--allow-region X Y W H` for multiple rectangles. `--allow-mask allowed.png` accepts nonzero L/1 intensity or RGBA/LA alpha; RGB-only masks are rejected. Regions/mask combine by union. Mask size must match. A hollow border needs a hollow mask, not its enclosing rectangle.

Exit codes: 0 valid boundary; 1 outside changes; 2 input/output error. `--out verification.json` saves counts, outside xywh bbox, up to 64 coordinates and omitted count. This does not judge appearance or state meaning. `validate` checks the image against its specified rules.

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

`scene-components.json` assembles editable terrain, mill, bridge and decoration PNGs. Matching component JSON remains editable: rerender changed components before assembling. `scene-control.json` is the whole-scene embedded-spec control. `scene-tiles.json` is a crop/reassemble control, not evidence that independent agents painted seamless chunks. For separately drawn chunks with repeating textures aligned across their seams, use [chunking.md](chunking.md) and its small executable recipe.

Each part declares `mode:"copy"` (raw RGBA replacement) or `"over"` (source-over once). Later layers explicitly set `allow_overlap:true` when intended. `crop:[x,y,w,h]` selects the owned interior of a context-padded source. Placement is never resized/clipped; padding is not silently discarded.

PNG paths are relative to the project directory and must stay within it after symlink resolution. Sources are static at-most-8-bit PNGs. Limits: 256 parts, existing canvas limits, 67,108,864 decoded source pixels. `require_coverage:true` checks rectangular coverage, including transparent pixels. Missing sources, invalid crops, undeclared overlaps, out-of-bounds placement and required gaps fail before writing.

Reports retain up to 256 adjacent-edge crops plus omitted counts. `--seams` displays up to 32 labeled 64px segments at nearest 4x, with omitted counts. Inspect undisplayed critical seams separately. Adjacent colors need not match: connectors, contours, lighting and material continuity need contextual visual review. Give each final tile pixel one owner to avoid repeated outlines/alpha.

Python `assemble(project,sources)` takes a filename-to-Pillow-image mapping and returns `(image,report)` without I/O. `replace_cell(spec,name,replacement)` and `verify_edit(image,comparison,regions=None,mask=None)` also perform no writes.

## Environment and output recovery

Use compatible installed Pillow when offline. Exact reproduction pins Pillow 12.3.0; supported 10.4–12.x can fill some polygons differently. Record the actual version. Frozen imported grid/row-run specs retain accepted pixels; keep editable geometry too.

Prefer a task-local venv. If the mount rejects venv symlinks, create the venv on a local temporary filesystem and keep the task files at their original location. If `venv` fails because `ensurepip` is missing, an existing pip 22.3+ can install into a pip-free venv. On Linux/macOS:

```sh
pixel_env="$(mktemp -d)"
python3 -m venv --without-pip "$pixel_env"
python3 -m pip --python "$pixel_env/bin/python" install -r "<skill>/requirements.txt"
"$pixel_env/bin/python" -c "import sys, PIL; print(sys.executable, PIL.__version__, PIL.__file__)"
```

Use that venv's Python for every tool command; activation is optional. If no usable pip or compatible installed interpreter is available, report the missing prerequisite. Do not replace global packages. A fresh task-local `pip install --target ./deps` plus process-local `PYTHONPATH` is another option when venv creation is unavailable.

By default, the tool prepares temporary files, then saves new outputs using hard links. If the filesystem rejects hard links, choose a local output directory or use `--portable-output`. Portable mode still refuses to overwrite an existing file, but another program may read a new file before writing has finished. With explicit `--force`, the tool prepares each replacement before swapping it into place. Lock files prevent simultaneous tool processes from writing to the same paths. On ordinary write errors, the tool attempts to restore earlier files and reports what remains. In any mode, a crash or power loss can leave only some files updated; check all outputs after an interruption.

For repeated commands in one task, choose portable output once in the shell that launches them:

```sh
export PIXELART_PORTABLE_OUTPUT=1
# Run pixel_art.py or scripts/recipes/*.py normally; child processes inherit this choice.
# Later: unset PIXELART_PORTABLE_OUTPUT
```

PowerShell: `$env:PIXELART_PORTABLE_OUTPUT = '1'`; later remove it with `Remove-Item Env:PIXELART_PORTABLE_OUTPUT`. Separate agent shell sessions may need the same process environment supplied by their launcher. This is not a saved project/global setting. Per-command `--portable-output` or `--no-portable-output` overrides the environment; unset or `0` keeps the default, other values are errors before writing. Read-only commands and Python `publish(..., portable=False)` do not consult this setting. Output visibility and overwrite rules are unchanged.

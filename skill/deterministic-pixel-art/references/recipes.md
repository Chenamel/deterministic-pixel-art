# Python recipes

Run a shipped recipe by absolute path with the same task-local Python/Pillow environment as `pixel_art.py`; no repository checkout is needed.

## Paged atlas review

View every named cell in a large atlas at native size:

```text
python "<skill>/scripts/recipes/review_atlas.py" --image atlas.png --metadata layout.json --out-dir atlas-review
```

Open `atlas-review/index.json`, then **every page it lists at 1:1**. Each block
appears on dark (left) and light (right) backgrounds. Captions show cell/block
IDs and global `[x,y,width,height]`; the index preserves full cell names, original
order, page mappings, source hashes and exact sheet rectangles. The input stays
unchanged. Missing or stale content-bound layouts are rejected; `--metadata` can
be omitted when the PNG has matching embedded layout metadata.

The default is at most 64 native blocks per page; `--blocks-per-page 1` through
`64` can reduce the number. A cell larger than 128×128 is split into blocks and
may span pages. Every declared cell pixel is represented without downsampling;
unnamed positions in a sparse grid are outside this coverage. This recipe makes
coverage sheets; use `review` separately for its contextual warnings, grayscale,
silhouettes and baseline differences. It does not judge artwork quality.

Use a **new output directory for each revision**. Existing directories and
`--force` are refused so old pages cannot be mistaken for a new complete result.
An ordinary publication failure attempts rollback; an interrupted process or a
cleanup failure can leave an incomplete directory. Check the complete index,
listed files and their hashes before treating a delivery as complete. Never
recursively delete a recovery directory without inspecting it.

Limits: one single-frame PNG with at most 8-bit channels, 8192 per side and
16,777,216 source pixels; 4096 declared cells/128×128 blocks, 64 pages, 4,194,304
pixels per page, 67,108,864 total page pixels and 32 MiB encoded delivery. PNG
input is at most 80 MiB, sidecar at most 1 MiB (embedded metadata keeps the runtime's
256 KiB limit). Over-budget inputs fail before publishing; split the atlas or
increase `--blocks-per-page` up to 64 when the page count is the obstacle. Pages
are rendered and encoded one at a time; these limits are not a process peak-RAM
guarantee. Existing whole-atlas commands retain their 256-cell limit.

## Single-tile repeat preview

See how one PNG looks when repeated. Choose `--axis x` for left/right (3×1), `y` for up/down (1×3), or `xy` for both (3×3):

```text
python "<skill>/scripts/recipes/tile_preview.py" --image tile.png --axis xy --out-dir candidate
```

Open `candidate/preview.png` for the overall repeat, then `seams.png` for close-ups. `repeated.png` is the unmarked native-size result; `source.png` preserves your input. Check the source and repeat at native size before accepting continuity. This helper does not certify or repair seamlessness.

### Options and project files

- Preview: `--scale 4` is the default integer enlargement; `--background` accepts `checker` or `RRGGBB[AA]`. Backgrounds and diagnostic labels do not change `repeated.png`.
- Input and limits: one single-frame PNG with at most 8-bit channels. Source, repeat and enlarged preview each have limits of 8192 per side and 16,777,216 pixels. An oversized preview reports a usable `--scale`; an oversized source or repeat needs a smaller crop. Nothing is silently resized. For an atlas, first export the desired cell with `import --cell` and `render`.
- Reuse: `source.png` keeps the original file bytes. The repeat copies full RGBA, including semitransparent pixels and RGB under transparency. Move `source.png` and `project.json` together to reassemble:

```text
python "<skill>/scripts/pixel_art.py" assemble --project candidate/project.json --out rebuilt.png
```

`report.json` records source hashes, dimensions, placements and seam coordinates. Its `assembly.valid` confirms geometric coverage. Close-ups are bounded: check `assembly.omitted_seam_views` and inspect the full repeat when views are omitted. Judge continuity and repetition rhythm only along the declared axes.

## Named tile scene

Arrange different named tiles from one atlas into a small scene:

```text
python "<skill>/scripts/recipes/tile_scene.py" --image atlas.png --metadata atlas-layout.json --layout map.json --out-dir scene-v1
```

Open `scene-v1/preview.png` for context, `scene.png` at native size, then
`seams.png` for close-ups. `report.json` maps every placement and adjacency to
tile names and global rectangles. The model can translate a request such as
“put a path through the grass and turn it right” into the layout; the user need
not write JSON. Confirm the picture follows the intended path and tile meanings.

For example, `map.json` can contain the following **when these exact names exist
in the atlas**; each row runs left to right, with the first row at the top:

```json
{"version":1,"rows":[["grass","path-ns","grass"],["grass","turn-ne","path-ew"],["grass","grass","grass"]]}
```

Names are exact, case-sensitive strings; repeated names reuse the same source
tile. The atlas must have matching content-bound layout metadata. `--metadata`
is optional with matching embedded metadata. Empty/ragged rows, unknown names,
stale/conflicting layouts and invalid source cells fail before publishing.
Tiles use the atlas's fixed cell size; nothing is rotated or resized. This is
explicit placement, without automatic terrain selection or transition repair.

The directory contains the original-byte `atlas.png`, complete matching
`atlas-layout.json`, name `layout.json`, native `scene.png`, integer `preview.png`,
`seams.png`, relative-path `project.json` and `report.json`. Keep them together.
To rebuild after moving the directory:

```text
python "<skill>/scripts/pixel_art.py" assemble --project scene-v1/project.json --out rebuilt.png
```

To change a tile, follow [named PNG editing](workflows.md#named-png-editing):
import the atlas, edit/replace the named cell, and render a new atlas PNG with
fresh metadata. Run `tile_scene.py` on that new pair with the same `layout.json`
and a **new output directory**. All references to that name then use its new
pixels. `assemble` alone reads the PNG in its project directory, so it will keep
using that saved version until the source is explicitly updated.

`--scale 4` is the default; `--background checker` or `RRGGBB[AA]` affects only
the preview. An oversized preview reports a usable integer `--scale`. Raw RGBA
copy preserves partial alpha and invisible RGB in the scene. Geometric coverage,
matching edge colors and hashes do not certify visual continuity or meaning.
Each `adjacencies` entry lists zero-based `seam_view_indices` into
`assembly.seam_views` and its `omitted_views` count. Close-ups show at most 32
64px segments; `omitted_adjacency_views` includes all undisplayed segments,
including adjacencies beyond assembly's 256-seam report cap. Inspect important
undisplayed boundaries directly in the full scene.

Use a new directory for each revision; existing directories and `--force` are
refused. Inputs remain unchanged. Ordinary publication errors attempt rollback;
interruption or cleanup failure can leave an incomplete new directory. Check
`delivery.files` and `delivery.sha256` in the report before using it; the report
has no self-hash and its presence alone does not prove completeness.

Limits: 4096 declared cells, 256 placements; one static PNG with at most 8-bit
channels, 8192 per side and 16,777,216 pixels for the atlas, scene and preview
separately; PNG input at most 80 MiB, sidecar/layout each at most 1 MiB (embedded
metadata retains its 256 KiB limit), encoded delivery at most 128 MiB. Split an
over-budget atlas or scene. These are bounded artifact sizes, not a peak-RAM
guarantee. Other whole-atlas consumers keep their existing limits.

## Example artwork recipes

Use these for repeated variants or a large mask-based asset. Small JSON edits can stay small; an imported PNG remains a pixel specification, not recovered source objects. The recipes are original examples, not a required style or a new input format. Copy a recipe and `_common.py` together when adapting its geometry; use the Skill's runtime as described below.

```text
python <skill>/scripts/recipes/icons.py --out-dir icons --ink F5C26B
python <skill>/scripts/recipes/buttons.py --out-dir buttons --width 64 --content 28 4 30 10 --hover 426B83
python <skill>/scripts/recipes/courier128.py --out-dir courier --stripe E17B57 --stripe-light F9D5A0
python <skill>/scripts/recipes/scene256.py --out-dir scene --roof 684C6A --roof-light A07A89
python <skill>/scripts/recipes/chunk_pair.py --out-dir bridge --flag 73A5AA
```

The first four recipes each produce `asset.json`, `asset.png`, `layout.json` with a hash of the source pixels and a nearest-neighbor `preview.png`. Buttons also produce `context.json`, with absolute reserved-text rectangles derived from the current cell layout; text is drawn by the application using the atlas. These rectangles avoid the recipe's icon/focus/selection pixels. Check text fit with the application's actual font using [consumer-ui.md](consumer-ui.md). Omitting `--content` declares no text reservations.

The 64px button example is for short labels: its 30px reservation is not enough for `EXPORT MAP` in Silkscreen 8px. For that measured label use `--width 96 --content 28 4 62 10`, then run `label_atlas.py` as shown in [consumer-ui.md](consumer-ui.md). The optional helper uses actual font bounds and explicit grayscale/monochrome drawing, with configurable state offsets; it does not render text into `asset.png`.

`--content X Y W H` uses half-open bounds `[X,X+W)`, `[Y,Y+H)` in each cell. The button recipe requires `X>=23`, `Y>=4`, `X+W<=width-2`, `Y+H<=14`. `context.json` then stores the translated global regions. For `inspect`/`review`, pass both `--context .../context.json` and `--metadata .../layout.json`; do not add layout fields inside the Context just to recover existing names. `inspect --grid` is limited to 64×64: for a wider named cell, omit `--grid` for facts, or replace `--cell` with a smaller `--region X Y W H` in full-image coordinates.

`chunk_pair.py` instead produces an assembled PNG, local specs and a PNG project. See [chunking.md](chunking.md) for its two independently runnable chunks, repeating textures aligned across the seam and precise flag edit; it has no top-level `asset.json`. The original `scene256.py` below remains a component/control example with different provenance.

The scene recipe re-renders every small component before assembly and writes `scene/*.json/png`, `project.json`, `assembly.json` and `seams.png`. Its `asset.json` is the self-contained JSON rendering control. The project uses the new component PNGs, never previously generated files. It is a component/crop control, not independently authored seamless chunks.

Omit options to reproduce the bundled reference artwork exactly at the fixed Pillow 12.3.0 baseline. Other supported Pillow versions may differ in polygon rasterization. CLI parameters cover frequent variants; the short source functions name shapes and colors. Rendered JSON can remain large: it is the exchange/reproduction output, not necessarily the next file the model should read or edit. For the 128px courier, stripe and stripe-light changes stay inside `[42,68,48,10]`; changing hull also changes other surfaces. Check before/after with `verify --allow-region 42 68 48 10`.

Existing outputs are refused as a group. Use a fresh candidate directory, or explicitly `--force` for an authorized rebuild. The recipes prepare all output files before saving them. They support `--portable-output` on filesystems that reject hard links; in this mode, another program may read a new file before writing has finished. No cache or background process is required. Compare native-size images and the target application's image requirements after changing parameters; parameterization does not establish aesthetic quality or token savings.

When copying a recipe outside the Skill folder, keep `_common.py` alongside it and make the original Skill's `scripts` directory available via `PYTHONPATH`. Alternatively edit a task-local copy of the complete Skill folder; avoid changing the shared installed version for one project.

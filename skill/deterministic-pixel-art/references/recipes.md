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

## PNG animation export

`animation_export.py` exports existing, equal-size single-frame PNGs without drawing, scaling or cropping them. Create a UTF-8 `animation.json` beside the resources:

```json
{
  "version": 1,
  "kind": "png-animation",
  "frames": [
    {"image": "frames/idle-0.png", "duration_ms": 80},
    {"image": "frames/idle-1.png", "duration_ms": 120}
  ],
  "actions": [{"name": "idle", "range": [0, 2]}]
}
```

```text
python <skill>/scripts/recipes/animation_export.py --project animation.json --out-dir export-v1
```

In a source checkout, use `python recipes/animation_export.py --project animation.json --out-dir export-v1`. Resource paths resolve relative to the manifest, using `/` separators. Subdirectories, Chinese names and spaces work; absolute paths, `..`, backslashes and links that resolve outside the manifest directory are refused. Frame order is explicit. Paths are resolved and bytes frozen once per source file; this is not a sandbox against concurrent malicious link changes.

Each frame requires an integer duration from 1 to 60,000ms. Actions have distinct, case-sensitive names of 1–128 characters and zero-based half-open `range: [start, end]`. Optional `direction` is `forward` (default), `reverse` or `pingpong`; `[1,4]` expands to `[1,2,3]`, `[3,2,1]` or `[1,2,3,2]`. Source durations follow their frames. Single/two-frame pingpong actions do not duplicate endpoints. Repeated references and overlapping actions retain independent timeline entries. Unknown fields and boolean/float values in integer fields are errors.

The new directory contains original-byte `source-0000.png` files, a normalized `animation.json` and `report.json`. The report records source bytes/RGBA hashes, action order/timing, runtime versions and all delivery names and hashes except its own hash. Check every listed file and hash. Keep and move the whole directory, then regenerate from its `animation.json` into another new directory with the same command. Same runtime versions reproduce the whole delivery bytes; regeneration needs the Skill, Python and Pillow. Input PNGs are never re-encoded or changed.

GIF is optional. Add one explicit top-level configuration to the manifest:

```json
"gif": {"mode": "binary", "loop": 0}
```

Or use `"gif": {"mode": "background", "background": "172033", "loop": 2}`. Binary mode makes alpha below 128 transparent and alpha at least 128 fully opaque, reserving one palette index for transparency and up to 255 opaque colors. Background mode composites source-over on the required six-digit RGB background and permits 256 colors. Each action uses one palette; colors within capacity remain exact, otherwise Pillow MEDIANCUT quantizes without dithering. GIF conversion affects only `action-0000.gif` previews. Original PNG alpha, invisible RGB and exact milliseconds remain in the source delivery.

GIF projects each selected entry independently to `duration_ms // 10 * 10`: 45/75/115ms becomes 40/70/110ms. Selected frames below 10ms cause rejection when GIF is enabled. Adjacent identical projected frames may merge after this projection; the report maps logical entries to encoded visible runs and records timing loss. Every GIF is decoded before publication to verify its size, loop field and visible timeline, including transparency clearing. `loop` defaults to 0 and accepts 0–65,535; 0 means indefinite looping, while finite values record the GIF field without promising identical player loop behavior. Inspect actual playback and target backgrounds in your receiving application.

Limits: JSON 1MiB; 128 frame entries; 16 actions; native sides at most 1024px and 1,048,576 pixels/frame; PNG bytes at most 8MiB/file and 64MiB across entries; 16,777,216 source pixels across entries. Repeated references count toward entry budgets. Each action permits at most 256 expanded entries and 120,000 original milliseconds, with 1024 expanded entries total. GIF work permits 67,108,864 expanded pixels total; delivery permits 128MiB encoded bytes. PNG bit depth above 8 and APNG/multiframe inputs are refused. Split sources or actions when a limit is exceeded.

Use a fresh output directory for every revision; this recipe rejects `--force` and every existing directory, including empty directories and dangling links. All input/GIF/budget validation precedes directory creation. `--portable-output`, `--no-portable-output` and `PIXELART_PORTABLE_OUTPUT` use the standard output rules. Ordinary write failures attempt rollback; a nonempty or unremovable directory is retained with a recovery path. Publication is not a crash-safe transaction across files; portable files may be visible while writing. The report is published last, and its existence alone does not prove completeness.

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

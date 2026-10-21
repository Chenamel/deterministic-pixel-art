# Advisory review command

```text
python <skill>/scripts/pixel_art.py review --image asset.png --out-dir review --context context.json --compare previous.png
```

`--context` and `--compare` are optional. Valid input exits 0 even with warnings; malformed input, mismatched comparison dimensions or I/O errors exit 2. Existing managed outputs require `--force`; inputs cannot be replaced. Source pixels remain unchanged. Use a separate output directory per review; `report.json` identifies the current comparison, not a leftover file from a previous invocation.

Outputs: `report.json`, `review.png`, plus `difference.png` when comparing. Views include native 1:1, nearest-neighbor, dark/light/declared backgrounds, grayscale and annotations. Sprite context adds alpha silhouettes; atlas cells get separate cards. Integer enlargement is at most 8. Columns adapt to the sheet budget; oversized views use explicitly labeled native crops and a nearest-neighbor overview. `facts.review_views` records displayed rectangles and scales. Unicode names remain in JSON; diagnostic labels do not use the consumer's font.

## Context v1

All fields are optional. Unknown fields are errors. Coordinates are native; rectangles are `[x,y,width,height]`, positive extents, inside the image.

```json
{
  "version":1,
  "asset_type":"sprite",
  "backgrounds":[{"name":"target","color":"1D293D"}],
  "allowed_specks":[[2,13]],
  "contrast_pairs":[{"name":"active indicator","foreground":"D8E3ED","background":"1D293D","min_ratio":3,"rect":[2,2,12,12]}],
  "regions":[{"name":"runtime label","rect":[2,2,12,4],"role":"reserved_text"}]
}
```

- `asset_type`: `general` (default), `sprite`, `ui`.
- `backgrounds`: up to eight named opaque colors, retaining default `dark`/`light` whose names are reserved. Colors use the render API format.
- `primary_background`: a declared name used for native, grayscale and cell cards. Defaults to the first custom background, or `dark` when none is declared.
- `atlas`: copy the object under `atlas` in `render --metadata` output: `cell_size`, `columns`, `rows`, and `cells` with `name,x,y,w,h`. It must match the PNG grid with unique aligned cells; at most 256. PNGs do not retain CLI layout metadata automatically.
- `regions`: names/rectangles with role `content`, `control`, `reserved_text` or `decoration`. Annotations cannot determine whether real text overlaps or fits.
- `allowed_specks`: global coordinates of intentional isolated pixels, omitted from warnings. Eight-neighbor connectivity is checked separately within each named cell. RGB under zero alpha is ignored; any positive alpha is visible.
- `contrast_pairs`: declared functional foreground/background colors, optional `rect` and `min_ratio` (1-21, default 3). Foreground alpha is composited over the required opaque background before sRGB relative-luminance calculation. Pairs are not extracted from the image: declare actual adjacent colors. Threshold comparison uses the unrounded ratio.

## Interpretation

Warnings identify isolated pixels, visually identical named cells and declared pairs below target. Particles may be isolated; states may share a texture; decoration has no general 3:1 requirement. Isolated warnings are capped at 256 entries; the full count and omitted count remain in facts.

Comparison reports changed visible RGBA pixels and a bounding box, ignoring RGB under zero alpha. Changes do not establish improvement. Diagnostic images are not replacement artwork. There is no aesthetic score, automatic repair, text-layout acceptance, independent judgement or in-game verification.

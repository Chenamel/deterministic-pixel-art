# PNG assets in a real UI

Read when integrating an atlas with actual content, input and scaling. For art direction see [ui.md](ui.md); use [recipes.md](recipes.md) to regenerate geometry. PNG state cells supply artwork. The consumer supplies text, state transitions and interaction.

## Verify content with the real font

Load the intended font successfully before measuring; a fallback font does not establish fit. Compare actual glyph bounds and line metrics with the declared content rectangle at native logical size, including icons, selection marks, focus treatment and pressed offsets. Check the longest real labels and relevant translations. Blank space in a texture is a reservation, not a completed text test.

For example, the repository browser study measured `EXPORT MAP` as 58 logical pixels in Silkscreen 8px. A 30px reservation failed; a 62px reservation fit after the button widened from64 to96px. These are measurements of that Latin font/label, not universal defaults. A wider component costs layout space; a fixed layout may instead need a shorter label, reflow or another agreed treatment. Do not silently shrink text or stretch the border.

The shipped button recipe can produce the revised dimensions and reservations:

```text
python <skill>/scripts/recipes/buttons.py --out-dir buttons --width 96 --content 28 4 62 10
```

This generates PNG/JSON/layout/context. For an offline real-font measurement and composite, use the optional helper with your own font file:

```text
python <skill>/scripts/recipes/label_atlas.py --image buttons/asset.png --metadata buttons/layout.json --context buttons/context.json --font Silkscreen-Regular.ttf --font-size 8 --font-mode monochrome --labels START LOOP "EXPORT MAP" --color E5ECEE --state-color disabled 8997A5 --state-offset pressed 0 1 --out-dir consumer
```

Outputs are `consumer.png` (labels in columns, states in atlas order down rows), `consumer-3x.png` and `text-fit.json` with actual font bounds, global drawing origins and ink rectangles. Choose `monochrome` for binary glyph coverage or `grayscale` for antialiased coverage; neither is a universal pixel-art requirement. No font is bundled or silently substituted. This example was measured with Silkscreen Regular8px; another font may need different dimensions. Check the intended glyphs visually.

The helper validates layout against the source pixels and reads one `reserved_text` rectangle per cell from Context. Pass both files: Context describes content/backgrounds, while `layout.json` provides cell names and positions. Embedded content-bound layout can replace `--metadata`. Rectangles are `[x,y,width,height]`, covering `[x,x+width)` and `[y,y+height)`; global Context coordinates are not cell-local coordinates.

For each label the helper finds one shared cell-local origin that fits all reservations with the specified padding (default2), then applies explicit state offsets. `--state-offset pressed 0 1` moves the text down1px with this recipe's pressed icon. It refuses an impossible fit instead of shrinking, clipping or moving unrelated states independently. Adjust the reservation or component dimensions when necessary. The original atlas is unchanged; the report's `origin` values are for Pillow's default `ImageDraw.text` anchor, and composition is source-over.

The receiving application still needs its own font and input checks. The helper is an offline composite, not an interactive widget. Do not claim Chinese, Minecraft or other font support from the Latin example.

## Preserve state combinations

Resolve cells by verified name/position; refresh PNG, layout and text reservations together after geometry changes. State names are not semantic authentication: verify what the receiving app actually does.

Check normal, hover, held press/release/cancel, selection and disabled behavior when applicable. Keep persistent selection visible while hover or keyboard focus changes. If the atlas has only one state at a time, render the focus indicator as a separate overlay instead of replacing a selected marker. Use the app's native controls/input conventions for keyboard activation and disabled behavior.

A compact integration pass covers: actual pointer activation; Enter/Space where expected; moving away before release; focus movement; selected+focused; disabled activation/focus; target backgrounds and1/2/3x integer display. Adapt these to the real consumer rather than forcing browser semantics on a game.

## Regenerate and inspect

Retain the editable source, output paths and consumer configuration. After one parameter change, rebuild and reload; confirm displayed dimensions, labels, cell order and metadata reflect the new files. Reject or replace stale sidecars deliberately. Inspect native-size content and enlarged edges; nearest-neighbor scaling does not establish arbitrary OS-DPI or browser-zoom behavior.

Distinguish renderer checks, offline composites, actual runtime checks and game integration in the result. If the font or runtime is unavailable, deliver the reservations and state contract with those checks explicitly pending. This Skill does not bundle a browser or application runtime.

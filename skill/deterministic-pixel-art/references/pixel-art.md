# Pixel art: decisions at native resolution

## Silhouette and negative space

Reduce a sprite to its alpha silhouette on the target background. Find direction-bearing features: nose versus engine, arrow tip versus shaft, handle versus blade. Give those features space before adding highlights. At 12-16px, an extra pixel of negative space may matter more than another shade. Compare alternatives at 1:1 and 8x. Equal mathematical bounds do not imply equal visual weight.

`assets/quality/directions-12.json` is a flat, already-readable set: shading would add little to that brief. `ship-32.json` shows a nose/cockpit/engine axis and separated exhaust. A silhouette can lose internal meaning, so inspect the full image too.

## Clusters, lines and light

Treat connected areas of light and dark as shapes describing a form. Place large base/shadow groups before tiny texture. Check diagonals and curves for accidental changes in step rhythm; retain a deliberate bend when it describes the subject. Distinguish a stray pixel from a deliberate spark or highlight.

Choose a light source and check related surfaces. Concentric shading from an outline inward can flatten a rounded object; shade its volume rather than its distance from the border. Hue shifts and selective outlines are options. A flat pictogram may need neither volume nor shading.

The renderer adds no automatic antialiasing. Manually placed intermediate colors remain valid pixels. Outer-edge antialiasing designed for one background can create a halo on another. Dithering can communicate texture or a broad gradient but obscure a tiny symbol. Do not remove it merely to reduce warnings.

## Palette and material

Assign colors jobs: silhouette, base, light, shadow, accent. Merge similar colors only when their jobs are not visible at native scale. Avoid a universal color-count limit. Controlled value contrast distinguishes planes; backgrounds may intentionally use quiet neighboring tones.

`assets/quality/materials-32.json` holds one silhouette across crystal, metal and stone: facets, a hard reflection band and matte clustered planes carry material cues. Check whether those differences survive grayscale; color can reinforce them without carrying them alone.

Original paired studies with native-size rows: [icons](../assets/studies/icons.png), [ship/material](../assets/studies/art.png). These are author self-review, not independent model trials.

## Targeted revision

Name the issue before editing: “the exhaust touches the wing at 1:1” or “highlights split the face into unrelated pieces.” Change that region and compare. Preserve useful roughness, character and style; smoothness is not automatically improvement. See the author tutorials in [sources.md](sources.md).

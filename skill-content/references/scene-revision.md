# Scene revisions and delivery

Consult the relevant section when a scene edit moves connected parts, a fill extends beyond its intended surface, a pattern is hard to read, or files must be delivered for later editing or reuse. Simple recoloring can skip unrelated sections. Follow the user's reference and deliberate style choices.

## Read the resulting composition

**Artist practice [1]:** Establish large areas of color before adding small texture. In SLYNYRD's daylight examples, distance changes hue, value, contrast and texture scale; the forest example shifts toward warm distant light rather than applying a universal blue shift.

**Application:** Check the composite against the requested mood and focal area. An opaque layer can hide a warm sky band even when that band is present in the source. Examine which bands remain visible before adding stars, glow or texture. Where gameplay space is requested, judge it with representative foreground content when available; otherwise describe it as unverified.

## Change the connected object

**Mechanism [2]:** Tiled groups propagate visibility and offsets to child layers.

**Application:** For parts meant to move together, derive their coordinates from a shared anchor or explicit relationships. Before hiding a light source, identify its glow, projected light and reflections; remove or recompute those that depend on it. Independent ambient light can remain. When a light source moves, its light on a fixed surface may need to be redrawn rather than moved by the same offset. Doors, windows and connectors should follow the intended geometry. This can be a small helper or shared parameter; no scene graph or separate file per part is required. Limit a parameter's documented scope when some parts remain fixed.

## Keep a fill inside its surface

**Mechanism [3,4]:** Alpha inheritance and image masks restrict where a layer contributes.

**Application:** Define the intended land, wall or other receiving shape, then keep added color bands or texture within that shape. Use its silhouette, a binary mask or an explicit set of allowed pixels to control where color is applied. A bounding rectangle around a sloped shore does not describe that shore. Revisit the mask when the surface changes. Reflections and cast shadows may cross an object's silhouette; restrict them to their intended receiving surfaces instead.

In this tool, a drawing operation's `clip` option permits clipping at the canvas boundary; it does not restrict drawing to an earlier polygon. The `mask` drawing operation paints supplied points and an optional outline, without establishing a persistent selection. Choose the appropriate existing pixel or Pillow mask method; do not invent a JSON clipping field.

## Make patterns serve the form

**Artist practice [5]:** Dithering varies pixel density to suggest intermediate tones; its amount and texture are stylistic choices.

**Application:** If a supposed soft light reads as stripes or a checkerboard, inspect its pattern in both axes, density changes, contrast and outer shape at native size. For coded patterns, check how the pattern repeats across rows and columns and where it starts in the image. Preserve readable steps, paths and material boundaries underneath. Adjust the pattern or use larger unbroken clusters where appropriate; dithering is not a required replacement for flat shading.

## Check reuse and the delivered version

**Mechanism [6]:** Aseprite distinguishes repeating a pattern from arranging reusable tiles.

**Application:** State whether the asset is a single screen, a horizontal repeat, a vertical repeat, or a tile set. For an advertised repeat, inspect multiple copies across the promised axes and their joins. Matching edge colors alone do not show whether land, water and other features line up across the seam. A single-screen brief does not require redrawing the scene to make it tileable.

After final renaming or packaging, check assembly PNG references relative to the delivered project file; sources must remain inside its directory after resolving symlinks. Include referenced rules and helpers, and state remaining environment requirements. Follow the existing [assembly](workflows.md#native-artwork-and-assembly) and [versioning](workflows.md#candidates-without-overwriting-evidence) rules.

Use [visual review](review.md#when-a-visual-description-conflicts) on the current whole image and a contextual before/after crop when needed. If image access fails, record the limitation; filenames, zero warnings and pixel measurements do not prove that the current image was viewed.

## Sources

1. SLYNYRD, [Pixelblog 62: Landscape Backgrounds](https://www.slynyrd.com/blog/2026/5/27/pixelblog-62-landscape-backgrounds), Intro, Valley and Forest. Personal palette counts and canvas sizes are not general constraints.
2. [Tiled: Group Layers](https://doc.mapeditor.org/en/stable/manual/layers/#group-layers), documented inherited properties; application to recipe dependencies is our suggestion.
3. [Krita: Clipping Masks and Alpha Inheritance](https://docs.krita.org/en/tutorials/clipping_masks_and_alpha_inheritance.html), including isolated groups and pass-through exception.
4. [Pillow: Image.composite](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.composite) and [Image.paste](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.paste), mask and alpha semantics.
5. Derek Yu, [Pixel Art Basics: Dithering](https://www.derekyu.com/makegames/pixelart.html#dithering). The pattern checks above are our suggestions, not an algorithm prescribed by the artist.
6. [Aseprite: Tiled Mode](https://www.aseprite.org/docs/tiled-mode/).

Tool-specific mask and assembly statements follow this project's [formats](formats.md) and [workflows](workflows.md). These sources explain techniques and inform the suggestions above; they do not demonstrate that this guidance improves artwork or efficiency. The named applications are not required.

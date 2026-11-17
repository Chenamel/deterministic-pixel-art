# External methods and limits

Consulted 2026-10-21. Notes and teaching artwork are original summaries/studies. Source images, game textures and fonts are not redistributed.

| Source | Applied method | Limits |
|---|---|---|
| Derek Yu, [Basics](https://www.derekyu.com/makegames/pixelart.html) and [Common Mistakes](https://www.derekyu.com/makegames/pixelart2.html) | Line rhythm, palette jobs, shading forms with large groups | An artist's style is not a universal target; flat graphics and roughness remain valid. |
| Pedro Medeiros / Saint11, [Tutorials](https://saint11.art/blog/pixel-art-tutorials/) | Silhouette, outlines, material, planning, UI borders | Not every technique belongs in a tiny UI icon. |
| Kenney, [Pixel UI Pack](https://kenney.nl/assets/pixel-ui-pack) | Coherent panels, borders, arrows and component families | The pack is listed as CC0; none of its files are bundled here. |
| Kelley Gordon / NN/g, [Visual Hierarchy](https://www.nngroup.com/articles/visual-hierarchy-ux-definition/) | Contrast, scale, grouping, inspection with actual content | Transfer relationships, not web font sizes or color-count suggestions. |
| W3C, [Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) | 3:1 contextual reference for declared active indicators | No aesthetic score or game accessibility certification; exceptions include inactive controls, decoration and nonadjacent states. |
| Forge, [1.20.1 Screens](https://docs.minecraftforge.net/en/1.20.1/gui/screens/) | Relative coordinates, GUI Scale, explicit UV/texture dimensions, separate content layers | Version-specific integration; offline PNG review does not run the client. |

Borrow reasoning and adapt it to the user's reference and constraints. If a source is unavailable, local summaries remain usable; do not claim to have rechecked it.

## Additional scene references

Sources for the [scene-space guide](scene-space.md#sources) were checked on 2026-11-01 and 2026-11-17; the additional projection and engine references below were checked on 2026-11-17. Sources for the [scene-revision guide](scene-revision.md#sources) were checked on 2026-11-01. Geometry, artist practice and engine behavior have different scopes; none sets a universal art style.

| Source | Used for | Limits |
|---|---|---|
| [Clint Bellanger, Isometric Tiles Math](https://clintbellanger.net/articles/isometric_math/) | Mapping orthogonal map coordinates to a 2:1 screen grid and relating diamond origins to sprite bounds | Describes a 2:1 projection; it does not choose a game's view or sprite anchor for every asset. |
| [Godot, Using TileMaps](https://docs.godotengine.org/en/stable/tutorials/2d/using_tilemaps.html) | Y sorting, sort origins and separating layers | Engine-specific behavior and property names. |
| [Tiled, Using Terrains](https://doc.mapeditor.org/en/stable/manual/terrain/) | Tile transformations and directional-shadow constraints | Applies to Tiled's terrain workflow; inspect other transforms against the chosen lighting. |
| [Pixnote, Isometric Pixel Art Guide](https://pixnote.net/en/learn/isometric/) | Vertical edges and an example of face values under a stated light direction | An artist guide, not a lighting standard. |
| [Sprixen, Isometric Pixel Art Guide](https://sprixen.com/blog/isometric-pixel-art-tile-and-building-sizes) | Examples of tile sizes and bottom-centered building anchors | Practical suggestions, not required dimensions or engine rules. |

Source images remain with their publishers. These references do not establish artwork quality or efficiency improvements.

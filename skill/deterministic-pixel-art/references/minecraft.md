# Optional Minecraft styling

Select `preset: minecraft` for JSON button/slot operations. The DSL selects it automatically. These are reusable demo conventions, not a promise to match every Minecraft version or mod's artwork; an existing project's asset contract takes priority.

- Panel grey: C6C6C6. Slot: 18x18, fill 8B8B8B, top/left 373737 and bottom/right FFFFFF.
- Button state names: NORMAL, HOVER, PRESSED, SELECTED, DISABLED. Minimum 4x4. NORMAL/HOVER/PRESSED preserve the original demo palette. SELECTED is neutral recessed A0A0A0; DISABLED uses 707070. See `assets/minecraft-button-states.json`.
- Raised controls generally have bright top-left and dark bottom-right; recessed controls reverse that relationship. Distinguish state by silhouette/position when color alone is ambiguous.
- For assets targeting binary transparency, validate alpha [0,255]. Set cell_size and transparent_margin only if that specific atlas requires them. Opaque attached controls should stay opaque.
- Keep native logical sizes, source UVs, state order and reserved content regions from the target project. Do not impose a universal 16x16 content area or transparent border.
- For new icon sets, an optional mode palette is grey A0A0A0, input 559FE8, output E36B6B, bidirectional B679D1, cache 6DBB78. Existing accepted artwork may use different shades.

For an existing mod, generate a candidate asset and compare native-size composites. The generic renderer does not install files into a resource tree or claim in-game visual acceptance.

## Version and integration checks

Identify edition, game version, loader and resource consumer before borrowing an online recipe. The study project targets Forge 1.20.1. Newer Fabric documentation and modern GUI sprite metadata are not automatically compatible. The preset is a demo style, not a full vanilla replacement.

Inspect accepted assets for border width, bevel corner ownership, slot inset, padding and attached footer edges. A five-pixel-high footer has little room for decoration: changing one row can break a seam. Preserve texture sizes, UV rectangles and state order when drawing a separate candidate.

`assets/quality/minecraft-states.json` separates input and output arrows in the bidirectional cell rather than overlapping them. `minecraft-panel.json` retains a serviceable panel: a quality workflow should recognize when no redesign is needed.

The original [Minecraft paired study](../assets/studies/minecraft.png) shows both cases at native size and enlarged. It is offline author self-review.

Forge 1.20.1 renders text, items, textures and tooltips separately. Use real font/content measurements when available; avoid baking a substitute font into assets. Inspect native-size composites first, then integer GUI-scale views. Offline views cannot verify UV selection, hover hitboxes, z ordering, font fallback or in-game scaling; record these as unverified until the consumer runs.

Use the versioned [Forge screen documentation](https://docs.minecraftforge.net/en/1.20.1/gui/screens/) for integration. The hierarchy and state guidance in [ui.md](ui.md) applies within the existing Minecraft style.

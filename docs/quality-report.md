# Visual quality report

[简体中文](quality-report.zh-CN.md) · [Machine-readable snapshot](measurements/visual-quality.json)

The eight-task author self-review preferred six candidates and retained two unchanged. No material direction, state-meaning or content-reservation regression was identified in the inspected offline views. All 43 v1.0.0 migration outputs remain pixel-compatible. This report records a small authored study, not independent proof of a general aesthetic or model-quality improvement.

## Method and evidence

The baseline was frozen using the v1.0.0 guidance before changing the runtime/instructions. Both passes share the same briefs, maximum two candidates and maximum two targeted revision rounds. The actual work used fewer alternatives where the shape was clear. Frozen specifications, PNGs and hashes are in [quality/baseline](../quality/baseline/); [task briefs](../quality/tasks.json), [process records](../quality/process.json), [unused alternatives](../quality/drafts/) and [early revisions](../quality/revisions/) remain reviewable. Baselines are never silently regenerated.

The author also evaluated the result and knew the proposed improvement directions in advance. There was no randomization, independent reviewer, blinded preference test or independent model trial. Native-size views, nearest-neighbor paired sheets, grayscale, silhouettes where applicable and contextual review sheets were inspected. Automated pixel checks establish contracts and compatibility, not beauty. The published images are original studies; no tutorial images, third-party UI pack or Minecraft vanilla texture was bundled.

## Per-task findings and tradeoffs

| Task | Self-review | Concrete observation | Tradeoff / limit |
|---|---|---|---|
| Four 12×12 directions | Unchanged | Equal-weight silhouettes and margins retained; exact pixels match | Additional shading was unnecessary for this flat brief |
| Six 16×16 functions | Improved | Filter/lock better match stem weight; refresh has a curved clockwise ring and arrowhead | Thicker refresh is less suitable for a fine-line set |
| 32×32 asymmetric ship | Improved | Cockpit, pointed nose and engine align upper-right; separate exhaust clarifies silhouette | More detail than a minimal pictogram |
| Three 32×32 materials | Improved | Facets, a hard reflection band and matte planes/cracks distinguish crystal, metal and stone in grayscale | More colors and operations than palette swaps |
| Six button states | Improved | Focus has an outer cue, selection a check/underline, pressed an offset glyph and reversed bevel | Decoration uses inner padding; long labels not tested |
| 96×64 UI panel | Improved | Navigation selection, two content groups and primary action have distinct hierarchy | Reserved regions do not prove font or translated-text fit |
| Five 16×16 Minecraft controls | Improved | Familiar power mark, explicit on cue and separate opposing-arrow lanes | Both-mode shafts are smaller; UV/hitbox behavior untested |
| 96×54 Minecraft composition | Unchanged | Existing recessed slots, raised actions and adjoining edges retained; exact pixels match | Remaining space is available to consumer content |

The refresh icon and ship each needed one targeted revision. A wider ship and brighter panel header were kept as unselected alternatives: they crowded the silhouette or competed with the primary action. The final contact-sheet layout was also corrected to show complete native-size panels; that presentation fix did not alter the source assets.

![Icons](quality/icons.png)
![Form and material](quality/art.png)
![UI states and layout](quality/ui.png)
![Minecraft controls and seams](quality/minecraft.png)

## Timing and effort

| Task | Baseline render ms | Candidate render ms | Review CLI seconds | Candidates / revisions |
|---|---:|---:|---:|---:|
| directions-12 | 0.4347 | 0.4206 | 0.172 | 1 / 0 |
| functions-16 | 0.3532 | 0.3686 | 0.175 | 1 / 1 |
| ship-32 | 0.1310 | 0.2453 | 0.167 | 2 / 1 |
| materials-32 | 0.2922 | 0.3614 | 0.176 | 1 / 0 |
| ui-states | 0.3795 | 0.5313 | 0.197 | 1 / 0 |
| ui-panel | 0.1272 | 0.2036 | 0.195 | 2 / 0 |
| minecraft-states | 0.6590 | 0.4278 | 0.202 | 1 / 0 |
| minecraft-panel | 0.2574 | 0.2267 | 0.182 | 1 / 0 |

Render values are individual local measurements from the authoring records, not repeated performance benchmarks. Review duration includes Python startup, loading, diagnostics and writing reports. Total model authoring time and tokens were not instrumented and are recorded as null. These numbers do not establish a faster workflow; some richer candidates render more slowly. The earlier runtime benchmark and its CLI/allocation regressions remain in the [historical report](optimization-report.zh-CN.md). No token-saving or quality-percentage claim is made.

## Technical verification and behavior changes

- All 43 stable outputs match frozen dimensions and RGBA hashes; eight study baselines also match their frozen files and re-rendered pixels. The historical 40/43 plus three intentional fixes describes the earlier migration, not a new regression.
- 33 unit tests and 37 execution scenarios from the actual 42-file ZIP pass. Tests cover partial/zero alpha, cell boundaries, intentional isolated pixels, repeated states, explicit contrast pairs, malformed contexts, comparisons and overwrite refusal.
- The official Skill validator passes on the unpacked artifact. The package executes from an unrelated Chinese/space path in a fresh Python environment; identical sources produce identical ZIP bytes. Python/Pillow remain the only runtime dependencies; PyYAML is development-only.
- The local preservation audit found all 96 protected original-tool and mod-resource files unchanged. The machine-specific preservation archive remains outside this repository.
- JSON v1 and existing Python interfaces/commands are preserved. `review` is additive and advisory: valid input with warnings exits 0, invalid input exits 2. It does not edit the source. `validate` remains the explicit contract checker.
- Contrast checks apply only to declared functional foreground/background pairs after alpha compositing. The default 3:1 is a contextual reference, not a requirement for all decorative pixels or all state pairs. No universal ban is applied to isolated pixels, dithering or hand-placed antialiasing.

## Sources and release boundary

[Derek Yu](https://www.derekyu.com/makegames/pixelart.html) and [common issues](https://www.derekyu.com/makegames/pixelart2.html) informed silhouette, clusters and value grouping; [Saint11](https://saint11.art/blog/pixel-art-tutorials/) informed planning, outline and material inspection; [Kenney](https://kenney.nl/assets/pixel-ui-pack) informed set consistency and component organization; [NN/g](https://www.nngroup.com/articles/visual-hierarchy-ux-definition/) informed hierarchy; [W3C](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) informed scoped functional contrast checks; [Forge 1.20.1](https://docs.minecraftforge.net/en/1.20.1/gui/screens/) informed GUI scale, UV and texture/interaction boundaries. See the [source register](../skill-content/references/sources.md) for applicability and the original teaching examples in the paired sheets.

The specified author-review gate is met: six preferred, two unchanged, and no identified material semantic regression. It supports releasing this scoped update after artifact checks. It does not replace independent preference testing, accessibility evaluation, real-font layout or in-game acceptance. The Minecraft scenes are offline compositions, not evidence of runtime behavior.

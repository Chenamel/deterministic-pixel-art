# Pixel UI: hierarchy, state and context

## Layout before decoration

Identify the main action, current selection, secondary information and unavailable controls. Use grouping and spacing before adding bevels or texture. Related items usually need less space between them than between groups. Inherit the project's rhythm rather than importing web-pixel values into a low-resolution canvas.

Use a small family of border weights and corner shapes. Match optical weight across icons; identical bounding boxes can contain different amounts of visible ink. Establish a representative component, then expand the set. Keep large accents scarce enough to retain meaning.

`assets/quality/ui-panel.json` separates navigation, content and a primary action; its context marks runtime text reservations. No font is embedded. Long translated labels and dense lists can change the hierarchy. Blank reservations alone do not prove text fits.

See the original [UI paired study](../assets/studies/ui.png), including native-size views. This is author self-review, with no font-layout or runtime acceptance.

## State vocabulary

`assets/quality/ui-states.json` contains normal, hover, focus, pressed, selected and disabled cells. Preserve the application's own state names/order if different.

- Hover attracts attention temporarily; focus identifies keyboard/controller position. Do not silently merge them.
- Pressed reads as an action in progress; a displacement or reversed bevel can reinforce it.
- Selected persists: a marker, inset or check remains after hover moves away.
- Disabled reduces availability cues while retaining identity. Inactive controls have contrast exceptions.

Color alone may be insufficient. Inspect shape, marker and value cues in grayscale too; grayscale is not a color-vision simulation or accessibility certification.

## Frames, content and scaling

Keep corners and border thickness stable across sizes. Produce alternate sizes through geometry or existing blit composition rather than stretching a finished border indiscriminately. This release has no nine-slice theme/component engine.

Composite icons into their button/panel at 1:1; inspect seams, padding, clipping and competing emphasis. Avoid baking text into reusable textures unless requested. Use the application's actual font and line metrics for text checks.

For explicitly identified functional indicators, a 3:1 adjacent-color ratio is a starting reference from WCAG non-text contrast. It is not a condition for every highlight, decorative edge, disabled control or pair of nonadjacent states. Declare relevant pairs in review context and interpret results in the real layout. See [sources.md](sources.md).

For actual font fit, selected+focused rendering, input and a regenerate/reload loop, read [consumer-ui.md](consumer-ui.md). A correct PNG alone does not establish a usable interactive component.

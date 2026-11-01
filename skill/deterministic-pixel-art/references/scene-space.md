# Scene space and solid forms

Use this when objects must share a scene, or a roof, wall or ground relationship looks wrong. You may read it before drawing a scene, or consult one section for a specific question. Skip it for clear flat icons or simple recoloring. User references and explicit style choices take priority, including deliberate distortion or mixed viewpoints.

## Choose the space

**Geometry [1]:** Identify the viewing direction (front, side, top-down or oblique) and the projection (parallel, perspective or a deliberate hybrid). In parallel projection, edges that are parallel in the scene stay parallel on screen; equal objects do not shrink merely because they are farther away. In perspective, edges that are parallel in the scene converge toward a shared vanishing point, unless they are parallel to the image plane.

True isometric projection equally foreshortens three perpendicular axes; in the usual upright view, its ground axes lie at 30° to horizontal. The common pixel-art convention uses two pixels across for one up/down: about 26.565° (`atan(1/2)`), rather than exactly 30°. Use a short 2:1 ruler only if that convention fits the task. It guides the chosen ground axes, not every diagonal: pitched roofs, curves and rotated objects can need other directions. Pixelblog 4's house uses 2:1 ground-parallel wall edges and different roof slopes [2].

## Establish the large forms

**Artist practice [1–3]:** SLYNYRD builds with simple geometry and separate parts; Yu describes a canopy as a few spheres instead of individual leaves.

**Application:** Sketch the uncertain part as simple solids before adding texture: a box for the walls, a wedge for the roof, cylinders for posts, or a few spheres for a canopy. Decide the footprint, height and joined corners. If a roof feels twisted, trace its eaves back to the wall corners before moving highlights. For an unclear overlap, sketch how the covered shape continues behind the object in front; a temporary guide or separately editable parts can help without rebuilding the entire image.

## Place objects in the same space

**Application suggestions:** Choose a scale reference already relevant to the brief, such as a door, person or tile. Compare repeated objects under the chosen projection; an oversized landmark may be intentional. Check where each support meets its surface: feet on the ground, a tree trunk where it meets the ground, posts beneath a platform. Do those contact points fit the same ground plane and intended height? Resolve unintended gaps before adding a shadow at the contact point.

At an overlap, decide which object is in front and where the rear contour disappears. If two edges merge into an unintended shape at native size, move an edge or open a gap where the design allows it. Compare only edges meant to share a direction; a sloped bank or roof need not follow a horizontal tile edge.

## Light the forms, then inspect the result

**Artist practice [2,3]:** Choose the light direction and group light/shadow around the large forms, rather than shading inward from every outline. Compare similarly oriented surfaces under similar lighting, allowing for material and local light. Where cast shadows belong to the style, check which object casts them and how they fall across the receiving surface. Flat shading, selective outlines and deliberate lighting cheats remain valid choices.

**Application check:** Inspect the whole image at native size on its intended background, then a local crop that includes the supporting surface and neighboring objects. Use nearest-neighbor enlargement to inspect line steps. Name an observable mismatch—“the post ends above the platform”—and revise that relationship before adding texture. Keep intentional stylization when the reference supports it. These checks guide decisions; they do not guarantee artistic quality.

## Sources

1. SLYNYRD, [Pixelblog 41: Isometric Pixel Art](https://www.slynyrd.com/blog/2022/11/28/pixelblog-41-isometric-pixel-art): projection, geometric construction and separate parts.
2. SLYNYRD, [Pixelblog 4: Graphical Projection Part 2](https://www.slynyrd.com/blog/2018/4/12/pixelblog-4-graphical-projection-part-2): house construction and optional grid/ruler.
3. Derek Yu, [Common Mistakes, §2: Creating Forms with Volume](https://www.derekyu.com/makegames/pixelart2.html): simplified volumes and pillow shading.

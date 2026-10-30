# Gemini UI01 image review: verified findings

The review and platform summary describe one image review, not two independent runs. The exact backend and raw tool session were not supplied. The coordinator verified all eight packet images against the frozen archive, original producer files, placement reports and existing APIs.

The findings provide useful layout and state-decoration feedback. They do not establish a new renderer defect or general visual-quality improvement.

| Finding | Verification and decision |
|---|---|
| The 88px and 96px variants have identical local text coordinates | Confirmed. Both explicitly use `[23,4,62,10]`; this is authored layout, not a failure to recompute coordinates. |
| Move labels right by four pixels | Already possible with `[23,4,70,10]`. All 18 placements satisfy padding and motion contracts; atlas pixels stay identical. Shifting text alone violates the old right padding for six long-label instances. |
| Focus/selected bars touch the arrow | Confirmed adjacency, without overlap. This is visual-density feedback, not text clipping or an explicit arrow-spacing contract violation. Preserve inherited outputs and compare alternatives separately. |
| Remove the selected check | Not adopted. The check and arrow communicate selection and action respectively. Preserve a non-color selection cue. |
| Gold has low contrast on a light background | Its ratio against the light background is 1.657:1; against the internal fill, 5.654:1. An isolated diagnostic still shows the control. One color pair or a tightly packed contact sheet does not establish application failure or accessibility conformance. |
| Darken every border | The proposed color yields only 1.307:1 against the target background. This is an unvalidated style alternative. |
| Move all text down one pixel | The geometric center difference is real. A direct move violates the bottom padding for three pressed instances. Optical alignment needs a coordinated layout decision. |
| 88px supports at most ten characters; 96px supports localization | Unsupported. Eleven `I` characters measure 33px, eleven `L` characters 55px, and eleven `W` characters 77px. Original text capacity is identical in both versions. Localized glyphs and content were not tested. |
| Disabled colors fail contrast expectations | Ratios were reproduced, but disabled controls and nonadjacent state fills do not have a universal decorative-color threshold. No certification or general failure claim follows. |

An existing-API diagnostic distributes long-label margins more evenly while increasing the distance from short labels to the icon. Optional left/center/right alignment remains useful for a different layout intent; it is not required to recenter this example.

Hashes of 280 protected files stayed identical. No runtime, generated skill, installed v1.1.1, frozen rc.6 package or original submission changed. The unchanged full suite and historical CI were not rerun or relabeled as new checks. Raw materials and diagnostics remain in the ignored local evaluation directory.

Next: prepare Qwen LT03-Linux using frozen rc.6, checking task-local dependencies, lossless PNG round trips, overwrite rejection and portable output. The packet is not built or uploaded yet. Do not repeat the completed Windows or Gemini review runs.

The four main stages remain P1–P3 and P4a complete, with native512 P4b deferred. This is candidate acceptance evidence, not paired benchmarking or in-game testing. The release gate is unchanged.

[Detailed Chinese findings](ui-review-results-20261029.zh-CN.md) · [Machine summary](measurements/ui-review-results-20261029.json)

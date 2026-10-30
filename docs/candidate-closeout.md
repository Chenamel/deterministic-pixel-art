# rc.4 candidate closeout

2026-10-24. **v1.2.0-rc.4 is sealed locally, not published or installed.** [Chinese detail](candidate-closeout.zh-CN.md) · [Measurements](measurements/candidate-closeout.json). Stable/local remains v1.1.1; published rc.2 and frozen rc.3 are retained.

The four-phase plan is now at closeout: P1 has three distributed tasks and zero new external returns; P2 recipes and P3 actual-font/input integration are complete; P4a native 256 independent chunk authoring is complete. P4b's native 512 drawing is deferred: there is no concrete consumer/detail requirement demonstrating an advantage over 256. Reopen it for an explicit native-size composition, crossing structures and bounded edit need, with a new frozen agreement. Do not count an unperformed conditional trial as passed.

The candidate converts tested P3/P4 methods into two on-demand Skill references: real-font text fit and combined input states; chunk ownership, global material phase, crossings and scoped edits. A minimal 64×32 bridge ships as two separately runnable 32×32 sources plus shared primitives/contract. The six-pixel material period deliberately does not divide the owner width. The completed image is assembled only after local rendering, without repainting. This is one author's work, not a multi-agent or independent visual study.

![Minimal bridge, nearest-neighbor 4×](chunks/minimal.png)

The standalone recipe produces 15 files and supports full or one-owner rebuilds. The flag variant changes exactly 24 RGBA pixels, zero outside `[51,5,6,4]`; the other owner is unchanged. Reassembly after a single-owner change is exercised, and a stale merged sidecar is rejected. The guide explicitly identifies which old merged outputs remain stale. Actual-font browser resources and the larger native 256 example remain repository-only; no font/browser dependency enters the Skill.

Verification passed 98 source tests, 43 stable images, 10 historical external final PNG/layout regressions, 138 protected-file hashes and 86 isolated ZIP command scenarios. The extracted Skill passed the official format validator in a Unicode/space directory. Repeated packaging and all 97 file hashes agree. The small image was viewed at native size, 4× and along its seam, with zero visual revision rounds. This is author inspection of a deliberately simple teaching example, not complex-scene or in-game acceptance.

The ZIP is 230,474 bytes: +7,490 bytes/+3.359% versus rc.3. It adds optional references and short recipe sources, with no new core commands, rendering behavior or dependencies. Runtime code changes only its version identifier. No new model-time, token, correction-round, render-speed or general aesthetic improvement is claimed. The generated consumer manifest refreshes a shared-source documentation hash; its images are unchanged.

SHA-256: `cb3472769754dbd9b5d56397e2620f6be12c253a8162a1642acd71225b4e69c1`.

Local bundle: `dist/v1.2.0-rc.4/`, with ZIP, per-file manifest, check results and SHA-256 list. Raw runs remain ignored under `evaluation/closeout-20261024/`. Implementation `c0330223114288a0790a4af9c3f2019e0f5bbeb7` is pushed and all eight jobs of [CI run39985591333](https://github.com/Chenamel/deterministic-pixel-art/actions/runs/39985591333) passed, covering Windows/Ubuntu main checks and each platform's Pillow10.4/11.3/12.1 matrix. [Per-job record](measurements/candidate-closeout-ci.json). CI establishes engineering results, not independent aesthetic or external-platform acceptance.

Next: collect the P1 platform artifacts, attribute unresolved findings and apply the existing controlled stable-release gate. This closeout is not a fifth feature phase and does not authorize stable promotion by itself. Original cloud mounts, independent visual evaluation and game integration remain unverified. MIT and bilingual documentation are retained.

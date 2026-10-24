# P1 follow-up results and usability changes

Date: 2026-10-25. All three submissions use the frozen **v1.2.0-rc.2** task packages. Development starts at `e66d87d` on `codex/visual-quality`. [中文详情](p1-results.zh-CN.md).

**Submitted engineering artifacts pass independent coordinator checks. No new core pixel defect was found; named-cell extraction has a concrete usability improvement.** These are three uncontrolled follow-ups, not a paired version comparison or proof of general art-quality, time or token gains. Changes are sealed separately as local **v1.2.0-rc.5**. Installed stable remains 1.1.1.

## Evidence

Submitted scripts were treated as evidence, not executed. Known hash-checked frozen runtime and current source independently render declarative specs, check decoded RGBA/layouts/digests and verify allowed edit areas. Native-size, nearest-neighbor, background and silhouette images were actually inspected. Raw submissions and conversations stay in ignored local `evaluation/p1-results-20261025/`, outside public Git and Skill context.

| Task / reported model | Recorded environment | Commands | Independently checked outcome |
|---|---|---:|---|
| P1-W / Deepseek-V4.1-Flash in WorkBuddy | Windows; Python 3.13.14 / Pillow 12.3.0 | 31 | Atlas: 70 and hover: 96 changed RGBA pixels; zero outside each allowed edit; exact final rendering/layout |
| P1-C / qwen3.8-max | Linux; Python 3.12.3; Pillow 13.0.0 then task-local 12.3.0 | 5 | Version guard, native EPERM, explicit portable output and no-clobber recorded; exact PNG and target-background preview |
| P1-V / Gemini | Linux; Python 3.11.2 / Pillow 11.1.0 | 17 | Metal: 195 changed RGBA pixels, zero outside; unchanged alpha/outline; visible black silhouettes on light review cards |

The 53 commands include 5 nonzero exits: W7/C4/V17 refuse overwrites, C1 rejects unsupported Pillow 13, and C2 reports native hard-link EPERM. None automatically adds `--force`. Expected refusals are not rendering defects; counts are not model rankings or task-success rates.

All **13 archived spec/PNG pairs** render exactly. The three edited final images reproduce with frozen rc.2 and current rc.5. Rejected writes preserve hashes; imported base specs reproduce frozen inputs. Declared task/Skill hashes match, but RUN-only submissions omit remote runtime files: remote tool contents were not independently rehashed.

## Visual observations

![Coordinator before/after view; not a blind evaluation](p1-results/visual-summary.png)

W's side-by-side up/down arrows are readable; its gold hollow hover ring includes corners and preserves the interior. The original Chinese direction/placement wording was ambiguous, so no retroactive failure is imposed. Future templates explicitly specify left-up/right-down, side by side.

V's metal has a clearer rounded highlight/volume, with softer value steps replacing harder horizontal bands. This is a style tradeoff, not universal improvement. Adjacent cells stay intact. C's complete panel/preview uses target background `E9EDF2`; V's light-background silhouettes are visibly present before and after.

These are participant self-reports plus coordinator author review, not blind or in-game acceptance. Candidate budgets and workflows differ. Command runtimes are not total creation time; unavailable tokens remain null. No reduction in model rounds, time or tokens is established.

## Feedback decisions

| Feedback | Finding / action |
|---|---|
| Full-atlas import followed by manually locating/copying a replacement | Confirmed friction; add optional `import --cell NAME` |
| A standalone cell render has no atlas metadata | Correct standalone behavior; clarify that `replace-cell --metadata` already writes the full atlas and fresh digest |
| Refusals after reusing final paths | Preserve no-clobber; document separate candidate directories, final selection and explicitly authorized rebuilds |
| Symbols change after adding colors | Grid palette sorts exact RGBA, not frequency; retain the edited spec's own palette and local zero-based indices |
| Qwen says outside-RUN commands cannot be recorded | Trusted frozen recorder probe disproves this: command/environment/status are recorded; only automatic artifact hashes are RUN-scoped |
| Native cloud-mount failure, then claimed /tmp success | EPERM is recorded; mount identity unknown (reported ossfs2); /tmp success has no submitted command/PNG, so remains self-report only |
| Gemini calls failure command 15 | JSONL shows 17; use the command record |
| Duplicate-state warnings / missing tokens | Baseline fixture warnings remain visible; protocol already permits null tokens |
| Rotation syntax, auto numbering, gallery, locked palette, more paired preview scales | Deferred pending stronger evidence that new interfaces help more than the narrow workflow change |

## rc.5 workflow

```text
python <skill>/scripts/pixel_art.py import --image atlas.png --metadata layout.json --out editable.json
python <skill>/scripts/pixel_art.py import --image atlas.png --metadata layout.json --cell metal --out metal.json
# Edit metal.json, then:
python <skill>/scripts/pixel_art.py replace-cell --spec editable.json --cell metal --replacement metal.json --out candidate.json --image-out candidate.png --metadata candidate-layout.json
```

API: `image_to_spec(image, *, region=None, metadata=None, cell=None)`. Validate the complete source digest/layout before selecting a named cell. Output is a local-origin grid/draw, not a one-cell atlas. Sidecar, embedded and in-memory layouts work. Hidden RGB, partial alpha and >62-color row runs remain exact. Unknown names, missing/conflicting/stale layouts fail before writing; region/cell are exclusive. Existing default imports, JSON v1 and drawing/compositing semantics are retained.

A five-command coordinator rehearsal using V's real submission reproduces its final exactly: 195 changed pixels, zero outside, zero unexpected failures. Full spec: 5,857 bytes; selected spec: 1,551 bytes. Selected content matches prior manual extraction. This removes locating/copying a cell; no model-time/token savings were measured.

The first implementation omitted the public forwarding wrapper's new argument: 4 API tests failed. The wrapper was fixed and all 11 targeted tests passed; the failure is retained in the development log, not attributed to participants.

## Validation and costs

- 103 source tests, 43 stable-image regressions, 91 isolated ZIP scenarios, official Skill validation and an additional extracted Chinese/space-path import/render pass. Repeated packaging is reproducible.
- 10 historical external final PNGs/layouts remain exact; 138 historical protected files plus 10 new source files retain hashes. Frozen rc.2/rc.3/rc.4 remain untouched; installed stable is 1.1.1.
- ZIP: 97 files, 231,561 bytes; +1,087 bytes / 0.472% versus rc.4. SHA-256: `2b9cb652fb9e4a50bd3e4d11e098003b86c6195a16c9b1730dbc6907839178a4`. Local `dist/v1.2.0-rc.5/` includes ZIP, manifest, checks and reports; no new stable release.
- Named selection checks the full image digest. No new paired performance benchmark establishes speedup or zero overhead. No old rendering regression was observed, which does not prove all styles/environments are unaffected.
- Actual implementation Windows/Ubuntu and Pillow-matrix CI is recorded separately in [p1-results-ci.json](measurements/p1-results-ci.json).

[Audit summary](measurements/p1-results.json) · [Candidate validation](measurements/p1-candidate.json) · [Recovery state](../WORK_STATE.md)

## Phase position

Four main phases remain: P1 all three received/engineering-audited; P2 editable recipes complete; P3 real-font/input consumer complete; P4a independent native 256 complete, with P4b native 512 deferred until a concrete consumer/detail/edit requirement. Feedback handling is not a fifth feature phase.

Next: actual project use and the existing stable-release gate. The previously agreed eight paired tasks and concrete workflow gains are not replaced by these three follow-ups. Keep the candidate unless the gate is met; no automatic stable promotion/install. Original cloud-mount reproduction, independent aesthetic assessment and in-game effects remain unverified.

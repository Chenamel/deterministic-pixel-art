# External feedback and reliability

Four external agent audit reports informed this work. They are useful usage and
defect-discovery evidence, not independent proof of general aesthetic improvement.
Their common checklist mixes bugs, design choices and unsupported features; its
2–10% coverage figures are not quality-gain percentages. Raw private conversations
are retained outside the distributed skill.

## Confirmed and acted on in 1.1.1

| Finding | Evidence and change |
|---|---|
| Null mask outline erased neighbors | Red-background reproduction; null now equals omission. Explicit transparent outline still erases. |
| Primary native/cell review used dark background | Native-card pixel assertion; explicit primary name or first custom background is used. |
| Valid 2800×100 source overflowed the sheet | Bounded adaptive layout; oversized views are labeled crops with coordinate manifests. |
| Deep JSON escaped input errors | Python 3.14 reproduction at depth 20,000; decoder RecursionError becomes a JSON error. Other versions have different thresholds. |
| Partial outputs on I/O failure | Directory target preflight and injected second-commit failure; staged publication and rollback preserve originals. |
| Concurrent no-force writers could overwrite | Controlled overlapping CLI writers; reservations and exclusive publication allow one winner. |
| POSIX venv symlink resolved to system Python | Keep the absolute interpreter invocation path without dereferencing its symlink; covered by portable CI. |

Replacement drawing versus source-over blitting is retained and documented.
PNG layout reuse and editable import are separate next-version capabilities.

## Corrections to audit interpretations

`get_flattened_data` first appears in [Pillow 12.1 source](https://github.com/python-pillow/Pillow/blob/12.1.0/src/PIL/Image.py),
and is absent in 12.0. Reports claiming it is missing through 12.2 are inaccurate.
The fixed reproduction dependency remains Pillow 12.3.0. Older-version tests use
an explicit compatibility adapter, not monkey patches to the tested installation.

The actual committed skill changed from 17 files / 46,648 bytes in v1.0.0 to
42 files / 194,695 bytes in v1.1.0; SKILL.md changed from 3,500 to 4,714 characters.
Reference files are loaded on demand, so total package size does not measure
mandatory model context. The earlier eight-task artwork study remains an author
self-review, not a controlled external model experiment.

## Verification and limits

The release check runs source tests, 43 migration comparisons, the existing eight
authored examples, reproducible packaging and isolated Unicode-path execution.
CI adds Windows/Ubuntu Pillow 10.4, 11.3 and 12.1 alongside the 12.3 baseline.
Exact results and commit status accompany the release; configured CI is not itself
evidence that a job has passed.

Publication is atomic per file, with cooperating-writer reservations and rollback
for ordinary errors. It is not a durable multi-file transaction across crashes.
No-force publication requires filesystem hard-link support and otherwise fails
explicitly. Crash-left lock files require checking the owning process before
manual cleanup. No fonts or in-game behavior were evaluated in this patch.

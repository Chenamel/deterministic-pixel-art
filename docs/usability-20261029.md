# Post-LT03 usability changes

2026-10-29. Local development verified; installed v1.1.1 and frozen candidates remain intact. No new candidate, release or external trial packet was created.

Set `PIXELART_PORTABLE_OUTPUT=1` in the task process to share the portable-output choice across CLI and recipe commands. An explicit `--portable-output` or `--no-portable-output` wins; unset or `0` keeps the original default. Other values fail before writing. Read-only commands and the Python publication API ignore this setting. Portable visibility, no-overwrite, explicit force and rollback semantics remain unchanged. Separate agent shell sessions must receive the environment from their launcher.

The [conditional recovery guide](../skill-content/references/workflows.md#environment-and-output-recovery) now gives a short pip-free-venv path using an existing pip's `--python` option. A fresh target environment was installed and used for actual rendering; no global packages were replaced.

Validation: 131 source tests, 106 extracted-ZIP checks, the official Skill validator, 43 exact stable images and 357 protected-file hashes passed. The suite's old 60-second timeout was increased to 180 after an interrupted run; the complete suite passed in 74.381 seconds. Tests used Windows, Python 3.14.2 and Pillow 12.3.0; hard-link rejection was injected, and no new Linux/FUSE run is claimed.

The reproducible development ZIP has 98 files and grew by 1,080 bytes (0.46%). Twelve interleaved complete commands per arm measured medians of 243.2ms before, 253.5ms after with defaults, and 263.3ms with inherited portable output. These startup/IO-inclusive samples do not establish a speedup or a sustained slowdown. Output bytes match. Agent time/token benefits and aesthetic improvement were not measured.

See the [Chinese report](usability-20261029.zh-CN.md) and [machine results](measurements/usability-20261029.json). Four main stages remain: P1–P3 and P4a complete, native512 P4b deferred. This usability batch is complete; next prepare a scoped LT04 creative-use trial. Original release gates remain unchanged.

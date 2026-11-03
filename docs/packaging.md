# Building the standalone Skill

Run the development checks from a working checkout:

```sh
python -B tools/check.py
```

The packager retains the existing runtime/fixture quality gates. It reads runtime code from src/, recipes from recipes/, guidance from skill-content/, supported examples from examples/, quality images from docs/quality/, and the root license and requirements. The generated skill/ tree is an output, never an input.

Each build uses a new staging directory. It checks the exact generated file set, SHA-256 values, ZIP entries and CRC before publishing. Private AGENTS.md files, hidden paths and Python caches are excluded. Missing required entry/runtime files, conflicting destination names or changed inputs stop the build. Package paths must stay in the checkout and must not use symbolic links.

The published paths remain skill/deterministic-pixel-art/, evaluation/package-manifest.json and deterministic-pixel-art.zip. Identical inputs produce the same archive; an unchanged output does not need replacement. The manifest remains a mapping of package-relative paths to SHA-256 values.

## Preserved previous outputs

Before replacing a changed output, the tool moves its previous version into a new evaluation/package-backup-* directory. This includes hand-edited or obsolete files in a previous generated Skill. These files are preserved for recovery and are excluded from the new package. The success JSON returns the target and backup paths under previous_outputs; recovery.json inside that backup directory records the planned locations.

Sources are read-only throughout packaging. A copy, validation or ZIP-write failure leaves the published outputs untouched. For an ordinary publication failure, the tool attempts to restore previous outputs. If restoration also fails, recovery_backups in the error identifies the retained copies. A published output changed by another writer is left untouched.

Backups are not deleted automatically. Review their contents before removing ones you no longer need, and keep any unsaved work in authoritative sources. The packager's lock prevents cooperating packagers from running simultaneously; avoid editing its inputs or outputs during a build.

## Interruption limits

Publication spans a directory and two files, so it is not a crash-safe group transaction. A forced termination or power loss can leave partial publication, retained backups and a stale evaluation/.package_skill.lock. After confirming no packager is running, inspect the generated paths and recovery.json before recovering or retrying. The source directories remain separate from these output moves; storage or hardware failure is outside this tool's guarantees.

Packaging does not install a Skill, publish a release or upload to SkillHub. Platform adaptation remains a separate operation on a complete generated Skill.

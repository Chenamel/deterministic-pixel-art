# Deterministic Pixel Art for DSH

[简体中文](README.zh-CN.md)

Optional third-party DSH bundle carrying the original `deterministic-pixel-art`
Skill, references, editable examples, Python renderer and recipes. The Skill stays
available to both the user and model; a same-name local Skill can take precedence.
The renderer and the normal Skill installation remain usable independently.

## Install a local package

This package is not published to npm or listed in the DSH marketplace. Build a
local `.tgz` from a checkout with Python and the repository's development
requirements installed:

```sh
python -B tools/package_dsh.py --out dist/dsh-package
npm pack ./dist/dsh-package --ignore-scripts --pack-destination dist
dsh plugin --profile pixel-art add /absolute/path/to/dist/dsh-skill-deterministic-pixel-art-0.1.0.tgz
```

Choose an unused profile for a trial. These commands create or change that DSH
profile. In DSH NEXT, run `dsh` inside its DSH Terminal. The package output
directory must be new; the builder refuses to replace existing files. The npm
archive has no installation scripts. Its host peers are DSH Skill 0.2.2-rc.1 and
Cordis ~4.1.0; Node must be >=24.9.0. The initial `engines.dsh` range is exactly
0.2.2-rc.1. Other DSH versions are not claimed compatible.

Quote paths containing spaces, for example:
`dsh plugin --profile pixel-art add "C:/my packages/dsh-skill-deterministic-pixel-art-0.1.0.tgz"`.
If the Skill is absent, confirm that you launched the profile where the bundle
was installed, then inspect `dsh --profile pixel-art --dump-config` for
`deterministic-pixel-art-skill`. Resolve missing host peers or an unsupported DSH
version before trying a model task.

Platform validation uses DSH NEXT 2.0.22-next with core 0.2.2-rc.1 on Windows,
Node 24.21.0, Python 3.12.14 and Pillow 12.3.0. The repository's DSH check also
tests the packed provider against the real published Cordis and Skill services.
No model call is required for those checks.

## Use

Ask DSH to use `deterministic-pixel-art` to create or edit a PNG and keep its
editable JSON or Python source. Select Python 3.10+ with Pillow >=10.4,<13 using
DSH's workspace dependency tools; the fixed reproduction baseline is Pillow
12.3.0. Follow the Skill's absolute resource base for scripts and references,
write outputs in the workspace, and present the resulting PNG. Missing Python or
Pillow is a runtime prerequisite to resolve in the workspace, not a plugin
installation failure.

## Build, verify and publish status

`python -B tools/check_dsh.py` builds a fresh package, runs actual `npm pack`,
compares every packed Skill file with its authoritative input, checks Node
syntax, and exercises the real Skill registry and packaged PNG renderer. It
needs Node/npm and the repository's development requirements. Generated package
resources are not maintained in this directory: `tools/package_dsh.py` reuses
`tools/package_skill.py`'s source mapping from `skill-content/`, `src/`, `recipes/`
and the existing example assets.

Public installation still requires an npm name/version ownership check,
publication of the reviewed archive, and a separate DSH marketplace submission
under its current rules. No registry install command is promised before that.
DSH itself and its peers are not bundled; see NOTICE.md and LICENSE for sources
and licensing. This project is not endorsed by DeepSeek.

For native Skill installation instead, follow the repository's
[INSTALL.md](https://github.com/Chenamel/deterministic-pixel-art/blob/main/INSTALL.md).

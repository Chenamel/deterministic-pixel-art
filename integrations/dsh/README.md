# Deterministic Pixel Art for DSH

[简体中文](README.zh-CN.md)

Optional third-party DSH bundle carrying the original `deterministic-pixel-art`
Skill, references, editable examples, Python renderer and recipes. Users and
models can invoke it as needed; a same-name local Skill can take precedence.
This package is not published to npm or listed in the DSH marketplace.

## Build a local package

From a checkout with Python and the repository's development requirements:

```sh
python -B tools/package_dsh.py --out dist/dsh-package
npm pack ./dist/dsh-package --ignore-scripts --pack-destination dist
```

The package output directory must be new. The archive has no installation
scripts. Its initial compatibility range is DSH core **0.2.2-rc.1**, Node
**>=24.9.0**, DSH Skill **0.2.2-rc.1** and Cordis **~4.1.0**. Other DSH versions
are not claimed compatible.

## Try a new command-line profile

In DSH NEXT, run `dsh` inside **DSH Terminal**. Choose an unused profile name;
the examples use `pixel-art`. Initialize it **once, before installing**:
`--from-default-profile` replaces the target profile, including its plugins and
local configuration. Do not rerun that initialization to start another task.

```text
dsh --profile pixel-art --from-default-profile headless --help
dsh plugin --profile pixel-art add "/absolute/path/to/dsh-skill-deterministic-pixel-art-0.1.0.tgz"
```

Replace the archive path with the file built above; quote paths containing
spaces. The first command initializes the profile without a model call. These
commands affect `pixel-art`; they do not install into the Desktop profile.

The shipped `headless` template disables stored-account services. To use your
normal DeepSeek account sign-in, save this as `dsh-account.patch.yml` in your
task directory. It contains configuration, not a token:

```yaml
- id: agent-default-model
  config:
    provider: deepseek-account
    model: deepseek-flash
- id: credentials
  disabled: false
- id: authorization
  disabled: false
- id: deepseek-account
  disabled: false
```

Sign in through DSH's normal account UI using the same `DSH_HOME`; do not copy
credentials into this file. From the directory where you want the JSON and PNG,
start a new task:

```text
dsh --profile pixel-art --patch ./dsh-account.patch.yml --json --permission-mode workspace-write --approval-policy never "Use deterministic-pixel-art to make a 16x16 lantern PNG and keep editable JSON."
```

`--json` emits run events, including a new `sessionId`. To continue that session,
keep the same working directory and replace the example ID with the returned ID:

```text
dsh --profile pixel-art --patch ./dsh-account.patch.yml --json --permission-mode workspace-write --approval-policy never --session-id session-YOUR-ID "Make the outline darker."
```

The command selects `workspace-write`; enforcement depends on DSH and the
platform. `never` disables interactive approval requests, so operations needing
approval fail. Model tasks may consume
account balance. These examples do not set a monetary spending limit. If you
already use an API-key or another configured profile, keep its model setup and
install the bundle into that profile instead of applying the account overlay.

## Use and troubleshoot

Python **3.10+** and Pillow **>=10.4,<13** are required; Pillow **12.3.0** is the
fixed reproduction baseline. If `load_workspace_dependencies` is available, use
it to select an environment. Otherwise use the available shell to check Python
and Pillow. Missing prerequisites are a runtime issue; installing this bundle
does not run pip. Resolve scripts and references from the Skill's resource base,
and keep editable sources and PNG outputs in the task directory.

Use `present` when that tool exists. In the default headless profile, provide
absolute output paths instead. `read_image` lets the model inspect an image;
that call alone does not prove the image was delivered to the user. Desktop
profiles can have additional tools. Loading a Skill does not by itself create
or display a PNG.

If the Skill is absent, check that you launched the profile where it was
installed. `dsh --profile pixel-art --dump-config` should include
`deterministic-pixel-art-skill`. Resolve missing host peers or an unsupported DSH
version before a model task. `ACCOUNT_SIGN_IN_REQUIRED` means the account route
is unavailable: check the overlay, normal sign-in and `DSH_HOME`, rather than
reinstalling the Skill. A same-name local Skill can override the bundled one.

## Verification and publication

Platform validation uses Windows DSH NEXT **2.0.22-next**, core **0.2.2-rc.1**,
Node **24.21.0**, Python **3.12.14** and Pillow **12.3.0**. Run
`python -B tools/check_dsh.py` with Node/npm and development requirements to
build and check the actual archive, real Skill services and relocated renderer.
That check requires no model call.

`tools/package_dsh.py` reuses the authoritative inputs in `skill-content/`,
`src/`, `recipes/` and existing examples. Generated resources are not maintained
here; `skill-manifest.json` records their hashes. DSH and its peers are not
bundled. See LICENSE and NOTICE.md for licensing and sources.

Public installation still needs npm name/version ownership, publication of the
reviewed archive and a separate marketplace submission. This project is not
endorsed by DeepSeek. For native Skill installation, follow
[INSTALL.md](https://github.com/Chenamel/deterministic-pixel-art/blob/main/INSTALL.md).

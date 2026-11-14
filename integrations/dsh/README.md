# Deterministic Pixel Art for DSH

[简体中文](README.zh-CN.md)

Optional third-party DSH bundle carrying the original `deterministic-pixel-art`
Skill, references, editable examples, Python renderer and recipes. Users and
models can invoke it as needed; a same-name local Skill can take precedence.

## Already installed: start a conversation

Open a conversation in the same DSH profile where the plugin is installed and
enabled, then send:

> Use deterministic-pixel-art to make a 16×16 pixel lantern with a transparent background. Read the Skill and check the available Python/Pillow environment first. Deliver the PNG, editable JSON and an 8× nearest-neighbor preview, and inspect the finished image.

After receiving the image, you can continue:

> Change only the lantern's metal outline to dark brown. Keep the glass and everything else unchanged. Preserve the first version and deliver a separate revised PNG with its editable source.

You can also provide an existing PNG and describe the region to change, what to
preserve and the intended result. You do not need to learn commands or JSON first.
Provide references or explicit requirements for a particular game style.

Expect a native-size PNG and editable source. An enlarged preview alone is not
enough. Desktop tools can deliver files directly; command-line-only environments
should return absolute file paths.

## Installation and compatible versions

| Name | Purpose |
| --- | --- |
| Deterministic Pixel Art | Display name |
| `dsh-skill-deterministic-pixel-art` | npm package name |
| `deterministic-pixel-art` | Skill name to use in a conversation |

This directory targets bundle **0.1.2**, supporting DSH core and DSH Skill
**0.2.2-rc.1 through 0.2.2-rc.3**. Node must be **>=24.9.0** and Cordis
**~4.1.0**. Drawing requires Python **3.10+** and Pillow **>=10.4,<13**.
Earlier versions, future release candidates and stable releases are outside this
declaration. Desktop app and core versions differ; check the core with that
installation's `dsh --version`.

Use DSH's supported npm plugin installation method to install and enable the
package in the profile used for chat. CLI users with an existing working profile
can replace `YOUR-PROFILE` with its non-`desktop` profile name:

```text
dsh plugin --profile YOUR-PROFILE add dsh-skill-deterministic-pixel-art@0.1.2
```

If 0.1.2 is absent from the registry, it has not been published yet. Build a local
candidate using the [instructions below](#build-a-local-package); the old 0.1.0
package declares support for rc.1 only. The npm CLI does not manage Electron's
reserved `desktop` profile; use the desktop's plugin interface or bundled command.
npm installation does not require a marketplace listing.

## Optional: create a command-line profile

Skip this section if you already have a working profile. Use the official DSH CLI,
or run `dsh` inside **DSH Terminal** in DSH NEXT. Choose an unused profile name;
the examples use `pixel-art`. Initialize it **once, before installing**:
`--from-default-profile` replaces the target profile, including its plugins and
local configuration. Do not rerun that initialization to start another task.

```text
dsh --profile pixel-art --from-default-profile headless --help
```

This initializes the profile without a model call. Then choose **one** installation
method. When the official npm registry provides version **0.1.2**, use its exact
package version:

```text
dsh plugin --profile pixel-art add dsh-skill-deterministic-pixel-art@0.1.2
```

For a local candidate, build the archive using the instructions below and use its
absolute path instead; quote paths containing spaces:

```text
dsh plugin --profile pixel-art add "/absolute/path/to/dsh-skill-deterministic-pixel-art-0.1.2.tgz"
```

Both methods install into `pixel-art`; Desktop uses a separate profile.
npm installation does not require a DSH marketplace listing.

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

On Windows, `sandbox-local: windows-acl workspace grant failed` can stop shell
commands before Python starts. Try a separate task folder under your user
directory, where your account has full control, while keeping `workspace-write`.
If it persists, use DSH's sandbox diagnostics; reinstalling this bundle does not
repair host permissions.

## Verification and sources

Platform validation uses Windows DSH NEXT **2.0.22-next**, core **0.2.2-rc.1**,
Node **24.21.0**, Python **3.12.14** and Pillow **12.3.0**. Run
`python -B tools/check_dsh.py` with Node/npm and development requirements to
build and check the actual archive, real Skill services and relocated renderer.
That check requires no model call.
CI uses `--skill-version` to check the three matching service versions on Windows
and Ubuntu.

`tools/package_dsh.py` reuses the authoritative inputs in `skill-content/`,
`src/`, `recipes/` and existing examples. Generated resources are not maintained
here; `skill-manifest.json` records their hashes. DSH and its peers are not
bundled. See LICENSE and NOTICE.md for licensing and sources.

This project is not endorsed by DeepSeek. For native Skill installation, follow
[INSTALL.md](https://github.com/Chenamel/deterministic-pixel-art/blob/main/INSTALL.md).

## Build a local package

Only source development and local candidate acceptance need this section. From a
checkout with Python and the repository's development requirements:

```sh
python -B tools/package_dsh.py --out dist/dsh-package
npm pack ./dist/dsh-package --ignore-scripts --pack-destination dist
```

The package output directory must be new. The archive has no installation scripts;
ordinary use can install the npm package directly.

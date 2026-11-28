# Deterministic Pixel Art for DSH

[简体中文](README.zh-CN.md)

Chat naturally in DSH to create new hard-edged pixel art or edit only a selected part of an existing PNG. The plugin bundles the pixel rendering tools, examples, and guides so you do not need to write coordinates or Python code by hand.

## Quick start (once installed)

Open a conversation in the DSH profile where the plugin is enabled and try:

> Use deterministic-pixel-art to draw a 16×16 pixel lantern with a transparent background. Read the Skill and check Python/Pillow first. Return the native PNG, editable JSON, and an 8× zoomed preview, and inspect the result.

To tweak only part of the finished image:

> Change only the lantern's metal frame to dark brown, leaving the glass and everything else unchanged. Keep the original files and deliver the revised PNG and source.

You can also attach an existing PNG and say which area to change and which parts to keep untouched. Look for both the **native-size PNG** and its **editable source file** (zoomed previews alone are not enough).

## Install & requirements

| Field | Value |
| --- | --- |
| Display name | Deterministic Pixel Art |
| npm package | `dsh-skill-deterministic-pixel-art` |
| Skill name in chat | `deterministic-pixel-art` |
| Current plugin version | `0.1.6` (tested on DSH `0.2.2-rc.1`–`rc.5`, `0.2.3-alpha.1`) |
| Runtime prerequisites | Node **>=24.9.0**, Python **3.10+**, Pillow **>=10.4,<13** (pinned 12.3.0) |

Install **0.1.6** via DSH's plugin command into your chat profile (replace `YOUR-PROFILE` with a non-`desktop` profile name; desktop users should use the DSH desktop plugin manager or [GitHub Releases](https://github.com/Chenamel/deterministic-pixel-art/releases/latest)):

```text
dsh plugin --profile YOUR-PROFILE add dsh-skill-deterministic-pixel-art@0.1.6
```

> Bundle `0.1.3` only supported up to DSH `0.2.2-rc.3`; `0.1.5`+ (`0.1.6` current) uses open version ranges so newer DSH releases can install it directly without waiting for marketplace re-indexing.

## Optional: create a headless CLI profile

Skip this section if you already have a working DSH profile. Using `dsh` (or **DSH Terminal**), pick an unused profile name (e.g. `pixel-art`) and initialize it **once** before installing (`--from-default-profile` resets that profile):

```text
dsh --profile pixel-art --from-default-profile headless --help
```

Install the plugin from npm (or from a downloaded/local `.tgz` path):

```text
dsh plugin --profile pixel-art add dsh-skill-deterministic-pixel-art@0.1.6
```

```text
dsh plugin --profile pixel-art add "/absolute/path/to/dsh-skill-deterministic-pixel-art-0.1.6.tgz"
```

If you use a signed-in DeepSeek account instead of an API key, place `dsh-account.patch.yml` (config only—never put credentials in this file) in your task folder after signing in through DSH:

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

Start a task in the folder where you want outputs saved, then continue by reusing the printed `sessionId` (remove `--patch` if your profile already configures an API key):

```text
dsh --profile pixel-art --patch ./dsh-account.patch.yml --json --permission-mode workspace-write --approval-policy never "Use deterministic-pixel-art to make a 16x16 lantern PNG and keep editable JSON."
```

```text
dsh --profile pixel-art --patch ./dsh-account.patch.yml --json --permission-mode workspace-write --approval-policy never --session-id session-YOUR-ID "Make the outline darker."
```

*(Note: `--approval-policy never` fails any action that asks for approval, and running model tasks uses account quota/balance.)*

## Troubleshooting & technical details

- **Skill not loaded:** Check `dsh --profile pixel-art --dump-config` includes `deterministic-pixel-art-skill` and confirm you launched the same profile you installed into (note: a local Skill of the same name overrides the plugin bundle).
- **Missing Python/Pillow:** Installing the npm bundle does not install Python packages; make sure Python 3.10+ and Pillow are installed in the workspace environment (`load_workspace_dependencies` if available).
- **Account sign-in error (`ACCOUNT_SIGN_IN_REQUIRED`):** Verify DSH login, `DSH_HOME`, and the account patch; reinstalling the Skill will not fix sign-in state.
- **Windows ACL sandbox error (`windows-acl workspace grant failed`):** Move the task folder to a directory under your user folder where your account has full permissions and retry with `workspace-write`.
- **Want the standalone non-DSH Skill?** See [INSTALL.md](https://github.com/Chenamel/deterministic-pixel-art/blob/main/INSTALL.md).

<details>
<summary>Technical compatibility, audit notes & local packaging (for maintainers)</summary>

- **Host compatibility declaration:** Declares `engines.dsh: "*"` and wildcard peer ranges for DSH Skill registry and Cordis host services (resolved via pnpm inside DSH's plugin installer; plain npm with strict peer checks may reject prerelease peers matched by `*`).
- **Validated DSH host versions:** Windows/Ubuntu CI checks `0.2.2-rc.1` through `0.2.2-rc.5` and `0.2.3-alpha.1` (`python -B tools/check_dsh.py`). Windows dev baseline: DSH NEXT `2.0.22-next`, core `0.2.2-rc.1`, Node `24.21.0`, Python `3.12.14`, Pillow `12.3.0`. Note: an npm audit on 2026-11-15 flagged 7 upstream findings (`zod`, etc.) on DSH `rc.1` host deps and 0 on `rc.2`/`rc.3`.
- **Source provenance & local build:** `tools/package_dsh.py` builds the bundle from `skill-content/`, `src/`, `recipes/`, and examples without duplicating rendering code (`skill-manifest.json` records hashes; see `LICENSE` and `NOTICE.md`). Not endorsed by DeepSeek.

```sh
python -B tools/package_dsh.py --out dist/dsh-package
npm pack ./dist/dsh-package --ignore-scripts --pack-destination dist
```

</details>

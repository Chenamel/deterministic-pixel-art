# Install for an AI agent

Use this guide when asked to install deterministic-pixel-art. You need terminal/file access, Python 3.10+ and Pillow. Browsing the repository alone does not install the tool.

## 1. Choose the destination

Prefer a project-local install unless the user requests an all-projects install.

| Environment | Destination |
|---|---|
| Current Codex | `<project>/.agents/skills/deterministic-pixel-art`; user-wide: `~/.agents/skills/deterministic-pixel-art` |
| Another agent with Skill support | Its documented Skill directory; do not assume Codex paths |
| Cloud task or agent without Skill discovery | `<task>/tools/deterministic-pixel-art`; read its SKILL.md explicitly and invoke its scripts |

[Current Codex locations](https://developers.openai.com/codex/skills/) differ from older installations under `~/.codex/skills` or `$CODEX_HOME/skills`. If an existing copy is already discovered, reuse it or report its version; do not create a duplicate or overwrite it silently. Keep update backups outside the folders the agent scans for Skills, so it does not load both versions.

## 2. Get a stable package

Choose by the requested task. **v1.2.0** includes `render`, `preview`, `validate`, `review`, `import`, `inspect`, `replace-cell`, `verify`, `assemble` and editable recipes. Older **v1.1.1** installs offer only the first four commands. Do not report an install as ready for a task its command set cannot perform.

Read https://api.github.com/repos/Chenamel/deterministic-pixel-art/releases/latest and select the `deterministic-pixel-art-<tag>.zip` and `SHA256SUMS.txt` assets from that same release. This endpoint selects a published stable release, not a prerelease or the repository checkout. Follow the returned download URLs; do not guess a versioned filename.

Download to a temporary directory, check the ZIP SHA-256 against its exact entry in the manifest, then extract its single `deterministic-pixel-art` folder to the chosen destination. Reject a mismatch, unexpected paths outside that folder, or an existing destination. A same-release checksum detects corruption or mismatched downloads; it is not an independent publisher signature.

Use a repository checkout or prerelease only when requested. Copy the chosen ref's complete `skill/deterministic-pixel-art` folder to the destination, then follow steps 3–4. Do not copy `skill-content/`, which has no runtime. Record the resolved commit. If stable lacks a requested capability, explain the limit instead of silently selecting a development version.

## 3. Prepare Python

Reuse a compatible task environment, or create `<project>/.venv-pixel-art` with `python -m venv .venv-pixel-art`. Use that environment's Python for both installation and execution:

- Windows: `.venv-pixel-art/Scripts/python.exe`
- macOS/Linux: `.venv-pixel-art/bin/python`

In the following commands replace `<python>` with that executable and `<skill>` with the absolute installed folder; quote paths containing spaces. Install the package's own requirements, not a system-wide dependency:

```text
<python> -m pip install -r <skill>/requirements.txt
```

Do not require Python 3.14 specifically. If the current environment's Pillow is incompatible, use a task-local environment. If the mounted task directory cannot create a virtual environment, create it on local temporary storage. If pip/ensurepip is unavailable, use an available pip's `--python <venv-python>` to install into that environment, or report the blocker. Do not replace the operating system's Python.

## 4. Verify before reporting success

Read the installed SKILL.md, then run from the task directory, using a fresh output directory:

```text
<python> <skill>/scripts/pixel_art.py --help
<python> <skill>/scripts/pixel_art.py render --spec <skill>/assets/gem-16.json --out output/pixel-art-install-check/gem.png --preview output/pixel-art-install-check/gem-preview.png
```

Use Pillow to open and decode both outputs. Expect a 16×16 image and a 128×128 nearest-neighbor preview. If the mounted filesystem rejects hard links when creating output files and the installed version offers `--portable-output`, retry with that option; otherwise render to a local temporary directory. `--force` does not fix mount support. Use a new output directory on repeated checks.

Report the version/source, Skill folder, Python executable and verified PNG paths. Distinguish successful script execution from native Skill discovery: check the agent's Skill list when available; otherwise say discovery is unverified. Codex may need a restart if the Skill does not appear.

Also check `--help` for any commands required by the user's task. A successful sample render alone does not verify import, scoped editing or assembly support.

## Optional: existing Node.js users

The third-party [skills CLI](https://github.com/vercel-labs/skills) can install this repository's Skill without publishing this project to npm. It installs **the default-branch repository version**, which may differ from a stable release. It does not install Python or Pillow.

For a **fresh project-local Codex install**, with Node.js >=22.20 and no existing copy, this command was tested with skills 1.7.4:

```sh
npx --yes skills@1.7.4 add https://github.com/Chenamel/deterministic-pixel-art/tree/main/skill/deterministic-pixel-art --skill deterministic-pixel-art --agent codex --copy --yes
```

Use the full subdirectory URL: the repository also contains `skill-content/`, an authoring source without the runtime, which a repository-name-only install can select. Then complete steps 3–4 using `.agents/skills/deterministic-pixel-art`. Other supported agents use their own `--agent` identifier; check the CLI documentation. User-wide installation is an explicit choice (`--global`), not the default. Python-only environments should use the stable-package path above.

[Back to README](README.md) · [简体中文入口](README.zh-CN.md)

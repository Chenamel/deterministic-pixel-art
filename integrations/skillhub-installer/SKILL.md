---
name: deterministic-pixel-art
description: Install the complete Deterministic Pixel Art Skill from its verified GitHub stable release. The SkillHub listing is a text-only installer; it does not contain the Skill tools or image assets.
slug: deterministic-pixel-art
version: 1.3.0
displayName: Deterministic Pixel Art
summary: Install the complete pixel-art Skill and editable PNG tools from the verified GitHub release.
license: MIT
homepage: https://github.com/Chenamel/deterministic-pixel-art
tags: [pixel-art, image-editing, python, deterministic]
---

# Deterministic Pixel Art installer

This SkillHub listing installs the complete Skill from the official GitHub stable release. The listing itself contains only this guide and its installer; it does not include the image assets or Python tools.

Run the installer with Python 3.10 or newer:

```text
python install.py --destination ./skills/deterministic-pixel-art
```

The installer downloads the pinned v1.3.0 Skill ZIP, verifies its SHA-256 digest, checks archive paths, and extracts the complete `deterministic-pixel-art/` directory. The destination must not already exist. Python and Pillow requirements are documented in the installed Skill's `SKILL.md` and `requirements.txt`.

The full package and MIT license are available from the [GitHub v1.3.0 release](https://github.com/Chenamel/deterministic-pixel-art/releases/tag/v1.3.0). The release contains the complete assets and source files. This installer needs an Internet connection and does not replace an existing installation.

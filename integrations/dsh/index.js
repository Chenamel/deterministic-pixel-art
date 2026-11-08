import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { BUNDLED_SKILL_RANK } from "@deepseek-ai/dsh-skill";

const metadata = JSON.parse(
  await readFile(new URL("./generated/skill.json", import.meta.url), "utf8"),
);
const directory = new URL("./skills/deterministic-pixel-art/", import.meta.url);
const skillFile = new URL("SKILL.md", directory);
const resourceBase = { kind: "directory", path: fileURLToPath(directory) };
const candidate = {
  name: metadata.name,
  description: metadata.description,
  invocation: { modelInvocable: true, userInvocable: true },
  provider: "deterministic-pixel-art-bundle",
  source: "bundled",
  resourceBase,
  rank: BUNDLED_SKILL_RANK,
  locator: skillFile,
};

const provider = {
  name: candidate.provider,
  async list() {
    return [candidate];
  },
  async get(_candidate, options) {
    const raw = await readFile(skillFile, {
      encoding: "utf8",
      signal: options.signal,
    });
    const frontmatter = /^---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)/u.exec(raw);
    if (!frontmatter) throw new Error("Packaged Skill has no YAML frontmatter");
    return {
      name: candidate.name,
      description: candidate.description,
      invocation: candidate.invocation,
      provider: candidate.provider,
      source: candidate.source,
      resourceBase,
      content: raw.slice(frontmatter[0].length) +
        "\n\n## DSH runtime\n\n" +
        "Use load_workspace_dependencies to select Python 3.10+ and Pillow >=10.4,<13. " +
        "Keep editable sources and PNG outputs in the workspace; call present " +
        "to deliver the finished PNG and provide its file path.\n",
    };
  },
};

export const name = "skill-deterministic-pixel-art";
export const inject = ["skills"];

/** Register the original Skill with the host's lifecycle and precedence rules. */
export function apply(ctx) {
  ctx.skills.registerProvider(() => provider);
}

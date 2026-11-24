import assert from "node:assert/strict";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import test from "node:test";

const packagePath = process.env.DSH_ADAPTER_PACKAGE;
if (!packagePath) throw new Error("Set DSH_ADAPTER_PACKAGE to an unpacked package");
const requirePackage = createRequire(join(packagePath, "package.json"));
const { Context } = await import(pathToFileURL(requirePackage.resolve("@deepseek-ai/cordis")));
const { SkillRegistry } = await import(
  pathToFileURL(requirePackage.resolve("@deepseek-ai/dsh-skill"))
);
const adapter = await import(pathToFileURL(join(packagePath, "index.js")));
const filesystem = await import(
  pathToFileURL(requirePackage.resolve("@deepseek-ai/dsh-skill-filesystem"))
);

test("packed compatibility metadata admits DSH prerelease versions", () => {
  const { satisfies } = requirePackage("semver");
  const manifest = requirePackage("./package.json");
  assert.equal(manifest.engines.node, ">=24.9.0");
  assert.equal(manifest.engines.dsh, "*");
  assert.equal(manifest.peerDependencies["@deepseek-ai/cordis"], "*");
  assert.equal(manifest.peerDependencies["@deepseek-ai/dsh-skill"], "*");

  const dshVersions = [
    "0.0.1-rc.1",
    "0.2.2-rc.5",
    "0.2.3-alpha.2",
    "0.2.3-rc.100",
    "1.0.0-alpha.1",
  ];
  for (const version of dshVersions) {
    assert.ok(satisfies(version, manifest.engines.dsh, { includePrerelease: true }), version);
  }

  assert.equal(satisfies("0.2.3-alpha.2", "*"), false);
});

test("packed host peer ranges include the published DSH tuples", () => {
  const { satisfies } = requirePackage("semver");
  const manifest = requirePackage("./package.json");
  const skill = requirePackage("@deepseek-ai/dsh-skill/package.json");
  assert.ok(
    satisfies(skill.version, manifest.peerDependencies["@deepseek-ai/dsh-skill"], {
      includePrerelease: true,
    }),
    skill.version,
  );

  const hostTuples = [
    ["0.2.2-rc.5", "4.1.0"],
    ["0.2.3-alpha.2", "4.2.0-alpha.1"],
  ];
  for (const [skillVersion, cordisVersion] of hostTuples) {
    assert.ok(
      satisfies(skillVersion, manifest.peerDependencies["@deepseek-ai/dsh-skill"], {
        includePrerelease: true,
      }),
      skillVersion,
    );
    assert.ok(
      satisfies(cordisVersion, manifest.peerDependencies["@deepseek-ai/cordis"], {
        includePrerelease: true,
      }),
      cordisVersion,
    );
  }
});

test("packed Skill loads, yields to a local definition, and disposes", async () => {
  const ctx = new Context();
  await ctx.plugin(SkillRegistry);
  const mounted = await ctx.plugin(adapter);
  try {
    const summaries = await ctx.skills.list();
    assert.equal(summaries.length, 1);
    assert.equal(summaries[0].name, "deterministic-pixel-art");
    assert.deepEqual(summaries[0].invocation, {
      modelInvocable: true,
      userInvocable: true,
    });
    const skill = await ctx.skills.get("deterministic-pixel-art");
    assert.equal(skill.resourceBase.kind, "directory");
    assert.equal(skill.resourceBase.path, join(packagePath, "skills/deterministic-pixel-art/"));
    const raw = await readFile(join(skill.resourceBase.path, "SKILL.md"), "utf8");
    assert.ok(skill.content.includes(raw.slice(raw.indexOf("# Deterministic Pixel Art"))));
    assert.ok((await readFile(join(skill.resourceBase.path, "references/formats.md"), "utf8")).length > 0);
    assert.ok((await readFile(join(skill.resourceBase.path, "scripts/pixel_art.py"), "utf8")).length > 0);

    const localRoot = join(process.cwd(), "local-skills");
    const localSkill = join(localRoot, "deterministic-pixel-art");
    await mkdir(localSkill, { recursive: true });
    await writeFile(join(localSkill, "SKILL.md"),
      "---\nname: deterministic-pixel-art\ndescription: Local replacement\n---\nLocal instructions\n",
    );
    const local = await ctx.plugin(filesystem, {
      includeDefaultRoots: false,
      customSkillDirs: [localRoot],
      dshHome: join(process.cwd(), "empty-dsh-home"),
      agentsHome: join(process.cwd(), "empty-agents-home"),
      watch: false,
    });
    assert.equal((await ctx.skills.get("deterministic-pixel-art")).content, "Local instructions");
    await local.dispose();
    assert.equal((await ctx.skills.get("deterministic-pixel-art")).provider, summaries[0].provider);
    await mounted.dispose();
    assert.deepEqual(await ctx.skills.list(), []);
  } finally {
    await ctx.fiber.dispose();
  }
});

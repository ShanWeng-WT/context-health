# Agent-context audit -- D:/Projects/open-slide

Read-only audit. Nothing in the target repo was created, edited, moved or deleted.
Audited at commit `7384649` on `main`; working tree otherwise clean apart from two untracked items noted below.

---

## TL;DR

Your instinct is right, but the problem is not the one you are expecting. There are only **four** hand-written agent-instruction files in the repo, and they are individually decent. The mess is elsewhere:

1. **On this Windows checkout the whole agent-context system is inert.** `CLAUDE.md` and all 13 `.claude/skills/*` entries are committed git symlinks, and `core.symlinks=false`. They materialised as tiny plain-text files containing their target path. Claude Code launched at the repo root reads a 9-byte `CLAUDE.md` whose entire content is the literal string `AGENTS.md`, and finds zero loadable skills.
2. **The repo's own five skills are undiscoverable from the repo root.** They live under `apps/demo/.claude/skills/` and `packages/cli/template/.claude/skills/`. A session started at the monorepo root sees only the nine vendored third-party design/React skills in `/.claude/skills/`.
3. **Third-party vendored context outweighs your own by 4.4x** -- 54,681 words / 730 KB in `.agents/skills/` versus 12,512 words / 104 KB in `packages/core/skills/`.
4. **Two untracked, un-ignored items sit one `git add -A` away from a public repo**, one of which is an internal corporate PowerPoint template.
5. **`AGENTS.md` and `CONTRIBUTING.md` are roughly 80% duplicated prose**, including verbatim tables and examples, with no single source of truth.

---

## Inventory

### Hand-written agent instructions (4 files: 2 real, 2 symlinks)

| Path | Size | Notes |
| --- | --- | --- |
| `D:/Projects/open-slide/AGENTS.md` | 3,149 B / 466 w | Framework-repo guide. Real content. |
| `D:/Projects/open-slide/CLAUDE.md` | symlink -> `AGENTS.md` | 9-byte text stub on this checkout. |
| `D:/Projects/open-slide/packages/cli/template/AGENTS.md` | 2,055 B / 294 w | Ships to end users via `npx @open-slide/cli init`. Good: short, hard rules only. |
| `D:/Projects/open-slide/packages/cli/template/CLAUDE.md` | symlink -> `AGENTS.md` | 9-byte text stub on this checkout. |

### Foreign files *named* `AGENTS.md` (2 files, 131 KB)

| Path | Size |
| --- | --- |
| `D:/Projects/open-slide/.agents/skills/vercel-react-best-practices/AGENTS.md` | 108,261 B / 13,174 w |
| `D:/Projects/open-slide/.agents/skills/vercel-composition-patterns/AGENTS.md` | 22,627 B / 2,506 w |

Both are **generated build artifacts** of their own `rules/` directories -- their upstream README says so explicitly (`.agents/skills/vercel-react-best-practices/README.md:13` lists `AGENTS.md` as "Compiled output (generated)"). They duplicate 299 KB of `rules/*.md` that is already vendored alongside them.

### Skills

| Location | Count | Size | Ownership |
| --- | --- | --- | --- |
| `packages/core/skills/` | 5 | 104 KB / 12,512 w | Yours. Canonical, shipped in the npm tarball. |
| `.agents/skills/` | 8 | 730 KB / 54,681 w | Vendored third-party (Vercel, shadcn, Emil Kowalski, Anthropic). |
| `.claude/skills/` | 8 symlinks + `pptx/` | 1.3 MB | Symlinks into `.agents/skills/`, plus one untracked directory. |
| `apps/demo/.claude` + `.agents/skills/` | 5 + 5 symlinks | -- | Double-hop symlinks into `packages/core/skills/`. |
| `packages/cli/template/.claude/skills/` | 5 symlinks | -- | **Dangling**; see finding 6. |

---

## Findings, worst first

### 1. Everything symlink-based is broken on this checkout (severity: high)

`git config core.symlinks` returns `false`. `git ls-files -s` reports 26 entries with mode `120000`. Every one of them is currently a plain text file whose content is the relative path it was supposed to point at.

Concretely, right now on disk:

- `CLAUDE.md` contains exactly `AGENTS.md` -- 9 bytes, no `@` prefix, so Claude Code does not treat it as an import. It is a nine-byte instruction file that says nothing.
- `.claude/skills/apple-design` is a 33-byte *file* containing `../../.agents/skills/apple-design`, not a directory. Same for the other seven. No valid skill is discovered at the repo root.

The irony: `packages/cli/src/init.ts:47-55` already implements the correct pattern -- a `linkOrCopy` helper that copies instead of symlinking when `process.platform === "win32"`. The product you ship handles Windows; the repo you develop in does not.

**Recommendation.** Either (a) set `git config core.symlinks true` and re-checkout, which needs Developer Mode or elevation on Windows, or (b) stop committing `CLAUDE.md` as a symlink and commit a one-line real file containing `@AGENTS.md`. The import syntax gives you the same single source of truth with zero platform dependency, and (b) fixes it for every Windows contributor, not just you. Note `CONTRIBUTING.md` currently says "A Unix-y shell. Windows works via WSL" -- that is the documented escape hatch, but it is not what you are actually doing.

### 2. The repo's own skills are invisible from the repo root (severity: high)

Project skills are discovered from `<project-root>/.claude/skills/`. At `D:/Projects/open-slide` that directory contains: `apple-design`, `emil-design-eng`, `frontend-design`, `review-animations`, `shadcn`, `vercel-composition-patterns`, `vercel-react-best-practices`, `web-design-guidelines`, `pptx`.

It does **not** contain `create-slide`, `slide-authoring`, `apply-comments`, `create-theme`, or `current-slide`. Those are only reachable if you `cd apps/demo` first.

`AGENTS.md:5` acknowledges this in prose -- "Slide-authoring guidance lives in the `slide-authoring` / `create-slide` skills under `apps/demo/.claude/skills/`" -- but prose is not discovery. From a root session the agent is told a skill exists that it cannot invoke by name.

**Recommendation.** Symlink or copy the five core skills into the root `.claude/skills/` as well, so a root-launched session can invoke them. They are the only skills in this repo that encode knowledge nobody else has.

### 3. Untracked cruft, including an internal corporate asset (severity: high -- confidentiality)

`git status --porcelain` in the target repo returns exactly two entries:

- `?? .claude/skills/pptx/`
- `?? Wanin_<chinese-named>.pptx` at the repo root (6.2 MB)

Neither is matched by `.gitignore` (verified with `git check-ignore`). This is a public repository (`github.com/1weiho/open-slide`). The `.pptx` is a **Wanin corporate template** -- an internal company asset that does not belong in an OSS repo under someone else's copyright. `.claude/skills/pptx/` is 1.3 MB of the Anthropic pptx skill, whose own frontmatter declares `license: Proprietary. LICENSE.txt has complete terms`, vendored into an MIT-licensed repo.

**Recommendation.** Delete both from the working tree, or add them to `.gitignore`. Do not commit either. The `pptx` skill is already available in your Claude Code install as `anthropic-skills:pptx`, so vendoring it here adds nothing but licence risk.

### 4. The `pptx` skill will hijack every slide request in this repo (severity: high)

The description in `.claude/skills/pptx/SKILL.md` says it should trigger whenever the user mentions "deck," "slides," "presentation," or references a `.pptx` or `.potx` filename, "regardless of what they plan to do with the content afterward."

This is a repo whose entire domain is decks, slides and presentations. That description is a 756-character trigger magnet -- the largest always-on description in the repo -- and it will fire ahead of `create-slide` (420 chars) and `slide-authoring` (632 chars) on essentially every authoring request, routing the agent into "write a pptxgenjs script" instead of "write a React page under `slides/<id>/`".

**Recommendation.** Remove `.claude/skills/pptx/` from this repo; finding 3 covers the same file. If you genuinely need PPTX export work here, invoke the global skill explicitly rather than installing a competing trigger next to your own.

### 5. AGENTS.md and CONTRIBUTING.md are near-duplicates that will drift (severity: medium)

Duplicated between `D:/Projects/open-slide/AGENTS.md` and `D:/Projects/open-slide/CONTRIBUTING.md`:

- the four-row repo-layout table (verbatim; only the `apps/demo` cell differs by a few words)
- the six-line `pnpm dev / build / typecheck / check / check:fix / test` script block (verbatim)
- the `pnpm core <script>` / `pnpm cli <script>` filter note
- the changeset patch/minor/major rules
- the changeset description guidance, **including the identical Good/Bad example** ("Replace spinner with a hairline + sliding bar...")
- the "do not hand-edit CHANGELOG.md" rule
- the "no casual dependencies" rule
- the "default to writing no comments" rule
- the "leave packages/core/src/app/components/ui alone" rule
- the `pnpm release` description

That is roughly 80% of `AGENTS.md`. Two copies of the same rules in two files means the next edit updates one of them.

**Recommendation.** Make `CONTRIBUTING.md` the human source of truth and cut `AGENTS.md` down to the delta an agent needs that a human contributor does not, plus a pointer. What is worth keeping agent-side is the *navigation* material in finding 8, not policy prose a human contributor already has.

### 6. The CLI template ships dangling symlinks, and its Windows fallback is dead code (severity: medium)

`.gitignore:8` ignores `packages/cli/template/.agents/skills`. But the five entries in `packages/cli/template/.claude/skills/` **are** committed, and they point at `../../.agents/skills/<name>` -- i.e. into the ignored directory. In a fresh clone, before `pnpm --filter @open-slide/cli build` runs `scripts/sync-template-skills.mjs`, those five symlinks dangle. `packages/cli/template/.agents` does not exist in this checkout right now.

Separately, `packages/cli/src/init.ts:58-61`:

    const claudeMd = join(target, 'CLAUDE.md');
    if (!existsSync(claudeMd) && existsSync(join(target, 'AGENTS.md'))) {
      await linkOrCopy('AGENTS.md', claudeMd);
    }

The template always ships a `CLAUDE.md` (it is committed), and `cp(TEMPLATE_DIR, target, { recursive: true })` runs immediately before this. So `existsSync(claudeMd)` is always true and the branch never executes. On a Windows-built or Windows-checked-out template that means the scaffolded project gets a `CLAUDE.md` containing the literal text `AGENTS.md` -- exactly the bug `linkOrCopy` was written to prevent. The docs already promise otherwise: `apps/web/content/docs/skills/overview.mdx:53` says "CLAUDE.md is a symlink to it (a copy on Windows)".

**Recommendation.** Stop committing `packages/cli/template/CLAUDE.md` and `packages/cli/template/.claude/skills/*` -- `materializeTemplateLinks` recreates both at init time anyway. Add them to `.gitignore` next to the existing `.agents/skills` line. That makes the fallback live and removes the dangling links. Worth a scaffold-on-Windows test either way.

### 7. skills-lock.json is an orphan (severity: medium)

`D:/Projects/open-slide/skills-lock.json` (1,786 B) pins eight vendored skills by source repo and SHA-256. Nothing in the repo reads it: grepping for `skills-lock` across the entire tree (excluding `node_modules`) returns **zero** hits -- no script, no source file, no CI job, no doc. It was written by an external skills-manager tool that is not recorded anywhere, so nobody reading this repo can tell how to refresh or verify those hashes.

Worse, the pinning is partly illusory. `.agents/skills/web-design-guidelines/SKILL.md` is a 4 KB wrapper whose entire content is: fetch `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md` before each review and apply all rules from the fetched content. The lockfile hashes the wrapper; the actual rules are unpinned remote content fetched at runtime and treated as instructions.

**Recommendation.** Either document the tool that owns `skills-lock.json` in `AGENTS.md` and add a CI check that the hashes still match, or delete the lockfile and treat `.agents/skills/` as ordinary vendored source. Consider dropping `web-design-guidelines` entirely -- a skill that is a fetch-and-obey stub gives you no reproducibility and an untrusted-instruction ingestion path.

### 8. AGENTS.md omits the facts an agent actually needs (severity: medium)

What it currently spends its 466 words on: repo layout, script list, changeset policy, comment policy. Most of that is also in `CONTRIBUTING.md` (finding 5). What it never mentions:

- **The React version split.** `packages/core` and `apps/demo` are React **18.3.1** + Vite. `apps/web` is React **19.2.7** + Next **16.2.12**. This is the single most load-bearing fact in the repo for anyone writing components, and it is nowhere in the agent context. (`forwardRef` appears 0 times in `packages/core/src`, despite React 18.)
- **`packages/core/skills/` is the canonical home of the five shipped skills**, mirrored into the CLI template at build time by `packages/cli/scripts/sync-template-skills.mjs`. Because `apps/demo/.claude/skills/*` -> `apps/demo/.agents/skills/*` -> `packages/core/skills/*` is a two-hop symlink, an agent that "tweaks a demo skill" is silently editing the published package. Nothing warns it.
- **`apps/web/content/docs/skills/*.mdx` mirrors the five skills** and will drift when a skill changes. Six MDX files, no sync mechanism.
- **e2e tests exist and gate CI.** `.github/workflows/ci.yml` has a fourth job running `pnpm test:e2e` (Playwright, pinned container `v1.62.1-noble`). The `AGENTS.md` workflow block lists `pnpm test` and stops, so an agent following it will believe it is green and be surprised by CI.
- **Node 22.** CI pins `node-version: 22` and `CONTRIBUTING.md` says "Node.js 22+ (matches CI)", while both packages declare `"engines": { "node": ">=18" }`. `AGENTS.md` says nothing.
- **What CI actually runs.** CI runs `pnpm format:check` and `pnpm lint` as separate steps -- it never runs `pnpm check`. `AGENTS.md` says to run `pnpm check` because "CI and the user's review both expect a clean tree", which is a superset, so following it is safe. But the assist/organizeImports action that `pnpm check:fix` applies is not verified by CI at all.

### 9. Vendored skill corpus: heavy, overlapping, partly off-target (severity: medium)

730 KB / 54,681 words across eight skills:

| Skill | Size | Assessment |
| --- | --- | --- |
| `vercel-react-best-practices` | 423 KB | 72 rule files plus a 108 KB generated `AGENTS.md` duplicating them. Heavily Next.js/RSC-oriented (server actions, `after()`, RSC prop serialisation) -- applies to `apps/web` only, which is one private marketing site. |
| `shadcn` | 129 KB | Includes `evals/evals.json`, two PNGs, and `agents/openai.yml` (a config for a different agent runtime). Its `allowed-tools` permits `Bash(npx shadcn@latest *)`, which includes `add` -- writing into `packages/core/src/app/components/ui`, the exact directory `AGENTS.md` says to leave alone. Its SKILL.md also embeds a command substitution that runs `npx shadcn@latest info --json` on load. |
| `vercel-composition-patterns` | 78 KB | 10 rule files plus a 22 KB generated `AGENTS.md` duplicating them. |
| `emil-design-eng` | 28 KB | Opens with an "Initial Response" block instructing the agent to reply with a promotional link to animations.dev and "Do not provide any other information until the user asks a question." |
| `apple-design` | 24 KB | Overlaps `emil-design-eng` heavily on springs, motion and interruptible transitions. |
| `frontend-design` | 20 KB | Vendored copy of the Anthropic skill, which is already available in your Claude Code install as `frontend-design:frontend-design`. Pure duplication. |
| `review-animations` | 20 KB | Same source author as `emil-design-eng`; `disable-model-invocation: true`, so user-invoked only. |
| `web-design-guidelines` | 4 KB | Network fetch stub -- see finding 7. |

Trigger overlap is real: `apple-design`, `emil-design-eng`, `review-animations`, `frontend-design` and `web-design-guidelines` all claim UI/design/motion territory with no stated precedence, and three of them cover animation specifically. Nothing in `AGENTS.md` tells an agent which to reach for, or that they exist at all.

Also worth noting: `vercel-react-best-practices/SKILL.md` claims "70 rules across 8 categories" while its own compiled `AGENTS.md` abstract says "40+ rules" -- the vendored copy is internally inconsistent.

**Recommendation.** Delete the two generated `.agents/skills/vercel-*/AGENTS.md` files (`rules/` is the source and is already present -- this alone removes 131 KB and stops them polluting every `AGENTS.md` search and any directory-scoped auto-load). Delete `frontend-design` as a duplicate of a globally installed skill. Pick one animation skill of the three. Prune the shadcn skill's `evals/`, `assets/` and `agents/openai.yml`. Then add a short "which design skill when" table to `AGENTS.md` for whatever survives.

### 10. Broken and mis-aimed cross-references (severity: low)

- `apps/demo/README.md:38` -- "See [CLAUDE.md](./CLAUDE.md) for the full authoring guide." `apps/demo/CLAUDE.md` **does not exist**. Broken link.
- `README.md:72` -- in a paragraph about *the scaffolded workspace*, "See [CLAUDE.md](CLAUDE.md) for the hard rules." Root `CLAUDE.md` resolves to the **framework-repo** guide (monorepo layout, changesets, biome), not the slide-authoring rules the sentence promises. It should point at `packages/cli/template/AGENTS.md` or `/docs/skills/overview`.
- `packages/cli/README.md:20` lists only "CLAUDE.md -- agent guide for authoring slides" in the scaffold output, while `apps/web/content/docs/skills/overview.mdx:52` states that `AGENTS.md` is the canonical rules file. Inconsistent framing of which file is primary.

### 11. apps/demo and apps/web have no scoped context (severity: low)

Neither has an `AGENTS.md`. An agent editing `apps/demo/slides/<id>/index.tsx` inherits only the root framework guide ("You are working on the **open-slide framework**") and never sees the slide-authoring hard rules that `packages/cli/template/AGENTS.md` gives to *end users* doing the identical task -- do not touch `package.json` or `open-slide.config.ts`, do not add dependencies, assets under `slides/<id>/assets/`. Your own dogfood app is held to a looser contract than your users.

Likewise `apps/web` is the only React 19 / Next 16 / fumadocs surface in the repo and has no scoped note saying so.

**Recommendation.** A ~15-line `apps/demo/AGENTS.md` pointing at the slide-authoring skills, and a ~10-line `apps/web/AGENTS.md` stating the React 19 / Next 16 / fumadocs stack and the docs-mirror obligation from finding 8.

### 12. Template pins a stale core version (severity: low)

`packages/cli/template/package.json` declares `"@open-slide/core": "^0.0.6"`. Current core is `1.18.0`. This is harmless at runtime -- `init.ts` rewrites it via `coreVersionRange()` from `__CORE_VERSION_AT_BUILD__` -- but it is actively misleading to anyone, human or agent, reading the template directly, and it would be the real pin if that rewrite ever regressed.

---

## Suggested order of work

| # | Action | Effort | Payoff |
| --- | --- | --- | --- |
| 1 | Remove the Wanin `.pptx` and `.claude/skills/pptx/` from the working tree, or gitignore them | 2 min | Closes a confidentiality and licence exposure, and removes the trigger hijack (findings 3, 4) |
| 2 | Replace the `CLAUDE.md` symlinks with real files containing `@AGENTS.md` | 10 min | Makes the whole system work on Windows (finding 1) |
| 3 | Delete the two generated `.agents/skills/vercel-*/AGENTS.md` | 2 min | -131 KB; stops false `AGENTS.md` hits and directory auto-load risk (finding 9) |
| 4 | Add the five core skills to the root `.claude/skills/` | 15 min | Your own skills become invocable at the root (finding 2) |
| 5 | Rewrite `AGENTS.md` as delta plus navigation; delegate policy to `CONTRIBUTING.md` | 45 min | Kills the 80% duplication and adds the React-split, skill-provenance and e2e facts (findings 5, 8) |
| 6 | Gitignore `packages/cli/template/CLAUDE.md` and `.claude/skills/`; verify a Windows scaffold | 30 min | Removes dangling links, revives the dead fallback (finding 6) |
| 7 | Prune the vendored skill set; document what survives and why | 1-2 h | -300 KB or more; resolves trigger overlap (finding 9) |
| 8 | Decide the fate of `skills-lock.json` -- document plus CI check, or delete | 30 min | Removes an unexplained orphan (finding 7) |
| 9 | Fix the three cross-references; add `apps/demo` and `apps/web` scoped files | 30 min | Findings 10, 11 |
| 10 | Refresh the stale `@open-slide/core` pin in the template | 1 min | Finding 12 |

---

## What is genuinely good

Worth saying, because it should survive the cleanup:

- `packages/cli/template/AGENTS.md` is a model agent file: 294 words, hard rules only, an explicit routing table for which skill to use, an explicit update path, and it closes with "Keep this file short: hard rules only. All deeper guidance lives in the skills above."
- The five skills in `packages/core/skills/` have real, non-overlapping descriptions with concrete trigger phrases, an explicit hub-and-spoke relationship (`slide-authoring` is the reference; `create-slide` and `apply-comments` own workflows and defer to it), and `slide-authoring` correctly pushes detail into `references/*.md` rather than inflating its own body. `current-slide` even instructs re-reading `current.json` every turn to avoid stale-cursor bugs, which is a genuinely sharp piece of context engineering. Verified against the code: `packages/core/src/vite/current-plugin.ts:69-70` writes exactly that path.
- Having one canonical skill source (`packages/core/skills/`) mirrored into the template by a build script, rather than hand-copied, is the right architecture. It is only the symlink presentation layer on top of it that is fragile.

---

## Method

- Enumerated every `CLAUDE.md`, `AGENTS.md`, `SKILL.md`, `.cursorrules`, `.mdc`, `GEMINI.md` and `copilot-instructions.md` in the tree, excluding `node_modules` and `.git`.
- Cross-checked `git ls-files -s` for mode `120000` entries against the working tree to establish the symlink breakage.
- Verified every factual claim in the root `AGENTS.md` against `package.json`, `biome.json`, `turbo.json`, `.github/workflows/ci.yml` and the source tree. The claims it does make are accurate, including the `packages/core/src/app/components/ui` exclusion, which matches the `files.includes` entry in `biome.json`. The problem is omission, not error.
- Spot-checked skill claims against implementation: the `current.json` path (`packages/core/src/vite/current-plugin.ts:69-70`), theme demo pairing (`packages/core/src/vite/themes-plugin.ts:72`), and the `sync:skills` command (`packages/core/src/cli/run.ts:137`).
- No file in `D:/Projects/open-slide` was modified.

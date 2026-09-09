# Context health — open-slide — 2026-09-08

Audited read-only at `D:/Projects/open-slide` (branch `main`, `9f53df7`). No files in that repo were created, edited or moved.

**Headline:** the instruction files themselves are in unusually good shape — short, current, well-scoped, and the product docs even document the Windows edge case correctly. The problem is not that the CLAUDE.md / AGENTS.md situation got fat. It is that **on this checkout almost none of it is loading at all**, and the one thing that *is* loading is a skill that should not be there.

---

## Always-on cost

| Tokens | % of 200k window | File | Kind |
|---:|---:|---|---|
| 1,081 | 0.54% | `(skill listing)` | skill name + description lines |
| 2 | 0.00% | `CLAUDE.md` | project memory — **DEAD**, unmaterialized symlink |
| **1,083** | **0.54%** | **ALWAYS-ON TOTAL** | |

On-demand context: ~90,489 tokens across 38 files. Nothing loads until reached for.

Two corrections the raw ledger does not make, both material:

- Of the 1,081-token skill listing, only **~186 tokens are repo-owned** (`.claude/skills/pptx`). The remainder is your personal `~/.claude/skills/` and follows you into every repo.
- The repo's *intended* always-on contribution — 47 lines of `AGENTS.md` via `CLAUDE.md`, plus 13 project skills — is currently **0 tokens**. See P1-1.

**Is 0.54% defensible?** As a number, yes — it is one of the leanest always-on tiers I could audit. But the number is low for the wrong reason. A healthy version of this repo would land near **~1,400 always-on tokens** (~800 for `AGENTS.md`, ~630 for a 13-skill listing) and that would still be excellent. You are not over budget. You are under-loaded.

---

## Findings

### P1-1 — `core.symlinks=false` silently voids `CLAUDE.md` and all 13 project skills · `CLAUDE.md:1` · Misleading × always-on · confidence **high**

**Quoted** — the entire content of `CLAUDE.md`, all 9 bytes of it:

```
AGENTS.md
```

**Evidence:**

```bash
$ git -C D:/Projects/open-slide config core.symlinks
false

$ git ls-files -s CLAUDE.md
120000 47dc3e3d863cfb5727b87d785d09abf9743c0a72 0    CLAUDE.md

$ file CLAUDE.md
CLAUDE.md: ASCII text, with no line terminators
```

Git has `CLAUDE.md` recorded as a symlink (mode `120000`) to `AGENTS.md`. With `core.symlinks=false`, git materializes every symlink as a **plain text file whose body is the link target string**. Twenty-five symlinks in this repo are affected:

```bash
$ git ls-files -s | awk '$1=="120000"{print $4}'
CLAUDE.md
packages/cli/template/CLAUDE.md
.claude/skills/{apple-design,emil-design-eng,frontend-design,review-animations,
                shadcn,vercel-composition-patterns,vercel-react-best-practices,
                web-design-guidelines}
apps/demo/.claude/skills/{apply-comments,create-slide,create-theme,current-slide,slide-authoring}
apps/demo/.agents/skills/{...same five...}
packages/cli/template/.claude/skills/{...same five...}
```

```bash
$ ls -la .claude/skills/
-rw-r--r-- 33 apple-design        # 33-byte text file, not a directory
-rw-r--r-- 36 emil-design-eng
...
drwxr-xr-x    pptx                # the only real directory
```

**Why it hurts the agent:** Every session on this machine starts with `CLAUDE.md` contributing the literal string `AGENTS.md` and nothing else. The agent never sees "add a changeset when `packages/core` changes", never sees "leave `packages/core/src/app/components/ui` alone", never sees "default to writing no comments", never sees the changeset tone examples. It does not fail loudly — it just quietly behaves like a repo with no instructions, while `git status` stays clean and everyone assumes the guidance is loaded. The same mechanism kills all 8 vendored design skills and all 5 slide skills: `.claude/skills/apple-design` is a 33-byte file, not a directory containing a `SKILL.md`, so Claude Code discovers nothing there.

This is almost certainly the "getting quietly worse over months" you are feeling. It is not context rot. It is context absence.

**Recommend** — the repo already solves this problem for *your users* and not for *itself*. `packages/cli/src/init.ts:48-55` has a `linkOrCopy()` that copies instead of symlinking on Windows, and `apps/web/content/docs/skills/overview.mdx:53` correctly documents "`CLAUDE.md` is a symlink to it (a copy on Windows)". Two options, in order of preference:

1. **Replace the `CLAUDE.md` symlink with a real one-line file** containing `@AGENTS.md`. Claude Code's `@import` resolves at launch on every platform, costs ~3 tokens, and needs no git or OS configuration. This is the portable fix and the one I would take.
2. For the skill symlinks (where `@import` does not apply), either set `git config core.symlinks true` plus Windows Developer Mode, or add a `postinstall` that runs the same `linkOrCopy` logic `init.ts` already ships. A `pnpm install` on Windows currently leaves a contributor with zero working project skills and no warning.

Token delta: `2 → ~800` always-on (`AGENTS.md` finally loads), plus ~630 for a real skill listing. That is an *increase*, and it is the right direction here.

---

### P1-2 — the only project skill that loads is an untracked PowerPoint skill that hijacks this repo's core vocabulary · `.claude/skills/pptx/SKILL.md:3` · Conflicting × always-on · confidence **high**

**Quoted** (`.claude/skills/pptx/SKILL.md`, frontmatter `description`):

> "Use this skill any time a .pptx or .potx file is involved in any way … Trigger whenever the user mentions "deck," "slides," "presentation," or references a .pptx or .potx filename, regardless of what they plan to do with the content afterward."

Against `packages/core/skills/create-slide/SKILL.md:3`:

> "Triggers on phrases like "make slides about X", "make a deck about X", "create a presentation" …"

**Evidence:**

```bash
$ git status --short
?? .claude/skills/pptx/
?? Wanin_...pptx                  # 6 MB, CJK filename, repo root

$ git ls-files .claude/skills/pptx          # empty — untracked
$ grep -c pptx skills-lock.json              # 0 — not managed by the skill lockfile
$ git check-ignore -v .claude/skills/pptx/SKILL.md   # no match — not ignored either
```

**Why it hurts the agent:** two distinct harms.

1. **Trigger collision.** `pptx` claims "deck", "slides", "presentation" — the exact three words this framework is built around. The README's own pitch is *"make slides about X"* (`README.md:25`). Right now `create-slide` is not loaded at all (P1-1), so `pptx` wins that phrase **uncontested**: ask this repo to "make a deck about X" and the agent's best available match is a skill that unzips XML and writes `pptxgenjs` scripts. Even after P1-1 is fixed, these two descriptions compete on identical phrasing and the agent will pick between them arbitrarily.
2. **It is local, uncommitted, and invisible to the team.** It is untracked *and* unignored, so it sits in `git status` waiting to be swept into a `git add .` and shipped to everyone. The 6 MB `.pptx` beside it in the repo root is the same story — a one-off task's working files that never got cleaned up.

**Recommend:** remove `.claude/skills/pptx/` and the stray `.pptx` from the repo root. If you use the pptx skill regularly, install it at `~/.claude/skills/pptx/` where it belongs — it is a personal tool, not a property of open-slide, and it should not shadow `create-slide` for anyone who clones this. Token delta: `~186 → 0` always-on, and the trigger collision goes to zero. If you would rather keep it in-repo, it needs a scoping clause in its description ("…except in this workspace, where slide authoring goes through `create-slide`") — but moving it out is cleaner.

---

### P2-1 — `AGENTS.md` and `CONTRIBUTING.md` are near-duplicates that have drifted, and the agent-facing copy lost the CI gate · `AGENTS.md:33-43` vs `CONTRIBUTING.md:67-104` · Conflicting × always-on (Codex/Cursor) · confidence **high**

**Evidence** — seven lines are byte-identical after normalization, and the surrounding paragraphs are near-identical restatements (layout table, changeset bump table, changeset tone with the *same* Good/Bad spinner example, the no-casual-deps rule, the comments rule, the `components/ui` rule, the releases line):

```
AGENTS.md:23 == CONTRIBUTING.md:52   pnpm dev        # turbo: runs demo against local core
AGENTS.md:24 == CONTRIBUTING.md:53   pnpm build      # build all packages
AGENTS.md:25 == CONTRIBUTING.md:54   pnpm typecheck  # tsc across the graph
AGENTS.md:26 == CONTRIBUTING.md:55   pnpm check      # biome (format + lint + organize imports)
AGENTS.md:27 == CONTRIBUTING.md:56   pnpm check:fix  # auto-fix what biome can
AGENTS.md:38 == CONTRIBUTING.md:91   Good: Replace spinner with a hairline + sliding bar...
AGENTS.md:40 == CONTRIBUTING.md:95   Do not bump versions or edit CHANGELOG.md by hand...
```

Reproduce: normalize both files to lowercase alphanumeric lines longer than 25 chars and intersect — 7 of `AGENTS.md`'s 24 substantive lines (29%) appear verbatim in `CONTRIBUTING.md`.

They have already drifted in three places, in **both directions** — which is the proof that this duplication is costing you, not just token weight:

| Rule | `AGENTS.md` (agent-facing) | `CONTRIBUTING.md` (human-facing) |
|---|---|---|
| Pre-push gate | `:35` — **only** "Biome must pass before commit" | `:71-76` — `pnpm check` **and** `pnpm typecheck` **and** `pnpm test` |
| Dependencies | `:41` — "Do not add dependencies casually" | `:102` — adds "Prefer a small piece of inline code over a new package" |
| Comments | `:43` — long form: no task/PR refs, no divider banners, no commented-out code | `:103` — short form, drops all three |

**Why it hurts the agent:** the first row is the expensive one. `.github/workflows/ci.yml` runs four jobs — `lint`, `typecheck`, `test`, `e2e` — but the file an agent actually reads makes only Biome a hard rule. An agent that follows `AGENTS.md` to the letter runs `pnpm check`, sees green, and pushes a branch that fails CI on `typecheck` or `test`. The knowledge exists in the repo; it is just not in the file the agent loads.

**Recommend:** do not merge the two files — they have genuinely different audiences, and `CONTRIBUTING.md` carries fork/PR/review material an agent does not need. Instead make `AGENTS.md` the single source for the *rules* and have `CONTRIBUTING.md` link to it rather than restate it (`## Style & conventions` → "See [AGENTS.md](./AGENTS.md)"), and add the missing gate to `AGENTS.md:35`:

> **Before pushing, `pnpm check`, `pnpm typecheck` and `pnpm test` must all pass** — CI gates on all three (plus `pnpm test:e2e`). `pnpm check:fix` auto-fixes most of the first.

Net: `AGENTS.md` grows ~20 tokens, `CONTRIBUTING.md` sheds ~40 lines of restatement, and there is one place to edit when a rule changes.

---

### P2-2 — `README.md` says `pnpm check` type-checks; it runs Biome · `README.md:90` · Misleading × on-demand · confidence **high**

**Quoted** (`README.md:86-92`):

```bash
pnpm check    # type-checks all packages
pnpm lint     # lints via biome
```

**Evidence:**

```bash
$ python -c "import json;print(json.load(open('package.json'))['scripts']['check'])"
biome check .
$ python -c "import json;print(json.load(open('package.json'))['scripts']['typecheck'])"
turbo run typecheck
```

`pnpm check` is Biome (format + lint + organize imports). It performs no type-checking whatsoever. Both `AGENTS.md:26` and `CONTRIBUTING.md:55` describe it correctly — `README.md` is the outlier, and it also contradicts itself by calling `check` a type-check and `lint` "lints via biome" when `check` is the Biome superset of `lint`.

**Why it hurts the agent:** an agent that reads the README — the file it reaches for first in an unfamiliar repo — believes it has type-checked when it has not, and never runs `pnpm typecheck`. Compounds directly with P2-1.

**Recommend:** replace lines 90-91 with the block already correct in the other two files:

```bash
pnpm typecheck  # tsc across the graph
pnpm check      # biome (format + lint + organize imports)
```

Token delta: neutral. This is a correctness fix, not a cut.

---

### P2-3 — `pnpm dev` also starts the Next.js marketing site; three files say it starts the demo · `AGENTS.md:23`, `CONTRIBUTING.md:52`, `README.md:88` · Misleading × always-on · confidence **high**

**Quoted** (identical in all three):

> `pnpm dev          # turbo: runs demo against local core`

**Evidence:**

```bash
$ python -c "import json;print(json.load(open('package.json'))['scripts']['dev'])"
turbo run dev                    # unfiltered — every workspace with a dev script
$ python -c "import json;print(json.load(open('apps/web/package.json'))['scripts']['dev'])"
next dev
$ cat pnpm-workspace.yaml         # apps/* — apps/web is in the graph
```

`turbo run dev` with no filter runs `dev` in **both** `apps/demo` (`open-slide dev`) and `apps/web` (`next dev`), both marked `persistent: true` in `turbo.json`. The repo already has the correct narrow script — `dev:demo` — and none of the three files mention it.

**Why it hurts the agent:** an agent told to "run the dev server and check the change" gets two long-running persistent processes on two ports, interleaved output, and a Next.js build it did not ask for. In an agent loop that is a hang, not a hiccup. It is also a clean illustration of the P2-1 cost: one wrong sentence, copy-pasted into three files, now needs three edits.

**Recommend:** in `AGENTS.md` (the source of truth after P2-1):

```bash
pnpm dev:demo     # demo against local core — what you usually want
pnpm dev          # every workspace, incl. the Next.js marketing site
```

---

### P3 — lower severity

| # | Finding | Location | Why it is P3 | Recommend |
|---|---|---|---|---|
| P3-1 | "See [`CLAUDE.md`](./CLAUDE.md) for the full authoring guide" — `apps/demo/` contains **no** `CLAUDE.md` or `AGENTS.md` at all (`ls -a apps/demo`) | `apps/demo/README.md:38` | Dead link, on-demand, a human notices instantly | Point at the `slide-authoring` skill, which is the actual full guide |
| P3-2 | The same line in the shipped template resolves to `AGENTS.md`, which says at `:21` *"Keep this file short: hard rules only. All deeper guidance lives in the skills above"* — so it is explicitly **not** "the full authoring guide" | `packages/cli/template/README.md:38` | Misleading, but reaches scaffolded users rather than this repo's agent | Reword: "See `AGENTS.md` for the hard rules; the `slide-authoring` skill is the full reference" |
| P3-3 | `apps/demo/README.md` is a 63-of-64-line copy of `packages/cli/template/README.md`, already drifted at line 12 (`diff -u` shows exactly one hunk). Both describe a *scaffolded workspace*, but `apps/demo` is a monorepo member where `pnpm install` / `pnpm preview` behave differently | both files | Duplication plus wrong audience, on-demand | Cut `apps/demo/README.md` to ~8 lines: "dogfood target for `@open-slide/core`; see the root `AGENTS.md`". ~800 → ~150 tokens |
| P3-4 | Root README sends the *scaffolded-workspace* reader to the *framework repo's* rules — whose first line is "You are working on the **open-slide framework**" | `README.md:72` | Wrong-audience pointer, on-demand | Link the docs site (`/docs/skills/overview`) instead of `CLAUDE.md` |
| P3-5 | Untouched Fumadocs scaffold boilerplate ("This is a Next.js application generated with Create Fumadocs"), last edited 128 days ago, offering `npm run dev` / `yarn dev` in a repo pinned to `pnpm@10.17.0` via corepack | `apps/web/README.md:1-45` | Pure derivable/default content; nothing depends on it | Replace with 3 lines: what the app is, `pnpm dev:web`, where content lives (`content/docs/`) |
| P3-6 | `.agents/skills/vercel-react-best-practices/AGENTS.md` is 108,261 bytes (~27k tokens) — a monolith duplicating the 70 files in that skill's own `rules/`. For a Codex user editing inside that directory it alone blows past Codex's 32,768-byte `AGENTS.md` budget | that file | Vendored third-party (`skills-lock.json` → `vercel-labs/agent-skills`); nobody edits inside that directory, so it rarely loads. Confidence **medium** on real-world reach | Leave it alone, it is upstream's. Worth knowing it exists before someone wonders where 27k tokens went |
| P3-7 | 7 identical lines shared between `.agents/skills/vercel-composition-patterns/README.md` and `.agents/skills/vercel-react-best-practices/README.md` | both | Vendored; neither sits in a Claude Code discovery path | No action — upstream's problem |
| P3-8 | Four vendored skills overlap heavily on "make the UI look good" — `apple-design`, `emil-design-eng`, `frontend-design`, `web-design-guidelines` (~305 listing tokens between them) in a repo whose UI surface is a slide runtime | `.agents/skills/*/SKILL.md` | Dilution only, and currently 0 tokens because of P1-1. Becomes P2 the moment P1-1 is fixed | Before re-materializing, ask which of the four has ever fired. Two of the eight already opt out (`review-animations: disable-model-invocation: true`, `shadcn: user-invocable: false`) — that pattern may fit others |

---

## Load-bearing — leave this alone

Named explicitly so a cleanup pass does not take them out with the noise.

- **`AGENTS.md:36` — the changeset rule with its bump table.** "`patch` for fixes/polish, `minor` for new public API, `major` for breaking. Apps (`demo`, `web`) and root tooling do **not** need one." A convention that departs from the tool default, and the carve-out for apps is exactly what an agent gets wrong every time without being told.
- **`AGENTS.md:37-39` — the changeset tone rule with the Good/Bad examples.** Textbook example-driven specification. The Bad example ("This change introduces a new loading indicator because…") is precisely what an LLM writes by default. Do not compress this to "keep it short".
- **`AGENTS.md:42` — "`packages/core/src/app/components/ui` is shadcn-generated and biome-ignored."** Verified against `biome.json:13` (`"!packages/core/src/app/components/ui"`). An agent that helpfully reformats that directory produces a diff nobody wants. External-constraint knowledge that exists nowhere else in prose.
- **`AGENTS.md:41` — "every dep inflates install size."** The *reason* attached to the rule. The rule without the reason gets argued away; with it, it holds.
- **`AGENTS.md:5` — the scope fence** ("slide-authoring guidance lives in the skills under `apps/demo/.claude/skills/`; use those only when editing files inside `apps/demo/slides/`"). Verified: that path exists. This is what stops an agent applying slide-authoring rules to runtime code, and it is the highest-value single line in the file.
- **`AGENTS.md:43` — the comments rule.** Long, and it should stay long. It enumerates four specific default LLM behaviours (section-divider banners, `// added for X` references, module headers, commented-out code) that a short version would not suppress.
- **The whole `packages/core/skills/` set (5 skills, ~78 KB).** Well factored: `slide-authoring` is the reference, `create-slide` / `apply-comments` are workflows that delegate to it, `current-slide` is a narrow resolver. `slide-authoring/SKILL.md:12` even says "Do not duplicate the knowledge below into other skills — link here instead", and that instruction is being followed. This is the best-organized context in the repo.
- **`current-slide/SKILL.md:11-19`** — the "re-read on every deictic turn, never reuse a prior read" section with its three named traps. Hard-won behavioural knowledge about a live cursor file; deleting it silently edits the wrong slide.
- **`CONTRIBUTING.md:31` — "A Unix-y shell. Windows works via WSL."** Currently the only trace of P1-1 anywhere in the repo's prose. Keep it, and strengthen it (see Missing).
- **`apps/web/content/docs/skills/overview.mdx`** — accurate, current, and it handles the Windows case correctly at `:53`. The docs site is in better shape than the repo's own instruction files.

---

## Missing

Where the *absence* of context is causing repeated mistakes.

1. **Nothing in `AGENTS.md` or `README.md` warns a Windows contributor that the checkout is broken.** `CONTRIBUTING.md:31` says "Windows works via WSL" but never says *why*, so it reads as a soft preference and gets ignored — as it was here. It should name the mechanism and the symptom: *"This repo uses git symlinks for `CLAUDE.md` and `.claude/skills/`. On Windows without `core.symlinks=true` and Developer Mode, git writes them as short text files and your agent silently loads no project context. Check with `git config core.symlinks`. Use WSL, or enable both."* Roughly 60 tokens that would have saved months of degradation.
2. **`AGENTS.md` never states the CI gate.** Covered in P2-1. `.github/workflows/ci.yml` runs `lint`, `typecheck`, `test`, `e2e`; the agent-facing file mandates only Biome.
3. **No map of where changes usually land.** `AGENTS.md` has a layout table — derivable, the agent gets the same information from `ls` — but no *judgment* about the repo: which module is load-bearing, where a typical runtime change touches, what to be careful near. For a months-old repo that is the highest-value thing you know and the agent does not. Two or three lines.
4. **No statement of the `packages/core/skills/` → `template/.agents/skills/` mirroring contract.** `packages/cli/scripts/sync-template-skills.mjs:20-29` wipes and re-copies from `packages/core/skills` on every `pnpm --filter @open-slide/cli build`. An agent that edits `packages/cli/template/.agents/skills/*` will have its work silently deleted at the next build, with no prose anywhere saying so. One line in `AGENTS.md`: *"`packages/core/skills/` is the only source of truth for skills — `template/.agents/skills/` is generated at build time and gitignored."*

---

## Out of scope

Noticed while gathering evidence. Different review, not this one.

- `packages/cli/template/package.json` pins `"@open-slide/core": "^0.0.6"` while the published core is far past that. Harmless, because `init.ts` rewrites it from `__CORE_VERSION_AT_BUILD__`, but a confusing constant to read.
- The 6 MB untracked, unignored `.pptx` in the repo root is one `git add .` away from being committed. (Also cited as evidence in P1-2.)
- `.gitignore` covers `packages/cli/template/.agents/skills` but nothing excludes `.claude/skills/pptx/` or loose `*.pptx`.

---

## Re-check next time

1. **`git config core.symlinks`** — the highest-value one-line check on this repo. If it reads `false`, nothing else in this report matters yet.
2. **The `AGENTS.md` / `CONTRIBUTING.md` pair.** They drifted three times in 127 days while nobody was looking. If you link instead of merge (P2-1), verify next audit that the link held and the restatements did not grow back.
3. **The skill listing, once P1-1 is fixed.** Thirteen skills will start loading at once, ~630 tokens of descriptions landing in every session — including the four overlapping design skills in P3-8. Re-read those descriptions together for trigger collisions at that point, not before.

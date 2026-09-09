# Context health — open-slide — 2026-09-08

Your CLAUDE.md/AGENTS.md situation is not out of hand — it is inert: on this Windows checkout every single CLAUDE.md and every skill link is an unmaterialized git symlink, so Claude Code currently loads **2 tokens** of your project's instructions, and the only slide skill it can actually see is an untracked PowerPoint skill you installed locally.

---

## Always-on cost

Loaded at the start of every session, before you type anything:

| Tokens | % of 200k window | File | Kind |
|---:|---:|---|---|
| 1,081 | 0.54% | `(skill listing)` | skill name+description lines |
| 2 | 0.00% | `CLAUDE.md` | project memory — **DEAD, unmaterialized symlink** |
| **1,083** | **0.54%** | **ALWAYS-ON TOTAL** | |

Reproduce: `python scripts/ledger.py D:/Projects/open-slide`

**Is 0.54% defensible?** The number is defensible; what it is made of is not. Of the 1,083 tokens, the repo contributes **2** — the literal string `AGENTS.md`. The other 1,081 are the skill listing, and of that, the repo's only contribution is ~191 tokens for the untracked `pptx` skill (P1-2). Your carefully written 47-line `AGENTS.md` contributes **zero**. This is the inverse of the usual bloat problem: you are not paying too much, you are paying for the wrong thing and getting none of what you wrote.

### On-demand tier — who owns it

~180,600 tokens of Markdown across 169 files (excluding `node_modules`). Split by author:

| ~Tokens | Files | Owner |
|---:|---:|---|
| 109,553 | 105 | **Vendored** — `.agents/skills/` (8 third-party skills, tracked in `skills-lock.json`) |
| 5,199 | 1 | **Vendored, unmanaged** — `.claude/skills/pptx/SKILL.md` (untracked, not in `skills-lock.json`) |
| 20,662 | 12 | Authored — `packages/core/skills/` (shipped to your users) |
| 13,905 | 27 | Authored — `apps/web/content/docs/*.mdx` |
| 31,106 | 21 | Authored — READMEs, CONTRIBUTING, changelogs, theme docs |

**Vendored context outweighs your own roughly 1.8 : 1.** Worth naming: when an agent goes looking for guidance in this repo, most of what is available to find is Vercel's and Emil Kowalski's opinions about React, not yours about open-slide. Not automatically wrong — you chose those skills deliberately and locked them — but it is the shape of the repo.

**Reachability:** on this checkout, 8 of the 9 skills under `.claude/skills/` are unreachable (P1-1), and the 5 slide skills under `apps/demo/.claude/skills/` are unreachable through a *double* broken hop. The only reachable one is `pptx`.

**External pulls:** one, and it is benign — `.agents/skills/shadcn/registry.md:229` instructs reading `https://raw.githubusercontent.com/{owner}/{repo}/{sha}/registry.json`. It is pinned to a resolved commit SHA by design and describes CLI *implementation*, not "fetch and obey." Noted, not flagged.

---

## Findings

### P1-1 — Every CLAUDE.md and every skill link in this checkout is a dead 9-byte string · `CLAUDE.md:1` · Misleading × always-on · confidence **high**

**Quoted:** the entire content of `CLAUDE.md` is the nine characters:

    AGENTS.md

**Evidence:**

    $ wc -c CLAUDE.md
    9 CLAUDE.md
    $ git -C D:/Projects/open-slide ls-files -s CLAUDE.md
    120000 47dc3e3d863cfb5727b87d785d09abf9743c0a72 0    CLAUDE.md
    $ git -C D:/Projects/open-slide config --get core.symlinks
    false

Mode `120000` is a git symlink; `core.symlinks=false` means git wrote the *target path as text* instead. The same is true of all 25 tracked symlinks:

- `CLAUDE.md` and `packages/cli/template/CLAUDE.md`
- all 8 skill links under `.claude/skills/` (`apple-design`, `emil-design-eng`, `frontend-design`, `review-animations`, `shadcn`, `vercel-composition-patterns`, `vercel-react-best-practices`, `web-design-guidelines`)
- all 5 links under `apps/demo/.claude/skills/`, which point at `apps/demo/.agents/skills/*`, which are *themselves* broken links to `packages/core/skills/*` — a two-hop chain, both hops dead
- all 5 links under `packages/cli/template/.claude/skills/`

    $ git -C D:/Projects/open-slide ls-files -s | awk '$1=="120000"{print $4}' | wc -l
    25

**Why it hurts the agent:** Claude Code opens `CLAUDE.md`, reads the nine characters `AGENTS.md`, and treats that as your entire project memory. It never learns that Biome must pass, that `packages/core` changes need a changeset, that `packages/core/src/app/components/ui` is shadcn-generated and off-limits, or that the house style is no comments. Every one of those rules is in `AGENTS.md:33-43` and none of it arrives. Worse, the failure is *silent* — nothing errors, so for months the sessions have looked normal while running with no project rules at all. That matches the symptom you described.

**Recommend:** two surgical changes, neither of which breaks the Unix setup.

1. Replace the `CLAUDE.md` symlink with a **real one-line file** containing `@AGENTS.md`. Claude Code's `@import` resolves it at launch on every platform, and it survives a Windows checkout. Do the same for `packages/cli/template/CLAUDE.md` — that one ships to *your users*, so today every Windows user who runs `npx @open-slide/cli init` gets a 9-byte CLAUDE.md too.
2. For the skill links, either `git config core.symlinks true` and re-checkout (needs Developer Mode or an elevated shell on Windows), or stop symlinking and let `sync:skills` copy real directories. Your call — but document whichever you pick, because nothing in the repo currently warns a Windows contributor (see **Missing**).

Token delta: `2 → ~800` always-on (`AGENTS.md` finally loads). This finding is an *addition*, not a cut.

**Honest caveat:** on your macOS/Linux machines this all works correctly. This is a checkout-local defect for Windows — except for `packages/cli/template/CLAUDE.md`, which is a shipped defect affecting your users.

---

### P1-2 — The one skill Claude Code can see in this repo is a PowerPoint skill tuned to hijack the word "slides" · `.claude/skills/pptx/SKILL.md:3` · Misleading × always-on · confidence **high** (the collision), **medium** (that it has already misfired)

**Quoted**, from the skill's always-on listing entry:

> Trigger whenever the user mentions "deck," "slides," "presentation," or references a .pptx or .potx filename, regardless of what they plan to do with the content afterward.

**Evidence:**

    $ git -C D:/Projects/open-slide status --short
    ?? .claude/skills/pptx/
    ?? Wanin_企業基本款V1範本_主題套用.pptx

    $ du -sh .claude/skills/pptx && find .claude/skills/pptx -type f | wc -l
    1.3M    .claude/skills/pptx
    56

It is **untracked**, **not in `.gitignore`**, and **absent from `skills-lock.json`** — so the repo's own skill-management mechanism does not know it exists and `sync:skills` will never touch it. Directory mtime is `2026-08-19 09:50`, eleven minutes after the repo checkout at `09:39`; it was installed here by hand.

**Why it hurts the agent:** this repo's entire vocabulary is `deck`, `slides`, `presentation`. Your own skills that should claim those words — `create-slide`, `slide-authoring`, `create-theme`, `apply-comments`, `current-slide` — are all behind the broken symlinks of P1-1 and are **invisible**. So when you type "make me a deck about X" in this repo, the only slide-shaped skill in the listing is one that instructs the agent to reach for python-pptx and write a `.pptx` file. The correct behaviour — scaffold `slides/<id>/index.tsx` on a 1920×1080 React canvas — is not on the menu. The stray `.pptx` in your repo root is circumstantial, not proof, but it is consistent.

**Recommend:** move `.claude/skills/pptx/` to `~/.claude/skills/pptx/` so you keep it for real PowerPoint work without it shadowing this repo, or delete it. It has zero open-slide value. If you keep any local skill inside the repo, add it to `.gitignore` so it cannot leak into a commit.

Token delta: `~191 → 0` always-on listing; `~5,199 → 0` on-demand; 1.3 MB and 56 files off the tree.

---

### P2 group — surface docs point at a "full authoring guide" that does not exist

Four files send the agent to a `CLAUDE.md` that is either absent or is the wrong document. Shared root cause: these lines were written when a real `CLAUDE.md` held the authoring guide, before it moved into the `slide-authoring` skill (`packages/core/skills/`, first committed 2026-04-30 in `5bfcfe9`).

| Site | Quoted | Reality |
|---|---|---|
| `apps/demo/README.md:38` | "See [`CLAUDE.md`](./CLAUDE.md) for the full authoring guide." | `apps/demo/CLAUDE.md` **does not exist** — `ls apps/demo/` shows no such file |
| `packages/cli/template/README.md:38` | the same line, shipped to every scaffolded project | resolves to the 9-byte symlink; the real guide is the `slide-authoring` skill |
| `README.md:72` | "See [CLAUDE.md](CLAUDE.md) for the hard rules." | sits in the *scaffolded-workspace* paragraph but links to the *framework* guide, whose first line is "You are working on the **open-slide framework**" — the opposite audience |
| `packages/cli/README.md:20` | "`CLAUDE.md` — agent guide for authoring slides." | the file it describes is a symlink whose target is the framework guide |

**Why it hurts:** an agent told "read CLAUDE.md for the rules" opens it, finds nothing (or the wrong nine characters), and proceeds to write slides with no canvas contract, no type scale and no palette guidance. It then invents its own.

**Recommend:** repoint all four at the skill *by name* rather than by path — "the `slide-authoring` skill is the technical reference for everything under `slides/<id>/`." Skill names survive file moves; relative paths do not. `packages/cli/template/AGENTS.md:13-19` already does exactly this and is the model to copy.

---

### P2-1 — `README.md` says `pnpm check` type-checks; it runs Biome · `README.md:90` · Misleading × on-demand (high traffic) · confidence **high**

**Quoted:**

    pnpm check    # type-checks all packages

**Evidence:** `package.json` defines `"check": "biome check ."` and `"typecheck": "turbo run typecheck"` — two different scripts. Both other instruction files get it right and contradict the README:

- `AGENTS.md:26` — `pnpm check        # biome (format + lint + organize imports)`
- `CONTRIBUTING.md:55` — the same line

**Why it hurts the agent:** asked to "make sure types are OK", an agent that read the README runs `pnpm check`, watches Biome pass, and reports the types are clean without ever invoking `tsc`. It then pushes, and CI's separate `typecheck` job (`.github/workflows/ci.yml:38-57`) fails. The README also omits `pnpm typecheck` entirely, so nothing corrects the mistake.

**Recommend:** two lines in `README.md:90-91` — change the comment to `# biome (format + lint)` and add `pnpm typecheck  # tsc across the graph`.

---

### P2-2 — Three files list 2 of the 8 supported config fields · `packages/core/src/config.ts:9-23` · Misleading × on-demand · confidence **high**

**Quoted** (identical in the first two, paraphrased in the third):

> Supported fields: `slidesDir`, `port`.

Sites: `apps/demo/README.md:64`, `packages/cli/template/README.md:64`, and `packages/cli/README.md:18` ("optional typed config (slidesDir, port)").

**Evidence:** `packages/core/src/config.ts:9-23` declares `base`, `slidesDir`, `themesDir`, `assetsDir`, `port`, `allowedHosts`, `locale` (deprecated) and `build`. `allowedHosts` landed in commit `dad4c24`, "feat(core): add allowedHosts to open-slide.config.ts (#336)" — after these READMEs were last touched.

**Why it hurts the agent:** asked to expose a dev server through a tunnel, the agent reads "supported fields: slidesDir, port", concludes `allowedHosts` is unsupported, and tells the user it cannot be done — or hacks around a feature that already exists.

**Recommend:** delete the enumeration from all three and point at the type: "See `OpenSlideConfig` in `@open-slide/core` for the full field list." The type cannot go stale relative to itself.

---

### P2-3 — `apps/web/README.md` offers npm and yarn in a pnpm-only workspace · `apps/web/README.md:9-13` · Conflicting × on-demand · confidence **high**

**Quoted:**

    npm run dev
    # or
    pnpm dev
    # or
    yarn dev

**Evidence:** root `package.json` pins `"packageManager": "pnpm@10.17.0"`; `pnpm-workspace.yaml` declares the workspace; `CONTRIBUTING.md:30` says "pnpm 10.17.0+ — `corepack enable` will pick up the version pinned in `package.json`"; all four CI jobs run `pnpm install --frozen-lockfile`.

This is the *real* package-manager conflict in the repo. The detector sweep pointed at `AGENTS.md` instead — a false positive: `npm` there is the registry at line 3 and `npx` at line 14, not a package-manager instruction. Verified and dropped.

**Why it hurts the agent:** an agent working in `apps/web` follows the first line it sees, runs `npm run dev` inside a pnpm workspace, and produces a `package-lock.json` plus a `node_modules` layout that does not resolve `workspace:*` links.

**Recommend:** delete the `npm` and `yarn` alternatives — three lines. Since this file is untouched Fumadocs scaffold boilerplate (P3-1), the cheapest fix is to rewrite the whole file.

---

### P2-4 — A vendored skill ships its entire ruleset twice, and names one copy `AGENTS.md` · `.agents/skills/vercel-react-best-practices/AGENTS.md` · Costly × on-demand · confidence **high**

**Evidence:**

    $ wc -c .agents/skills/vercel-react-best-practices/AGENTS.md
    108261
    $ cat .agents/skills/vercel-react-best-practices/rules/*.md | wc -c
    110590

A probe taking a distinctive mid-body line from each of the 70 `rules/*.md` files found **59 of 70 present verbatim** in the single `AGENTS.md`. It is a concatenation of the rule files the skill's own `SKILL.md` already points to — ~27,065 tokens of duplicate, and the largest Markdown file in the repo by 2.5×.

The filename is the second problem. Codex merges every `AGENTS.md` from the repo root down to the file being edited, so editing anything under `.agents/skills/vercel-react-best-practices/` pulls 108 KB into the prompt and blows past Codex's 32,768-byte instruction cap, silently truncating whatever sits at the end of the chain.

**Correction to the tooling:** the ledger reported this as an unconditional breach of Codex's cap. It is not — it fires only when Codex is editing a file inside that vendored skill's directory, which is rare. Reported here at its true severity.

**Recommend:** this is upstream Vercel content, so do not edit it in place — you would lose the edit on the next sync. Either exclude `.agents/skills/**/AGENTS.md` from your Codex setup, or raise it upstream. Low urgency; just know it is there.

---

### P3 — one row each

| # | Site | Finding | Recommend |
|---|---|---|---|
| P3-1 | `apps/web/README.md:1-45` | Untouched Fumadocs scaffold boilerplate. Every claim is *true* (`lib/source.ts`, `lib/layout.shared.tsx`, `app/api/search/route.ts` all exist) but nothing in it is about open-slide. ~1,100 tokens teaching an agent what Fumadocs is. | Replace with five lines: what this app is, where docs content lives (`content/docs/`), and `pnpm dev:web`. |
| P3-2 | `apps/demo/README.md` vs `packages/cli/template/README.md` | 63 of 64 lines identical — only line 12 differs. Two audiences, so mirroring is defensible, but they already carry the same two stale claims and must be fixed twice. | Generate one from the other at pack time, or accept it and fix both together. |
| P3-3 | `AGENTS.md:5` | Names 2 of the 5 shipped skills. `create-theme`, `apply-comments` and `current-slide` exist and are unmentioned. | Add the three names, or say "the skills under `packages/core/skills/`" and stop enumerating. |
| P3-4 | `AGENTS.md:13` vs `README.md:80` | AGENTS.md calls it the "`open-slide` dev/build CLI"; the README correctly says "dev/build/preview". `preview` and `export` are both real. | One word. |
| P3-5 | `skills-lock.json` | Locks 8 skills; `pptx` is a 9th on disk that the lockfile does not know about. | Resolved by fixing P1-2. |
| P3-6 | `.agents/skills/vercel-composition-patterns/README.md` and `.../vercel-react-best-practices/README.md` | 7 identical lines (39% of the smaller file). Shared authoring boilerplate from `vercel-labs/agent-skills`. | Upstream's problem. No action. |

---

## Load-bearing — leave this alone

These are earning their tokens. A cleanup pass that touches them makes the repo worse.

- **`AGENTS.md:36-40` — the changeset rules, including the good/bad examples.** A convention that departs from the model default (an agent's instinct is a paragraph-length changeset), and the two contrasting examples are what make it stick. Long, and worth every token.
- **`AGENTS.md:41` — "Don't add dependencies casually. The `core` runtime ships to users; every dep inflates install size."** Why, not what. Delete the clause after the semicolon and this becomes an ignorable style preference.
- **`AGENTS.md:42` — `packages/core/src/app/components/ui` is shadcn-generated and biome-ignored.** A deliberate exclusion. Code cannot show what you decided *not* to touch, and an agent will happily reformat generated files.
- **`AGENTS.md:43` — the comment policy.** The longest bullet in the file, and keep all of it: it enumerates the specific shapes it forbids (section-divider banners, module headers, "added for X" references). A shorter "don't over-comment" would not change behaviour.
- **`.github/workflows/ci.yml:84` — "Image version must match `@playwright/test` in `packages/core/package.json`."** An external constraint recorded nowhere else. Currently in sync (`v1.62.1-noble` against the bump in `2c9ad88`). This is the sentence that stops the next agent from bumping one and not the other.
- **`apps/demo/slides/morph-messages/index.tsx:518-523`** — the six-line explanation of why the element rotates about `top left` and why the layout position is offset by R(135°)·(12,12). It is what explains the magic number `16.97` on line 524. The comment detector flagged it as commented-out code; it is the opposite — it is the single most valuable comment in the repo.
- **`packages/core/src/vite/routes/folders.ts:16-21` and `packages/core/src/vite/routes/restart.ts:6-11`** — compact route-contract maps. Also detector false positives. A cross-module contract that exists in no single other file.
- **`packages/core/skills/current-slide/SKILL.md` description** — "Re-read `node_modules/.open-slide/current.json` at the start of every such turn — the user navigates between turns, so a value you read earlier in the conversation is almost certainly stale." Non-obvious agent behaviour that no amount of code-reading would reveal. Excellent.
- **`packages/cli/template/AGENTS.md`, all 32 lines** — the healthiest instruction file in the repo. Line 21 explains why: "Keep this file short: hard rules only. All deeper guidance lives in the skills above." A file with a self-limiting rule inside it is a file that does not rot. Consider adding that sentence to the root `AGENTS.md`.
- **`CONTRIBUTING.md:31` — "A Unix-y shell. Windows works via WSL."** Currently the only line in the repo that touches the P1-1 failure. Not enough (see Missing), but do not delete it.

---

## Missing

Where the *absence* of context is causing repeated mistakes.

1. **Nothing warns that a native Windows checkout silently destroys every instruction file.** `CONTRIBUTING.md:31` reads as a mild preference. It needs the mechanism instead: "This repo uses git symlinks for `CLAUDE.md` and all skill directories. A native Windows checkout without `core.symlinks=true` turns each of them into a text file containing its target path — no error, no warning, and every agent instruction in the repo silently stops loading. Use WSL, or run `git config core.symlinks true` in an elevated shell and re-checkout." That paragraph is the highest-value addition available in this repo. It belongs in `packages/cli/README.md` too, because your Windows *users* hit the same trap in the scaffolded template.

2. **`pnpm test:e2e` is missing from `AGENTS.md`'s workflow block (`AGENTS.md:22-29`).** CI gates on a Playwright e2e job (`.github/workflows/ci.yml:80-104`) added 2026-07-21; `AGENTS.md` was last edited 2026-05-04 (`efbcb4e`). An agent that runs `pnpm check`, `pnpm typecheck` and `pnpm test` believes it is green and is wrong. One line: `pnpm test:e2e     # playwright — CI gates on this`.

3. **Nothing says `packages/core/skills/` is the source of truth for the shipped skills.** `AGENTS.md:5` points at `apps/demo/.claude/skills/`, which is a symlink farm. An agent asked to improve `create-slide` will edit the wrong copy or fail to find it at all. One row in `AGENTS.md`'s Layout table fixes it: "`packages/core/skills` — the five authoring skills shipped to users; `apps/demo` and `packages/cli/template` symlink to these, never edit through the links."

4. **`themes/` is invisible in `AGENTS.md`.** The demo carries six themes as paired `.md` + `.demo.tsx` files and there is a whole `create-theme` skill for them, but the framework guide never mentions the concept exists.

---

## Out of scope

Noticed in passing; not this audit's business.

- `Wanin_企業基本款V1範本_主題套用.pptx` — a 6 MB untracked binary in the repo root, dated 2021. Not prose, but one `git add -A` away from being committed.
- `packages/cli/template/.claude/skills/*` are symlinks into `packages/cli/template/.agents/skills`, which is gitignored and absent from the checkout — dangling by design. Whether the npm pack step materializes them is a packaging question worth checking separately.
- `packages/core/src/config.ts:16-21` carries a `@deprecated` `locale` field. Correctly documented; just noting it exists.

---

## Re-check next time

1. **Whether `CLAUDE.md` actually loads.** After the P1-1 fix the ledger's always-on total should jump from 1,083 to roughly 1,900. If it still reads 1,083, the fix did not take. One command: `python scripts/ledger.py D:/Projects/open-slide`.
2. **The config-field lists.** They have gone stale once already (`allowedHosts`, `themesDir`, `assetsDir`, `base`, `build` all missing). If the P2-2 fix re-enumerates fields instead of pointing at `OpenSlideConfig`, expect this same finding next audit.
3. **`AGENTS.md` against the CI workflow.** These drifted apart over four months and produced the e2e gap. Query: `git log --since=<last audit> -- .github/workflows/ci.yml`.
4. **New untracked skills under `.claude/skills/`.** `pptx` arrived eleven minutes after checkout and nothing noticed. `git status --short` on `.claude` catches the next one.

---

*Method: `scripts/ledger.py` and `scripts/sweep.py` (all nine detectors run), then full reads of the always-on set and of every instruction file, with each candidate verified against the repo. The sweep raised 14 candidates: 6 confirmed, 4 false positives (the `npm run preview` / `npm run sync:skills` docs are correct — those scripts exist in `packages/cli/template/package.json`, which is the project those docs describe), 3 comment flags that turned out to be load-bearing and are now in the protect list, and 1 (`AGENTS.md` package managers) mislocated and re-sited to `apps/web/README.md`. The two largest findings came from reading, not from a detector. No file in `D:/Projects/open-slide` was created, modified or deleted.*

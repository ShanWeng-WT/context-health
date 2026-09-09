# Context health — fixture-repo — 2026-09-08

Claude ignores your pnpm rule because the file that states it also demonstrates `npm` twice, two lines above it, and nothing else in the repo corroborates pnpm — so the rule is one shouted line against a page of contrary evidence.

Repo audited: `C:/Users/SHAN~1.WEN/AppData/Local/Temp/claude/D--Projects-context-health/fcaaff73-c399-4001-9a21-acf79292aa34/scratchpad/fixture-repo` (read-only; nothing was modified).

## The short answer to your question

Four separate things work against the pnpm rule at once. In order of force:

1. **`CLAUDE.md` contradicts itself.** Line 7 says pnpm. Lines 3-4 — which the agent reads *first* — spell `npm run build`, `npm run lint`, `npm run test`. Demonstrated usage beats asserted policy in an LLM's context almost every time.
2. **`AGENTS.md:7` says the exact opposite**: "ALWAYS use npm to install dependencies." Claude Code does not read that file today (P2-1), but other tools do, and if you ever bridge it in the contradiction becomes direct.
3. **The rule has no contrast.** Four of the first four rules shout (ALWAYS / NEVER / IMPORTANT+MUST / CRITICAL). Emphasis works by contrast; at that density none of it registers.
4. **Nothing in the repo backs it up.** No `pnpm-lock.yaml`, no `packageManager` field in `package.json`. The agent looks for corroboration, finds only `npm run` strings, and follows those.

This is not a token problem. Your repo's own always-on context is 165 tokens. It is a *correctness and contradiction* problem, and pruning will not fix it — reconciling will.

## Always-on cost

| Tokens | % window | File | Kind |
|---:|---:|---|---|
| 895 | 0.45% | `(skill listing)` | skill name+description (your global `~/.claude/skills`, not this repo) |
| 149 | 0.07% | `CLAUDE.md` | project memory |
| 16 | 0.01% | `.claude/rules/style.md` | project rule (unscoped — no `paths:`, loads every session) |
| **1,061** | **0.53%** | **ALWAYS-ON TOTAL** | |

Command: `python scripts/ledger.py <repo>`

Defensible, easily. 0.53% of a 200k window, and only 165 of those tokens belong to this repo. Nothing here is oversized. Every finding below is about text being *wrong*, not text being *long*.

**On-demand tier:** ~51,403 tokens across 34 files — and all 34 live in your global `~/.claude/skills`; none is authored in this repo. `docs/architecture.md` (~30 tokens) is the only repo prose outside the always-on tier, and no skill or rule points at it, so the agent finds it only by chance.

- *Who wrote it?* Your own global skills. No vendored or generated bulk. Nothing to flag.
- *Can it be reached?* `AGENTS.md` cannot (P2-1). Everything else can.
- *Does it pull anything from outside?* No. `grep -rniE "https?://" <repo> --include=*.md` returns nothing — no fetch-and-obey exposure.

## Findings

### P1-1 — The package-manager rule is contradicted by its own file  ·  `CLAUDE.md:3,4,7`  ·  Conflicting × always-on  ·  confidence **high**

**Quoted:**

```
3: Run `npm run build` to build. Run `npm run lint` to lint the code.
4: Tests live in `src/api/legacy.ts` and are run with `npm run test`.
7: - ALWAYS use pnpm to install dependencies.
```

And in the second always-on file that other tools read:

```
AGENTS.md:7: - ALWAYS use npm to install dependencies.
```

**Evidence:**

```bash
grep -n "npm\|pnpm" CLAUDE.md AGENTS.md   # 3 npm mentions vs 1 pnpm inside CLAUDE.md; AGENTS.md says npm
ls | grep -iE "lock|pnpm"                 # no lockfile of any kind
cat package.json                          # {"name":"fix","scripts":{"build":"tsc","test":"vitest"}} - no packageManager field
```

**Why it hurts the agent:** the agent resolves ambiguity by looking for the repo's actual practice. Here the only visible practice is `npm run ...`, written three times in the same file, and there is no lockfile to break the tie. So it concludes npm is what this project does and treats line 7 as an aspiration someone typed once. Nothing enforces the rule and nothing confirms it — a lone assertion surrounded by counter-evidence.

**Recommend:** three surgical changes, all small.

1. Rewrite lines 3-4 in pnpm form so the file stops arguing with itself (`pnpm build`, `pnpm test`). Zero token change; the single highest-value edit in this report.
2. Give line 7 a reason, so it reads as a constraint rather than a preference and survives future pruning — e.g. "Use pnpm: the workspace links and lockfile are pnpm-specific, and `npm install` rewrites the tree." Substitute the real reason; I cannot see it from inside the repo.
3. Enforce it mechanically instead of asking (catalogue S2). A committed `pnpm-lock.yaml` and `"packageManager": "pnpm@<version>"` in `package.json` do more than any sentence in CLAUDE.md — Corepack then makes the wrong tool fail loudly. An instruction file is a request; this makes it a guarantee.

### P1-2 — Every statement about testing in the always-on tier is wrong  ·  `CLAUDE.md:4,17` vs `.claude/rules/style.md:3`  ·  Misleading + Conflicting × always-on  ·  confidence **high**

**Quoted:**

```
CLAUDE.md:4:  Tests live in `src/api/legacy.ts` and are run with `npm run test`.
CLAUDE.md:17: - As of 2024-03, we use Jest for testing.
.claude/rules/style.md:3: - Use vitest for all unit tests.
```

**Evidence:**

```bash
ls src/api/legacy.ts                                                # No such file or directory
git -C <repo> log --all --diff-filter=A --name-only | grep legacy   # never existed in history
cat package.json                                                    # "test":"vitest"
```

`src/api/legacy.ts` has never existed in this repository. `package.json` runs vitest. Two always-on files therefore name rival test runners with nothing to resolve them, and the third claim points at a file that was never there.

**Why it hurts the agent:** asked to add a test, the agent tries to open `src/api/legacy.ts`, fails, then has to guess between Jest and vitest — and Jest is the one written in the file most people treat as higher precedence. The likely output is `jest.mock` and Jest imports, which vitest rejects. The `As of 2024-03` prefix makes it worse, not better: it reads as a deliberate, dated, authoritative fact.

**Recommend:** delete `CLAUDE.md:17` outright (~15 tokens) — `.claude/rules/style.md:3` already carries the correct answer, and a duplicated rule is how drift begins. Fix line 4 to name where tests actually live, or drop the clause if there are none yet; do not leave a path that has never existed. CLAUDE.md 149 → ~130 tokens, and one fewer coin-flip per session.

### P1-3 — `npm run lint` does not exist  ·  `CLAUDE.md:3` (copied to `AGENTS.md:3`)  ·  Misleading × always-on  ·  confidence **high**

**Quoted:** "Run `npm run build` to build. Run `npm run lint` to lint the code."

**Evidence:**

```bash
cat package.json                    # scripts: build, test - no lint
ls .github Makefile justfile        # none exist
grep -rn "lint" . --include=*.json --include=Makefile --include=justfile   # no hits
```

No manifest, no CI, no task runner defines `lint`. The command is simply gone, or never landed.

**Why it hurts the agent:** it will run it — a documented command in always-on context is treated as verified. It fails, a turn is burned diagnosing, and the agent often "helpfully" invents a lint setup you did not ask for. `npm run build` on the same line *is* valid (`"build":"tsc"`), which is what makes this dangerous: the true clause lends credibility to the false one.

**Recommend:** add the `lint` script or delete the clause (~9 tokens). Do not leave it. This line is also where the npm habit is being taught, so fix it in the same edit as P1-1.

## P2 — grouped

### P2-1 — `AGENTS.md` is a divergent second copy that Claude never reads  ·  `AGENTS.md:1-7`  ·  Conflicting (cross-tool) × unreachable-for-Claude  ·  confidence **med-high**

The ledger flags it: no `CLAUDE.md` import and no symlink, so Claude Code does not load it, while Codex and other AGENTS.md-aware tools do. It has drifted from `CLAUDE.md` on three points and agrees with it on the two that are wrong:

| Topic | `CLAUDE.md` | `AGENTS.md` |
|---|---|---|
| package manager | pnpm (`:7`) | npm (`:7`) |
| network timeout | 30s (`:13`) | 60s (`:6`) |
| exports | named (`:12`) | default (`:5`) |
| `npm run lint` | present (`:3`) | present (`:3`) — same dead command |
| tests in `legacy.ts` | present (`:4`) | present (`:4`) — same dead path |

Verification: `comm -12 <(sort CLAUDE.md) <(sort AGENTS.md)` shows lines 1, 3 and 4 are byte-identical — a copy made once and then maintained on only one side. Two agents behave differently on this repo, and whichever one a reviewer happens to use becomes the standard by accident.

**Recommend:** pick one source of truth. Cheapest is to make `AGENTS.md` a symlink to `CLAUDE.md` so they cannot diverge again; an `@AGENTS.md` import also works but adds its tokens to every Claude session. If AGENTS.md is meant to be Codex-only guidance, say so in its first line — today it reads as a stale mirror, because it is one. Either way, the timeout pair and the exports pair each need one value deleted, not both kept.

### P2-2 — Emphasis saturation: four of eleven rules shout  ·  `CLAUDE.md:7-10`  ·  Diluting × always-on  ·  confidence **high**

```
7:  - ALWAYS use pnpm to install dependencies.
8:  - NEVER commit directly to main.
9:  - IMPORTANT: you MUST run the formatter before every commit.
10: - CRITICAL: always write tests first.
```

`grep -cE '\b(ALWAYS|NEVER|MUST|IMPORTANT|CRITICAL)\b' CLAUDE.md` returns 4 — four emphasis lines out of 11 rule lines (36%) and 17 total lines (24%). The catalogue's threshold is ~15%; past it, emphasis marks nothing. Worse, the four shouts are consecutive and leading, so the first impression is that everything is critical — the same information as nothing being critical.

This is the second-order reason your pnpm rule gets ignored: it is not just outnumbered by `npm` strings, it is also indistinguishable from the three rules beside it.

**Recommend:** keep the absolute on the one or two genuine invariants (likely: never commit to main, and pnpm once it has a reason attached) and strip the markers from the rest. Same content, ~8 tokens lighter, and the surviving absolutes start meaning something again.

### P2-3 — Rules asking for something the repo cannot do  ·  `CLAUDE.md:9,10`  ·  Misleading × always-on  ·  confidence **med**

Line 9 requires "the formatter" — there is no `format` script and no Prettier, ESLint or editor config anywhere (`find <repo> -type f -not -path "*/.git/*"` returns 8 files: three context files, `docs/architecture.md`, `package.json`, three `.ts` stubs). Line 10 requires tests-first, and the repo contains no test file at all. Both are aspirational: the agent cannot comply, so it learns that rules in this file are sometimes decorative — which generalizes to the rules that are not.

**Recommend:** name the actual formatter command or drop line 9. For both, prefer enforcement to instruction (catalogue S2): a pre-commit hook or CI check makes the rule hold and lets you delete the line — the only move here that removes tokens and increases compliance.

### P2-4 — `docs/architecture.md` describes a deleted file and one that never existed  ·  `docs/architecture.md:2`  ·  Misleading × on-demand  ·  confidence **high**

**Quoted:** "The router lives in `src/api/router.ts` and dispatches to `src/api/missing.ts`."

**Evidence:**

```bash
SHA=$(git -C <repo> log -1 --format=%H -- docs/architecture.md)      # c96e1d2 (init)
git -C <repo> rev-list --count $SHA..HEAD -- src                     # 10
git -C <repo> log $SHA..HEAD --diff-filter=AD --name-status -- src   # D src/api/router.ts | A src/api/new_module.ts
```

`src/api/router.ts` was deleted in `30d2f16 remove router`. `src/api/new_module.ts` was added in `57fc89d add module` and appears in no document. `src/api/missing.ts` has never existed at all. The doc has not been touched since `c96e1d2 init`, through 10 commits to `src/`.

**Why it hurts the agent:** architecture notes shape the plan before any code is read. An agent asked to change routing plans around `router.ts`, cannot find it, and then either invents it or thrashes. Line 3 (`Connection pooling is in src/db/pool.ts`) is correct — again, the true half makes the false half credible.

**Recommend:** fix line 2 to describe where routing lives now, or state that it was removed. `src/api/handler.ts` carries 9 of the repo's 12 commits and is documented nowhere; that is where one added line would pay for itself.

## P3

| # | Finding | Location | Why | Recommend |
|---|---|---|---|---|
| P3-1 | "Think step by step before answering." | `CLAUDE.md:14` | Default behaviour — reasoning models do this unprompted; the line buys nothing | Delete (~10 tokens) |
| P3-2 | "You are an expert TypeScript engineer." | `CLAUDE.md:15` | Role-priming scaffolding from an older model generation; inert now | Delete (~10 tokens) |
| P3-3 | "We currently have 12 services in this monorepo." | `CLAUDE.md:16` | Drifted count — one `package.json`, three source files, no services dir. Time-relative and unmaintainable | Delete (~12 tokens); the agent can count |
| P3-4 | "Prefer named exports." stated twice | `CLAUDE.md:12` and `.claude/rules/style.md:2` | Paid twice per session, and duplicated rules are exactly how the AGENTS.md divergence began | Keep one — the rules file, its topical home |
| P3-5 | "Use 2-space indentation." | `CLAUDE.md:11` | An `.editorconfig` enforces this for free and more reliably than a request | Move to `.editorconfig` |
| P3-6 | `.claude/rules/style.md` has no `paths:` front matter | `.claude/rules/style.md:1` | Unscoped, so it loads every session even for a docs-only edit. At 16 tokens the cost is trivial — noted for the pattern, not the size | Add a `paths:` scope when it grows |

Every P3 cut combined: ~32 tokens. Stated plainly so you do not spend your effort here — P1-1 and P1-2 are where your problem lives.

## Load-bearing — leave this alone

- **`CLAUDE.md:7`, the pnpm rule itself.** It is the right *kind* of content: a convention that departs from the tool default, which is what an instruction file is for. Do not resolve P1-1 by deleting it — resolve it by making the rest of the file agree with it.
- **`CLAUDE.md:8`, "NEVER commit directly to main."** A real team constraint the model would not assume on its own. Keep the absolute here.
- **`.claude/rules/style.md:3`, "Use vitest for all unit tests."** The one statement about testing in this repo that matches `package.json`. It is the survivor in P1-2, not a casualty.
- **`docs/architecture.md:3`, "Connection pooling is in `src/db/pool.ts`."** Verified correct, and a genuine map — the kind of judgment the agent cannot derive as cheaply by looking.
- **`CLAUDE.md:3`, "Run `npm run build` to build."** The build half is true (`"build":"tsc"`). Fix the tool name and the lint clause; keep the sentence.

## Missing

- **No precedence statement.** Three always-on sources (`CLAUDE.md`, `.claude/rules/style.md`, and `AGENTS.md` for other tools) and nothing says which wins. One line — "where this file and `.claude/rules/` disagree, the rules file wins" — converts a whole class of arbitrary coin-flips into resolved ones. Cheapest fix in this report.
- **No recorded reason for pnpm.** This is why the rule is fragile. A constraint with a mechanism attached survives both pruning and disagreement; a bare preference does not. Whoever chose pnpm knows why; it exists nowhere in the repo.
- **No mechanical corroboration for pnpm** — no lockfile, no `packageManager` field (P1-1). Instruction files are requests; those are guarantees.
- **`src/api/handler.ts` is undocumented despite carrying 9 of 12 commits** (`git -C <repo> log --name-only --format= | sort | uniq -c | sort -rn`). Where changes actually land is a judgment the agent cannot derive, and it is the highest-value sentence you could add.

## Out of scope

- `package.json` has no `packageManager` field and no lockfile is committed — configuration, not prose, but it is the real fix for P1-1.
- `src/api/handler.ts` is eight `// change N` comments and one export; `new_module.ts` and `pool.ts` are one-line stubs. Code review, not this audit.
- No `.editorconfig`, no linter config, no CI — which is why several rules in `CLAUDE.md` have nothing to lean on.

## Re-check next time

1. **`docs/architecture.md` against `src/api/`.** It drifted through 10 commits untouched; it will do so again unless a review step catches it.
2. **`AGENTS.md` vs `CLAUDE.md`.** Kept as separate files, they will re-diverge — that is what a copy does. Re-run `comm -12 <(sort CLAUDE.md) <(sort AGENTS.md)` and watch whether the shared lines shrink.
3. **The pnpm rule.** If these fixes land and the agent still reaches for npm, the cause is corroboration, not wording — check that the lockfile and `packageManager` field actually got committed.

---
*Re-run: `python scripts/ledger.py <repo>` and `python scripts/sweep.py <repo>`. This audit reports only; no file in the audited repo was created, edited, moved or deleted.*

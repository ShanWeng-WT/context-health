# Context health — fixture-repo — 2026-09-08

**Repo audited:** `C:/Users/SHAN~1.WEN/AppData/Local/Temp/claude/D--Projects-context-health/fcaaff73-c399-4001-9a21-acf79292aa34/scratchpad/fixture-repo`

**Nothing in the repo was modified.** Every recommendation below is a proposal for you to apply.

---

## Short answer to your question

Your package-manager rule is not being ignored because the agent is careless. It is being ignored because **`CLAUDE.md` argues against itself**, and because the file has spent its credibility: half of its checkable claims are false, so an agent that verifies two of them stops trusting the rest.

Concretely, `CLAUDE.md` states the pnpm rule **once**, then demonstrates `npm` **three times** in its own worked examples two lines above it — and nothing in the repo (no lockfile, no `packageManager` field) breaks the tie. `AGENTS.md` then says the literal opposite: `ALWAYS use npm to install dependencies`.

The fix that will actually hold is not a louder rule. It is one line of enforcement in `package.json` plus a lockfile — see **Missing / X1**.

---

## Always-on cost

Loaded at the start of every session, before you type anything:

| Tokens | % of 200k window | File | Kind |
|---:|---:|---|---|
| 895 | 0.45% | `(skill listing)` | skill name+description lines — from your **machine-level** `~/.claude/skills`, not this repo |
| 149 | 0.07% | `CLAUDE.md` | project memory |
| 16 | 0.01% | `.claude/rules/style.md` | project rule, **unscoped** (no `paths:`) — loads every session |
| **1,061** | **0.53%** | **ALWAYS-ON TOTAL** | |

On-demand context: ~51,402 tokens across 34 files — again almost entirely your global skills directory. This repo itself ships `docs/architecture.md` (~34 tokens) and nothing else.

**Is that defensible? Yes, and it is not your problem.** This repo's own always-on footprint is ~165 tokens; 84% of the always-on total is your personal skill listing, which every repo on this machine pays equally. **Do not go looking for tokens to cut here.** The defect in this repo is correctness, not weight — a 149-token file that is 50% wrong is far more expensive than a 1,500-token file that is right, because the agent acts on the wrong parts and then discounts the right ones.

One mechanical breach the ledger flagged:

- `AGENTS.md` (~64 tokens) exists, but `CLAUDE.md` neither `@import`s nor symlinks it (`grep -n '@' CLAUDE.md` returns no matches). Under Claude Code's loading model that file is **dead weight for Claude and live for Codex / other AGENTS.md-aware tools** — so the two agents behave differently on this repo. See P1-4.

---

## Findings

### P1-1 — Your pnpm rule is outvoted by `CLAUDE.md`'s own examples, and reversed by `AGENTS.md` · `CLAUDE.md:7` · Conflicting × always-on · confidence **high**

**Quoted:**

```
CLAUDE.md:3   Run `npm run build` to build. Run `npm run lint` to lint the code.
CLAUDE.md:4   Tests live in `src/api/legacy.ts` and are run with `npm run test`.
CLAUDE.md:7   - ALWAYS use pnpm to install dependencies.

AGENTS.md:7   - ALWAYS use npm to install dependencies.
```

**Evidence:**

```bash
$ grep -rn "npm\|pnpm" CLAUDE.md AGENTS.md
CLAUDE.md:3:Run `npm run build` ... `npm run lint` ...
CLAUDE.md:4:... `npm run test`.
CLAUDE.md:7:- ALWAYS use pnpm to install dependencies.
AGENTS.md:3,4,7: (the same two npm lines, plus "ALWAYS use npm")

$ ls -a | grep -Ei 'lock|\.npmrc'
(no lockfile, no .npmrc)

$ grep -c packageManager package.json
0
```

**Why it hurts the agent:** three things stack, and each alone would be survivable.

1. **Modeled behaviour beats stated behaviour.** The file shows `npm ...` three times and says "pnpm" once. An agent generalising from the file's own examples reaches for npm.
2. **The rule is narrower than you think.** It says "to install dependencies" — strictly, it does not govern `npm run build`. So the file is technically self-consistent and practically incoherent: pnpm to install, npm to run. An agent cannot tell whether that split is deliberate or an oversight, and nothing says which.
3. **The repo supplies no tiebreak.** No `pnpm-lock.yaml`, no `package-lock.json`, no `packageManager` field. Normally an agent resolves this ambiguity by looking at the repo and finding a lockfile. Here, looking at the repo tells it nothing, so it falls back to the common default — npm.

`AGENTS.md:7` then states the exact opposite rule. If you use Codex, Cursor, or any tool that reads `AGENTS.md`, that is a direct, unmediated contradiction and explains the symptom on its own. For Claude Code specifically `AGENTS.md` is not loaded (no import, no symlink), so the cause there is (1)–(3) above — inside `CLAUDE.md` itself.

**Recommend** (surgical, ~0 token delta):

- Rewrite `CLAUDE.md:3-4` and `CLAUDE.md:7` to use one package manager consistently. If pnpm is the answer:

  ```
  Run `pnpm build` to build. Run `pnpm test` to run tests.
  - Use pnpm for everything, including running scripts. npm and yarn are not used here.
  ```

  The "npm and yarn are not used here" clause is the load-bearing half — it is a *deliberate exclusion*, and it is what stops an agent silently substituting.
- Delete `AGENTS.md:7`, or make `AGENTS.md` a pointer to `CLAUDE.md` (see P1-4).
- **Then stop relying on the instruction entirely** — see Missing / X1. An instruction file is a request; `packageManager` plus a committed lockfile is a guarantee.

---

### P1-2 — Half of `CLAUDE.md`'s checkable claims are false, which is why the true ones get ignored too · `CLAUDE.md:3,4,16,17` · Misleading × always-on · confidence **high**

This is the root cause behind "Claude keeps ignoring stuff in my CLAUDE.md" in general, not just the package manager. Of the eight claims in this file an agent can verify, **four are false**:

| Line | Quoted | Verdict | Evidence |
|---|---|---|---|
| `CLAUDE.md:3` | Run `npm run lint` to lint the code. | **Dead command** | `package.json` defines only `build` and `test`. No Makefile, justfile or `.github/`. `grep -rIn "lint" .` matches only `CLAUDE.md:3` and `AGENTS.md:3` — the docs are the only place lint exists. |
| `CLAUDE.md:4` | Tests live in `src/api/legacy.ts` | **Dead path** | `git log --all -- src/api/legacy.ts` is empty. The file **never existed in the history**. `git log --all --name-only` shows zero files matching test/spec/__tests__, ever. |
| `CLAUDE.md:16` | `- We currently have 12 services in this monorepo.` | **Drifted count** | `grep -c workspaces package.json` returns 0; `find . -name package.json` returns 1. It is a single package, not a 12-service monorepo. |
| `CLAUDE.md:17` | `- As of 2024-03, we use Jest for testing.` | **Dead + conflicting** | `package.json` says `"test":"vitest"`. `.claude/rules/style.md:3` says "Use vitest for all unit tests." Nothing named Jest exists anywhere — `grep -rn "jest" .` returns no matches. |

The two that *are* true — `npm run build` and `npm run test` — resolve to real scripts.

**Why it hurts the agent:** an agent that runs `npm run lint` gets a hard failure, then opens `src/api/legacy.ts` and gets a second one. Two falsified claims in the first four lines is enough for the model to treat the whole file as unreliable background rather than as instructions — at which point your *correct* rules ("NEVER commit directly to main") get the same discount as the wrong ones. **This is the mechanism you are experiencing.** Dilution here is a correctness problem, not a cost problem.

**Recommend:**

- `CLAUDE.md:3` — drop the `npm run lint` sentence entirely (there is no linter), or add a linter and keep the line. Do not leave a command documented that cannot run.
- `CLAUDE.md:4` — delete. There are no tests. If you want tests, say so as an intent, not as a false statement of fact.
- `CLAUDE.md:16` — delete. A count cannot be maintained and the agent can count.
- `CLAUDE.md:17` — delete. `.claude/rules/style.md:3` already says vitest, correctly, and `package.json` proves it. (~15 tokens saved and one conflict removed.)
- Consider dropping `CLAUDE.md:3-4` altogether: restating `package.json` scripts is derivable content — the manifest cannot go stale relative to itself, and this file demonstrably can.

Net for this finding: ~149 → ~105 tokens, and the file's hit rate on verifiable claims goes from 50% to 100%.

---

### P1-3 — Jest vs vitest: two files that both load every session disagree · `CLAUDE.md:17` vs `.claude/rules/style.md:3` · Conflicting × always-on · confidence **high**

**Quoted:**

```
CLAUDE.md:17               - As of 2024-03, we use Jest for testing.
.claude/rules/style.md:3   - Use vitest for all unit tests.
```

**Evidence:** `cat package.json` returns `{"name":"fix","scripts":{"build":"tsc","test":"vitest"}}`. `grep -rn "jest\|vitest" .` returns only `style.md:3` and `package.json`. No Jest config, no Jest dependency, no Jest anywhere in git history.

**Why it hurts the agent:** unlike the `AGENTS.md` conflicts, **both of these files genuinely load into Claude Code every session**, and nothing states which wins. Asked to add a test, the agent must pick arbitrarily — and reasoning models burn tokens trying to reconcile a contradiction rather than resolving it. The dated framing ("As of 2024-03") makes it worse: it reads as authoritative history, so the agent may treat Jest as the current answer and vitest as the aspiration, which is exactly backwards.

**Recommend:** delete `CLAUDE.md:17`. `style.md` is the correct file and it is already right. Do not "fix" it by changing Jest to vitest — that just re-creates the duplication in P3-4.

---

### P1-4 — `AGENTS.md` is an unread, drifted fork of `CLAUDE.md` that reverses three rules · `AGENTS.md:5,6,7` · Conflicting × cross-tool · confidence **medium-high**

**Quoted** — `diff CLAUDE.md AGENTS.md` shows lines 1-4 are byte-identical, then the rule blocks diverge:

| Topic | `CLAUDE.md` | `AGENTS.md` | The repo's actual answer |
|---|---|---|---|
| exports | `:12` "Prefer named exports." | `:5` "Prefer default exports." | **named** — all three source files use `export const` |
| network timeout | `:13` "Set timeout to 30s" | `:6` "Set timeout to 60s" | **unknowable** — `grep -rn "timeout"` finds no timeout in any code, only in these two docs |
| package manager | `:7` "ALWAYS use pnpm" | `:7` "ALWAYS use npm" | **unknowable** — no lockfile, no `packageManager` |

**Evidence:**

```bash
$ diff <(sed -n '1,4p' CLAUDE.md) <(sed -n '1,4p' AGENTS.md)   # identical
$ diff CLAUDE.md AGENTS.md                                     # rule blocks diverge, as above
$ grep -rn "export" src/
src/api/handler.ts:1:export const x=1;
src/api/new_module.ts:1:export const w=4;
src/db/pool.ts:1:export const z=3;
$ grep -n '@' CLAUDE.md                                        # no @imports — no bridge
```

**Why it hurts the agent:** this is the classic duplicated-block-that-drifted. The two files started as a copy (identical headers prove it) and the rule sections were edited independently. Now **which answer you get depends on which tool you happened to open**, and whichever tool your reviewer used silently becomes the standard. The export rule is the clearest case: `AGENTS.md` tells a Codex/Cursor session to prefer default exports, which contradicts every line of source in the repo.

**Confidence note:** medium-high rather than high only because it depends on your toolchain. If Claude Code is the only agent you run, `AGENTS.md` is currently inert — pure cost with zero effect, which is its own smaller defect. If you also run Codex, Cursor, or a Claude Code build that reads `AGENTS.md`, this is a live P1 and very likely a second, independent cause of your symptom.

**Recommend** — pick one home and bridge; do not maintain two:

- Make `AGENTS.md` the single source of rules and replace `CLAUDE.md`'s rule block with `@AGENTS.md`. An `@import` works on every platform; a symlink does not survive a Windows checkout (git stores it as a text blob containing the target path, and the agent then loads the nine characters `AGENTS.md` and nothing else).
- Or delete `AGENTS.md` outright if Claude Code is your only agent.
- Before merging, resolve the three flipped rules: **named** exports (the code decides it), and pick one timeout with the reason attached (see Missing / X2).

---

### P2-1 — Emphasis saturation: 4 of 11 rules shout, so none of them does · `CLAUDE.md:7-10` · Diluting × always-on · confidence **high**

**Quoted:**

```
:7   - ALWAYS use pnpm to install dependencies.
:8   - NEVER commit directly to main.
:9   - IMPORTANT: you MUST run the formatter before every commit.
:10  - CRITICAL: always write tests first.
```

**Evidence:** `grep -cE '\b(ALWAYS|NEVER|IMPORTANT|MUST|CRITICAL)\b' CLAUDE.md` returns 4, against 15 non-blank lines (**27%**) and 11 rule lines (**36%**). The practical threshold is around 15%.

**Why it hurts the agent:** emphasis works by contrast. Four consecutive absolutes, stacked (`IMPORTANT: you MUST`), flatten into ordinary prose — the model cannot tell your genuine invariant (never commit to main) from your preference (formatter before commit). This is directly relevant to your complaint: **the pnpm rule is one shout in a row of four**, so capitalising it bought nothing. Making it louder will make things worse, not better.

**Recommend:** reserve absolutes for true invariants. Keep `NEVER commit directly to main` as an absolute; demote the rest to plain statements. Zero token cost, and it restores the signal on the one rule you cannot afford to lose.

---

### P2-2 — "Always write tests first" is aspirational — the repo has never had a test · `CLAUDE.md:10` · Misleading × always-on · confidence **high**

**Quoted:** `- CRITICAL: always write tests first.`

**Evidence:**

```bash
$ git log --all --name-only --format='' | sort -u | grep -Ei 'test|spec|__tests__'
(no output — zero test files across all 12 commits)
$ git log --oneline | wc -l
12
```

`CLAUDE.md:4` even names a test location (`src/api/legacy.ts`) that never existed.

**Why it hurts the agent:** a rule the repo demonstrably does not follow teaches the agent that this file's rules are optional — which discounts every other rule in it, including the package-manager one. Same credibility mechanism as P1-2, applied to a rule rather than a fact.

**Recommend:** enforce it or drop it. If tests are genuinely the goal, keep the line but make it honest and actionable: "There are no tests yet — new modules should ship with a vitest suite." If they are not, delete it rather than leaving it as decoration.

---

### P2-3 — Two advisory rules that should be enforcement, not instructions · `CLAUDE.md:8,9` · Structural · confidence **high**

**Quoted:**

```
:8   - NEVER commit directly to main.
:9   - IMPORTANT: you MUST run the formatter before every commit.
```

**Why it hurts the agent:** both are genuinely load-bearing intents, but an instruction file is a request, not a guarantee — and you pay for them in every session forever while still having no assurance they hold. `CLAUDE.md:9` is additionally unenforceable as written: `grep -rIn "lint\|format" .` finds no formatter configured anywhere in the repo, so an agent that wants to comply has nothing to run.

**Recommend** — usually the highest-leverage move in an audit, because it removes always-on tokens *and* makes the rule actually hold:

- `:8` → branch protection on `main`, or a Claude Code permission rule denying `git commit` on main. Then shorten or drop the line.
- `:9` → a pre-commit hook, or a `format` script that actually exists. Right now the rule points at a tool that is not installed.

---

### P2-4 — `docs/architecture.md` describes an architecture that no longer exists · `docs/architecture.md:2` · Misleading × on-demand · confidence **high**

**Quoted:** The router lives in `src/api/router.ts` and dispatches to `src/api/missing.ts`.

**Evidence:**

```bash
$ git log -1 --format='%h %s' -- docs/architecture.md
c96e1d2 init                       # never touched since the first commit
$ git rev-list --count c96e1d2..HEAD -- src
10                                 # ten commits to src/ since
$ git log c96e1d2..HEAD --diff-filter=AD --name-status --format='' -- src
D  src/api/router.ts               # deleted in 30d2f16 "remove router"
A  src/api/new_module.ts           # added in 57fc89d, undocumented
$ git log --all -- src/api/missing.ts
(empty — src/api/missing.ts has never existed in this repo)
```

**Why it hurts the agent:** architecture notes shape the plan *before* the agent reads any code, so a stale one is the most expensive kind of wrong. An agent asked to touch routing will plan around `src/api/router.ts`, fail to find it, and either invent a replacement or conclude the docs are unreliable. `src/api/missing.ts` is worse — it was never real, so the doc has been wrong since the day it was written.

Only `src/db/pool.ts` on line 3 is accurate.

**Recommend:** three surgical edits — delete the `router.ts` clause (the router is gone), delete the `missing.ts` reference (it never existed), and add `src/api/new_module.ts`. This is P2 rather than P1 only because the file is on-demand; the claims themselves are as false as any P1 above.

---

### P3 — Low severity

| # | Location | Quoted | Class | Recommend |
|---|---|---|---|---|
| P3-1 | `CLAUDE.md:14` | `- Think step by step before answering.` | Default behaviour — current reasoning models do this unprompted | Delete (~8 tokens) |
| P3-2 | `CLAUDE.md:15` | `- You are an expert TypeScript engineer.` | Role-priming — little measurable effect on current models | Delete (~9 tokens) |
| P3-3 | `CLAUDE.md:11` | `- Use 2-space indentation.` | Standard convention a formatter enforces | Move to Prettier / EditorConfig; delete the line |
| P3-4 | `CLAUDE.md:12` + `.claude/rules/style.md:2` | `Prefer named exports.` (verbatim in both) | Duplicated block — **not yet drifted**, so low severity, but this is exactly how `AGENTS.md` started | Keep one home. `style.md` is the better one; delete `CLAUDE.md:12` |
| P3-5 | `.claude/rules/style.md` | no frontmatter (`head -1` returns `# Style`) | Unscoped rule — loads every session | Add `paths: ["**/*.ts"]` to move it to the on-demand tier at zero cost to its usefulness. Only 16 tokens, so hygiene, not urgency |
| P3-6 | `CLAUDE.md:3-4` | `npm run build` / `npm run test` | Derivable — restates `package.json` scripts | Optional: point at the manifest instead of copying it. Copies rot; `package.json` cannot |
| P3-7 | machine-level | `(skill listing)` = 895 tokens, **84% of your always-on total** | Cost — not this repo's doing | A **question**, not a defect: your global `~/.claude/skills` holds several near-neighbours (`p4-port-cl`, `p4-stream-port`, `p4-merge-cl`, `p4-merge-stream`). If their descriptions overlap, the agent may load the wrong one. Worth a separate look; usage is not the same as value, so do not prune on frequency alone |

---

## Load-bearing — leave this alone

Do not let this report turn into a deletion spree. These are earning their tokens:

- **`CLAUDE.md:8` — "NEVER commit directly to main."** A real invariant that departs from the tool default. P2-3 recommends *also* enforcing it, never removing the intent.
- **`.claude/rules/style.md:3` — "Use vitest for all unit tests."** Correct, matches `package.json`, and it is the file that wins the Jest/vitest conflict. This line is the reason P1-3 is cheap to fix.
- **`.claude/rules/style.md:2` — "Prefer named exports."** Matches all three source files and is the correct side of the `AGENTS.md` disagreement. Keep this copy; delete the other.
- **`npm run build` / `npm run test` (`CLAUDE.md:3-4`)** — the only two commands in the file that actually resolve. If you trim these lines, keep the working commands.
- **The `.claude/rules/` directory itself.** Modern, correctly shaped, and the right home for everything currently misfiled in `CLAUDE.md`.
- **The intent behind `CLAUDE.md:7`.** Your package-manager preference is a genuine convention-that-differs-from-default, which is exactly what an instruction file is for. The finding is that it is stated in a way that cannot win — not that it should go.

---

## Missing

An audit that only subtracts is doing half the job. These absences are causing your symptom.

### X1 — No machine-enforceable package manager *(highest leverage in this report)*

There is no lockfile, no `.npmrc`, and no `packageManager` field (`grep -c packageManager package.json` returns 0). Every agent, and every new teammate, has to take your prose on faith — and prose loses to a shell that finds `npm` on PATH.

**Recommend:**

```json
{ "name": "fix", "packageManager": "pnpm@9.0.0", "scripts": { "build": "tsc", "test": "vitest" } }
```

plus a committed `pnpm-lock.yaml`. With corepack, the wrong package manager then *fails* rather than silently succeeding. This converts your rule from a request into a guarantee and is the single change most likely to end the problem you wrote in about — regardless of what you do with the rest of this report.

### X2 — No rationale for the 30s timeout

`CLAUDE.md:13` says 30s, `AGENTS.md:6` says 60s, and **neither says why**. Nothing in the code sets a timeout at all (`grep -rn "timeout"` finds only the two docs), so there is no way to adjudicate — not for an agent, and not for you in six months. A number with no reason attached is the first thing that gets "simplified" away.

**Recommend:** pick one and attach the mechanism — "Network calls time out at 30s; the upstream gateway drops connections at 35s." One clause makes the rule survivable and settles the conflict permanently.

### X3 — No precedence statement

Three instruction files load (`CLAUDE.md`, `.claude/rules/style.md`, and `AGENTS.md` for non-Claude tools) and none says which wins — a repo-wide grep for "precedence", "takes priority", "wins" and "overrides" returns nothing. Cheap to add, and it converts a whole class of conflicts from *arbitrary* into *resolved*.

**Recommend:** one line at the top of `CLAUDE.md` — e.g. "`.claude/rules/` is authoritative for style; this file is authoritative for workflow. Where they disagree, `.claude/rules/` wins."

### X4 — Two files document a linter that does not exist

`CLAUDE.md:3` and `AGENTS.md:3` both promise `npm run lint`, and the repo has no linter at all. Either add one (and the `lint` script), or stop promising it. Right now the docs describe a tool nobody can run.

---

## Out of scope

Noticed while reading code as evidence. Not this audit's business — flagged in one line each so they are not lost:

- `src/api/handler.ts` is one line of code followed by eight `// change 1` … `// change 8` marker comments. Placeholder noise; git remembers the history better.
- `package.json` is minified onto a single line, which makes diffs and merges harder than they need to be.
- No `.gitignore`, no CI configuration, and no lint or format tooling anywhere in the repo.

---

## Re-check next time

1. **Did the package-manager decision get *enforced*, or only re-stated?** If `packageManager` and a lockfile are still absent at the next audit, the symptom will still be here no matter how `CLAUDE.md` is worded.
2. **`AGENTS.md` will re-fork.** Its header is byte-identical to `CLAUDE.md`'s while its rules have already flipped three ways. If it still exists as a separate file rather than an `@import`, diff it first — that is where the next contradiction will be.
3. **`docs/architecture.md` vs `src/` churn.** The doc has not moved since `init` while `src/` took ten commits, one deletion and one addition. Re-run the git rev-list count of commits to `src` since the doc's last touch; if it is climbing again, the doc has drifted again.
4. **Emphasis ratio.** It is at 27% today. Re-count ALWAYS / NEVER / IMPORTANT / MUST / CRITICAL in `CLAUDE.md` — instruction files rot by accretion, and the reflex when a rule is ignored is to capitalise it, which makes the problem worse.

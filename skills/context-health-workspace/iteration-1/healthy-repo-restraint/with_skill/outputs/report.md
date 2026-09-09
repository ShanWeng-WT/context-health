# Context health — fixture-clean — 2026-09-08

Repo audited: `C:\Users\SHAN~1.WEN\AppData\Local\Temp\claude\D--Projects-context-health\fcaaff73-c399-4001-9a21-acf79292aa34\scratchpad\fixture-clean`
Read-only audit. Nothing in the repo was created, edited, moved or deleted.

**Short answer to "is there bloat I should cut": no.** This repo's own always-on context
is 104 tokens — 0.05% of a 200k window — and every line of it is load-bearing. There
are no P1 or P2 findings. The four P3s below are notes, not a to-do list; only one of
them (adding a year to a deadline) is clearly worth doing, and it costs zero tokens.

## Always-on cost

Loaded at the start of every session in this repo, before you type anything:

| Tokens | % window | File | Kind |
|---:|---:|---|---|
| 895 | 0.45% | `(skill listing)` | skill name+description lines, from `~/.claude/skills` |
| 104 | 0.05% | `CLAUDE.md` | project memory |
| **999** | **0.50%** | **ALWAYS-ON TOTAL** | |

On-demand context inside the repo: `docs/overview.md` only (~29 tokens). The ledger's
~51k on-demand figure is your machine-wide skill bodies and references, which cost
nothing until invoked.

That total is comfortably defensible — and note the split: 90% of it is your global
skill listing, which follows you into every repo, and 10% is this repo. There is no
repo-level lever here worth pulling.

Reproduce: `python scripts/ledger.py <repo>` and `python scripts/sweep.py <repo> --comments`
(the sweep returned 0 candidates across all nine detectors).

## Findings

No P1 (misleading or conflicting always-on context). No P2 (misleading on-demand
context, or dilution in the always-on tier). The detector sweep raised zero candidates,
and reading all five files end to end raised nothing that survived verification into a
P1 or P2. The P3s:

| # | Claim | Site | Harm x reach | Confidence | Recommend |
|---|---|---|---|---|---|
| P3-1 | Build/test/lint line restates `package.json` scripts — derivable | `CLAUDE.md:3` | Costly x always-on | high | Leave it. ~20 tokens; see below. |
| P3-2 | "deleted in Q4" has no year, so it cannot go stale detectably | `CLAUDE.md:7` | Diluting x always-on | high | Add the year. Zero token cost. |
| P3-3 | The three commands CLAUDE.md points at have no declared toolchain | `CLAUDE.md:3` | Misleading x always-on *if confirmed* | low-med | Verify, then add one clause. |
| P3-4 | 895 of 999 always-on tokens are 13 global skills, none applicable here | `(skill listing)` | Costly x always-on | high | A question, not a defect. |

### P3-1 — Command line is derivable from `package.json`, and that is fine  ·  `CLAUDE.md:3`  ·  Costly x always-on  ·  confidence high

**Quoted:** "Build with `npm run build`, test with `npm run test`, lint with `npm run lint`."

**Evidence:** `cat package.json` returns
`{"name":"clean","scripts":{"build":"tsc -p .","test":"vitest run","lint":"eslint ."}}`.
All three script names resolve exactly; nothing is wrong with the line, it is simply
restating a file the agent can read.

**Why it hurts the agent:** It does not, materially. Restated `package.json` scripts are
textbook derivable content, and in a bloated file this would be the first cut.

**Recommend:** No action. Removing it saves ~20 tokens (0.01% of the window) and buys a
small risk that the agent guesses `yarn` or `pnpm`. Credible sources disagree here —
Anthropic's guidance says prune the derivable; GitHub's Copilot guidance explicitly
recommends stating validated build commands. At this file size the debate has no stakes.
Cutting this line is the only "bloat" available in the repo, and it is not worth the edit.

### P3-2 — An undated deadline cannot be caught by the next audit  ·  `CLAUDE.md:7`  ·  Diluting x always-on  ·  confidence high

**Quoted:** "`src/legacy_adapter.ts` is intentionally not covered by tests; it is deleted in Q4."

**Evidence:** `git log -1 --format=%ad --date=short -- CLAUDE.md` returns `2026-09-08`, and
the file still exists (`ls src/legacy_adapter.ts`). Q4 of which year is unstated, so no
reader — human or agent — can tell whether this line is current or two years past due.

**Why it hurts the agent:** Today the line is true and useful. The moment the deletion
slips or lands, it becomes a claim about the repo that nobody can date, and stale
always-on claims are exactly how an agent starts confidently acting on things that are
no longer so.

**Recommend:** Write "Q4 2026" instead of "Q4". One word, no token delta, and it converts
an unfalsifiable claim into one a future audit can mechanically check.

### P3-3 — Verify the toolchain is actually available before trusting the command line  ·  `CLAUDE.md:3`  ·  Misleading x always-on if confirmed  ·  confidence low-med

**Quoted:** "Build with `npm run build`, test with `npm run test`, lint with `npm run lint`."

**Evidence:** `package.json` declares no `dependencies`, no `devDependencies`, and there is
no lockfile (`find . -not -path "./.git/*" -type f` returns exactly five files). So `tsc`,
`vitest` and `eslint` are not provisioned by the repo. There is also no CI config and no
justfile to cross-check against, and no test file exists anywhere
(`find . -name "*test*" -o -name "*spec*"` returns nothing), so `vitest run` currently has
nothing to run.

**Why it hurts the agent:** If the toolchain is not globally installed, an agent that
follows `CLAUDE.md:3` runs three commands that fail, then starts improvising — installing
packages, editing `package.json`, or concluding the build is broken. That would be a P1.
I am holding it at P3 because this repo is small enough that the toolchain may be
deliberately global, and a five-file repo may simply be mid-setup. I could not settle it
from inside the repo.

**Recommend:** Run `npm run build` once. If it works from the repo, add nothing. If it works
only because the tools are installed globally, add a five-word clause — "toolchain is
expected globally" — which is precisely the kind of external constraint that is expensive
to rediscover.

### P3-4 — The skill listing is 90% of your always-on tax, and none of it applies here  ·  `(skill listing)`  ·  Costly x always-on  ·  confidence high

**Evidence:** `ls ~/.claude/skills` shows 24 skills, 13 of which carry descriptions and
therefore appear in every session's listing (~895 tokens). They cover Unity, Perforce,
PowerShell and game-ID refactoring. This repo is a three-file TypeScript/npm project.

**Why it hurts the agent:** Mild dilution rather than harm. I checked the 13 descriptions
for the failure that actually matters — overlapping triggers causing the wrong skill to
fire — and found none: even the four Perforce skills have cleanly disjoint triggers
(`p4-export` on changelist extraction, `p4-workspace-check` on client/dir mismatch,
`p4-port-cl` on cross-stream porting, `p4-claude-simplify` on reviewing changed files).
The descriptions are well-formed.

**Recommend:** Report as a question, not a defect. 0.45% per session is cheap insurance for
skills you want available everywhere. If you ever do want it back, the move is to
project-scope the Unity/Perforce skills into the repos that use them rather than to shorten
their descriptions — `powershell-preflight` is the longest at ~130 words, and its length is
doing real trigger work. This is machine-wide config, outside this repo; I changed nothing
there.

## Load-bearing — leave this alone

Every line in `CLAUDE.md` except the command line passes the deletion test. Named
explicitly so a future pruning pass does not take them:

- **`CLAUDE.md:5-6` — the retry cap and its reason.** "Retries on outbound calls are
  capped at 3: the payment provider rate-limits at 4, and exceeding it caused the January
  outage. Do not raise this without asking." Verified against `src/index.ts:1`
  (`export const RETRY_LIMIT = 3`) — code and doc agree. The number is in the code; the
  *mechanism* (provider limit of 4), the *incident* (January outage) and the
  *change-control expectation* exist nowhere else in the repo and are unrecoverable from
  it. This is the single highest-value sentence in the repo. Do not shorten it.
- **`CLAUDE.md:7` — the deliberate test exclusion.** Without it, an agent asked to improve
  coverage will write tests for a file that is being deleted, and then defend them.
  Deliberate exclusions cannot be inferred from code, which only shows what *is* there.
- **`CLAUDE.md:8` — "Migrations run forward-only. There is no down-migration path by
  design."** Same category: an agent writing a migration will produce a down-migration by
  default unless told not to. The phrase "by design" is doing the work — it marks the
  absence as intentional rather than as an oversight to fix.
- **`docs/overview.md`** (on-demand, ~29 tokens). It overlaps `CLAUDE.md:7` on the legacy
  adapter, so I diffed them: they agree ("deleted in Q4" vs "scheduled for removal") and
  have not drifted, and both referenced paths exist. Duplication that has not drifted, in
  the on-demand tier, at 29 tokens, is not a finding.

## Missing

Where the absence of context could cost you, in rough priority order:

1. **Where migrations actually live.** `CLAUDE.md:8` states a migration policy, but
   `grep -rI "migrat" . --exclude-dir=.git` matches only `CLAUDE.md` — no migrations
   directory, no migration tooling in `package.json`. The rule is correct and worth
   keeping, but an agent has no referent for it. One clause naming the directory or the
   sibling service would make it actionable instead of abstract.
2. **A one-line statement of what this project is.** `CLAUDE.md:1` is `# clean` and nothing
   else. The retry rule mentions a payment provider; that is the only hint an agent gets
   about the domain. One sentence is cheap, and it is not derivable from three files of code.
3. **Whether a test suite is expected.** `npm run test` is documented, `vitest run` is
   configured, and zero test files exist. If the convention is "tests are coming" or "tests
   live elsewhere", say so; otherwise an agent reads the `CLAUDE.md:7` carve-out as implying
   the rest of the repo *is* covered.

Deliberately **not** recommended: adding a unit comment to `src/legacy_adapter.ts:3`
(`export const MAGIC=86400000`, evidently milliseconds in a day). Normally an unexplained
magic constant is a clean "add a comment" finding, but this file is scheduled for deletion
and is explicitly excluded from tests — documenting it would be work spent on something you
have already decided to remove.

## Out of scope

Noticed while reading code as evidence; all belong to a different review:

- `src/legacy_adapter.ts:1` — `p(a:any,b:any,c?:any)` with three nested conditionals and an
  untyped return. Code quality, and the file is being deleted anyway.
- `package.json` — no `devDependencies` and no lockfile for `tsc`/`vitest`/`eslint`. A
  packaging concern; it reaches this audit only through P3-3.
- No CI configuration in the repo, so no automated check would catch drift between
  `CLAUDE.md` and the code.

## Re-check next time

1. **The Q4 legacy-adapter deletion.** When it lands, two places go stale at once —
   `CLAUDE.md:7` and `docs/overview.md:2-3`. This is the only doc coupling in the repo, and
   the single most likely thing to rot.
2. **`RETRY_LIMIT` drift.** `src/index.ts:1` and `CLAUDE.md:5` both say 3 today. If someone
   raises the constant without touching `CLAUDE.md`, the most valuable sentence in the repo
   turns into the most misleading one. Cheap check:
   `grep -n "RETRY_LIMIT" src/index.ts && grep -n "capped at" CLAUDE.md`.
3. **The skill listing.** 895 tokens now, and the only line item in the ledger with real
   growth potential — it grows every time you add a skill anywhere on the machine. Worth
   re-pricing, not worth acting on yet.

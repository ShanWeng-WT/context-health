# Context health — fixture-clean — 2026-09-08

**No, there is no bloat worth cutting here** — the repo's own always-on context is a single 8-line CLAUDE.md at ~104 tokens (0.05% of a 200K window), every command and path in it checks out, and the three notes below are accuracy nits worth ~38 tokens combined.

## Always-on cost

Loaded at the start of every session, before you type anything:

| Tokens | % window | File | Kind |
|---:|---:|---|---|
| 895 | 0.45% | `(skill listing)` | skill name+description |
| 104 | 0.05% | `CLAUDE.md` | project memory |
| **999** | **0.50%** | **ALWAYS-ON TOTAL** | |

Reproduce: `python scripts/ledger.py <repo>`.

That is defensible by a wide margin. Two things are worth separating, because the headline number is misleading in your favour:

- **The repo contributes 104 of those 999 tokens.** The other 895 (90%) is the listing of your 24 personal skills in `C:\Users\shan.weng\.claude\skills\`, which loads on *every* repo you open, not just this one. If you ever want to reduce always-on cost, that is the only lever with real weight — and it belongs to a separate audit of your global skills, not to this repo.
- **The ledger's "~51,338 tokens across 33 files" of on-demand context is also entirely your global skills directory**, not this repo. I checked every path in `ledger.py --json`: all 33 are under `~/.claude/skills`. This repo's on-demand context is one file, `docs/overview.md`, at 114 chars (~29 tokens).

On the three on-demand questions the ledger does not answer:

- **Who wrote it?** The repo's own agent-facing prose is 528 bytes total, all authored, none vendored or generated. There is no `.claude/`, no `.cursor/`, no `.github/copilot-instructions.md`, no `AGENTS.md`, no rules files, no skills, no subagents (`find <repo> -not -path '*/.git/*'` returns 5 files).
- **Can it be reached?** Yes. `CLAUDE.md` loads at launch; `docs/overview.md` is a normal doc an agent finds by looking. Nothing is shadowed, nothing sits in a directory the tool never scans.
- **Does it pull in anything from outside?** No. `grep -rniE "http://|https://|fetch |curl |WebFetch"` over the repo returns nothing — no fetch-and-obey (catalogue M9), the one context defect that is also a security defect.

## Findings

**No P1s. No P2s.** The detector sweep (`python scripts/sweep.py <repo> --comments`) returned `"findings": []` — zero candidates across all nine detectors: dead command, dead path, drifted doc, drifted count, perishable claim, unmaterialized symlink, stale comment, aspirational rule, fetch-and-obey. I then read the always-on set end to end and verified each claim in it by hand; three low-severity notes survived, and none of them is a cost problem.

| # | Claim | Site | Harm × reach | Confidence | Recommend |
|---|---|---|---|---|---|
| P3-1 | `Q4` has no year, so this line cannot be seen to expire | `CLAUDE.md:7` — "it is deleted in Q4" | Costly × always-on | high | Write `Q4 2026` (or the tracking issue). ~+1 token. Catalogue M5's fix: date the line so its age is visible. |
| P3-2 | Migrations rule has nothing in this repo to attach to | `CLAUDE.md:8` — "Migrations run forward-only. There is no down-migration path by design." | Costly × always-on | low | Confirm it still applies. If the migration tooling lives in another repo, keep it; if it is vestigial, cut it (~18 tokens). `grep -rin "migrat" <repo>` matches only this line. |
| P3-3 | Build/test/lint line restates `package.json` scripts | `CLAUDE.md:3` | Costly × always-on | high (derivable), low (that cutting is right) | Optional. ~20 tokens, and credible guidance disagrees — Copilot's docs explicitly recommend keeping validated build commands in the instruction file. Leaving it is a defensible choice; I would not spend a change on it. |

Total recoverable if you cut both cuttable lines: ~38 tokens, taking `CLAUDE.md` from ~104 to ~66. That is not a reason to act. Act on P3-1 because it will be wrong in a year, and on P3-2 only if the answer is "vestigial."

## Load-bearing — leave this alone

Do not let an audit talk you into pruning these. They are the reason this file is good.

- **`CLAUDE.md:5-6` — the retry cap and its rationale.** "Retries on outbound calls are capped at 3: the payment provider rate-limits at 4, and exceeding it caused the January outage. Do not raise this without asking." `src/index.ts:1` carries `export const RETRY_LIMIT = 3` — the *number* is in the code, but the mechanism (provider limit of 4), the incident, and the change-control expectation exist nowhere else. This is the textbook keep: without it an agent "simplifies" the cap and reintroduces the outage. ~35 tokens, the best-spent tokens in the repo.
- **`CLAUDE.md:7` — the deliberate test exclusion.** "`src/legacy_adapter.ts` is intentionally not covered by tests." The file exists (`src/legacy_adapter.ts`, 144 bytes, deliberately ugly) and there are no test files anywhere in the repo. Code can only show what *is* there; only this line stops an agent from "fixing" the coverage gap or refactoring a file that is on its way out. Keep the sentence when you fix the `Q4` date in P3-1.
- **`CLAUDE.md:8` — forward-only migrations,** *if* P3-2 resolves as "still true." A stated deliberate exclusion an agent cannot infer from anything in the tree.
- **`docs/overview.md`** — 114 chars, on-demand, correct: `src/index.ts` is the entry point and the legacy adapter is scheduled for removal. Its overlap with `CLAUDE.md:7` is corroboration, not contradiction, and at on-demand cost it is a rounding error. Nothing to do.

## Missing

Nothing rises to a recommendation. For a repo of five files, the context file already carries the two things code cannot say (the retry rationale, the deliberate exclusion). The one thing that would help future-you more than any cut: name the owner or tracking issue for the legacy-adapter removal alongside the date in `CLAUDE.md:7`, so the line has something to expire against.

## Out of scope

Noticed while verifying commands; these are repo/config issues, not context findings, and belong to a different review.

- `package.json` declares `"build": "tsc -p ."` but there is no `tsconfig.json` in the repo, so the documented build command would fail as written.
- `"test": "vitest run"` resolves, but there are no test or spec files anywhere, so it has nothing to run.
- `src/legacy_adapter.ts` is dense and untyped (`any` throughout, an unexplained `MAGIC=86400000`). Deliberate per `CLAUDE.md:7`; not this audit's business.

## Re-check next time

1. **`CLAUDE.md:7`, the Q4 deletion.** Either `src/legacy_adapter.ts` is gone and the whole line should go with it, or the date slipped and the line is now quietly false. This is the single most perishable sentence in the repo.
2. **`CLAUDE.md:8`, the migrations rule** — whether migrations ever arrive in this repo, or the line is confirmed as inherited policy.
3. **`CLAUDE.md:5-6` against `src/index.ts`.** If `RETRY_LIMIT` ever changes without this paragraph changing, that flips instantly from the repo's best context to a P1 misleading always-on claim.
4. **Your global skills listing (895 tokens, 24 skills).** It is 90% of what loads every session in every repo. Worth its own audit at some point; nothing about this repo will surface it.

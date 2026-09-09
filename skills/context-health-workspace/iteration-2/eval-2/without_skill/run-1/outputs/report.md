# Agent Context Audit

**Repo:** `fixture-clean` (5 tracked files, 1 commit)
**Audited:** 2026-09-08
**Verdict: No bloat. Cut nothing.**

---

## Headline

I went looking for bloat and did not find any. The entire agent context is one
file, `CLAUDE.md`, at **8 lines / 414 bytes (~110 tokens)**. Every factual claim
in it checks out against the code, and three of its four content lines carry
rationale an agent could not derive by reading the repo.

This is a well-maintained context file. The honest recommendation is to leave it
alone.

## What counts as agent context here

| Path | Bytes | Role |
|---|---|---|
| `CLAUDE.md` | 414 | The only agent instruction file |
| `docs/overview.md` | 114 | Human docs, not auto-loaded |

Confirmed absent: `.claude/`, `.cursor/`, `.github/`, `AGENTS.md`,
`.cursorrules`, `*.mdc`, `settings.json`. There is no second context surface
and no rules sprawl.

## Claim-by-claim verification

| Claim in `CLAUDE.md` | Verified against | Result |
|---|---|---|
| Build / test / lint commands | `package.json` scripts block | **Accurate** — all three script names match exactly |
| Retries capped at 3; provider rate-limits at 4; caused the January outage | `src/index.ts:1` `RETRY_LIMIT = 3` | **Accurate**, and the *reason* exists nowhere in code |
| `src/legacy_adapter.ts` intentionally untested, deleted Q4 | No test files exist anywhere in repo; corroborated by `docs/overview.md` | **Consistent** |
| Migrations are forward-only by design | No migrations directory in repo | **Unverifiable here** — see note below |

## Why this file earns its tokens

The test for a context line is: *would an agent get this wrong without being
told?* Three lines clear that bar decisively.

- **The retry cap.** An agent reading `src/index.ts` sees `RETRY_LIMIT = 3` and
  learns nothing about *why*. `3` looks like an arbitrary default and a
  well-meaning agent would happily bump it to 5. The file supplies the two facts
  that make it load-bearing — the provider's ceiling of 4, and the January
  outage — plus an explicit "do not raise without asking." This is the single
  highest-value line in the repo.
- **The untested legacy adapter.** `src/legacy_adapter.ts` is genuinely ugly
  code (nested conditionals, `any` types, an unexplained `MAGIC = 86400000`). It
  is exactly the file an agent would volunteer to add tests for or refactor.
  The line pre-empts that wasted work by naming it deliberate and dated.
- **Forward-only migrations.** A stated design constraint with no code artifact
  to infer it from. Prevents an agent from helpfully authoring a down-migration.

Each of these prevents a specific, plausible wrong action. That is what
non-inferable context looks like.

## The one arguably-trimmable line — and why I would keep it

Line 3, the build/test/lint commands, *is* technically derivable: it restates
`package.json`. By a strict "never duplicate the code" rule it could go.

I do not recommend cutting it. It is a single line, it saves an agent a file
read on essentially every task, and the scripts here are non-obvious enough to be
worth stating (`vitest run`, not `npm test`; `tsc -p .`, not a bundler). The
token cost is roughly 20. Removing it would be tidiness for its own sake, not a
real saving.

## Two things to watch (not cuts)

1. **`Q4` will go stale.** The legacy-adapter line is pinned to a relative date
   with no year. Once Q4 passes, an agent cannot tell whether the deletion
   already happened. When `src/legacy_adapter.ts` is removed, delete that line
   in the same commit. Consider writing it as an absolute quarter (e.g. "Q4
   2026") in the meantime.
2. **The migrations claim has no in-repo anchor.** There is no migrations
   directory here, so I could not confirm it. It most likely describes
   infrastructure living outside this repo, which is a legitimate thing for a
   context file to cover. Flagging only so you can confirm it is still true —
   an unverifiable rule is the kind that quietly rots. Do not cut it on my say-so.

## Recommended action

**None.** No file to delete, no section to trim, no duplication worth resolving.
Re-audit when `CLAUDE.md` grows past roughly 50 lines, or when the legacy
adapter is deleted — whichever comes first.

---

*The repo was treated as read-only; no files were created, modified or removed
inside it.*

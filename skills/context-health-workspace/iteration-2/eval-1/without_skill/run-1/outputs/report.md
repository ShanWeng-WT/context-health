# Why Claude ignores your CLAUDE.md

Repo audited (read-only, nothing modified):
`C:/Users/SHAN~1.WEN/AppData/Local/Temp/claude/D--Projects-context-health/fcaaff73-c399-4001-9a21-acf79292aa34/scratchpad/fixture-repo`

Short version: Claude isn't ignoring your rule. It's receiving three different answers to
"which package manager?" in the same context window, and one of those answers is demonstrated
three times as a working command right above the rule that forbids it. Under that much
conflict, "obey the rule" and "ignore the rule" look identical from the inside - the model just
picks one. The same disease affects at least three other rules you probably think are active.

---

## 1. The package manager symptom, traced

Three signals, two of them against you:

| Source | Line | Says |
|---|---|---|
| `CLAUDE.md` | 7 | `- ALWAYS use pnpm to install dependencies.` |
| `AGENTS.md` | 6 | `- ALWAYS use npm to install dependencies.` |
| `CLAUDE.md` | 3-4 | Run `npm run build` ... `npm run lint` ... `npm run test` |

Three things are going wrong at once.

**a) `AGENTS.md` contradicts `CLAUDE.md` head-on.** Both files sit at the repo root. `CLAUDE.md`
is loaded by Claude Code; `AGENTS.md` is the cross-tool convention that many agent setups load
as well, and even when it isn't auto-loaded it's a root-level file the model will read the moment
it looks around. Two rules, both marked `ALWAYS`, mutually exclusive. Nothing in either file says
which one wins. There is no principled way for the model to resolve this, so the outcome is
effectively arbitrary - which is exactly the "it just does whatever" you're seeing.

**b) `CLAUDE.md` contradicts itself.** Lines 3-4 model `npm run build`, `npm run lint`, and
`npm run test` as the way to work in this repo. Line 7 then says always use pnpm. Concrete,
copyable examples are much stronger behavioral signals than abstract directives - the model has
three worked `npm` examples and one bare assertion pointing the other way. This is likely the
single biggest driver, and it would still bite you even if `AGENTS.md` were deleted tomorrow.

**c) Nothing on disk breaks the tie.** There is no `pnpm-lock.yaml`, no `package-lock.json`, no
`yarn.lock`, and no `packageManager` field in `package.json`. When the docs disagree, the model
falls back to evidence in the repo - and there is none. The one tie-breaker that would settle
this mechanically is absent.

## 2. The same contradiction pattern, three more times

The package manager rule is not a one-off. Every place your context is duplicated, the copies
have already drifted apart:

| Topic | `CLAUDE.md` | `AGENTS.md` | `.claude/rules/style.md` | Actual ground truth |
|---|---|---|---|---|
| Package manager | pnpm | npm | - | none (no lockfile) |
| Exports | named | **default** | named | - |
| Network timeout | 30s | **60s** | - | - |
| Test framework | Jest ("as of 2024-03") | - | **vitest** | `package.json`: `"test": "vitest"` |

Note the last row: `CLAUDE.md` states a testing framework that `package.json` disproves. When a
model reads a rule file and can verify one of its claims is false, it rationally discounts the
rest of the file - including the rules that *are* correct.

## 3. `.claude/rules/style.md` is probably never loaded at all

There is not a single `@` import directive in `CLAUDE.md` or `AGENTS.md` (verified by grep).
Claude Code auto-loads `CLAUDE.md` and nested `CLAUDE.md` files; it does not walk
`.claude/rules/*.md` and pull it into context on its own - that content reaches the model only if
something imports it or the model happens to open the file.

So the two rules living there - "Use vitest for all unit tests" (the *correct* one, matching
`package.json`) and "Prefer named exports" - are most likely dead text. Your accurate testing
rule is in the file that doesn't load; your inaccurate one (Jest) is in the file that does.

## 4. Five references that point at nothing

Once a model follows a dead pointer, it stops trusting the map. These all fail:

| Reference | Where | Reality |
|---|---|---|
| `src/api/legacy.ts` ("tests live in") | `CLAUDE.md:4` | Never existed in the entire git history |
| `npm run lint` | `CLAUDE.md:3`, `AGENTS.md:3` | No `lint` script in `package.json` |
| "run the formatter before every commit" | `CLAUDE.md:9` | No formatter script and no formatter dependency anywhere - the instruction is unexecutable |
| `src/api/router.ts` | `docs/architecture.md:2` | Deleted in commit `30d2f16 "remove router"` |
| `src/api/missing.ts` | `docs/architecture.md:2` | Never existed |

`package.json` defines exactly two scripts: `build` and `test`. Two of the three commands your
context teaches the model to run do not exist.

## 5. Stale facts that were never true, or are no longer true

- "We currently have 12 services in this monorepo." - the repo contains three source files and no
  services directory.
- "As of 2024-03, we use Jest for testing." - `package.json` says vitest. Date-stamping a fact
  documents when it rotted; it doesn't stop the rot.

## 6. Emphasis inflation

Five of the twelve bullets in `CLAUDE.md` shout: `ALWAYS`, `NEVER`, `IMPORTANT: ... MUST`,
`CRITICAL`. When ~40% of rules are maximum priority, emphasis carries no information - the model
cannot distinguish the rule you'd be angry about (package manager) from a routine preference
(2-space indentation), because they are styled identically.

The failure is self-demonstrating: your pnpm rule is marked `ALWAYS`, and so is the `npm` rule
that overrides it. Emphasis was spent rather than earned, so when you actually needed it, it had
no purchasing power left.

## 7. Filler that costs context and buys nothing

- "Think step by step before answering." - generic prompt boilerplate, not a fact about your project.
- "You are an expert TypeScript engineer." - role-play preamble; no behavioral effect sitting in a rules list.

Beyond wasting tokens, these signal that the file is an unmaintained grab bag, which further
lowers the authority of the real rules sitting next to them.

## 8. Git proves the drift

Every context file (`CLAUDE.md`, `AGENTS.md`, `docs/architecture.md`, `.claude/rules/style.md`)
was written in the initial commit `c96e1d2` and **has not been touched since**. Eleven commits
landed afterward, all of them in `src/`.

Churn ranking:

```
9 commits  src/api/handler.ts     <- hottest file in the repo, mentioned in ZERO context files
2 commits  src/api/router.ts      <- deleted; still documented as live
1 commit   src/api/new_module.ts  <- added; documented nowhere
1 commit   src/db/pool.ts
```

The file Claude will touch most often is invisible to it, and the file it is told to look for was
deleted. Your context describes a repo that stopped existing eleven commits ago.

---

## Recommendations

I did not modify anything in the repo. In rough priority order:

1. **Pick one package manager and make the prose agree.** Fix the rule *and* rewrite the
   `npm run build/lint/test` examples in `CLAUDE.md` to match. Leaving the examples as-is keeps
   the bug alive no matter what the bullet says.
2. **Commit the matching lockfile** and add a `packageManager` field to `package.json`. This is
   the real fix - a lockfile enforces the choice mechanically; the doc line is just a reminder.
3. **Collapse `AGENTS.md` and `CLAUDE.md` into one source of truth.** Make one canonical and
   reduce the other to a one-line pointer (or a symlink). Two hand-maintained rule lists will
   always diverge - they already have, on four separate topics.
4. **Either wire up `.claude/rules/style.md` with an `@` import, or inline it.** Right now your
   only correct testing rule lives in a file that probably never loads.
5. **Delete the five dangling references.** Prefer deletion over correction where the content
   isn't load-bearing: a doc that names no file paths cannot rot into a lie.
6. **Delete the unverifiable facts** ("12 services", "as of 2024-03 Jest"). Point at
   `package.json` rather than restating it - restated facts are the ones that go stale.
7. **Strip emphasis down to the one or two rules where a violation is actually expensive.**
   If everything is `CRITICAL`, nothing is.
8. **Cut the two filler lines** ("think step by step", "you are an expert").
9. **Document `src/api/handler.ts`**, or accept that the most-edited file in the repo is
   invisible to the model.
10. **Enforce what you can, mechanically.** Add real `lint` and `format` scripts (the docs already
    promise both), a pre-commit hook, and branch protection on `main` to back the "never commit
    directly to main" rule. Rules a tool enforces do not depend on the model remembering them
    under contradictory instructions.

### The general lesson

The rules you care about most were the ones stated most emphatically and duplicated into the most
places - and duplication is precisely what caused them to drift into self-contradiction.
Reliability comes from stating each fact exactly once, in the file that actually loads, and
letting tooling enforce anything that genuinely matters.

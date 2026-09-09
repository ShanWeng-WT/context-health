# context-health

A Claude Code skill that audits a repository's **agent-facing context** — CLAUDE.md,
AGENTS.md, cursor and copilot rules, skills, subagent prompts, READMEs, architecture
notes and code comments — for the rot that accumulates over months of work: stale
claims, contradictions, duplication, and text that costs tokens every session without
changing what the agent does.

It diagnoses and prioritizes into one report file. It never edits the context it audits.

## Why

Instruction files rot the way sediment settles: adding a line feels safe, removing one
feels risky, so every session leaves a layer behind. Nothing looks broken — the agent
just gets slightly worse each month. It follows a rule that stopped being true, or
misses the rule that mattered because forty others were shouting too.

The cost is not only tokens. Bloated instruction files measurably cause agents to
*ignore* rules that are still correct, so this is a correctness problem wearing a
budget problem's clothes.

## Install

```bash
cp -r skills/context-health ~/.claude/skills/
```

Then ask for an audit, or just describe the symptom — "Claude keeps ignoring my
CLAUDE.md" triggers it too.

## What it does

1. **Prices the always-on tier.** Everything loaded at the start of every session,
   before you type: CLAUDE.md at every level plus its `@imports` (which do *not* reduce
   context), unscoped rules, MEMORY.md, the skill listing, and other tools'
   equivalents. Then characterizes the on-demand tier by who owns it — authored,
   vendored, or generated.
2. **Sweeps for candidates.** Ten detectors, all on by default (`--no-comments` skips
   the source-comment pass): broken paths, vanished commands, cross-file duplication,
   docs whose subject moved on, emphasis saturation, three shapes of contradiction,
   perishable claims, prompt scaffolding written for a model generation that no longer
   needs it, fetch-and-obey — a context file that tells the agent to pull in unpinned
   remote content and follow it — and comment smells: commented-out code, changelog
   in a comment, perishable measurements.
3. **Reads the always-on set in full** — small by definition, and where the worst
   findings hide from greps.
4. **Verifies.** Each candidate must survive its named false-positive trap and carry a
   command someone else can re-run. Findings without both are dropped.
5. **Reports to a file.** The audit is written to `context-health-<date>.md`; the chat
   gets the one-sentence answer, the always-on total and its recoverable share, one
   line per P1, and the path. Findings are prioritized by harm × reach — token cost is
   a peer harm here, ranked by measured size — and carry four fields: claim, quote,
   evidence, recommendation, with a token delta and what the shorter version still
   carries. A cut counts as **recoverable** only when every line in it fails the
   load-bearing test; otherwise the recommendation is to **salvage** — compress it,
   move it down a tier, merge the duplicate copies — so the tokens come back and the
   knowledge stays. Hence the explicit *leave this alone* section, and what's
   **missing**: an audit that only subtracts is doing half the job.

## Layout

```
skills/context-health/
├── SKILL.md                      the process
├── SOURCES.md                    every principle traced to its source
├── references/
│   ├── catalogue.md              40 finding types: why each hurts an agent,
│   │                             how to detect it, the trap, the fix
│   └── keep-or-cut.md            the load-bearing rubric, and where
│                                 credible sources genuinely disagree
└── scripts/
    ├── ledger.py                 always-on token accounting
    └── sweep.py                  the ten detectors
```

Both scripts need only Python 3 (plus git, for staleness) and emit `--json` for CI
gating or run-to-run diffing.

## Scope

The subject is **the prose an agent reads**. Code is *evidence* — read constantly to
check whether the prose is still true, cited in findings, never the thing being
changed. Recommendations that would alter implementation, naming, architecture or
formatting belong to a different review, and the report says so under Out of scope.

It also does not optimize for shorter. A dense paragraph explaining why retries are
capped at three is load-bearing context that saves an agent from reintroducing a bug;
cutting it makes the file shorter and the repo worse. The target is useful information
per token, which sometimes means recommending *more* context.

## Design provenance

[`SOURCES.md`](skills/context-health/SOURCES.md) records every adopted principle with
its source, the vendor constants the scripts depend on (which go stale — check them
first), where sources disagree and what the skill does about it, and the evaluation
record. Built from parallel research across Anthropic documentation and skills, OpenAI
documentation and cookbook, 2026 community practice, and the software-design
literature on comments and documentation rot.

## Evaluation

Three cases — an explicit audit of a real production monorepo, a symptom-led request on
a fixture with planted defects, and a deliberately healthy repo with deliberately ugly
code — each run with and without the skill.

Iteration 1 scored 100% with the skill against a 91.7% baseline. The baseline was
strong; the separation came from token accounting, scope discipline, factual precision
on citations, and correctness about what actually loads. Iteration 2 closed four gaps
the baseline had exposed. Details in `SOURCES.md` §5b.

Detector precision was tuned against a repo believed healthy — the naive sweep produced
233 candidates there, of which almost none were real; the tuned sweep produces 14 —
then recall was confirmed against planted defects. **A detector that fires on a
well-maintained repo is broken.**

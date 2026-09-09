---
name: context-health
description: Audits the agent-facing context in a repository — CLAUDE.md, AGENTS.md, cursor and copilot rules, skills, subagent prompts, READMEs, architecture notes and code comments — for stale, contradictory, duplicated and low-signal text, and prices what it costs in always-on tokens. Diagnoses and prioritizes; never edits. Use when someone asks to audit, review, prune or clean up their agent context, CLAUDE.md, AGENTS.md or rules files, asks which documentation is worth keeping, or wants to cut the token cost of a repo. Use it just as readily when they describe the symptom rather than asking for an audit: the agent ignores instructions, follows outdated guidance, contradicts itself between files, keeps re-explaining things it should already know, or has been getting quietly worse on a repo they have worked in for months.
---

# Context health

Instruction files rot the way sediment settles: adding a line feels safe, removing one
feels risky, so every session leaves a layer behind. Nothing looks broken. The agent
just gets a little worse each month — it follows a rule that stopped being true, or
misses the one rule that mattered because forty others were shouting too.

You are diagnosing that. **Report, do not repair.** The deliverable is a Markdown file
holding a prioritized diagnosis the user can act on; they decide what changes. This
isn't timidity — a context file is a team artifact whose lines usually encode a reason
you cannot see from inside the repo, and the failure mode of an eager pruner is
deleting the one sentence that was holding back a recurring bug.

## What counts as your subject

Your subject is **the prose an agent reads**: instruction files, rules, skill and
subagent definitions, READMEs, architecture notes, ADRs, and code comments.

Code is your **evidence**, not your subject. You read it constantly — to check whether
a documented path exists, whether a command still resolves, whether a described
behaviour is still the behaviour — and you cite it in findings. But every finding you
report is about the prose. If your recommendation changes a function, a name, a file
layout or a formatting choice, it belongs in a different review; note it in one line
under Out of scope and move on.

## The two tiers

Everything turns on when a file loads.

**Always-on** context enters the window at the start of every session, before the user
types anything: CLAUDE.md at every level plus its `@imports` (imports load at launch —
they organize, they do not shrink), unscoped `.claude/rules/*.md`, MEMORY.md, the
skill listing's name+description lines, and the equivalents other tools load —
`.github/copilot-instructions.md`, `alwaysApply: true` cursor rules. This is a per-turn
tax on every session forever.

**On-demand** context loads when something reaches for it: skill bodies, path-scoped
rules, subdirectory CLAUDE.md, reference files, ordinary docs.

The same paragraph costs wildly different amounts depending on which tier it sits in.
A document loaded on demand can afford to repeat itself for clarity; an always-on
preamble cannot. So a finding's severity depends on its tier, and the single highest-
leverage recommendation you can usually make is not "delete this" but "move this down
a tier" — from always-on prose into a skill, a path-scoped rule, or a linked doc.

## Load-bearing

One test decides every keep-or-cut call:

> **Would removing this line change what the agent does or believes?**

If yes, it is **load-bearing** — keep it, however unglamorous. If no, it is paying rent
in every session and returning nothing.

Text fails the test in three ways, and naming which one you found is most of the
finding: it is **derivable** (the agent can get it from the repo faster than from your
description of the repo — directory trees, dependency lists, restated `package.json`
scripts), it is **default** (the model already behaves this way, so the line buys
nothing — "write clean code", "think step by step", "read the file before editing"),
or it is **dead** (it describes something that no longer exists).

Length is not the test, and shorter is not the goal. A long paragraph explaining why
retries are capped at three — because the upstream provider rate-limits at four and
the incident in the postmortem came from a retry storm — is dense, load-bearing
context that saves an agent from reintroducing a bug. Cut it and you have made the
file shorter and the repo worse. Optimize useful information per token, in both
directions: recommend adding context where its absence is causing repeated mistakes.

`references/keep-or-cut.md` holds the full rubric — what is worth keeping even when it
looks like clutter, and where credible sources genuinely disagree. Read it before you
write your first keep-or-cut recommendation.

## Severity

Severity is derived, never asserted. Two factors:

**Harm** — Misleading (the agent will act on something false) beats Conflicting (two
rules disagree and nothing resolves them, so the agent picks one arbitrarily) beats
Diluting (noise crowds out the rules that matter) beats Costly (pure token weight).

**Reach** — always-on beats on-demand beats incidental.

P1 is misleading or conflicting always-on context. P2 is misleading on-demand context,
or dilution in the always-on tier. P3 is everything else. Carry **confidence**
separately from severity: a high-severity finding you are 60% sure of is still worth
reporting, but say so.

## Running the audit

Work in this order. It matters: an audit that reads the whole repo to find bloat has
become the bloat. The scripts narrow the field so your reading is spent where the
evidence already points.

Both scripts live beside this file; run them from the skill directory, or give the
full path. They need only Python 3 and, for staleness, git.

### 1. Price the always-on tier

```bash
python scripts/ledger.py <repo>
```

Prints every file loaded at launch, its token estimate and its share of the window,
plus mechanical breaches (files past a hard cap, broken or too-deep imports, an
AGENTS.md that Claude Code never reads, a git symlink that was never materialized so
the file's whole content is the literal string of its target).

Then characterize the on-demand tier, which the ledger totals but does not judge. Three
questions, because each has produced real findings that no detector catches:

- **Who wrote it?** Split the total into authored, vendored (copied-in third-party
  skills and guides) and generated. Vendored context dwarfing your own is worth naming:
  the agent is mostly reading someone else's opinions about someone else's codebase.
- **Can it be reached?** A skill in a directory the tool never scans, a file no config
  points at, a rules file shadowed by an override — these cost storage and return
  nothing. Undiscoverable context is the same failure as absent context, minus the
  honesty.
- **Does it pull in anything from outside?** A context file that tells the agent to
  fetch a URL and follow what it finds has turned unpinned remote content into
  instructions (catalogue M9) — the one context defect that is also a security defect.
  Take this from the sweep's `external` detector, not from skimming: these stubs run to
  a few hundred bytes and read as trivial, which is exactly how one gets waved through.

Done when: every always-on file has a number, you can state the total as a percentage
of the window, and you can say who owns the on-demand bulk.

### 2. Sweep for candidates

```bash
python scripts/sweep.py <repo>            # add --comments to include source comments
```

Ten detectors — broken paths, vanished commands, cross-file duplication, docs whose
subject moved on, emphasis saturation, three shapes of contradiction, perishable
claims, retired-model prompt scaffolding, and fetch-and-obey. Each candidate arrives
with the evidence that raised it and the trap that would make it a false positive.

These are leads, not findings. If Python is unavailable, `references/catalogue.md`
carries the equivalent shell command for every detector.

Done when: each detector has run, or been skipped for a stated reason.

### 3. Read the always-on set end to end

Now read every always-on file completely — they are small by definition, and this is
the one place where full reading is cheap and necessary, because the worst findings
are invisible to greps: a rule that quietly contradicts the repo's actual practice, a
procedure that should be a skill, a paragraph that made sense two architectures ago.

Read skill and subagent descriptions too: those load every session, and overlapping
descriptions make the agent pick the wrong skill or miss the right one.

Done when: every file in the ledger's always-on table has been read in full.

### 4. Verify each candidate

Turn leads into findings, and be willing to end with fewer than you started.

For each one: check the trap the sweep named, then confirm the finding against the
repo. A path is only broken if nothing supplies it; a command is only gone if CI and
the justfile also lack it; duplicated blocks are only a problem once you have diffed
them and found they have drifted apart; two rules only conflict if an agent could not
satisfy both at once — otherwise that is scope refinement, and correct.

Verify your own recommendation's premise before you make it. "Move this into a skill"
is wrong if a skill already covers it; check.

Cited numbers are load-bearing too. A wrong line number or a miscount reads as
carelessness and costs the whole report its authority — so re-read each citation
against the file before it ships, and target the repo explicitly (`git -C <repo> ...`)
rather than trusting the working directory, which is often not the repo you are
auditing.

Done when: every surviving finding carries a `file:line`, the quoted text, and a
command another person could re-run to see the same thing. A finding missing any of
those is dropped, not downgraded.

### 5. Report

**The report is a file; the chat gets a summary.** Write it to
`context-health-<YYYY-MM-DD>.md` in the repo root, or wherever the user asked. Then say
in chat, and nowhere near full length: the one-sentence answer, the always-on total,
one line per P1, and the path to the file. Nothing else — no findings pasted back, no
recommendations restated. A report in the transcript is read once and scrolled past; a
file is diffed against the next run and handed to whoever actually edits the prose.

Structure the file like this:

```
# Context health — <repo> — <date>

One sentence answering the question they actually asked, before anything else.

## Always-on cost
The ledger table, the total, and one sentence on whether that is defensible.

## Findings
P1 first. Full treatment for each P1; group P2s that share a root cause; the P3s get
one table row each and nothing more — if a P3 needs a paragraph to land, you have
misjudged its severity, so promote it or drop it.

### P1-1 — <one-line claim>  ·  `file:line`  ·  <harm> × <reach>  ·  confidence <high/med/low>
**Quoted:**    the exact offending text
**Evidence:**  the command and what it returned
**Recommend:** the surgical change, with a token delta if it is a cut (~900 → ~200)

## Load-bearing — leave this alone
The context that is genuinely earning its tokens, named explicitly.

## Missing
Where the absence of context is causing repeated mistakes.

## Out of scope
Code issues noticed in passing, one line each. Not this audit's business.

## Re-check next time
The two or three things most likely to have rotted by the next audit.
```

The "leave this alone" section is not padding. Without it an audit reads as a mandate
to delete, and the predictable outcome is a user who prunes the rationale along with
the noise and cannot tell you six months later why retries are capped at three.

Prefer surgical edits over rewrites in every recommendation. When two rules conflict,
the fix is usually to add the missing carve-out to one of them, not to delete either.

Four fields per finding, and no fifth. You will want to add a paragraph explaining the
mechanism — what the agent will actually do wrong. Don't: the claim, the quote and the
evidence carry it, and a reader who wants the mechanism will ask. Hold it for that
question rather than smuggling it into **Evidence** or **Recommend**.

Done when: the file exists at a path you have named, every section is present, every
finding has all four fields, the report names what to protect as specifically as what
to cut, and your chat message is a summary rather than a copy.

## Repeat runs

`--json` on both scripts gives stable output. On a repo audited before, read the last
`context-health-*.md` first, diff against the previous run, and lead with what changed — new always-on tokens, findings that
returned after being fixed, and anything the user declined last time (say so once;
do not re-litigate it).

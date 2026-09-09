---
name: context-health
description: Audit a repo's agent-facing context — CLAUDE.md, AGENTS.md, rules, skills, docs, code comments — for context rot, and price the always-on tokens. Use when the user asks to audit, prune or clean up their CLAUDE.md, agent context or docs, or wants to cut a repo's token cost; or when they describe the symptom — the agent ignores instructions, follows stale guidance, contradicts itself between files, or has got quietly worse on a repo they have worked in for months.
---

# Context health

Instruction files rot the way sediment settles: adding a line feels safe, removing one
feels risky, so every session leaves a layer behind. Nothing looks broken. The agent
just gets a little worse each month — it follows a rule that stopped being true, or
misses the one rule that mattered because forty others were shouting too.

You are diagnosing that. **Report, do not repair.** The deliverable is a Markdown file
holding a prioritized diagnosis the user can act on; they decide what changes. A
context file is a team artifact whose lines usually encode a reason you cannot see from
inside the repo.

## What counts as your subject

Your subject is **the prose an agent reads**: instruction files, rules, skill and
subagent definitions, READMEs, architecture notes, ADRs, and code comments.

Code is your **evidence**, not your subject. You read it constantly — to check whether
a documented path exists, whether a command still resolves, whether a described
behaviour is still the behaviour — and you cite it in findings. Every finding you
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
preamble cannot. So a finding's severity depends on its tier — and the highest-leverage
recommendation available to you is usually a tier move: always-on prose into a skill, a
path-scoped rule, or a linked doc. Same words, same usefulness, none of the per-turn
tax.

## Load-bearing

One test decides every keep-or-cut call:

> **Would removing this line change what the agent does or believes?**

If yes, it is **load-bearing** — keep it, however unglamorous. If no, it is paying rent
in every session and returning nothing.

Text fails the test in three ways, and naming which one you found is most of the
finding: it is **derivable** (the agent can get it from the repo faster than from your
description of the repo — directory trees, dependency lists, restated `package.json`
scripts; a *judgment* about the repo, such as where changes usually land, is not
derivable), it is **default** (the model already behaves this way, so the line buys
nothing — "write clean code", "think step by step", "read the file before editing"),
or it is **dead** (it describes something that no longer exists).

Length is not the test. Reclaiming always-on tokens is a real goal of this audit —
weight is the one defect you can put a number on — and that number is bounded by the
test above. A cut is **recoverable** only when every line in it fails the test. A cut
that takes knowledge with it is not a win at any size.

So **salvage** before you delete. A long paragraph explaining why retries are capped at
three — the provider rate-limits at four, and the postmortem's outage was a retry
storm — is dense, load-bearing context; deleting it makes the file shorter and the repo
worse. Salvaging it does not: rewrite it down to its load-bearing sentence, move the
session-rare rule into a skill, collapse the third copy of a rule into one. The tokens
come back and the knowledge stays. Reserve deletion for text that was carrying nothing.

Optimize useful information per token, in both directions: recommend adding context
where its absence is causing repeated mistakes.

`references/keep-or-cut.md` holds the full rubric — what to protect even when it looks
like clutter, the salvage move worked through, where credible sources genuinely
disagree, and what is and is not worth a P1. Read it before you write your first
keep-or-cut recommendation.

## Severity

Severity is derived, never asserted. Two factors:

**Harm** — what the text does wrong. **Misleading**: the agent will act on something
false. **Conflicting**: two rules disagree and nothing resolves them, so the agent
picks one arbitrarily. **Diluting**: noise crowds out the rules that matter.
**Costly**: the text is accurate and unread, and bills for the privilege every turn.

**Reach** — always-on beats on-demand beats incidental.

Misleading and Conflicting rank on harm alone: they corrupt behaviour, so a small
wrong line outranks a large right one. Diluting and Costly rank on **magnitude** — the
ledger's token number, weighed against the tier it sits in. Cost is the one harm that
arrives with a measurement attached, so let the measurement set its priority.

**P1** — misleading or conflicting always-on context; or a recoverable cut worth **≥2k
always-on tokens, or ≥20% of the always-on total**.

**P2** — misleading on-demand context; dilution in the always-on tier; a cost
concentration under the P1 bar that still earns a number, such as on-demand bulk that
every session actually pays for.

**P3** — everything else.

Carry **confidence** separately from severity: a high-severity finding you are 60%
sure of is still worth reporting, but say so.

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
  skills and guides) and generated (catalogue T6, T7). Vendored context dwarfing your
  own is worth naming.
- **Can it be reached?** A skill in a directory the tool never scans, a file no config
  points at, a rules file shadowed by an override (S4, S7, S8). Undiscoverable context
  is the same failure as absent context, minus the honesty.
- **Does it pull in anything from outside?** A context file that tells the agent to
  fetch a URL and follow what it finds has turned unpinned remote content into
  instructions (M9) — the one context defect that is also a security defect. Take this
  from the sweep's `external` detector: these stubs run to a few hundred bytes and read
  as trivial, which is exactly how one gets waved through.

Done when: every always-on file has a number, you can state the total as a percentage
of the window, and you can say who owns the on-demand bulk.

### 2. Sweep for candidates

```bash
python scripts/sweep.py <repo>            # --no-comments to skip the source-comment pass
```

Ten detectors, all on by default. Each candidate arrives with the evidence that raised
it and the trap that would make it a false positive.

These are leads, not findings. If Python is unavailable, `references/catalogue.md`
carries the equivalent shell command for every detector.

Done when: each detector has run, or been skipped for a stated reason.

### 3. Read the always-on set end to end

Now read every always-on file completely — they are small by definition, and this is
the one place where full reading is cheap and necessary, because the worst findings
are invisible to greps: a rule that quietly contradicts the repo's actual practice, a
procedure that should be a skill, a paragraph that made sense two architectures ago.

Read against the catalogue's **Structural** (S1–S8) and **Missing** (X1–X3) classes as
you go: none of them has a detector, so this read is the only place they get caught.

Read skill and subagent descriptions too: those load every session, and overlapping
descriptions make the agent pick the wrong skill or miss the right one.

Done when: every file in the ledger's always-on table has been read in full, and each
S and X class has been considered.

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
in chat, and nowhere near full length: the one-sentence answer, the always-on total
and how much of it is recoverable, one line per P1, and the path to the file. A report
in the transcript is read once and scrolled past; a file is diffed against the next
run and handed to whoever actually edits the prose.

Structure the file like this:

```
# Context health — <repo> — <date>

One sentence answering the question they actually asked, before anything else.

## Always-on cost
The ledger table, the total, the recoverable subtotal — how many of those tokens the
findings below reclaim without losing anything — and one sentence on whether what is
left is defensible.

## Findings
P1 first. Full treatment for each P1; group P2s that share a root cause; the P3s get
one table row each and nothing more — if a P3 needs a paragraph to land, you have
misjudged its severity, so promote it or drop it.

### P1-1 — <one-line claim>  ·  `file:line`  ·  <harm> × <reach>  ·  confidence <high/med/low>
**Quoted:**    the exact offending text
**Evidence:**  the command and what it returned
**Recommend:** the surgical change — a token delta whenever it reduces
               (~900 → ~200), plus what the shorter version still carries

## Load-bearing — leave this alone
The context that is genuinely earning its tokens, named explicitly.

## Missing
Where the absence of context is causing repeated mistakes.

## Out of scope
Code issues noticed in passing, one line each. Not this audit's business.

## Re-check next time
The two or three things most likely to have rotted by the next audit.
```

Name what to protect as specifically as what to cut. Without the "leave this alone"
section an audit reads as a mandate to delete, and the user prunes the rationale along
with the noise.

Four fields per finding. The claim, the quote and the evidence carry the mechanism —
what the agent will actually do wrong — so hold that explanation for the reader who
asks for it rather than adding a fifth field or folding it into **Evidence** or
**Recommend**.

Done when: the file exists at a path you have named, every section is present, every
finding has all four fields, every reducing recommendation carries a token delta that
sums into the recoverable subtotal, the report names what to protect as specifically
as what to cut, and your chat message is a summary rather than a copy.

## Repeat runs

`--json` on both scripts gives stable output. On a repo audited before, read the last
`context-health-*.md` first, diff against the previous run, and lead with what
changed — new always-on tokens, recoverable tokens the user has since reclaimed,
findings that returned after being fixed, and anything the user declined last time
(say so once, and leave it there).

# Keep or cut

The judgment half of the audit. The detectors find candidates; this decides what they
mean.

## Two refinements to the load-bearing test

The test itself lives in SKILL.md: would removing this line change what the agent does
or believes? Two refinements sharpen it at the margins.

**Derivable is about descriptions, not judgments.** The repo cannot go stale relative
to itself, so a description of the repo is strictly worse than the repo. A *judgment*
about the repo is not derivable at all. "The parser lives in `src/parse/`" is
derivable. "Changes almost always land in these four files" is not.

**For comments, ask whether it uses different words.** A comment that restates its own
signature in English adds nothing. A comment using *different words* — about units,
bounds, caller obligations, why the ordering matters — adds what the signature
structurally cannot express.

Size never promotes a cut past the test — the biggest file in the ledger stays if its
lines change what the agent does. Salvage it instead: compress it, or move it down a
tier.

## Protect this

The failure mode of a context audit is a user who prunes the rationale along with the
noise. Name these explicitly in the report so that does not happen.

- **Why, not what.** A constant with a reason attached — capped at three because the
  provider rate-limits at four. The number is in the code; the reason exists nowhere
  else and will be "simplified" away without it.
- **Deliberate exclusions.** What was tried and rejected, and why. Code can only show
  what *is* there. An agent will cheerfully reintroduce the approach you abandoned.
- **Non-obvious behaviour and edge cases.** Units, inclusive/exclusive bounds, which
  arguments accept null, what happens on partial failure.
- **Caller obligations and cross-module contracts.** Dependencies that cross a boundary
  are the highest-value comments in any codebase, because no single file records them.
- **External constraints.** "This shape is forced by the vendor's API", "this ordering
  is required by the migration tool." Not inferable, and expensive to rediscover.
- **Conventions that differ from the tool default.** The whole point of an instruction
  file. A rule matching the default is noise; a rule departing from it is essential.
- **Hard-won incident knowledge.** Anything traceable to a postmortem.
- **Curated maps and judgments.** Where changes usually land, which module is load-
  bearing, what to be careful near.

A dense 200-word paragraph carrying three of these is better context than twenty
crisp lines carrying none.

## Cut this

- Narration that restates the adjacent code or the adjacent sentence.
- Content the agent derives faster by looking: trees, dependency lists, restated
  scripts.
- Behaviour the model already exhibits by default.
- The same rule stated in a second file.
- Standard conventions a linter already enforces.
- Commented-out code — git remembers it, and the agent cannot tell whether it is a
  documented alternative or an oversight.
- Changelog inside comments or instruction files — `git blame` carries this better.
- Perishable measurements: "takes about 20 minutes", "currently three services".

## Preserving rationale while cutting bulk

Most bloated context is a load-bearing sentence wrapped in four that are not. The move
is extraction, not deletion:

> **Before** (always-on, ~90 tokens)
> "We use a retry limit of 3 for all outbound HTTP calls. This is important because
> retries can cause problems. Historically we had issues with this. The team discussed
> this at length and decided 3 was the right number. Please make sure to respect this
> limit when writing new clients, and be careful not to change it without discussing
> with the team first."
>
> **After** (~25 tokens)
> "Outbound HTTP retries are capped at 3 — the provider rate-limits at 4, and
> exceeding it caused the Jan outage. Changing this needs a conversation."

Everything load-bearing survives: the number, the causal reason, the incident, the
change-control expectation. What went was narration ("this is important"), vagueness
("historically we had issues"), and process theatre ("discussed at length").

Three quarters shorter and *more* informative — because the reason moved from "we had
issues" to a specific mechanism the agent can reason about.

## Where credible sources disagree

Surface these in the report rather than pretending consensus. If a user's setup sits on
the far side of one of these debates deliberately, that is a choice, not a defect.

**Minimal vs comprehensive instruction files.** Anthropic and most practitioners argue
for ruthless pruning: bloat causes rules to be ignored. GitHub's Copilot guidance
explicitly recommends including a folder-structure map and validated build sequences —
"something is better than nothing." The crux is a real tradeoff between per-turn cost
and per-session exploration cost, and it resolves differently for a repo an agent
touches ten times a day than for one it sees monthly.

**Are comments a smell?** One camp holds that a needed comment signals unclear code;
the other that rationale comments are irreplaceable. Both agree completely on the cases
this audit reports — restating comments, commented-out code, changelog comments, and
comments contradicting their code. Confine findings to that overlap and the debate does
not need settling.

**Prune failed attempts, or keep them?** Some argue leaving errors in context teaches
the model not to repeat them; others that context polluted with failed approaches
degrades everything after. The reconciliation nobody states: tool-level errors are
useful signal, human correction loops are pollution.

**Does progressive disclosure actually fire?** "Move it into a skill" assumes the skill
gets invoked. There is evidence that skills go uninvoked a substantial fraction of the
time. Path-scoped rules push rather than hope, so prefer them when the trigger is "the
agent is editing a file of this kind."

**Nested-file semantics.** The AGENTS.md spec resolves nearest-file-wins; Claude Code
concatenates the whole chain. A nested layout authored against one is actively wrong
under the other. Worth checking which tool the repo was written for.

**Specification density.** Anthropic's guidance leans toward concrete, example-rich
instruction; OpenAI's toward high-level guidance for reasoning models, warning that
examples can hurt. Do not flag terseness in a Codex-tuned repo as under-specification.

**Usage as a proxy for value.** An unused skill costs listing tokens, but usage counts
say nothing about whether it improved the result when it did fire. Report unused
artifacts as a question.

## Calibration

Findings that are worth a P1:

- A build command in CLAUDE.md that no longer exists — the agent will run it.
- Two always-on files giving different timeouts for the same call.
- A CLAUDE.md that is a nine-byte unmaterialized symlink, so all guidance is silently
  absent while the team believes it is loaded.
- A 3k-token always-on section that is a directory tree plus a restated `scripts`
  block — derivable end to end, so all 3k are recoverable and none of the meaning is.

Findings that are not worth reporting:

- A README slightly longer than it needs to be.
- A comment you would have worded differently.
- An always-on file at 210 lines against a 200-line target, with nothing else wrong.
- Anything about code structure, naming or formatting. Different review.

The honest empty result — "the always-on tier is 1,900 tokens, the instruction files
are current, here are two low-severity notes" — is a good audit. Manufacturing P1s to
look thorough is the one failure this skill cannot recover from, because it trains the
user to ignore the next report.

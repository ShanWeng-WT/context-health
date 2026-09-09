# Finding catalogue

Every finding type this audit reports, grouped by harm class. Each carries: what it
is, why it hurts an **agent** specifically, how to detect it by hand (for when
`scripts/sweep.py` cannot run), the false positive that will bite you, and the shape
of the recommendation.

Shell commands assume Git Bash. Run `export LC_ALL=C` first — without it `sort` hard-
fails on any repo containing CJK or UTF-8 punctuation and silently returns nothing.

**Contents**
- [Misleading](#misleading) — M1–M9
- [Conflicting](#conflicting) — C1–C5
- [Diluting](#diluting) — D1–D8
- [Costly](#costly) — T1–T7
- [Structural](#structural) — S1–S8
- [Missing](#missing) — X1–X3

---

## Misleading

The agent acts on something false. Highest severity: worse than no documentation,
because the agent trusts it and stops looking.

### M1 — Dead command
A documented command that no longer resolves.

*Why it hurts:* agents **execute** commands they find in instruction files. A stale
one is not a stale sentence, it is a failed run and a confused recovery attempt.

```bash
grep -rhoE '(npm|pnpm|yarn|bun) run [a-z:._-]+|make [a-z:._-]+' CLAUDE.md AGENTS.md docs/ \
  | awk '{print $NF}' | sort -u > /tmp/documented
jq -r '.scripts | keys[]' package.json | sort -u > /tmp/defined
comm -23 /tmp/documented /tmp/defined
```

*Trap:* the command may live in CI, a justfile, a Makefile include, a workspace
package's own manifest, or a global tool. Check all of them before reporting.

*Recommend:* replace with the current command, or point at the manifest instead of
restating it.

### M2 — Dead path
A file or directory named in a doc that no longer exists.

*Why it hurts:* the agent burns a tool call, then either invents a replacement or
concludes the doc is unreliable and ignores the rest of it.

```bash
grep -ohE '`[A-Za-z0-9_./-]+\.[a-z]{2,4}`' CLAUDE.md docs/*.md | tr -d '`' | sort -u \
  | while read -r p; do [ -e "$p" ] || echo "MISSING: $p"; done
```

*Trap:* calibrate against extensions the repo actually uses, and strip URLs first —
otherwise `example.com/r/button.json` is reported as a missing path. A path the reader
is told to *create* is not broken. Vendored third-party docs describe someone else's
tree; exclude them.

*Recommend:* update the path, or delete the reference if the thing is gone.

### M3 — Drifted doc
A doc untouched while the code it describes moved on.

*Why it hurts:* stale architecture notes are the most expensive kind of wrong, because
they shape the agent's plan before it reads any code.

```bash
DOC=docs/architecture.md; SUB=src
SHA=$(git log -1 --format=%H -- "$DOC")
git rev-list --count "$SHA"..HEAD -- "$SUB"                        # commits since
git log "$SHA"..HEAD --diff-filter=AD --name-status --format='' -- "$SUB"   # files added/deleted
```

Rank by `commits_since × log(1 + age)`, never age alone. Files added or deleted under
the subject are the strongest single signal: a doc cannot describe a file that did not
exist when it was written.

*Trap:* changelogs, licences, ADRs and postmortems are supposed to be old. One
repo-wide reformat resets every file's date — check for a commit touching 100+ files
before trusting any freshness number. And `git blame` attributes to the last touch, so
use `-w -C -M` to see through moves and reformats.

*Recommend:* name the specific drifted claims, not "this file is old".

### M4 — Drifted count
"We have 12 services", "three packages", "tests live in `spec/`".

*Why it hurts:* a countable claim is checkable, so the agent treats it as authoritative
and plans around it.

*Trap:* the claim may still be true. Count before reporting.

*Recommend:* delete the count. It cannot be maintained and the agent can count.

### M5 — Perishable claim
"Currently", "for now", "as of March", "we recently moved to X".

*Why it hurts:* this is the only rot that needs **no code change at all** — so nothing
in the repo will ever prompt someone to fix it. Git staleness detection cannot see it.

```bash
grep -rnE '\b(currently|for now|at the moment|temporarily|as of [0-9A-Za-z]+)\b' \
  CLAUDE.md AGENTS.md .claude/rules/
```

*Trap:* a dated entry inside an explicitly historical section is doing its job.

*Recommend:* state the durable fact, or date the line so its age is visible.

### M6 — Unmaterialized symlink
An always-on file whose entire content is the literal name of another file.

*Why it hurts:* git stores a symlink as a blob containing the target path. Checked out
without symlink support — the Windows default — it becomes a plain text file. The agent
loads the nine characters `AGENTS.md` and nothing else, while everyone assumes the
bridge works.

```bash
for f in CLAUDE.md AGENTS.md; do
  [ -f "$f" ] && [ "$(wc -c < "$f")" -lt 200 ] && cat "$f"
done
```

*Recommend:* replace the symlink with an `@AGENTS.md` import, which works everywhere.

### M7 — Stale comment
A comment contradicting the code it annotates: outdated parameter docs, invariants that
no longer hold, "returns null on failure" when it now throws.

*Why it hurts:* inconsistent code/comment changes are measurably associated with
bug-introducing commits. The agent reads the comment as a specification.

*Trap:* only report where you can point at the contradicting code. "This comment looks
old" is not a finding.

### M8 — Aspirational rule
A rule the repo demonstrably does not follow — "always write tests first" where the
history says otherwise.

*Why it hurts:* the agent either follows it and produces work inconsistent with the
codebase, or learns that this file's rules are optional — which discounts every other
rule in it.

*Recommend:* enforce it or drop it. Do not leave it as decoration.

### M9 — Fetch-and-obey
A context file instructing the agent to retrieve a URL and follow what it finds.

*Why it hurts:* it converts unpinned remote content into instructions. Whatever is at
that URL today becomes agent behaviour, with no review, no version, and no diff when it
changes. It is the one context defect that is also a security defect, and a stub file
of three lines can carry it.

```bash
grep -rnEi 'fetch |curl |WebFetch|https?://' CLAUDE.md AGENTS.md .claude/rules/ \
  .claude/skills/*/SKILL.md | grep -Ei 'follow|obey|apply|instruction|guideline|rule'
```

*Trap:* a link offered as *reference* is fine. The finding is an instruction to treat
fetched content as authoritative.

*Recommend:* vendor the content at a pinned version, or downgrade the wording from
"follow" to "consult".

---

## Conflicting

Two instructions disagree and nothing resolves the tie. The agent picks one
arbitrarily, and reasoning models burn tokens trying to reconcile them rather than
choosing — contradiction is more damaging than under-specification.

### C1 — Same setting, two values
`timeout: 30s` in one file, `60s` in another.

```bash
grep -rhoE '\b[a-z_]{4,}\s*[:=]\s*[0-9]+[a-z%]*' CLAUDE.md AGENTS.md .claude/rules/ \
  | tr -d ' ' | sort | awk -F'[:=]' '{if($1==p&&$0!=l)print l"\n"$0; p=$1; l=$0}'
```

*Trap:* near-zero false positives, so report these first and with confidence.

### C2 — Rival tools
Two package managers, test runners or formatters named across always-on files.

*Trap:* a monorepo may genuinely use both. Check the lockfiles.

### C3 — Opposite directives
"Prefer named exports" against "Prefer default exports".

Word-overlap alone misses these — those two lines share only a third of their words.
Also flag pairs differing by exactly one token, which is where polarity flips live.

*Trap:* skip headings and table-of-contents entries; a heading and its TOC link are the
same words by design. Scoped rules may legitimately differ from global ones.

*The test:* could an agent satisfy both at once? If yes, this is scope refinement, not
a conflict.

### C4 — Unstated exception
An unconditional rule that has a real exception nobody wrote down.

*Recommend:* add the carve-out. Do not delete either rule — this is the one conflict
shape where both instructions are correct and only the boundary is missing.

### C5 — Cross-tool divergence
CLAUDE.md and AGENTS.md, or `.cursor/rules` and copilot-instructions, giving different
guidance for the same thing.

*Why it hurts:* two agents behave differently on one repo, and whichever one a reviewer
uses becomes the standard by accident. Nested-file semantics differ by tool — the
AGENTS.md spec resolves nearest-wins, Claude Code concatenates — so a layout authored
against one is wrong under the other.

---

## Diluting

Nothing here is false. It crowds out what matters. Bloated instruction files cause the
agent to ignore rules that are still true, which is why dilution is a correctness
problem and not only a cost problem.

### D1 — Derivable content
Directory trees, dependency lists, file-by-file descriptions, restated `package.json`
scripts.

*Why it hurts:* the agent can read the repo faster than it can trust a description of
the repo, and the repo cannot go stale relative to itself.

*Trap:* a *curated* map — "these four files are where 90% of changes land" — is
judgment, not derivable. Keep it.

### D2 — Default behaviour
"Write clean code", "think step by step", "read the file before editing", "be
thorough". Also role-priming ("you are an expert engineer") and incentive framing.

*Why it hurts:* pays tokens for behaviour you already get. Some is worse than inert:
intensifier language has been documented to cause repetitive, unproductive searching.

*Trap:* a phrase may be load-bearing in one specific workflow. Ask whether the current
model already does it unprompted.

### D3 — Emphasis saturation
Many lines shouting IMPORTANT / ALWAYS / NEVER / MUST.

*Why it hurts:* emphasis works by contrast. Past roughly 15% of lines, none of them
stands out, and the genuine invariants become indistinguishable from preferences.

*Recommend:* reserve absolutes for true invariants. Report the ratio, not any one line.

### D4 — Duplicated block
The same paragraphs in CLAUDE.md, AGENTS.md, README and a rules file.

*Why it hurts:* paid more than once per session, and the copies drift — at which point
it becomes a C5 conflict.

Normalize (lowercase, strip punctuation, keep lines ≥40 chars), hash, and count shared
lines per file *pair*. Use containment `|A∩B| / |A|` rather than Jaccard when the files
differ in size — a short file copied wholesale into a long one scores badly on Jaccard
and is exactly the case worth catching.

*Trap:* deliberate mirroring for two audiences can be correct. The finding is real once
the copies have **drifted** — so diff them before reporting.

*Recommend:* one authoritative home, others link to it. Note that `@imports` do not
reduce cost; they organize.

### D5 — Model-generation cruft
Prompt scaffolding for a model generation that no longer needs it: `<scratchpad>` tags,
"take a deep breath", mandatory upfront plans, "do not be lazy".

*Why it hurts:* instructions written to work around an older model's limitation become
overhead once a newer model handles the case natively — and some now cause the harm
they were written to prevent.

*Recommend:* re-check instruction files after major model releases. This is the most
commonly missed maintenance trigger.

### D6 — Standard conventions
PEP 8, "use const not var", pasted style guides.

*Recommend:* the linter's job. Keep only conventions that **differ** from the tool
default — those are genuinely load-bearing.

### D7 — Changelog accretion
An instruction file used as an append-only log: "2026-04: switched to pnpm".

*Why it hurts:* the agent cannot tell which entries are current. Also churns the cached
prefix, which is expensive independent of content.

### D8 — Overlapping skill descriptions
Two skills whose descriptions cover the same trigger.

*Why it hurts:* descriptions are always-on, and ambiguity makes the agent load the
wrong skill or miss the right one. If a human cannot say which of two skills applies,
neither can the agent.

---

## Costly

### T1 — Oversized always-on file
Report against the documented target for the tool, and always against the ledger total.

### T2 — Import chain
`@imports` load at launch, recursively, to a depth limit. Splitting a large file into
imports organizes it; it does not reduce a single token.

### T3 — Skill listing over budget
The listing has a fixed share of the window. Over it, the least-used descriptions are
dropped **silently** — a skill can stop being discoverable with no error.

### T4 — Unscoped rules
Rule files without path scoping load every session. Adding `paths:` moves them to the
on-demand tier at zero cost to their usefulness.

### T5 — Never-invoked skill or unused MCP server
Costs listing tokens every turn.

*Trap:* usage is not value — a rarely-used skill may be the one that saves an entire
afternoon. **Report as a question, not a defect.**

### T6 — Vendored context outweighs authored context
Copied-in third-party skills and guides dwarfing what the team actually wrote.

*Why it hurts:* the agent is mostly reading someone else's opinions about someone
else's codebase. Vendored guidance also never gets reviewed in a PR the way authored
guidance does, so it rots invisibly and nobody feels ownership of it.

```bash
git ls-files -z | xargs -0 -n1 wc -c 2>/dev/null | awk '
  $2 ~ /(SKILL|AGENTS|CLAUDE)\.md$|\.claude\/|\.agents\/|\.cursor\// {
    if ($2 ~ /(node_modules|\.agents|vendor|third_party)/) v+=$1; else a+=$1 }
  END { printf "authored %d B, vendored %d B (%.1fx)\n", a, v, v/(a?a:1) }'
```

*Trap:* vendored context can be excellent and deliberately chosen. The finding is the
**ratio** plus the absence of a review or pinning story, not the presence.

### T7 — Generated file committed as context
Build artifacts — a generated `AGENTS.md` assembled from a `rules/` directory, an
OpenAPI dump, a bundled index — sitting where an agent will read them.

*Why it hurts:* it duplicates its own source, so the two drift, and the generated copy
is the one the agent reads. Regeneration silently reverts hand edits.

*Recommend:* point the agent at the source, or gitignore the artifact.

---

## Structural

### S1 — Procedure in an instruction file
A multi-step runbook living in always-on context. It should be a skill: same content,
loaded only when relevant.

### S2 — Advisory rule that should be enforcement
"Never commit to main", "always run the formatter". An instruction file is a request,
not a guarantee.

*Recommend:* a hook, a permission rule, a lint rule or a CI check. Usually the single
highest-leverage recommendation in the whole audit — it removes tokens *and* makes the
rule actually hold.

### S3 — Global file carrying local rules
Instructions that apply to one directory sitting in the root file.

*Recommend:* a per-directory file or a path-scoped rule.

### S4 — Unread file
An `AGENTS.md` with no CLAUDE.md bridge; a `CONVENTIONS.md` no tool is configured to
read; a file shadowed by an override. Pure cost, zero effect.

### S7 — Undiscoverable context
Context the tool will never look for: a skill directory below the root when only the
root is scanned, a rules file in a non-standard location, a filename not on the tool's
fallback list.

*Why it hurts:* identical in effect to having no context at all, except that everyone
believes it is working — so nobody writes the guidance a second time.

*Recommend:* move it where the tool looks, or configure the tool to look where it is.
Say plainly that it currently has **zero** effect; that is the part people act on.

### S8 — Orphaned context artifact
A lockfile, manifest or index referencing context that no longer exists, or referenced
by nothing.

*Trap:* it may be consumed by a script rather than the agent. Check before reporting.

### S5 — Legacy format
`.cursorrules` instead of `.cursor/rules/`, or a `.clinerules` file where a directory is
now expected.

### S6 — Unstable prefix
Timestamps, versions or generated content near the top of an always-on file. Busts the
cached prefix for everything after it, which is a real cost multiplier.

---

## Missing

An audit that only subtracts is doing half the job.

### X1 — Unwritten constraint
A mistake the agent keeps making that one sentence would prevent. Transcripts and the
user's own complaints are the evidence.

### X2 — Undocumented rationale
A non-obvious constant, a deliberate exclusion, an ordering that matters. Nothing in
the code can say *why*, so nothing stops the agent from "simplifying" it away.

### X3 — No precedence statement
Several instruction files load and none says which wins. Cheap to add, and it converts
a whole class of C-findings from arbitrary into resolved.

# Research 01 — Anthropic-authored skills relevant to `/context-health`
Local filesystem + web fallback research. Machine: Windows 11, user `shan.weng`.
Date of research: 2026-09-08.

---

## 0. Inventory: what exists on this machine, and where

| Artifact | Status | Absolute path / source |
|---|---|---|
| `anthropic-skills:context-health` | **FOUND** — SKILL.md captured in full (verbatim below). Bundled `references/`, `assets/`, `scripts/` **NOT retrievable**. | Delivered inline by the Claude Code harness. It reported its base dir as `C:\Users\shan.weng\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\43378522-ed4e-4221-9faf-3621d49aba5b\9e19918c-f3a5-4aca-ab50-0f35ccf1bc36\skills\context-health` — **that directory does not exist on disk** (verified by `ls`, `find`, and a full recursive PowerShell search of `AppData`, `.claude`, `.local`). |
| `prompt-audit` | **NOT on this machine.** Retrieved in full from the public repo. | `https://raw.githubusercontent.com/anthropics/skills/main/skills/claude-api/shared/prompt-audit.md` — it is a *subcommand file* of the `claude-api` skill, not a standalone skill. |
| `comment-analyzer` | **FOUND** — but it is a **subagent**, not a skill, and it is a *code-comment* analyzer. | `C:\Users\shan.weng\.claude\plugins\marketplaces\claude-plugins-official\plugins\pr-review-toolkit\agents\comment-analyzer.md` |
| `skill-creator` (installed plugin) | FOUND, full | `C:\Users\shan.weng\.claude\plugins\cache\claude-plugins-official\skill-creator\85cce0381e78\skills\skill-creator\SKILL.md` (+ `agents/`, `references/schemas.md`, `scripts/`, `eval-viewer/`) |
| `skill-creator` (marketplace copy) | FOUND, identical family | `C:\Users\shan.weng\.claude\plugins\marketplaces\claude-plugins-official\plugins\skill-creator\skills\skill-creator\SKILL.md` |
| `skill-creator` (Claude Desktop copy) | FOUND | `C:\Users\shan.weng\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\43378522-ed4e-4221-9faf-3621d49aba5b\9e19918c-f3a5-4aca-ab50-0f35ccf1bc36\skills\skill-creator\SKILL.md` |
| `claude-md-improver` | **FOUND, full** — the closest Anthropic prior art to a context audit that *edits*. | `C:\Users\shan.weng\.claude\plugins\marketplaces\claude-plugins-official\plugins\claude-md-management\skills\claude-md-improver\SKILL.md` + `references/quality-criteria.md`, `references/templates.md`, `references/update-guidelines.md` |
| `consolidate-memory` | FOUND, full | `C:\Users\shan.weng\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\43378522-ed4e-4221-9faf-3621d49aba5b\9e19918c-f3a5-4aca-ab50-0f35ccf1bc36\skills\consolidate-memory\SKILL.md` |
| `claude-automation-recommender` | FOUND (not read in depth; adjacent — recommends hooks/skills/subagents) | `...\plugins\claude-code-setup\skills\claude-automation-recommender\SKILL.md` + 5 reference files |
| `claude-api` SKILL.md (host of prompt-audit) | Fetched from web | `https://raw.githubusercontent.com/anthropics/skills/main/skills/claude-api/SKILL.md` |
| User's own prior art (not Anthropic) | FOUND | `C:\Users\shan.weng\.claude\skills\unity-context-file-generator\SKILL.md` — "Generate, audit, or improve a Unity project's CLAUDE.md" |

### Why the context-health bundle could not be read
- The `anthropic-skills` plugin **on disk** (`.claude-plugin/plugin.json` → `{"name":"anthropic-skills","version":"1.0.0","description":"Anthropic-managed skills for Claude Desktop"}`) has a `manifest.json` listing exactly 10 skills: `import-memory, skill-creator, xlsx, pptx, pdf, docx, schedule, setup-cowork, consolidate-memory, explain-usage`. **`context-health` is not in it.**
- `grep -a "context-health"` over `claude.exe` (218 MB) returns **0 hits** — the built-in skill payload is compressed/not plain text.
- Invoking the Skill tool a second time returns `Unknown skill: anthropic-skills:context-health` (one-shot injection), and `ListSkills` returns `[]`.
- The skill is **not** in the public `anthropics/skills` repo (`skills/` contains: academy-guide, algorithmic-art, brand-guidelines, canvas-design, claude-api, discernment-nudge, doc-coauthoring, docx, frontend-design, internal-comms, mcp-builder, pdf, pptx, skill-creator, slack-gif-creator, theme-factory, web-artifacts-builder, webapp-testing, xlsx).
- **Net:** the SKILL.md body below is complete and verbatim. Everything it *references* (`references/findings-catalog.md`, `references/detection-notes.md`, `references/research-basis.md`, `assets/report-template.md`, `scripts/ctx_map.py`, `scripts/ctx_refs.py`, `scripts/ctx_dupes.py`) is described only by what SKILL.md says about it.

---

## 1. `anthropic-skills:context-health` — THE primary artifact

**Frontmatter (from the skill listing, verbatim):**
```
name: context-health
description: Audits a repo's agent context — CLAUDE.md, AGENTS.md, cursor and copilot rules,
  skills, subagents, READMEs, architecture docs, code comments — for stale, contradictory and
  duplicated instructions and always-on token cost. Reports prioritized findings; never edits.
  Use it when someone wants their agent context audited or asks what context is worth keeping,
  and when they describe the symptom instead of asking for an audit: the agent ignores
  instructions, follows stale guidance, burns too many tokens, or has been getting worse over
  months on the same repo.
```
Note the description's shape: **what it audits (enumerated surfaces) + what it produces + a hard constraint ("never edits") + symptom-based triggers.** The symptom triggers are the interesting move — "the agent ignores instructions", "burns too many tokens", "has been getting worse over months on the same repo."

### 1.1 Opening frame — the three failure modes (verbatim)

> Repositories accumulate text that agents read. Some of it earns its place. Most of what accumulates does not, and it degrades the agent in three distinct ways that this audit keeps separate, because they call for different fixes:
>
> - **Wrong claims** send the agent somewhere that no longer exists. A path that moved, a command that was renamed, a rule describing an abandoned pattern. Reading more of the file cannot rescue it: the agent acts on the claim.
> - **Conflicting claims** force the agent to reconcile two rules that disagree. It may pick either one, and it may pick differently next run. Contradiction is worse than omission, and it gets *more* expensive as models follow instructions more literally.
> - **Volume** dilutes everything else. Attention is finite; every token spends some of it. This is the mechanism behind the most common complaint about agent instructions: *the rule is in the file and the agent ignores it.*

> The goal is **useful information per token**, not fewer tokens. A short file full of vague rules is worse than a longer one carrying real constraints. The audit that shortens indiscriminately deletes exactly the highest-value words - the rationale, the gotcha, the constraint nobody could infer - and leaves the padding, which is shorter. Hold that in mind for the whole run.

### 1.2 Scope rule — "the context around the code, never the code"

- **"Every finding names a document as its subject."**
- "The code is evidence, never the subject - so implementation, architecture, naming, formatting and test structure stay out of the report however much they invite comment."
- "Read the code freely; just do not opine on it. ... an audit that refuses to open it can only check that a path *exists*, never that a statement is *true*, and those are very different standards. A doc saying the window is 60 seconds is not verified by confirming `ratelimit.ts` exists. Open it, read the constant, and then you have a finding or you do not."
- In scope: "any claim in prose or a comment, checked against what the code actually does. 'The docs say the retry count is 5; `MAX_ATTEMPTS` is 3' is a finding about the doc."
- Out of scope: "what the code should be. 'This retry logic should be extracted', 'this function is poorly named', 'this module needs restructuring' - none of these belong in the report, however true."
- **The bridge case:** "When the code turns out to be the problem: the *fix* is out of scope, but the *observation* often is not... A rule telling the agent to run a test suite that cannot pass is an **unfollowable instruction** (catalog 1i) - a context finding, even though repairing the suite is a code task. Report the context consequence, name the code fact in one line as the evidence, and stop there rather than prescribing the code change."
- **The one exception running the other way:** "when a rule is stated in prose but could be *enforced* by a hook, linter or CI check, say so. Prose is advisory by construction; moving an always-must rule into enforcement is the single highest-leverage recommendation this audit makes, and it removes context rather than adding it."

### 1.3 Diagnose, never apply (verbatim)

> Produce a report. Do not edit, delete, or rewrite any file, even when a fix is obvious and even when the finding is certain, unless the person explicitly asks for the changes to be applied in this session. Recommendations carry proposed replacement text so they are easy to act on; the decision stays with the person, who knows things about their repo that the audit does not.

### 1.4 The eight steps

**Step 1 — Establish scope and baseline.** Worked out from the request and repo *rather than asking*; assumptions stated at the top of the report "where they can be corrected."
- *Depth*: "Default order is agent-facing files first, then human docs, then code comments - highest signal per unit of effort."
- *Exclusions*: "Vendored, generated and fixture trees. On a large repo these are the majority of the markdown, and leaving them in makes every metric meaningless." `SKIP_DIRS` at the top of `ctx_map.py` is the authoritative set.
- *Repeat run*: look for `CONTEXT_HEALTH_REPORT.md`, read it first, track what changed. "A finding that was declined last time should not be re-raised as if new; note it as previously declined and move on."

**Step 2 — Map the surface and its always-on cost.** `python3 <skill>/scripts/ctx_map.py <repo>`
> "This is the framing number for the whole report. It splits the context surface into what is paid **every turn, in every session, by every engineer** versus what is paid only when reached. The distinction drives most recommendations, because the cure for an overweight instruction file is almost never 'write it shorter' - it is 'move this material to where it is paid for only when it is used'"

The always-on / on-demand table (verbatim):

| Always-on | On-demand |
|---|---|
| Root `CLAUDE.md` / `AGENTS.md` and everything their `@imports` pull in | Nested `CLAUDE.md` / `AGENTS.md` in subdirectories |
| `.cursorrules`, `.windsurfrules`, `.clinerules`, copilot instructions | `.cursor/rules/*.mdc` scoped by `globs` or description |
| `.cursor/rules/*.mdc` with `alwaysApply: true` | `.claude/rules/*.md` with a `paths:` scope |
| `.claude/rules/*.md` with **no** `paths:` scope | Skill **bodies** and their bundled files |
| Skill and subagent **descriptions** (frontmatter only) | Subagent bodies, slash commands |
| MCP tool schemas - usually the largest single item, and not measurable from disk | Everything reached through a pointer |

Two "things people routinely get wrong", to check and to state in the report when true:
- **"`@imports` do not save context.** The imported file is pulled in at launch, in full. Splitting a long instruction file into imports improves how it reads for humans and changes nothing about what the agent pays. Genuine reduction comes from path-scoping, skills, or deletion."
- **"An unscoped rule file is CLAUDE.md content wearing a different hat.** A `.claude/rules/*.md` with no `paths:`, or an `alwaysApply: true` `.mdc`, costs exactly what the same text in `CLAUDE.md` costs."

On thresholds: "Report always-on tokens as an absolute number and as a share of the window. Do not quote a threshold as a rule: no published one is in tokens at all - the vendor numbers are line counts and byte caps that disagree by an order of magnitude (`research-basis.md` §3, 'Numeric thresholds do not agree'). The useful framing is what the number buys: a few thousand tokens of non-derivable constraints is money well spent; a few thousand tokens of directory listings and generic advice is pure loss that every finding downstream compounds."

**Step 3 — Check the claims against the repo.**
```
python3 <skill>/scripts/ctx_refs.py <repo> --scope agent   # instruction files
python3 <skill>/scripts/ctx_refs.py <repo> --scope all     # plus human docs
```
What `ctx_refs.py` verifies: "file paths, markdown links, runnable commands against `package.json` / `Makefile` / `justfile`, code symbols named in backticks, and a git-derived staleness signal."
Tuning philosophy (important): "It is deliberately tuned for **precision over recall** on agent-facing files, because a false 'your CLAUDE.md is wrong' costs the person's trust in the whole report, while a missed stale tutorial paragraph costs very little."

Triage of each script hit (verbatim):
- "The path really is gone or moved → report it, and give the current path."
- "The command was renamed → report it, and give the current command."
- "It is illustrative ('put your app in `app/main.py`'), a placeholder, or a deliberate reference to something outside the repo → not a finding, drop it."
- **"A finding you have not opened the file to confirm does not go in the report."**

Then the claims the script cannot reach:
- **Behavioural claims** — "a stated timeout, retry count, window, threshold, default, status code, or order of operations. These are among the highest-value findings in any audit, because the doc reads as authoritative and the agent has no reason to doubt it. Matching the *value* is only half the check: confirm something actually **reads** it. A constant that agrees with the doc and is referenced nowhere means the documented behaviour does not exist, which is a larger finding than a wrong number, and one that a value-comparison walks straight past. Grep for the symbol; read the function that is supposed to use it."
- **Environment claims** — "'the lockfile is `package-lock.json`', 'these are our dependencies', 'CI enforces X'. Check the lockfile exists, the dependency list matches the manifest, the CI config says what the doc says. A rule whose stated *reason* is false is a weaker rule than it appears, and knowing that changes which side of a contradiction you recommend keeping."
- **Your own recommendations** — "Before recommending that a prose rule move into lint or CI, confirm that config actually exists in the repo. 'Move this to your eslint config' is not actionable advice when there is no eslint config."
- "Track anything you could not verify and say so in the report rather than assuming. An audit stating a confident falsehood has reproduced the exact defect it exists to find."

**Step 4 — Read the agent-facing files and judge them.**
The single question:
> **Could the agent already know this, or find it out cheaply by looking?**

Three buckets (verbatim):
- **"Keep what only the author knows.** The reason behind a constraint. A gotcha no config confesses. The unwritten convention. Environment quirks. The quality bar. A rule that differs from the tool's default. This is the material the audit exists to protect, and it is never cruft regardless of length."
- **"Question every cache.** A directory listing, a dependency list, an architecture overview, the contents of `package.json` scripts: each is a **cache** of a lookup the agent can do in one tool call. A cache earns its tokens only when the lookup is expensive, and caches go stale - the repo cannot go stale relative to itself. They are also, empirically, the most common content in real instruction files and among the least useful."
- **"Question what restates the model's defaults.** 'Be thorough.' 'Write clean code.' 'Do not be lazy.' 'Be accurate and helpful.' These pay tokens to say nothing the agent was not already doing. The test is behavioural, not aesthetic: **would removing this sentence change what the agent does?**"

The catalog (contents inferred only from this paragraph — file itself unavailable):
> "It holds **eight pattern families** - wrong claims, conflicting claims, misplaced material, dated instruction patterns, volume, structure and pointers, comments, and the keep list - and every row carries an **ID**, **what the pattern does to an agent**, and **what to recommend**. Cite the row ID in each finding. That is what makes this step checkable: a finding you cannot tie to a row is an opinion, and it either gets labelled as one or dropped."
Known IDs referenced in SKILL.md: `1i` = "unfollowable instruction"; `§2` = conflicts (carries the scope-refinement worked example); `§7` = comments triad; `§8` = keep list.

> "**Read the keep list (§8) before flagging anything.** It is the guard against this audit's own worst failure mode - a report that only says 'delete' hurts the people who follow it most carefully - and it binds as hard as the pattern rows. **An audit that finds nothing should change nothing.**"

Completion criterion for Step 4 (verbatim): "This step is done when every **always-on** file in the Step 2 map has been opened and every line has an answer: keep, and why; or a finding carrying a catalog row ID. On-demand files get the same treatment only where Step 3 flagged them or the request named them - say in the report which ones you did not open."

**Step 5 — Find conflicts and duplication.**
> "Contradictions are the finding people are most grateful for and least likely to have spotted, because each rule looks reasonable in its own file."
> "Search across *all* instruction sources at once ... Conflicts hide at the seams between them: a team that adopted Cursor rules and then wrote a CLAUDE.md usually has at least one."

Four conflict signatures (verbatim):
- "Two rules that cannot both be followed (`always use pnpm` / `never use pnpm`)."
- "A rule and its stated exception living in files that never appear together."
- "The same rule stated twice with **different** wording or different thresholds - the drift is the finding; the agent must reconcile them and may pick either."
- "A router or index that points at something renamed or removed. **An index that lies is worse than no index.**"

The false-positive guard: "Distinguish a genuine conflict from a **scope refinement** - one rule narrowing another rather than opposing it. The test: **could an agent satisfy both at once?** If yes, it is a refinement. ... this is the most common false positive in the category, so run the test before reporting."

Duplication: `python3 <skill>/scripts/ctx_dupes.py <repo> --thresh 0.85`
> "Exact duplicates are copy-paste and cost tokens; the **near-duplicate band is where the real findings are**, because those copies have drifted and one of them is now wrong. Say which you believe is current and recommend a single authoritative home. Duplication between a human-facing README and an agent-facing file is often deliberate - flag it once it has diverged, or when the agent-facing copy is the stale one."

**Step 6 — Docs and comments, in that order.**
Four in-scope classes, and the step "is done when each is covered or explicitly recorded as empty":
1. "every doc an agent-facing file points at"
2. "every doc the reference check flagged"
3. "the docs covering the directories with the most commits in the last 90 days":
   ```bash
   git log --since='90 days ago' --name-only --pretty=format: | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head
   ```
4. "`README.md`"
> "Anything outside those four is out of scope for this run - say so in the report rather than sampling further."

Prose docs adjustment: "docs have human readers too, so an explanation that is redundant for the model may be load-bearing for a new contributor. Flag prose that is *wrong* or *contradicts the agent-facing files* with full confidence; flag prose that is merely verbose only when it sits in the always-on path or when someone asked for a docs pass."

Code comments: "the standard is **accuracy first, rationale second**, and the finding is always about the comment, never the code beneath it. Catalog §7 carries the full triad: what to report, what to protect (after checking the code still does what the comment claims), and what is only worth a grouped low-priority mention." Mechanical signals named: "commented-out blocks, TODO age via blame, docstring parameter drift."

**Step 7 — Write the report.** → `CONTEXT_HEALTH_REPORT.md` at the repo root unless asked otherwise; "tell them where it is"; structure from `assets/report-template.md`.

Severity table (verbatim), **set by what it does to the agent, not by how much text is involved**:

| Severity | What qualifies |
|---|---|
| **High** | The agent will act on something false: a broken path, command or symbol in an always-on file; two rules that contradict; an index pointing at something gone. |
| **Medium** | The agent is measurably worse off but not misled: material that is stale but not yet wrong, duplication that has drifted, large always-on caches of the environment, unscoped rules that should be path-scoped or moved to a skill. Splitting is not free - if the material is needed on every task it belongs where it is, and the fix for a weak pointer is sharper wording. |
| **Low** | Real but small: verbosity, restating defaults, comments that echo their code, minor redundancy. Group these; do not itemize thirty of them. |

Per-finding required fields (verbatim): "**location** (`file:line`), the **quoted text**, what **pattern** it matches, **why it matters to an agent** in one or two sentences, and a **concrete recommendation** with replacement text where the fix is a rewrite. **A finding without a specific location is not a finding. A recommendation that says 'consider revising' is not a recommendation.**"

Report proportionality (verbatim):
> "**Keep the report proportionate to its findings, not to the repo.** A report is context too, and it is subject to everything this skill says about context - but the thing to compress is repetition, never coverage. Every High finding gets full treatment however long that runs; a repo with seven real High findings earns a long report. What gets compressed is everything else: Medium findings that share one cause become one entry naming every site, and Low findings live in a table. The failure to avoid is thirty separately-argued entries where six causes explain them all - that buries the three that matter, and it is the same defect the audit exists to find."

Report shape:
1. **Summary** a busy person can act on without reading the rest: "the always-on token figure, counts by severity, and the three highest-impact findings in prose."
2. **Findings**, ordered by severity.
3. **"What is working"** — "and this matters as much as the findings - a short section naming **what is working**: the rationale worth protecting, the well-scoped rules, the comments that carry real reasons. **People act on cleanup reports, and this section is what stops a good comment being deleted alongside the bad ones.**"
4. **"Close with what to re-check next time, so repeat runs compound."**

**Step 8 — Verify before you hand it over.** "Removal is a hypothesis, not a conclusion, and the report's credibility rests on the findings being real."
- "**Re-open every high-severity finding** and confirm the quoted text and line number are right. A misquoted finding discredits the accurate ones beside it."
- "**Check every factual claim the report itself makes.** The report is now context too, and it is held to the standard it is applying. ... anything you could not verify is labelled as an assumption rather than stated flat."
- "**Re-check the protect list against the code.** Every item you are defending as valuable rationale needs to be true. A comment explaining why a constant is 61 earns its place only if the code still uses 61."
- "**Check no finding is a keep-list item** in disguise - particularly the ones where the fix is 'delete this paragraph'."
- "**Check the arithmetic**: token figures are estimates within roughly 15%. Say so, and round them to two significant figures ('~1,400', not '1,405') - four digits on an estimate is false precision, and differences between two such figures are noise unless they are large. If MCP servers are configured, state that their tool schemas are always-on and unmeasured from disk, and that `/context` is what reports them."
- "**Confirm every finding names a document as its subject.** A finding that reduces to 'this code should be written differently' does not belong."

### 1.5 The three scripts (as described; source not available)
- `ctx_map.py` — surface map + always-on vs on-demand token split; owns `SKIP_DIRS` (vendored/generated/fixture exclusions) as the authoritative list.
- `ctx_refs.py` — `--scope agent|all`; verifies file paths, markdown links, runnable commands vs `package.json`/`Makefile`/`justfile`, backticked code symbols, plus a git-derived staleness signal. Tuned precision-over-recall.
- `ctx_dupes.py` — `--thresh 0.85` near-duplicate prose detection.
- All three: "stdlib only, no network, no install. They degrade gracefully outside a git repo (staleness and deletion history go quiet; everything else still runs)."

---

## 2. `prompt-audit` (Anthropic) — full structure

**Not a standalone skill.** It is `skills/claude-api/shared/prompt-audit.md` in `anthropics/skills`, dispatched by the `claude-api` skill's subcommand table:

| Subcommand | Action |
|---|---|
| `prompt-audit` | "Audit prompts, skills, tool descriptions for dated patterns. Read `shared/prompt-audit.md` in order: Step 0, inventory, provenance, pattern scan. **Produce both report and proposed diff without pausing.**" |

### 2.1 Frame
> "Current Claude models follow instructions more closely and more literally than the models much of this text was written for, so the leftover text is not just wasted tokens - **specific outdated instructions actively degrade behavior** (over-triggering, over-planning, rigid responses in gray areas), while merely irrelevant text is comparatively harmless. The audit's job is therefore to find **specific dated instructions**, not to make prompts shorter. **'Every token earns its place' is the frame; 'make it short' is not.**"

**Two artifacts, always:** (1) an audit report with `file:line`, matched pattern, why obsolete, confidence; (2) a **proposed diff**. "Propose - never apply edits without the user's consent."

**Prime directive:** "distinguish cruft from load-bearing content. A finding you cannot tie to a named pattern below, with a reason grounded in the target model's documented behavior, is not a finding. When in doubt, flag it in the report with low confidence and leave it out of the diff. Indiscriminate deletion is the one way an audit makes things worse... The inverse binds too: **an audit that finds nothing should change nothing** - a clean surface is a valid outcome, and an empty diff beats a manufactured one."

### 2.2 Steps
- **Step 0 — scope + target model**, established "from the request and the repository, not by asking. This audit is non-interactive by design: it runs the same way in a chat session, a CI job, or a batch migration, so it states its assumptions and proceeds instead of pausing for confirmation."
- **Step 1 — Inventory the prompt surface**: system prompts and the code assembling them; tool `description` fields and parameter descriptions; `SKILL.md`, `CLAUDE.md`, `.cursorrules`-style rule files, agent instruction files; request-building code (model IDs, thinking config, sampling params, stop sequences, prefill, retry logic, beta headers); few-shot blocks. "List what you found before auditing it, so the user can correct the inventory."
- **Step 2 — Establish provenance**: `git blame` the prompt files. "The question for every emphatic or prohibitive line is: **which failure, on which model, did this prevent - and does that failure still reproduce on the target model?** ... a line nobody can justify is suspect by default." Idiom-dating alone = low confidence only.
- **Step 3 — the deletion rule**: "could the model already know this?" Keep = audience/product, environment facts, quality bar, tool contracts/mechanics, hard judgment calls, *reasons* behind constraints. Remove-candidates = restatements of trained defaults, behavior the model does unprompted, workarounds for fixed failures. Second discriminator: "is the line a **constraint on behavior** (deletion candidate - test it) or **context the model can't get elsewhere** (usually keep)? This check prevents the audit from becoming a length contest: a naive shortening pass deletes exactly the highest-value words."
- **Step 4 — four anti-pattern groups** (each with greppable "Signals"):
  - **Group 1 — Dated prompt text**: 1a pressure language; 1b scaffolds replaced by API features; 1c over-specification; 1d fossils; 1e prohibition clusters; 1f output-shaping choreography.
  - **Group 2 — Brittle skill files.**
  - **Group 3 — Tool descriptions.**
  - **Group 4 — Request config and architecture.**
- **Step 5 — report** (table below).
- **Step 6 — proposed diff.**
- **Step 7 — verify**: "removal is a hypothesis, not a conclusion."

### 2.3 Report format (verbatim field table)

| Field | Content |
|---|---|
| **Location** | `file:line` (or `file:line-range`) |
| **Evidence** | The exact text, quoted |
| **Pattern** | The group/row above it matches |
| **Why obsolete** | One or two sentences tying it to the target model's documented behavior |
| **Confidence** | **High** - documented in current Claude docs or errors on the target model. **Medium** - consistent, widely-observed behavior. **Low** - heuristic or idiom-dating; flag, don't edit. |
| **Action** | `remove` / `rewrite` (give the replacement) / `move` (say where) / `replace-with-API-feature` / `add` (under-description - the fix is *more* text; give it) / `flag` (no edit proposed) |

"Order the report by **confidence**, highest first. Summarize at the top: counts per group, and the two or three highest-impact findings in prose."

**The flag-versus-fix threshold** (a genuinely good anti-cop-out rule, verbatim):
> "A finding that matches a documented row in the groups above *is* a high- or medium-confidence finding, and it gets a concrete proposed action... `flag` is reserved for two things only: low-confidence idiom-dating that no row documents, and items outside the audit's scope. **Do not downgrade a documented-pattern match to `flag` because it 'seems minor,' 'reads as a soft nudge,' 'is a product judgment,' or 'measurably helps'** - those are reasons the user may *decline* your proposed fix, not reasons to withhold it. An audit that correctly identifies the pattern and then proposes nothing has done half the job."

### 2.4 The keep list — "What not to flag" (11 items, condensed but faithful)
1. **"Context is never cruft."** Audience, product, environment facts, quality bar, constraints and their *reasons*. "Too-short prompts produce generic output because the model fills gaps with safe defaults."
2. **"Cruft != length."** "Never justify a deletion by character count alone."
3. **Fragile operations keep exact scripts.** "Prompting effort should scale with how far the task is from what the model does naturally."
4. **Tool contract detail stays - and often grows.**
5. **Prohibitions against current, demonstrated failures stay.**
6. **Trigger/routing text may carry calibrated urgency.** "Flag shouting in bodies, not load-bearing trigger text."
7. **Format-pinning examples on genuinely format-sensitive outputs stay.**
8. **"Working redundancy is not cruft."** "propose deduplication or consolidation only when the duplicates actually **disagree**."
9. **A one-line role statement is fine.**
10. **Deliberate recap is not padding.** "A single end-of-prompt restatement of the few key constraints is a known, reasonable pattern; the anti-pattern is scattered duplication."
11. **"Re-baselining adds text too."** "The audit's job is fit, **in both directions**."

### 2.5 High-value greppable signals from prompt-audit (directly reusable)
- Density of `MUST|NEVER|ALWAYS|CRITICAL|IMPORTANT` in caps; `!!`; **emphasis with no adjacent "because"**.
- `try to|if possible|ideally` attached to actual requirements.
- `you (tend to|often|sometimes)` trait claims; `don't be too [adjective]`.
- `think step by step|take a deep breath`; `<scratchpad>|<thinking>` in instructions.
- `stop_sequences` guarding JSON; `json.loads` inside retry loops; `budget_tokens|temperature|top_p` in request code.
- `every \d+ (tool calls|messages)`; `at most \d+ (words|sentences)`.
- `STEP \d` / numbered imperatives for non-fragile work; runs of **3+** `Do not|Never|Avoid` lines.
- Near-duplicate sentences across sections; `Remember,|Again,|As stated above`.
- `grade|graded|rubric|hidden test`.
- Retired model names: `claude-2|claude-3|claude-instant|3\.5|3\.7`.
- `hold (all )?(findings|results)|don't narrate|no interim`; `never use (bullets|headers|bold)`.
- `reminder:` on a turn cadence; `before|after [date]` conditionals; `now|no longer|instead of` attached to behavioral rules.
- `^You are (a|an) (helpful|expert)` with nothing task-specific following.
- Skill-file signals: "`SKILL.md` not readable in one sitting; hardcoded paths and version pins; **past tense in instruction files**; descriptions that only ever grow in git history."
- Tool-description signals: "descriptions under ~3 sentences (add); `MUST|ALWAYS|NEVER` steering behavior inside descriptions (dial back); fake dialogue or worked examples in descriptions (move); tool names in system-prompt prose (delete)."

### 2.6 Named patterns worth stealing wholesale
- **"Unenforced instructions"**: "rules no code path, eval, or reviewer checks - visibly violated in the app's own transcripts... **Enforce in code what can be enforced in code; delete what nothing enforces and nobody misses.**" (Mirrors context-health's hook/linter/CI exception.)
- **"Patch accretion"**: "many narrow conditionals, each traceable to one incident. The model navigates a maze of special cases instead of a coherent principle... an eval win for adding a line on top of the stack is not evidence the stack should exist."
- **"The recency trap"**: "one session's stumble encoded as a permanent rule... Before keeping a rule, ask: **would this have helped most recent sessions, or just the one that wrote it?**"
- **"Volatile specifics"**: "hardcoded paths, flags, version numbers, API claims with no verification date... Encode architecture, data models, and workflows; verify surviving factual claims against current code as part of the audit."
- **"History narratives"**: "past tense, incident IDs, PR numbers, pinned model names. A rule's authority is the behavior it prescribes, not the incident that motivated it."
- **"Trigger-case enumeration"**: skill descriptions "growing one phrase per missed trigger... Name generalized categories of intent."
- **"Time-sensitive content"**: "An 'old patterns' section instead of dates; one default plus an escape hatch; **information lives in exactly one place**."
- **Removal completeness rule**: "A removal is complete only when everything referencing it goes too: tests asserting the old behavior, call sites and helper functions, docs, and every model-ID pin (READMEs and rule files included)."

---

## 3. `comment-analyzer` (Anthropic subagent, PR review toolkit)

Path: `C:\Users\shan.weng\.claude\plugins\marketplaces\claude-plugins-official\plugins\pr-review-toolkit\agents\comment-analyzer.md`

**Frontmatter:** `name: comment-analyzer`; `model: inherit`; `color: green`; description covers four invocation contexts: (1) after generating large doc comments/docstrings, (2) before finalizing a PR that adds/modifies comments, (3) reviewing existing comments for comment rot, (4) verifying comments accurately reflect the code.

**Persona/mission:** "protect codebases from comment rot by ensuring every comment adds genuine value and remains accurate as code evolves. You analyze comments through the lens of a developer encountering the code months or years later."

**Five analysis axes (verbatim headers + sub-checks):**
1. **Verify Factual Accuracy** — "Function signatures match documented parameters and return types; Described behavior aligns with actual code logic; Referenced types, functions, and variables exist and are used correctly; Edge cases mentioned are actually handled in the code; Performance characteristics or complexity claims are accurate."
2. **Assess Completeness** — "Critical assumptions or preconditions are documented; Non-obvious side effects are mentioned; Important error conditions are described; Complex algorithms have their approach explained; Business logic rationale is captured when not self-evident."
3. **Evaluate Long-term Value** — "Comments that merely restate obvious code should be flagged for removal; Comments explaining 'why' are more valuable than those explaining 'what'; Comments that will become outdated with likely code changes should be reconsidered; Comments should be written for the least experienced future maintainer; Avoid comments that reference temporary states or transitional implementations."
4. **Identify Misleading Elements** — "Ambiguous language that could have multiple meanings; Outdated references to refactored code; Assumptions that may no longer hold true; Examples that don't match current implementation; TODOs or FIXMEs that may have already been addressed."
5. **Suggest Improvements** — rewrite suggestions, added context, "Clear rationale for why comments should be removed", alternative approaches.

**Output format (verbatim skeleton):**
```
**Summary**: Brief overview of the comment analysis scope and findings
**Critical Issues**: Comments that are factually incorrect or highly misleading
- Location: [file:line]
- Issue: [specific problem]
- Suggestion: [recommended fix]
**Improvement Opportunities**: ...
- Location / Current state / Suggestion
**Recommended Removals**: ...
- Location / Rationale
**Positive Findings**: Well-written comments that serve as good examples (if any)
```

**Hard constraint (verbatim):** "IMPORTANT: You analyze and provide feedback only. Do not modify code or comments directly. Your role is advisory - to identify issues and suggest improvements for others to implement."

Note the "Positive Findings" section — same instinct as context-health's "what is working" section, and the same "Location:" requirement.

---

## 4. `claude-md-improver` (Anthropic, `claude-md-management` plugin)

Path: `...\plugins\claude-md-management\skills\claude-md-improver\SKILL.md`
**Frontmatter:** `name: claude-md-improver`; description "Audit and improve CLAUDE.md files in repositories..."; **`tools: Read, Glob, Grep, Bash, Edit`**.

**Explicitly the opposite editing stance from context-health:** "**This skill can write to CLAUDE.md files.** After presenting a quality report and getting user approval, it updates CLAUDE.md files with targeted improvements."

**5 phases:** Discovery → Quality Assessment → **Quality Report Output ("ALWAYS output the quality report BEFORE making any updates")** → Targeted Updates (ask for confirmation; show diffs) → Apply Updates.

**Discovery command:**
```bash
find . -name "CLAUDE.md" -o -name ".claude.md" -o -name ".claude.local.md" 2>/dev/null | head -50
```
File-type table: project root `./CLAUDE.md`; local overrides `./.claude.local.md`; global `~/.claude/CLAUDE.md`; package-specific `./packages/*/CLAUDE.md`; nested subdirectory.

**Scoring rubric (100 pts) — `references/quality-criteria.md`:**
| Criterion | Weight |
|---|---|
| Commands/Workflows | 20 |
| Architecture Clarity | 20 |
| Non-Obvious Patterns | 15 |
| Conciseness | 15 |
| Currency | 15 |
| Actionability | 15 |

Grades: **A 90-100 / B 70-89 / C 50-69 / D 30-49 / F 0-29.**

**Red Flags list (verbatim):** "Commands that would fail (wrong paths, missing deps); References to deleted files/folders; Outdated tech versions; Copy-paste from templates without customization; Generic advice not specific to the project; 'TODO' items never completed; Duplicate info across multiple CLAUDE.md files."

**Assessment process:** "Cross-reference with actual codebase: Run documented commands (mentally or actually); Check if referenced files exist; Verify architecture descriptions."

**`references/update-guidelines.md` core principle:** "Only add information that will genuinely help future Claude sessions. **The context window is precious - every line must earn its place.**"
- **What TO add:** commands/workflows discovered; gotchas & non-obvious patterns; package relationships; testing approaches that worked; configuration quirks. Each with a "Why:" line.
- **What NOT to add:** obvious code info ("The `UserService` class handles user operations." — "The class name already tells us this."); generic best practices; one-off fixes ("Won't recur; clutters the file."); verbose explanations (has a good before/after: 4 lines of JWT RFC exposition → "Auth: JWT with HS256, tokens in `Authorization: Bearer <token>` header.").
- **Validation checklist:** "Each addition is project-specific / No generic advice or obvious info / Commands are tested and work / File paths are accurate / Would a new Claude session find this helpful? / Is this the most concise way to express the info?"

**Report format** is a per-file scorecard table plus **Issues** and **Recommended additions** lists, preceded by a Summary (files found, average score, files needing update).

---

## 5. `consolidate-memory` (Anthropic)

Path: `...\skills-plugin\...\skills\consolidate-memory\SKILL.md`
Frontmatter: `name: "consolidate-memory"`, description: "Reflective pass over your memory files — merge duplicates, fix stale facts, prune the index."

3 phases: **Take stock** (list dir, read `MEMORY.md`, "Note which ones overlap, which look stale, which are thin") → **Consolidate** → **Tidy the index**.

Reusable rules (verbatim):
- **"Separate the durable from the dated."** "Preferences, working style, key relationships, and recurring workflows are durable — keep and sharpen them. Specific projects, deadlines, and one-off tasks are dated — if the date has passed or the work is done, retire the file or fold the lasting takeaway... into a durable one."
- **"Merge overlaps."** "combine into one and keep the richer file's path."
- **"Fix time references."** "Convert 'next week', 'this quarter', 'by Friday' to **absolute dates** so they stay readable later."
- **"Drop what's easy to re-find."** "If a memory just restates something you could pull from the user's calendar, docs, or connected tools on demand, cut it. **Keep what's hard to re-derive**: stated preferences, context behind a decision, who to go to for what."
- **Hard budget on the index:** "`MEMORY.md` ... under 200 lines and ~25KB. One line per entry, under ~150 chars: `- [Title](file.md) — one-line hook`."
- Finish with "a short summary: how many files you touched and what changed."

---

## 6. `skill-creator` (Anthropic) — relevant extracts for building `/context-health`

Path: `C:\Users\shan.weng\.claude\plugins\cache\claude-plugins-official\skill-creator\85cce0381e78\skills\skill-creator\SKILL.md` (487 lines). Files: `agents/{analyzer,comparator,grader}.md`, `references/schemas.md`, `scripts/{aggregate_benchmark,generate_report,improve_description,package_skill,quick_validate,run_eval,run_loop,utils}.py`, `eval-viewer/generate_review.py`, `assets/eval_review.html`.

- **Anatomy**: `SKILL.md` (required, YAML frontmatter `name`+`description`) + `scripts/` (deterministic/repetitive), `references/` (docs loaded as needed), `assets/` (files used in output).
- **Progressive disclosure, three levels**: (1) metadata always in context ~100 words; (2) SKILL.md body when triggered, **<500 lines ideal**; (3) bundled resources as needed, unlimited, "scripts can execute without loading".
- "Keep SKILL.md under 500 lines; if you're approaching this limit, add an additional layer of hierarchy along with clear pointers about where the model using the skill should go next."
- "For large reference files (>300 lines), include a table of contents."
- **Description is the trigger mechanism**: "include both what the skill does AND specific contexts for when to use it. **All 'when to use' info goes here, not in the body.**" And: "currently Claude has a tendency to '**undertrigger**' skills... make the skill descriptions a little bit 'pushy'."
- **Writing style (directly relevant to how a `/context-health` skill should be written):** "Try to explain to the model **why** things are important in lieu of heavy-handed musty MUSTs." / "If you find yourself writing ALWAYS or NEVER in all caps, or using super rigid structures, that's a **yellow flag** — if possible, reframe and explain the reasoning."
- **"Keep the prompt lean.** Remove things that aren't pulling their weight. Make sure to read the transcripts, not just the final outputs."
- **"Look for repeated work across test cases."** If every run independently writes the same helper script, bundle it in `scripts/`.
- **Skill triggering mechanics:** "Claude only consults skills for tasks it can't easily handle on its own — simple, one-step queries... may not trigger a skill even if the description matches perfectly. Complex, multi-step, or specialized queries reliably trigger skills."
- Description optimization loop: `scripts/run_loop.py --eval-set ... --skill-path ... --model ... --max-iterations 5`; 20 trigger evals (8-10 positive, 8-10 **near-miss** negatives), 60/40 train/test split, 3 runs per query, "selected by test score rather than train score to avoid overfitting."

---

## 7. Cross-cutting principles (appear in 2+ artifacts)

1. **Useful information per token — never "shorter".** context-health: "The goal is **useful information per token**, not fewer tokens." prompt-audit: "'Every token earns its place' is the frame; 'make it short' is not." claude-md-improver: "every line must earn its place."
2. **Indiscriminate shortening deletes the best content.** Both audits say this in almost the same words: the padding is short, the rationale is long, so a length-based pass keeps the wrong half.
3. **Keep what only the author knows.** Identical bucket in context-health §Step 4, prompt-audit §Step 3, claude-md-improver "What TO add", consolidate-memory "Keep what's hard to re-derive".
4. **Verify claims against the artifact they describe; existence ≠ truth.** context-health Step 3, comment-analyzer axis 1, claude-md-improver assessment process.
5. **An audit that finds nothing should change nothing.** Verbatim in both context-health (Step 4) and prompt-audit (prime directive + keep-list item 8).
6. **Report, don't edit.** context-health ("Diagnose, never apply"), comment-analyzer ("advisory... Do not modify"), prompt-audit ("Propose - never apply edits without the user's consent"). claude-md-improver is the exception and gates edits behind an explicit report-then-approve step.
7. **Every finding needs `file:line` + quoted evidence + concrete replacement.** All three audits.
8. **A "what's working / positive findings / protect list" section is mandatory**, precisely because people act on cleanup reports.
9. **Named-pattern discipline.** context-health: cite a catalog row ID or it's an opinion. prompt-audit: "A finding you cannot tie to a named pattern... is not a finding."
10. **Prose rules that could be enforced mechanically should be.** context-health's "one exception"; prompt-audit's "Unenforced instructions".
11. **Non-interactive by design; state assumptions, don't ask.** Both context-health Step 1 and prompt-audit Step 0.
12. **Explain the why in the skill's own prose; caps-lock MUSTs are a yellow flag** (skill-creator) — and the two audits both model this by arguing rather than commanding.

---

## 8. Top reusable detection heuristics for a new `/context-health`

**Structural / cost**
1. Split every context source into **always-on vs on-demand** and report always-on as an absolute token count *and* a share of the window. This is "the framing number for the whole report."
2. `@imports` **do not** reduce always-on cost — flag any doc or advice claiming otherwise.
3. `.claude/rules/*.md` with no `paths:` and `.cursor/rules/*.mdc` with `alwaysApply: true` are **CLAUDE.md content wearing a different hat**.
4. Skill/subagent **descriptions** are always-on; their **bodies** are not. Audit descriptions for trigger-case enumeration that grows one phrase per missed trigger.
5. MCP tool schemas are always-on, usually the single largest item, and **not measurable from disk** — say so and point at `/context`.
6. Exclude vendored/generated/fixture trees or "every metric is meaningless".

**Truth**
7. Broken path / renamed command / missing symbol in an **always-on** file = automatic High.
8. **Behavioural claims** (timeout, retry count, threshold, status code, order of operations) are the highest-value class — and the second half of the check is "does anything actually **read** this constant?" A value that matches but is referenced nowhere is a *bigger* finding than a wrong value.
9. **Environment claims**: lockfile name, dependency list vs manifest, "CI enforces X" vs the CI config. A rule whose stated reason is false is a weaker rule than it appears.
10. Verify your own recommendation's premise (don't say "move it to eslint" when there's no eslint config).
11. Triage every script hit by hand; drop illustrative/placeholder/external references. "A finding you have not opened the file to confirm does not go in the report."

**Conflict / duplication**
12. Search **all** instruction sources at once; conflicts live at tool seams (Cursor rules + CLAUDE.md).
13. False-positive guard: **scope refinement vs contradiction** — "could an agent satisfy both at once?"
14. The **near-duplicate** band (~0.85 similarity), not exact duplicates, is where the real findings are — because those copies have drifted and one is now wrong.
15. **An index that lies is worse than no index** — routers/indexes pointing at renamed or removed targets.

**Value**
16. The one question: **"Could the agent already know this, or find it out cheaply by looking?"**
17. **"Question every cache."** Directory listings, dependency lists, architecture overviews, `package.json` script dumps — a cache earns tokens only when the lookup is expensive, and "the repo cannot go stale relative to itself."
18. **Defaults restatement test is behavioural, not aesthetic:** "would removing this sentence change what the agent does?"
19. **Unfollowable instruction** (catalog 1i): a rule requiring something that cannot succeed (a test suite that can't pass, a command that errors) — a *context* finding even though the fix is a code task.
20. **Unenforced instruction**: nothing in code, CI, or review checks it, and transcripts show it violated → enforce or delete.
21. **The recency trap**: "would this have helped most recent sessions, or just the one that wrote it?"
22. **Patch accretion**: many narrow incident-shaped conditionals instead of one principle.
23. **Volatile specifics**: hardcoded paths, flags, version pins, API claims with no verification date.
24. **History narratives / past tense in instruction files**: incident IDs, PR numbers, pinned model names, "we changed X to Y".
25. **Migration-relative phrasing**: "now", "no longer", "also counts", "instead of" attached to behavioral rules — a diff against a prompt version the agent never saw.
26. **Time-sensitive content**: "if before [date]" conditionals, relative dates. Convert to absolute or replace with an "old patterns" section (consolidate-memory + prompt-audit agree).
27. **Pressure-language density** with no adjacent "because"; `try to|if possible` on real requirements; runs of 3+ prohibitions; `Remember,|Again,|As stated above`.
28. **Comments**: accuracy first, rationale second. Mechanical signals — commented-out blocks, TODO age via `git blame`, docstring parameter drift, signature/param mismatch.
29. **Comment triad**: report (wrong/misleading), protect (real rationale — *after* verifying the code still does what it claims), group as Low (echoes-the-code).
30. **Git-activity targeting for docs**: `git log --since='90 days ago' --name-only --pretty=format: | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head` → audit docs covering the hottest directories.

---

## 9. Distinguishing valuable rationale from low-value narration — the techniques

| Technique | Source | Test |
|---|---|---|
| **The knowability test** | context-health Step 4 | "Could the agent already know this, or find it out cheaply by looking?" |
| **The cache test** | context-health Step 4 | Is this a cached lookup? Does the lookup cost more than the tokens? Can it go stale relative to the repo? |
| **The behavioural-delta test** | context-health Step 4 | "Would removing this sentence change what the agent does?" |
| **Constraint vs context** | prompt-audit Step 3 | Constraint on behavior → deletion candidate, test it. Context the model can't get elsewhere → keep. |
| **Provenance interrogation** | prompt-audit Step 2 | "Which failure, on which model, did this prevent - and does that failure still reproduce?" A line nobody can justify is suspect by default. |
| **Strategy vs rule** | prompt-audit 1c | "If removing the sentence wouldn't change what is legal or how success is measured, it's strategy - delete it." |
| **Prohibition provenance** | prompt-audit 1e | Does it carry a stated reason or encode a real business/policy constraint? Style-tic bans with no provenance are cruft. **"A surrounding cluster of legitimate reasoned prohibitions does not launder the no-provenance ones mixed into it; classify each line separately."** |
| **Durable vs dated** | consolidate-memory | Preferences/workflows/relationships = durable. Projects/deadlines/one-off tasks = dated; fold the lasting takeaway forward and retire the rest. |
| **Why over what** | comment-analyzer axis 3 | "Comments explaining 'why' are more valuable than those explaining 'what'." |
| **The least-experienced-maintainer lens** | comment-analyzer | Written for a developer arriving months later with no context. |
| **Would-a-new-session-find-this-helpful** | claude-md-improver | Final validation checklist item. |
| **Working redundancy** | prompt-audit keep-list 8 | Duplication that is *functioning* is a refactoring preference, not a finding. Flag only when the duplicates **disagree**. |

---

## 10. Report / prioritization formats worth copying

**A. context-health's severity ladder** — best-in-class because severity is defined by *effect on the agent*, not by volume, and each tier has a concrete membership test (High = "the agent will act on something false"). Copy verbatim in spirit.

**B. context-health's report skeleton:**
1. Assumptions (scope, depth, exclusions) at the top "where they can be corrected"
2. Summary: always-on token figure + counts by severity + top 3 findings **in prose**
3. Findings ordered by severity; each = location / quoted text / pattern ID / why it matters to an agent / concrete recommendation with replacement text
4. **What is working** (the protect list)
5. What to re-check next time, "so repeat runs compound"

**C. context-health's proportionality rule** — "Every High finding gets full treatment... Medium findings that share one cause become one entry naming every site, and Low findings live in a table."

**D. prompt-audit's finding table + confidence ladder + `Action` verb** (`remove` / `rewrite` / `move` / `replace-with-API-feature` / `add` / `flag`) — the **`add` action is the piece most audits are missing**: sometimes the fix is more text.

**E. prompt-audit's flag-vs-fix threshold** — the explicit ban on downgrading a documented pattern to `flag` because it "seems minor". Prevents an audit that identifies everything and proposes nothing.

**F. comment-analyzer's four-bucket output** (Critical Issues / Improvement Opportunities / Recommended Removals / Positive Findings) — a good shape for the comments sub-report specifically.

**G. claude-md-improver's weighted scorecard** — the only artifact producing a single number. Weak on rigor (the weights are arbitrary and context-health explicitly warns against quoting thresholds), but a per-file grade is genuinely useful for tracking repeat runs and for a "which file do I fix first" summary.

**H. Two-artifact output (report + proposed diff)** from prompt-audit. context-health produces one; a diff appendix, clearly marked as not applied, is strictly more actionable.

---

## 11. Gaps / weaknesses a new `/context-health` could improve on

1. **The existing context-health cannot be re-read or extended.** Its `references/findings-catalog.md` (8 families, row IDs), `detection-notes.md`, `research-basis.md`, `assets/report-template.md`, and its three scripts are unavailable on this machine and unpublished. A new skill has to rebuild the catalog — which is also the opportunity: **publish the catalog as a first-class, citable, versioned file** so findings are auditable.
2. **No machine-readable output.** Everything is prose Markdown. Emitting `context-health.json` alongside the report (findings with `id`, `severity`, `file`, `line`, `pattern`, `token_delta`, `status`) enables CI gating, diffing between runs, and "previously declined" tracking without re-parsing prose.
3. **"Previously declined" is manual.** context-health says to read the last report and not re-raise declined findings, but there is no mechanism. A `.context-health-ignore` / a `status:` field in the JSON, or fingerprinting a finding by (file, quoted-text-hash, pattern-id) would make repeat runs actually compound.
4. **No token accounting for MCP.** context-health explicitly punts ("not measurable from disk... `/context` is what reports them"). A new skill could read `.mcp.json` / `claude_desktop_config.json`, actually enumerate configured servers, and at minimum name them and their tool counts — or shell out to get schemas.
5. **prompt-audit's model-relative dimension is missing from context-health entirely.** context-health checks claims against the *repo*; prompt-audit checks instructions against the *target model*. A repo's CLAUDE.md full of "think step by step", "be thorough, don't be lazy", `<scratchpad>` scaffolds and 3.5-era workarounds is a real context-health problem that context-health's eight families don't obviously name. **Merging prompt-audit Group 1 (dated prompt text) into a context-health catalog is the single biggest content win available.**
6. **No cost model for the recommendation.** Findings say "move this to a skill" without estimating the token delta. Reporting `always-on: ~4,200 → ~1,300 if all High+Medium accepted` makes the report far more persuasive and is cheap to compute.
7. **Precision-over-recall is asserted but unmeasured.** No skill here reports its own false-positive rate or offers a confidence field on *context-health* findings (prompt-audit has one; context-health does not). Adding an explicit confidence dimension orthogonal to severity would help — a High-severity/Low-confidence finding is a different object from a High/High.
8. **Nothing audits `.claude/settings.json` hooks, `output-styles`, slash commands, or `permissions`** as context surfaces, even though hooks inject text and permissions change behavior. The always-on table stops at rules/skills/subagents/MCP.
9. **Nothing audits agent-facing files for *missing* content.** All four audits are subtractive by default (prompt-audit's keep-list item 11 gestures at it: "Re-baselining adds text too", and its `add` action exists). A context audit that never says "you have no documented test command and three sessions rediscovered it" is leaving value on the table. claude-md-improver's "Recommended additions" is the only place this appears.
10. **No transcript evidence.** prompt-audit mentions rules "visibly violated in the app's own transcripts" but no skill actually reads `~/.claude/projects/*/*.jsonl`. Those transcripts are on disk and would let a new skill say **"this rule was violated in 4 of your last 20 sessions"** — the strongest possible evidence for an unenforced instruction, and completely unexploited by all existing artifacts.
11. **Duplication detection is prose-similarity only** (`--thresh 0.85`). Semantic duplication across files with different wording — the exact thing that produces drifted, contradictory rules — is precisely what a similarity threshold misses, and no skill addresses it.
12. **The scorecard/grade idea is orphaned.** claude-md-improver has grades; context-health rejects thresholds. There is a middle path: no absolute grade, but a **delta against the previous run** (always-on tokens, High count, unresolved findings), which is threshold-free and makes repeat runs meaningful.
13. **No worked example anywhere.** None of these skills ships a sample report. Bundling one `assets/example-report.md` would sharpen the output far more reliably than describing the format.

---

## 12. Verbatim lines most worth reusing

- "The goal is **useful information per token**, not fewer tokens."
- "Contradiction is worse than omission, and it gets *more* expensive as models follow instructions more literally."
- "Every finding names a document as its subject."
- "The code is evidence, never the subject."
- "A finding you have not opened the file to confirm does not go in the report."
- "An audit stating a confident falsehood has reproduced the exact defect it exists to find."
- "Could the agent already know this, or find it out cheaply by looking?"
- "The repo cannot go stale relative to itself."
- "Would removing this sentence change what the agent does?"
- "An index that lies is worse than no index."
- "A finding without a specific location is not a finding. A recommendation that says 'consider revising' is not a recommendation."
- "A report is context too, and it is subject to everything this skill says about context."
- "Removal is a hypothesis, not a conclusion."
- "An audit that finds nothing should change nothing."
- "Indiscriminate deletion is the one way an audit makes things worse."
- "'Every token earns its place' is the frame; 'make it short' is not."
- "Cruft != length."
- "Context is never cruft."
- "A surrounding cluster of legitimate reasoned prohibitions does not launder the no-provenance ones mixed into it."
- "People act on cleanup reports, and this section is what stops a good comment being deleted alongside the bad ones."

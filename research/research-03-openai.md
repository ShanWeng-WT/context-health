# Research 03 — OpenAI official docs, guides, cookbook and blog

Source material for the `/context-health` skill. Everything below is from OpenAI-owned
properties (agents.md is Linux Foundation / Agentic AI Foundation stewarded, seeded by OpenAI).
Fetched 2026-09-08.

Note on URLs: `developers.openai.com/codex/*` now 308-redirects to `learn.chatgpt.com/docs/*`.
Both are canonical OpenAI docs. Every doc page has a machine-readable twin at `<url>.md`.
Index: <https://learn.chatgpt.com/llms.txt> and <https://developers.openai.com/api/docs/llms.txt>.

---

## 1. AGENTS.md — what it should contain, structure, precedence

### 1.1 The spec site (agents.md)

URL: <https://agents.md/>

- Framing: "Think of AGENTS.md as a README for agents". Claimed adoption "over 60k
  open-source projects".
- Why separate from README: READMEs are for humans; AGENTS.md holds "the extra, sometimes
  detailed context coding agents need: build steps, tests, and conventions that might
  clutter a README". Three stated reasons: predictable place for instructions; keep READMEs
  concise; "Provide precise, agent-focused guidance".
- **Suggested sections** (explicitly "popular choices", not required): Project overview;
  Build and test commands; Code style guidelines; Testing instructions; Security
  considerations. Plus "Commit messages or pull request guidelines, security gotchas, large
  datasets, deployment steps: anything you'd tell a new teammate belongs here too."
- **No required fields.** FAQ: "Are there required fields? No. AGENTS.md is just standard
  Markdown. Use any headings you like; the agent simply parses the text you provide."
- **No size guidance whatsoever on agents.md.** This is a notable gap — the only size cap
  in the OpenAI ecosystem is Codex's `project_doc_max_bytes` (see 1.2).
- **Nesting / precedence (the "closest file wins" rule)** — two verbatim statements:
  - FAQ: "What if instructions conflict? **The closest AGENTS.md to the edited file wins;
    explicit user chat prompts override everything.**"
  - How-to step 4: "Agents automatically read the nearest file in the directory tree, so the
    closest one takes precedence and every subproject can ship tailored instructions. For
    example, at time of writing the main OpenAI repo has **88 AGENTS.md files**."
    → *This is the single most citable number for "many small nested files beats one big file"
    in the OpenAI worldview.*
- Living document: "Treat AGENTS.md as living documentation."
- Migration: rename + symlink (`mv AGENT.md AGENTS.md && ln -s AGENTS.md AGENT.md`).
- Auto-run of commands: "Will the agent run testing commands found in AGENTS.md
  automatically? Yes—if you list them." → implication for the audit: **commands written in
  an AGENTS.md are executable surface, not just prose.** Stale/wrong commands are a real
  failure mode, not cosmetic.
- Ecosystem list (why this matters for a multi-tool repo audit): Codex, Jules, Factory,
  Aider, goose, opencode, Zed, Warp, VS Code, Devin, UiPath, Junie, Amp, Cursor, RooCode,
  Gemini CLI, Kilo Code, Phoenix, Semgrep, GitHub Copilot coding agent, Ona, Windsurf,
  Augment Code.

### 1.2 Codex docs — discovery, precedence, size cap

URL: <https://learn.chatgpt.com/docs/agent-configuration/agents-md>
(alias <https://developers.openai.com/codex/guides/agents-md>)

Opening line: "Codex reads `AGENTS.md` files before doing any work."

**Discovery order (verbatim structure):**
1. **Global scope** — in `~/.codex` (or `$CODEX_HOME`): `AGENTS.override.md` if it exists,
   else `AGENTS.md`. "Codex uses only the first non-empty file at this level."
2. **Project scope** — starting at project root (typically the Git root), walk *down* to the
   CWD. At each directory: `AGENTS.override.md`, then `AGENTS.md`, then any
   `project_doc_fallback_filenames`. "Codex includes at most one file per directory."
3. **Merge order** — concatenated root-to-leaf, joined by blank lines. "**Files closer to
   your current directory override earlier guidance because they appear later in the
   combined prompt.**"

→ Important mechanical detail for the audit: precedence in Codex is **positional, not
semantic**. Nothing resolves a contradiction; the later text just sits after the earlier
text and the model is left to reconcile. This is exactly the failure the GPT-5 guide warns
about (§2). A repo with a root AGENTS.md saying X and `services/foo/AGENTS.md` saying not-X
is shipping a contradiction into the prompt, not an override.

**Size cap — the one hard number:**
- "Codex skips empty files and stops adding files once the combined size reaches the limit
  defined by `project_doc_max_bytes` (**32 KiB by default**)."
- Advice at the cap: "**Raise the limit or split instructions across nested directories when
  you hit the cap.**"
- Troubleshooting: "**Instructions truncated:** Raise `project_doc_max_bytes` or split large
  files across nested directories to keep critical guidance intact."
- Config reference wording is subtly different: `project_doc_max_bytes` = "Maximum bytes
  read from `AGENTS.md` when building project instructions."
  (<https://learn.chatgpt.com/docs/config-file/config-reference>) and config-advanced says
  "how much to read from **each** `AGENTS.md` file"
  (<https://learn.chatgpt.com/docs/config-file/config-advanced#project-instructions-discovery>).
  → The three pages disagree on whether 32 KiB is per-file or combined. **Audit-safe reading:
  treat 32 KiB (32,768 bytes ≈ 8k tokens) as the ceiling for the whole merged instruction
  chain.** Anything approaching it risks silent truncation.
- `project_doc_fallback_filenames` (e.g. `["TEAM_GUIDE.md", ".agents.md"]`) — "Filenames not
  on this list are ignored for instruction discovery." → *Audit check: a repo with
  `CONVENTIONS.md`/`CONTRIBUTING-AI.md` that nobody wired into the fallback list is dead
  weight for Codex.*

**Override files:** `AGENTS.override.md` in a directory **suppresses** the `AGENTS.md` in
that same directory. "Codex stops searching once it reaches your current directory, so place
overrides as close to specialized work as possible." A sample tree in the doc shows
`services/payments/AGENTS.md` annotated "Ignored because an override exists".
→ *Audit check: an `AGENTS.md` sitting next to an `AGENTS.override.md` is dead context.*

**Refresh semantics:** "Codex rebuilds the instruction chain on every run (and at the start
of each TUI session), so there is no cache to clear manually." Instruction chain is built
once per run, not per turn.

**How to audit which files loaded (OpenAI's own recipe — directly reusable):**
- `codex --ask-for-approval never "Summarize the current instructions."` from repo root
- `codex --cd subdir --ask-for-approval never "Show which instruction files are active."`
- `codex -c log_dir=./.codex-log` then read `./.codex-log/codex-tui.log`, or inspect the
  latest `session-*.jsonl`.

**Code review rules section** (also in the GitHub integration doc):
- Add a `## Code Review Rules` heading "to the `AGENTS.md` closest to the code the rules
  govern".
- "Keep rules concise, explain the behavior to flag and any safe path or exception, and
  **reserve formatting and lint checks for CI**."

### 1.3 How AGENTS.md is actually injected (Codex Prompting Guide)

URL: <https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide>
(section "Using agents.md")

- "Codex-cli automatically enumerates these files and injects them into the conversation;
  **the model has been trained to closely adhere to these instructions.**"
- Each discovered file becomes **its own user-role message**, headed
  `# AGENTS.md instructions for <directory>` and wrapped in `<INSTRUCTIONS>...</INSTRUCTIONS>`.
- "Messages are injected near the top of the conversation history, before the user prompt,
  in root-to-leaf order: global instructions first, then repo root, then each deeper
  directory."
- Override files still show the directory name in the header.

→ Two consequences for the audit:
1. AGENTS.md content is treated as **user-role instruction**, not background documentation.
   Trained-in adherence means a stale rule is followed, not ignored.
2. Because it sits at the top of history **before the user prompt**, it is exactly the
   "stable prefix" that prompt caching depends on (see §5).

### 1.4 "Keep it small" — the Customization overview

URL: <https://learn.chatgpt.com/docs/customization/overview>

This is the strongest OpenAI statement of the context-bloat thesis:

- "`AGENTS.md` gives Codex durable project guidance that travels with your repository and
  applies before the agent starts work. **Keep it small.**"
- Use it for: build/test commands, review expectations, repo-specific conventions,
  directory-specific instructions.
- "**Start with only the instructions that matter.** Codify recurring review feedback, put
  guidance in the closest directory where it applies, and tell the agent to update
  `AGENTS.md` when you correct something so future sessions inherit the fix."

**When to update AGENTS.md** — four triggers, each of which inverts cleanly into an audit
signal:
- "**Repeated mistakes**: If the agent makes the same mistake repeatedly, add a rule."
- "**Too much reading**: If it finds the right files but reads too many documents, add
  routing guidance (which directories/files to prioritize)." → *Context bloat is explicitly
  framed as a symptom of missing routing, not just too many words.*
- "**Recurring PR feedback**: If you leave the same feedback more than once, codify it."
- "**Automate drift checks**: Use scheduled tasks to run recurring checks (for example,
  daily) that look for guidance gaps and suggest what to add to `AGENTS.md`."
  → *OpenAI explicitly endorses a recurring automated audit of the context files. Direct
  precedent for a `/context-health` skill.*

- Enforcement layering: "Pair `AGENTS.md` with infrastructure that enforces those rules:
  pre-commit hooks, linters, and type checkers catch issues before you see them."
  → *Audit check: any AGENTS.md rule that a linter/formatter/type-checker could enforce
  deterministically is misplaced. It costs tokens every run and buys nothing.*

- Global vs repo split: "Use the global file to shape how Codex communicates with you (for
  example, review style, verbosity, and defaults), and keep repo files focused on team and
  codebase rules."
  → *Audit check: personal style preferences checked into a team repo file is a category
  error by OpenAI's own layering.*

- Layer table:

  | Layer  | Global               | Repo                                           |
  |--------|----------------------|------------------------------------------------|
  | AGENTS | `~/.codex/AGENTS.md` | `AGENTS.md` in repo root or nested directories |
  | Skills | `~/.agents/skills`   | `.agents/skills` in repo                        |

- Skills vs AGENTS.md — the progressive-disclosure argument: "Skills are loaded and visible
  to the agent (at least their metadata), so Codex can discover and choose them implicitly.
  **This keeps rich workflows available without bloating context up front.**"
  Progressive disclosure spelled out: metadata (`name`, `description`) → `SKILL.md` when
  chosen → references/scripts only when needed.
  → *Audit check: a long procedural workflow living in AGENTS.md should be a skill. That's
  the single highest-leverage always-on-token reduction OpenAI describes.*

- Build order recommended: AGENTS.md (+ hooks/linters) → plugin or skill → MCP → subagents.

### 1.5 Blog framing

<https://openai.com/index/introducing-codex/> (openai.com serves 403 to fetchers; quote
recovered via search index, consistent across secondary sources):
"Codex can be guided by AGENTS.md files placed within your repository. These are text files,
akin to README.md, where you can inform Codex how to navigate your codebase, which commands
to run for testing, and how best to adhere to your project's standard practices."

<https://learn.chatgpt.com/guides/build-ai-native-engineering-team> ("Building an AI-Native
Engineering Team") — AGENTS.md appears in three getting-started checklists:
- Build: "Iterate on an AGENTS.md file that unlocks agentic loops like running tests and
  linters to receive feedback"
- Test: "Set guidelines for test coverage in your AGENTS.md file"
- Document: "Incorporate documentation guidelines into your AGENTS.md"; "With AGENTS.md,
  instructions to update documentation as needed can be automatically included with every
  prompt for more consistency."

---

## 2. Instruction conflicts and contradictions — the core material

### 2.1 GPT-5 prompting guide, "Instruction following" (the canonical passage)

URL: <https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide>
(mirror: <https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide>)

The load-bearing sentence, verbatim:

> "Like GPT-4.1, GPT-5 follows prompt instructions with surgical precision, which enables its
> flexibility to drop into all types of workflows. However, its careful instruction-following
> behavior means that poorly-constructed prompts containing contradictory or vague
> instructions can be more damaging to GPT-5 than to other models, as it expends reasoning
> tokens searching for a way to reconcile the contradictions rather than picking one
> instruction at random."

Short pull-quotes:
- "poorly-constructed prompts containing contradictory or vague instructions"
- "expends reasoning tokens searching for a way to reconcile the contradictions"
- "rather than picking one instruction at random"

**The mechanism claim is what matters for the skill:** a contradiction is not a coin-flip.
The model *burns reasoning tokens* trying to satisfy both. Cost is paid on every turn, and
it degrades the trace quality, not just the answer. This is the strongest available
justification for "contradictions are the #1 finding class in a context audit."

**The worked adversarial example** (CareFlow Assistant, a healthcare scheduling agent). The
guide plants two contradictions and names them explicitly:
1. "Never schedule an appointment without explicit patient consent recorded in the chart"
   conflicts with "auto-assign the earliest same-day slot without contacting the patient as
   the first action to reduce risk."
2. "Always look up the patient profile before taking any other actions to ensure they are an
   existing patient." conflicts with "When symptoms indicate high urgency, escalate as
   EMERGENCY and direct the patient to call 911 immediately before any scheduling step."

Note the *shape* of both: they are **both individually reasonable rules, written at
different times, in different sections, by (implicitly) different people.** Neither is
wrong. That is exactly what accretes in a two-year-old CLAUDE.md/AGENTS.md.

**The fixes** (also instructive — both are one-line surgical edits, not rewrites):
- Change "without contacting the patient" → "after informing the patient of your actions"
  so it is consistent with the consent rule.
- Add "Do not do lookup in the emergency case, proceed immediately to providing 911
  guidance." — i.e. **carve an explicit exception rather than deleting either rule.**

Framed as: "By resolving the instruction hierarchy conflicts, GPT-5 elicits much more
efficient and performant reasoning."

**The closing paragraph is effectively the mission statement for a context-health skill:**

> "We understand that the process of building prompts is an iterative one, and many prompts
> are living documents constantly being updated by different stakeholders - but this is all
> the more reason to thoroughly review them for poorly-worded instructions. Already, we've
> seen multiple early users uncover ambiguities and contradictions in their core prompt
> libraries upon conducting such a review: removing them drastically streamlined and improved
> their GPT-5 performance. We recommend testing your prompts in our prompt optimizer tool to
> help identify these types of issues."

Short pull-quotes:
- "many prompts are living documents constantly being updated by different stakeholders"
- "all the more reason to thoroughly review them for poorly-worded instructions"
- "removing them drastically streamlined and improved their GPT-5 performance"

### 2.2 GPT-5.1 migration guidance

URL: <https://cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide>

- "Instruction following: For other behavior issues, GPT-5.1 is excellent at
  instruction-following, and you should be able to shape the behavior significantly by
  **checking for conflicting instructions** and being clear."
- Reinforces the same theme: the first debugging move for bad agent behavior is to look for
  a contradiction, not to add another rule.

### 2.3 GPT-5.6 Sol guidance (the crispest single sentence)

URL: <https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6>

> "Review the remaining instructions for contradictions. GPT-5-class models follow prompt
> contracts closely, so **conflicting rules can create more instability than missing detail.**"

Short pull-quote: "conflicting rules can create more instability than missing detail"

Also: "When a prompt regresses, debug it with a small set of real traces. Identify the
failure mode, find the instruction or contradiction that likely caused it, make a surgical
edit, and rerun the same cases."

### 2.4 GPT-6 Astra — OpenAI explicitly recommends auditing AGENTS.md

URL: <https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra>

> "GPT-6 Astra is stronger at general instruction following than our previous models, giving
> you greater control over its behavior. It can be more sensitive to instructions contained
> in skills and other files, such as `AGENTS.md`. **We strongly recommend auditing skills and
> other files accessible to your model for instructions that could influence its behavior.**"

And under "Instruction following":

> "GPT-6 Astra is better able to follow longer instructions, but can also be more sensitive
> to information in context. For example, **unclear or conflicting guidance in a skill file
> may cause the model to pause and block work early.** Make the priority of user instructions
> and skills explicit."

Recommended remediation prompts (verbatim, useful as skill primitives):
- Priority statement to add: "The user's instructions take precedence over guidelines
  provided in a skill. If explicit user instructions conflict with a skill's instructions,
  prioritize the user's instructions."
- **Self-diagnosis prompt** — "If a skill causes you to ask for permission or confirmation,
  pause, leave requested work unfinished, or diverge from the user's intent, name and link to
  the exact SKILL.md file you read, quote the relevant instruction, and briefly explain how
  it applies. Distinguish explicit skill requirements from your interpretation of
  guidelines."
- With the explicit framing: "**Use this prompt to find silent and conflicting guidance when
  your application loads many skills and instruction files such as `AGENTS.md`.**"

→ *This is the closest thing OpenAI has published to a `/context-health` recipe. It's a
runtime probe rather than a static audit, but the skill should probably offer both.*

Symptom list from the same page, worth reusing as "the agent is telling you your context is
sick" indicators:
- unnecessary approval pauses / "keeps asking for approval before proceeding"
- pausing and blocking work early
- leaving requested work unfinished
- diverging from user intent

---

## 3. Redundancy, over-specification, verbosity, instruction hierarchy

### 3.1 GPT-5.6 Sol — the "simplify first" protocol WITH NUMBERS

URL: <https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6>

The single most quotable quantitative claim in the whole OpenAI corpus for this skill:

> "Removing repeated instructions and examples and simplifying tool descriptions can improve
> task performance and token efficiency. In a sample of internal coding-agent eval runs,
> configurations with **leaner system prompts improved evaluation scores by roughly 10–15%
> while reducing total tokens by 41–66% and cost by 33–67%.** Results will vary by workload,
> so treat these ranges as directional and validate changes on representative tasks from your
> own application."

**"Simplify prompts first" — ablation method:** "Start with a prompt and tool set that
already works. Remove one group of instructions, examples, or tools at a time, then rerun the
same evals."

**TRIM list (verbatim, five items — a ready-made audit taxonomy):**
- repeated statements of the same rule;
- repeated style or process instructions that do not change behavior;
- examples that do not change behavior;
- process instructions for behavior the model already performs reliably;
- tools and tool descriptions unrelated to the task.

**KEEP list (verbatim, five items):**
- the user-visible outcome;
- success criteria and stopping conditions;
- safety, business, evidence, and permission constraints;
- tool-routing rules when the route depends on context;
- required output shape and validation requirements.

→ *These two lists are directly transplantable as the classification buckets for a
context-health report.*

**On absolutes / prohibitions:**
> "Avoid unnecessary absolute rules. Use ALWAYS, NEVER, must, and only for true invariants
> such as safety rules, required fields, or actions that should never happen. For judgment
> calls, such as when to search, ask, use a tool, or keep iterating, prefer decision rules."

→ *Audit check: count ALWAYS/NEVER/MUST/CRITICAL/IMPORTANT tokens. Each one that isn't a
true invariant is over-specification by OpenAI's rule. Note this is the OPPOSITE emphasis
from the common Anthropic-side advice to state rules positively; see §7.*

**On repeated approval language causing pathology:**
> "Keep the policy in one place and state each rule once. **Repeating instructions such as
> 'ask first,' 'do not mutate,' or 'wait for approval' can cause unnecessary approval requests
> for safe, expected actions.**"

→ *Concrete, testable audit finding: duplicated caution language across CLAUDE.md +
AGENTS.md + a skill produces measurable behavioral harm (over-pausing), not just token cost.*

**On outcome-first vs step-prescription:**
> "Describe the destination rather than prescribing every step. GPT-5.6 can usually choose an
> efficient search, tool, or reasoning path when the prompt states what good looks like."

**On stale brevity instructions:**
> "When migrating, check whether broad brevity instructions such as 'Be concise' or 'Keep it
> short' are still useful. They may be unnecessary for some tasks and can sometimes make
> responses too brief."
→ *Audit check for stale model-era instructions: a rule written for a 2023-era model that
the current model already does natively is pure token cost + possible over-correction.*

**Suggested prompt structure** (their recommended skeleton — "Keep each section short. Add
detail only where it changes behavior."):
`Role / Personality / Goal / Success criteria / Constraints / Tools / Output / Stop rules`

**Prompt migration workflow (5 steps):**
1. Switch the model and preserve the current reasoning effort.
2. Run representative evals before changing the prompt.
3. Remove obsolete scaffolding, repeated instructions, and irrelevant tools.
4. Add only the smallest targeted instruction that fixes a measured regression.
5. Re-run evals after each prompt or reasoning change.
Plus: "Do not rewrite a working prompt stack all at once."
→ *Directly supports a "report, don't edit" / one-change-at-a-time posture for the skill.*

### 3.2 Agentic eagerness & context-gathering budgets (GPT-5 guide)

URL: <https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide>

Concept: "agentic eagerness ... its balance between proactivity and awaiting explicit
guidance." GPT-5 default is "thorough and comprehensive when trying to gather context".

**`<context_gathering>` block — the medium-budget version (verbatim, abridged):**
```
Goal: Get enough context fast. Parallelize discovery and stop as soon as you can act.
Method:
- Start broad, then fan out to focused subqueries.
- In parallel, launch varied queries; read top hits per query. Deduplicate paths and cache;
  don't repeat queries.
- Avoid over searching for context. If needed, run targeted searches in one parallel batch.
Early stop criteria:
- You can name exact content to change.
- Top hits converge (~70%) on one area/path.
Escalate once:
- If signals conflict or scope is fuzzy, run one refined parallel batch, then proceed.
Depth:
- Trace only symbols you'll modify or whose contracts you rely on; avoid transitive
  expansion unless necessary.
Loop:
- Batch search → minimal plan → complete task.
- Search again only if validation fails or new unknowns appear. Prefer acting over more
  searching.
```
**Numeric thresholds here:** early-stop at **~70% convergence**; **escalate exactly once**.

**Maximally prescriptive version (hard tool budget):**
```
- Search depth: very low
- Bias strongly towards providing a correct answer as quickly as possible, even if it might
  not be fully correct.
- Usually, this means an absolute maximum of 2 tool calls.
- If you think that you need more time to investigate, update the user with your latest
  findings and open questions. You can proceed if the user confirms.
```
**Numeric threshold: "an absolute maximum of 2 tool calls."**

**Escape-hatch principle:** "When limiting core context gathering behavior, it's helpful to
explicitly provide the model with an escape hatch that makes it easier to satisfy a shorter
context gathering step. Usually this comes in the form of a clause that allows the model to
proceed under uncertainty, like 'even if it might not be fully correct'."

**Reverse direction (`<persistence>` block)** for more eagerness — keep going until resolved,
never hand back on uncertainty, don't ask the human to confirm assumptions.

**Per-tool uncertainty thresholds:** "in a coding setup, the delete file tool should have a
much lower threshold than a grep search tool." → *tool-risk-calibrated confirmation policy.*

**Turn decomposition:** "we observe peak performance when distinct, separable tasks are
broken up across multiple agent turns, with one turn for each task."

### 3.3 Cursor case study — the "prompt written for an older model actively hurts now"
finding (GPT-5 guide)

Cursor had this block, which worked on older models:
```
<maximize_context_understanding>
Be THOROUGH when gathering information. Make sure you have the FULL picture before replying.
Use additional tool calls or clarifying questions as needed.
</maximize_context_understanding>
```
Guide's verdict: "While this worked well with older models that needed encouragement to
analyze context thoroughly, they found it **counterproductive** with GPT-5, which is already
naturally introspective and proactive at gathering context. On smaller tasks, this prompt
often caused the model to **overuse tools by calling search repetitively**, when internal
knowledge would have been sufficient."

Fix: "they refined the prompt by removing the `maximize_` prefix and softening the language
around thoroughness."

→ *This is the canonical "stale instruction that was correct when written" case study.
Perfect exemplar for an audit skill: emphatic ALL-CAPS thoroughness language is a
detectable, dated pattern with a documented harm.*

Also from Cursor: "In Cursor's testing, using structured XML specs like `<[instruction]_spec>`
improved instruction adherence on their prompts and allows them to clearly reference previous
categories and sections elsewhere in their prompt."

And the verbosity split pattern: set the API `verbosity` parameter to **low** globally, then
override to **high** only inside coding tools via prompt language. "Use high verbosity for
writing code and code tools."

### 3.4 GPT-5.2 — verbosity clamps and scope discipline

URL: <https://cookbook.openai.com/examples/gpt-5/gpt-5-2_prompting_guide>

`<output_verbosity_spec>` with concrete numbers:
- "Default: 3–6 sentences or ≤5 bullets for typical answers."
- "For simple 'yes/no + short explanation' questions: ≤2 sentences."
- Complex multi-step/multi-file: 1 overview paragraph + ≤5 bullets tagged
  What changed / Where / Risks / Next steps / Open questions.

`<long_context_handling>` threshold: "For inputs longer than **~10k tokens** (multi-chapter
docs, long threads, multiple PDFs)" — outline key sections first, re-state constraints,
anchor claims to sections. Named failure mode: "**lost in the scroll**".

Scope drift block: "Implement EXACTLY and ONLY what the user requests. No extra features, no
added components, no UX embellishments." + "If any instruction is ambiguous, choose the
simplest valid interpretation."

Migration workflow (5 steps): switch model without touching prompts → pin reasoning_effort →
baseline evals → only then tune the prompt → re-run evals after each small change.

### 3.5 GPT-5.1 — final-answer compactness rules (numeric)

URL: <https://cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide>

`<final_answer_formatting>` for a coding agent:
- "Tiny/small single-file change (≤ ~10 lines): 2–5 sentences or ≤3 bullets. No headings.
  0–1 short snippet (≤3 lines) only if essential."
- "Medium change (single area or a few files): ≤6 bullets or 6–10 sentences. At most 1–2
  short snippets total (≤8 lines each)."
- "Large/multi-file change: Summarize per file with 1–2 bullets ... (still ≤2 short snippets
  total)."
- "Never include 'before/after' pairs, full method bodies, or large/scrolling code blocks."

`<user_updates_spec>` cadence numbers:
- "Send short updates (1–2 sentences) every few tool calls when there are meaningful changes."
- "**Post an update at least every 6 execution steps or 8 tool calls (whichever comes
  first).**"

`<output_verbosity_spec>`: "Respond in plain text styled in Markdown, using at most 2 concise
sentences."

### 3.6 Codex Prompting Guide — final-answer style rules (numeric)

URL: <https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide>

- "Headers: optional; short Title Case (**1-3 words**)"
- "Bullets: use `-`; merge related points; keep to one line when possible; **4–6 per list**
  ordered by importance"
- "Don'ts: **no nested bullets/hierarchies**; no ANSI codes; don't cram unrelated keywords"
- Plan tool: "Skip using the planning tool for straightforward tasks (roughly the **easiest
  25%**). Do not make single-step plans."
- Migration note with direct bearing on stale prompts: "You should also **remove all prompting
  for the model to communicate an upfront plan, preambles, or other status updates** during
  the rollout, as this can cause the model to stop abruptly before the rollout is complete."
  → *A once-recommended instruction (tool preambles, from the GPT-5 guide) is now explicitly
  harmful for Codex models. Textbook stale-guidance detection target.*

---

## 4. Tool / skill description quality and count

### 4.1 Function calling guide

URL: <https://developers.openai.com/api/docs/guides/function-calling>

"Best practices for defining functions" (verbatim highlights):
- "Write clear and detailed function names, parameter descriptions, and instructions."
- "Explicitly describe the purpose of the function and each parameter (and its format), and
  what the output represents."
- "Use the system prompt to describe **when (and when not)** to use each function."
- "Include examples and edge cases, especially to rectify any recurring failures. (**Note:
  Adding examples may hurt performance for reasoning models.**)"
- "For deferred tools, put detailed guidance in the function description and keep the
  namespace description concise."
- "**Pass the intern test.** Can an intern/human correctly use the function given nothing but
  what you gave the model? (If not, what questions do they ask you? Add the answers to the
  prompt.)"
- "Make the functions obvious and intuitive (principle of least surprise)."
- "Use enums and object structure to make invalid states unrepresentable."
- "Don't make the model fill arguments you already know."
- "Combine functions that are always called in sequence."

**NUMERIC THRESHOLD:** "Keep the number of initially available functions small for higher
accuracy. ... **Aim for fewer than 20 functions available at the start of a turn at any one
time**, though this is just a soft suggestion." Plus: "Use tool search to defer large or
infrequently used parts of your tool surface instead of exposing everything up front."

**Token accounting:** "functions are injected into the system message ... callable function
definitions **count against the model's context limit and are billed as input tokens**. If you
run into token limits, we suggest limiting the number of functions loaded up front,
**shortening descriptions where possible**, or using tool search."

### 4.2 GPT-5.2 tool guidance

URL: <https://cookbook.openai.com/examples/gpt-5/gpt-5-2_prompting_guide>
- "Describe tools crisply: **1–2 sentences** for what they do and when to use them."

### 4.3 GPT-5.6 Sol tool guidance

URL: <https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6>
- "**Expose only task-relevant tools.** Tool descriptions should state what the tool does,
  when to use it, important return fields, and error behavior."

### 4.4 GPT-5.1 tool guidance

URL: <https://cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide>
- "we recommend describing functionality **in the tool definition** and how/when to use tools
  **in the prompt**." → clean separation-of-concerns rule for auditing where a rule lives.

### 4.5 Skills — the explicit context budget (NUMERIC)

URL: <https://learn.chatgpt.com/docs/build-skills>

> "Skills use **progressive disclosure** to manage context efficiently. ChatGPT and Codex
> start with each skill's name and description, then load the full `SKILL.md` instructions
> when they decide to use that skill."

> "In Codex, the initial list also includes each skill's file path. **To avoid crowding out
> the rest of the prompt, this list uses at most 2% of the model's context window, or 8,000
> characters when the context window is unknown.** If many skills are installed, Codex
> shortens skill descriptions first. For large skill sets, Codex may omit some skills from the
> initial list and show a warning."

→ **Hard numbers: 2% of context window, or 8,000 characters fallback, for the entire
skill-metadata block.** And degradation is *silent-ish*: descriptions get truncated first,
then skills get dropped.
→ *Audit check: total bytes of all skill `name` + `description` + path. If it approaches 2%
of the window, some skills are invisible. Very concrete, very checkable.*

Description-writing rule: "Because implicit matching depends on `description`, **write
concise descriptions with clear scope and boundaries. Front-load the key use case and trigger
words so a host can still match the skill if descriptions are shortened.**"

Skill frontmatter template: `description: Explain exactly when this skill should and should
not trigger.` → *both when it SHOULD and should NOT.*

Duplicate-name behaviour: "If two skills share the same `name`, Codex doesn't merge them;
**both can appear in skill selectors**." → *duplicate skill names are a real, detectable
defect.*

Skill discovery locations (repo → user → admin → system):
`$CWD/.agents/skills`, `$CWD/../.agents/skills`, `$REPO_ROOT/.agents/skills`,
`$HOME/.agents/skills`, `/etc/codex/skills`, plus OpenAI-bundled.

---

## 5. Prompt caching — stable vs churning preamble

URL: <https://developers.openai.com/api/docs/guides/prompt-caching>

Mechanics relevant to a repo-level audit:
- "Prompt caching reuses work when requests share the same **prompt prefix**." Benefits:
  compute reuse, "**discounted up to 90%**" on cached input tokens, lower latency.
- "OpenAI caches the model's full rendered context including OpenAI-provided instructions,
  developer messages, **tool definitions**, and conversation history."
- "**Cache reuse requires the entire rendered prefix to match.** If content or a relevant
  setting changes before a breakpoint, the prefix after that change cannot match the existing
  cache entry."
- **Minimum cacheable prompt length: 1,024 tokens** (GPT-5.6+) / **2,048 tokens** (older).
- Cache write costs **1.25×** uncached rate; reads **0.1×**. One write + one full reuse =
  1.35× vs 2×. Ten requests: 2.15× vs 10×.
- TTL **30m** (GPT-5.6+, only supported value). Earlier models: in-memory ~5–10 min idle, up
  to an hour.
- Up to **4 cache writes per request**; reads consider "up to the latest **50** breakpoints".
- Cache location: "traffic above **15 requests per minute** can lead to overflow routing."

**The optimization rule that maps straight onto an AGENTS.md/CLAUDE.md audit:**
> "**Keep the prefix stable.** Put stable developer instructions and shared reference material
> first. If developer instructions or shared material contain **timestamps, user-specific
> content, or other dynamic content, place those at the end** rather than the beginning, or
> move them into later conversation messages."

> "Preserve conversation history. Append new messages rather than rewriting earlier turns.
> **Summarization, compaction, or context truncation can change the prefix and reset cache
> reuse.**"

Tool stability:
> "**Keep tools consistent.** Preserve tool definitions, ordering, and schemas."
> "Disable tool use for a request. Set `tool_choice` to `none` instead of removing the tool
> definitions."
Settings that bust the cache: `model`, `tools` (names, descriptions, schemas, **ordering**),
`parallel_tool_calls`, `text.format`, `reasoning.effort`, `text.verbosity`,
`context_management`.

From the prompt engineering guide (same idea, older phrasing):
> "you should try and keep content that you expect to use over and over in your API requests
> at the beginning of your prompt"
URL: <https://developers.openai.com/api/docs/guides/prompt-engineering>

From GPT-5.6 Sol guidance:
> "Prompt caching also affects prompt construction. **Keep reusable prefixes stable and avoid
> unnecessary churn in large system prompts.** Use explicit cache breakpoints only when they
> improve measured cache behavior and cost for the workload."

→ **Audit checks that fall out of this:**
1. Any AGENTS.md/CLAUDE.md content that changes per-session (dates, "as of <version>",
   current sprint, ticket numbers, "TODO: revisit") sits in the cached prefix and busts it.
   Move to the end or out entirely.
2. Because Codex injects AGENTS.md *near the top, before the user prompt*, churn there is
   maximally expensive — it invalidates everything downstream.
3. Very small context files may never even reach the 1,024-token cache floor on their own,
   but they're part of a larger prefix, so the churn argument still holds.
4. Reordering tool/MCP definitions is itself a cache-buster, independent of content.

Related: persisted reasoning, from GPT-5.6 Sol guidance —
> "Do not treat persisted reasoning as an always-on optimization: **stale reasoning can add
> tokens, increase latency, and anchor the model to an outdated approach.**"
→ nice rhetorical parallel: stale *context* does the same thing.

---

## 6. Metaprompting and self-auditing

### 6.1 GPT-5 guide — metaprompting

URL: <https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide>

> "early testers have found great success using GPT-5 as a **meta-prompter for itself**.
> Already, several users have deployed prompt revisions to production that were generated
> simply by asking GPT-5 what elements could be added to an unsuccessful prompt to elicit a
> desired behavior, or removed to prevent an undesired one."

Their template (verbatim):
```
When asked to optimize prompts, give answers from your own perspective - explain what
specific phrases could be added to, or deleted from, this prompt to more consistently elicit
the desired behavior or prevent the undesired behavior.

Here's a prompt: [PROMPT]

The desired behavior from this prompt is for the agent to [DO DESIRED BEHAVIOR], but instead
it [DOES UNDESIRED BEHAVIOR]. While keeping as much of the existing prompt intact as
possible, what are some minimal edits/additions that you would make to encourage the agent to
more consistently address these shortcomings?
```
Note the constraint: "**keeping as much of the existing prompt intact as possible**" and
"**minimal edits/additions**".

### 6.2 GPT-5.1 guide — the two-step audit protocol (most directly reusable artifact)

URL: <https://cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide>
(section "How to metaprompt effectively")

Framing: "Building prompts can be cumbersome, but it's also the highest-leverage thing you
can do to resolve most model behavior issues. **Small inclusions can unexpectedly steer the
model undesirably.**"

They present a deliberately-flawed "GreenGather" event-planning system prompt with **planted
contradictions across sections** — the exact anti-pattern of an accreted CLAUDE.md:
- TONE: "Sound calm, professional, and neutral ... Avoid emojis" **vs** "you may occasionally
  write in first person ('I'd recommend…') and use tasteful emojis"
- TONE: "Do not use first-person singular" **vs** "you may occasionally write in first person"
- STRUCTURE: "Prefer short paragraphs, not bullet lists. Use bullets only when the user
  explicitly asks" **vs** "always structure your answer with labeled sections ... and use
  bullet points liberally"
- AUTONOMY: "Do not ask the user for clarifications unless absolutely necessary" **vs** "when
  key information ... is missing, pause and ask 1–3 brief clarifying questions"
- TOOLS: "avoid tools and rely on internal knowledge so responses are fast" / "avoid
  unnecessary tool calls" **vs** "For any event with more than 30 attendees, always call at
  least one search tool"
- VERBOSITY: "Err on the side of completeness" **vs** "long walls of text are discouraged.
  Aim for compact responses"
- PRIMARY OBJECTIVE: "Most responses should be about 3–6 sentences" **vs** "provide a
  detailed, step-by-step plan ... even if it requires a longer answer"
- CLOSING: "Return control to the user frequently by summarizing the current plan and
  **inviting them to adjust**" **vs** "End every response with a subtle next step ...
  **phrased as a suggestion rather than a question**, and avoid explicit calls for
  confirmation"

Observed failure modes: unnecessary tool calls on small conceptual questions; oscillation
between over-verbose and over-hesitant; ignoring unit rules (miles/°F for a Berlin event).

**Step 1 — diagnose (do NOT ask for a fix yet).** Their prompt asks for:
1. "Identify the distinct failure mode you see (e.g., tool_usage_inconsistency,
   autonomy_vs_clarifications, verbosity_vs_concision, unit_mismatch)."
2. "For each failure mode, **quote or paraphrase the specific lines or sections** of the
   system prompt that are most likely causing or reinforcing it. **Include any contradictions**
   (e.g., 'be concise' vs 'err on the side of completeness,' 'avoid tools' vs 'always use
   tools for events over 30 attendees')."
3. "Briefly explain, for each failure mode, how those lines are steering the agent toward the
   observed behavior."
Output schema they specify:
```
failure_modes:
- name: ...
  description: ...
  prompt_drivers:
    - exact_or_paraphrased_line: ...
    - why_it_matters: ...
```
Scoping caution: "Metaprompting works best when the feedback can logically be grouped
together. **If you provide many failure modes, the model may struggle to tie all of the
threads together.**" → one query per failure family.

**Step 2 — patch (separate call).** Constraints (verbatim):
- "Do not redesign the agent from scratch."
- "Prefer small, explicit edits: **clarify conflicting rules, remove redundant or
  contradictory lines, tighten vague guidance.**"
- "Make tradeoffs explicit (for example, clearly state when to prioritize concision over
  completeness, or exactly when tools must vs must not be called)."
- "**Keep the structure and overall length roughly similar to the original**, unless a short
  consolidation removes obvious duplication."
Output: `patch_notes` (change + reasoning) then `revised_system_prompt`.

Their example patch_notes read almost exactly like a context-health report:
- "Merged conflicting tool-usage rules into a single hierarchy"
- "Removed overlapping tone instructions that encouraged both executive formality and casual
  first-person with emojis"
- "Removed language that told the agent to 'err on the side of completeness' for all cases and
  replaced it with **conditional rules based on query complexity**"

Loop: "After this iteration cycle, run the queries again to observe any regressions and repeat
this process until your failure modes have been identified and triaged."

Growth advice: "As you continue to grow your agentic systems ... consider **metaprompting the
additions you'd like to make rather than adding them by hand**. This helps maintain discrete
boundaries for each tool and when they should be used."

→ **The two-phase separation (diagnose-only, then patch-only) is a strong design cue for the
skill: report findings, don't edit.**

### 6.3 Prompt optimizer (product)

URL: <https://developers.openai.com/api/docs/guides/prompt-optimizer>
- "a chat interface in the dashboard, where you enter a prompt, and we optimize it according
  to current best practices before returning it to you."
- Dataset-backed: needs ≥3 rows with responses, ≥1 grader result or human annotation each.
- "Always evaluate and manually review optimized prompts before using them in production."
- **Deprecation:** the dataset-backed optimizer is being retired with the Evals platform —
  Evals read-only **2026-10-31**, shutdown **2026-11-30**. The GPT-5 guide's "we recommend
  testing your prompts in our prompt optimizer tool" is therefore going stale itself.

Also: <https://developers.openai.com/api/docs/guides/prompting>
- "**Treat prompts as application code.** Store prompt content in named modules ... and review
  prompt changes in the same pull requests as the product behavior they support."
- "Run your prompt tests and evaluation cases every time you publish; catching issues early is
  cheaper than fixing them in production."
- "Put overall tone or role guidance in the system message; keep task-specific details and
  examples in user messages."
- Reusable prompt objects are also deprecated (de-emphasized 2026-06-03, shutdown
  2026-11-30); the advice is now to version prompts in git.

---

## 7. Where OpenAI DIFFERS from Anthropic

These are the axes worth flagging in the skill so it doesn't blindly apply one house style.

### 7.1 How much to specify — OpenAI says LESS for reasoning models

OpenAI, prompt engineering guide
(<https://developers.openai.com/api/docs/guides/prompt-engineering>):
> "reasoning models will provide better results on tasks with **only high-level guidance**.
> This differs from GPT models, which benefit from very precise instructions."
> "A reasoning model is like a **senior co-worker**. You can give them a goal to achieve and
> trust them to work out the details. A GPT model is like a **junior coworker**."

Reasoning best practices (<https://developers.openai.com/api/docs/guides/reasoning-best-practices>):
- "**Keep prompts simple and direct**: The models excel at understanding and responding to
  brief, clear instructions."
- "**Avoid chain-of-thought prompts**: Since these models perform reasoning internally,
  prompting them to 'think step by step' or 'explain your reasoning' is unnecessary."
- "**Try zero shot first, then few shot if needed**: Reasoning models often don't need
  few-shot examples ... try to write prompts without examples first."
- Function-calling guide caveat: "Adding examples **may hurt performance for reasoning
  models**."

**Contrast with Anthropic:** Anthropic's Claude Code / CLAUDE.md guidance leans toward
explicit, concrete, example-rich instruction — "be specific", give the model examples,
show don't tell, and Claude's prompt-engineering docs actively recommend multishot
prompting and letting Claude think. OpenAI's reasoning-model line is the reverse:
zero-shot first, examples may hurt, high-level goals beat step lists.
**Skill implication:** don't flag terseness in a CLAUDE.md as under-specification just
because a "senior co-worker" framing applies; and conversely, a repo tuned for Codex may
legitimately carry far less detail than a Claude-tuned one. Where the two agree — and this is
the safe common ground — is on *contradictions*, *redundancy*, and *staleness*.

### 7.2 Markdown vs XML — OpenAI is genuinely bimodal, Anthropic favours XML tags

- OpenAI prompt engineering guide recommends **both together**: "you can help the model
  understand logical boundaries of your prompt and context data using a **combination of
  Markdown formatting and XML tags**. Markdown headers and lists ... to mark distinct sections
  ... XML tags can help delineate where one piece of content ... begins and ends."
  Their canonical developer-message shape is Markdown `# Identity / # Instructions /
  # Examples / # Context` with XML tags used for *data* payloads and examples.
- But every GPT-5/5.1/5.2/Codex cookbook prompt uses **XML-ish spec blocks for
  instructions**: `<context_gathering>`, `<persistence>`, `<tool_preambles>`,
  `<code_editing_rules>`, `<solution_persistence>`, `<user_updates_spec>`,
  `<final_answer_formatting>`, `<output_verbosity_spec>`, `<design_and_scope_constraints>`,
  `<long_context_handling>`, `<uncertainty_and_ambiguity>`, `<web_search_rules>`.
  Cursor's finding, endorsed in the GPT-5 guide: "using structured XML specs like
  `<[instruction]_spec>` **improved instruction adherence**".
- **Yet AGENTS.md itself is prescribed as plain Markdown**: "AGENTS.md is just standard
  Markdown. Use any headings you like."
- Reasoning best practices splits the difference: "Use delimiters like **markdown, XML tags,
  and section titles**".
- Codex's *injection* wrapper is XML: each AGENTS.md arrives inside
  `<INSTRUCTIONS>...</INSTRUCTIONS>`.

**Contrast with Anthropic:** Anthropic's prompt-engineering docs are much more emphatic that
XML tags are *the* structuring device for Claude, and Claude Code's CLAUDE.md convention is
plain Markdown headings. So both vendors end up at "Markdown for the repo file, tags for
system-prompt spec blocks" — but OpenAI is the one with published evidence (Cursor) that
XML spec blocks improve adherence, and OpenAI is the one that says Markdown+XML combined.
**Skill implication:** do NOT flag "your CLAUDE.md/AGENTS.md uses plain Markdown headings" as
a defect. Both vendors bless Markdown for the repo-level file. Structure findings should be
about *sectioning and scope*, not tag syntax.

### 7.3 File length — OpenAI gives a hard byte cap; Anthropic gives none

- OpenAI/Codex: **32 KiB** (`project_doc_max_bytes`), with truncation as the failure mode and
  "split instructions across nested directories" as the prescribed fix. Plus "Keep it small"
  and the OpenAI monorepo's **88 AGENTS.md files** as the exemplar.
- Anthropic has no equivalent published byte limit for CLAUDE.md; the guidance is qualitative
  (keep it concise, it's prepended to every prompt).
**Skill implication:** the skill can use 32 KiB as a *hard, citable* ceiling for the merged
instruction chain even in Claude repos, because it's the only published number of its kind —
but should present it as an OpenAI/Codex mechanical limit, not a universal law. A softer,
better-supported target is the Sol finding (§3.1): leaner prompts cut tokens 41–66% while
*improving* scores 10–15%.

### 7.4 Positive statements vs prohibitions — OpenAI is comfortable with prohibitions,
but rations absolutes

- OpenAI's own reference prompts are *full* of prohibitions:
  "**NEVER** use destructive commands like `git reset --hard`"; "Do not use nested bullets";
  "Never include 'before/after' pairs"; "Do NOT invent colors, shadows, tokens, animations";
  "Do not commit to optional checks"; "never combine with `**`".
- The prompt engineering guide's own Instructions-section definition asks for both directions:
  "What should the model do, and **what should the model never do**?"
- But the Sol guidance rations them: "**Avoid unnecessary absolute rules.** Use ALWAYS, NEVER,
  must, and only for **true invariants** such as safety rules, required fields, or actions
  that should never happen. For judgment calls ... **prefer decision rules**."
- And the Cursor case study shows *emphasis* itself (ALL-CAPS "Be THOROUGH", "FULL picture",
  the `maximize_` prefix) as an active harm on modern models.

**Contrast with Anthropic:** Anthropic's guidance leans harder toward telling Claude what TO
do rather than what not to do ("tell Claude what to do instead of what not to do"), on the
theory that negations are weaker attractors.
**Skill implication:** a well-calibrated finding is not "you used NEVER" — it's:
(a) count of absolutes that aren't true invariants, and (b) presence of emphasis inflation
(ALL-CAPS, "CRITICAL", "IMPORTANT", "ALWAYS", "**MUST**") that has escalated over time.
Both vendors support (a). Only OpenAI has published a case study for (b).

### 7.5 Where they AGREE (safe ground for the skill)

- Contradictions are expensive and should be hunted first.
- Redundant/repeated rules are net-negative, not merely neutral.
- Put guidance in the closest place it applies; nest rather than centralize.
- Progressive disclosure (skills / metadata-first loading) beats always-on prose.
- Deterministic checks (lint, format, types) belong in CI/hooks, not in the prompt.
- Instruction files are living documents that need periodic review.
- Tool/skill descriptions are prompt surface and count against the budget.

---

## 8. Consolidated numeric thresholds and rules of thumb

| Number | What it governs | Source |
|---|---|---|
| **32 KiB (32,768 bytes)** | `project_doc_max_bytes` — combined AGENTS.md instruction chain before Codex stops adding files / truncates | <https://learn.chatgpt.com/docs/agent-configuration/agents-md> |
| **88** | AGENTS.md files in OpenAI's main repo — the nesting exemplar | <https://agents.md/> |
| **60k+** | open-source projects using AGENTS.md | <https://agents.md/> |
| **2% of context window, or 8,000 characters** | max share of prompt used by the initial skill-metadata list in Codex; descriptions truncated first, then skills omitted | <https://learn.chatgpt.com/docs/build-skills> |
| **<20 functions** | soft cap on tools available at the start of a turn, for accuracy | <https://developers.openai.com/api/docs/guides/function-calling> |
| **1–2 sentences** | target length of a tool description | <https://cookbook.openai.com/examples/gpt-5/gpt-5-2_prompting_guide> |
| **10–15% score gain / 41–66% fewer tokens / 33–67% lower cost** | measured effect of leaner system prompts in internal coding-agent evals | <https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6> |
| **~70% convergence** | early-stop criterion for context gathering | <https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide> |
| **max 2 tool calls** | the "maximally prescriptive" context-gathering budget | same |
| **escalate once** | if signals conflict or scope is fuzzy, one refined batch then proceed | same |
| **~10k tokens** | input length above which to force outline + re-grounding ("lost in the scroll") | <https://cookbook.openai.com/examples/gpt-5/gpt-5-2_prompting_guide> |
| **1,024 / 2,048 tokens** | minimum cacheable prompt prefix (GPT-5.6+ / older) | <https://developers.openai.com/api/docs/guides/prompt-caching> |
| **90% / 0.1× read / 1.25× write / 30m TTL** | prompt-cache discount, read & write multipliers, lifetime | same |
| **4 writes per request / 50 breakpoints considered / 15 rpm** | explicit cache-breakpoint limits and overflow threshold | same |
| **every 6 execution steps or 8 tool calls** | max interval between user updates | <https://cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide> |
| **3–6 sentences or ≤5 bullets** | default answer verbosity clamp | <https://cookbook.openai.com/examples/gpt-5/gpt-5-2_prompting_guide> |
| **≤10 lines → 2–5 sentences / ≤3 bullets** | final-answer budget for a tiny change | <https://cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide> |
| **4–6 bullets per list, headers 1–3 words, no nested bullets** | Codex final-answer style | <https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide> |
| **easiest 25% of tasks** | skip the planning tool | same |
| **every 3–5 user messages** | re-append a Markdown formatting instruction if adherence decays over a long conversation | <https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide> |
| **1–3 clarifying questions** | cap when handling ambiguity | <https://cookbook.openai.com/examples/gpt-5/gpt-5-2_prompting_guide> |
| **2 or 3 rules to start** | how many custom code-review rules to begin with | <https://learn.chatgpt.com/docs/third-party/github> |

---

## 9. Directly actionable audit checks derived from OpenAI sources

Each with its citation, so the skill can justify a finding.

**Contradiction / conflict**
1. Cross-file contradiction between a root `AGENTS.md`/`CLAUDE.md` and a nested one. Codex
   merges positionally; nothing resolves it. [agents-md discovery; GPT-5 guide §Instruction
   following]
2. Intra-file contradiction between sections written at different times (tone vs tone,
   verbosity vs completeness, autonomy vs clarify, tools vs no-tools). Use the GreenGather
   taxonomy: `tool_usage_inconsistency`, `autonomy_vs_clarifications`,
   `verbosity_vs_concision`, `unit_mismatch`. [GPT-5.1 metaprompting]
3. Contradiction between the context file and a skill / subagent prompt. [GPT-6 Astra:
   "unclear or conflicting guidance in a skill file may cause the model to pause and block
   work early"]
4. An unconditional rule with an unstated exception — the fix pattern is to add the explicit
   carve-out, not delete either rule. [GPT-5 guide CareFlow fix]
5. Missing precedence statement when many instruction files load. [GPT-6 Astra: "Make the
   priority of user instructions and skills explicit."]

**Redundancy / over-specification**
6. Same rule stated in two or more files (CLAUDE.md + AGENTS.md + README + a skill).
   [Sol: "repeated statements of the same rule"]
7. Repeated caution/approval language ("ask first", "do not mutate", "confirm before")
   across files — documented to cause over-pausing. [Sol]
8. Examples that don't change behavior; few-shot blocks in a reasoning-model context.
   [Sol; function-calling guide; reasoning best practices]
9. Process instructions for behavior the model already does natively (e.g. "read the file
   before editing it", "think step by step"). [Sol; reasoning best practices]
10. Emphasis inflation: ALL-CAPS, `maximize_`-style intensifiers, stacked
    CRITICAL/IMPORTANT/ALWAYS/NEVER. Documented to cause tool over-use. [GPT-5 guide, Cursor
    case study]
11. Absolutes (ALWAYS/NEVER/must/only) that are not true invariants. [Sol]

**Misplaced content**
12. Lint / formatting / type rules that a deterministic tool already enforces.
    ["reserve formatting and lint checks for CI" — agents-md + GitHub review docs;
    "Pair AGENTS.md with ... pre-commit hooks, linters, and type checkers" — customization]
13. Personal/style preferences checked into a team repo file (belongs in the global file).
    [customization overview: global file for communication style, repo file for team rules]
14. Long procedural workflows sitting in the always-on context file that should be a skill
    (progressive disclosure). [customization overview]
15. Repo-wide file carrying service-specific rules that should live in the nested directory.
    ["put guidance in the closest directory where it applies"; "so unrelated changes don't
    have to carry service-specific context" — GitHub review doc]
16. A file named something Codex won't discover (`CONVENTIONS.md`, `CONTRIBUTING-AI.md`) and
    not listed in `project_doc_fallback_filenames`. ["Filenames not on this list are ignored"]
17. An `AGENTS.md` shadowed by an `AGENTS.override.md` in the same directory — dead context.

**Size / budget**
18. Merged instruction chain approaching or exceeding **32 KiB** → silent truncation.
19. Total skill `name`+`description`+path bytes approaching **2% of context / 8,000 chars**
    → skills silently truncated or omitted.
20. More than ~20 tools/MCP functions exposed at turn start.
21. Tool descriptions longer than 1–2 sentences, or describing tools irrelevant to the repo.

**Caching / churn**
22. Dynamic content (dates, versions, sprint names, ticket IDs, "as of…") near the top of a
    context file → busts the cached prefix for everything after it. Move to the end or drop.
23. Reordering of tool/MCP definitions between runs (cache-busting independent of content).

**Staleness**
24. Instructions written for an older model that the current model already handles, or that
    are now counterproductive (e.g. "always output an upfront plan / preamble", which Codex
    docs now say to remove). [codex_prompting_guide migration notes]
25. Commands listed in AGENTS.md that no longer exist — and note these are *executed*, not
    just read. ["Yes—if you list them" — agents.md FAQ]
26. Guidance that no longer matches the tree (paths, module names, directory structure).

**Process / posture**
27. Recommend a recurring drift check, per OpenAI's own advice: "Use scheduled tasks to run
    recurring checks (for example, daily) that look for guidance gaps."
28. Report-then-patch separation, per the GPT-5.1 two-call metaprompt protocol: diagnose
    (quote the exact offending lines, name the failure mode, explain the causal link) as one
    step; patch surgically as a separate step. "Do not redesign the agent from scratch."
29. Runtime probe as a complement to static analysis: ask the agent to name and quote the
    instruction that caused it to pause/diverge. [GPT-6 Astra]
30. Verification recipe for which files actually loaded:
    `codex --ask-for-approval never "Summarize the current instructions."` and the
    `log_dir` / `session-*.jsonl` inspection route.

---

## 10. Source URL index

Spec / Codex docs
- <https://agents.md/>
- <https://learn.chatgpt.com/docs/agent-configuration/agents-md> (= `/codex/guides/agents-md`)
- <https://learn.chatgpt.com/docs/customization/overview>
- <https://learn.chatgpt.com/docs/build-skills>
- <https://learn.chatgpt.com/docs/prompting> (= `/codex/prompting`)
- <https://learn.chatgpt.com/docs/third-party/github>
- <https://learn.chatgpt.com/docs/config-file/config-advanced#project-instructions-discovery>
- <https://learn.chatgpt.com/docs/config-file/config-reference>
- <https://learn.chatgpt.com/guides/build-ai-native-engineering-team>
- <https://learn.chatgpt.com/llms.txt> (full doc index; every page has a `.md` twin)

Cookbook
- <https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide>
- <https://cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide>
- <https://cookbook.openai.com/examples/gpt-5/gpt-5-2_prompting_guide>
- <https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide>
- <https://cookbook.openai.com/articles/codex_exec_plans> (PLANS.md / ExecPlans)

Platform / API guides
- <https://developers.openai.com/api/docs/guides/prompt-engineering>
- <https://developers.openai.com/api/docs/guides/prompting>
- <https://developers.openai.com/api/docs/guides/prompt-optimizer>
- <https://developers.openai.com/api/docs/guides/prompt-caching>
- <https://developers.openai.com/api/docs/guides/function-calling>
- <https://developers.openai.com/api/docs/guides/reasoning-best-practices>
- <https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6> (Sol)
- <https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra>

Blog
- <https://openai.com/index/introducing-codex/> (403s to fetchers)
- <https://openai.com/index/introducing-upgrades-to-codex/> (403s)
- <https://developers.openai.com/blog/run-long-horizon-tasks-with-codex>

## 11. Bonus: PLANS.md / ExecPlans (adjacent, may matter for the skill)

URL: <https://cookbook.openai.com/articles/codex_exec_plans>

Pattern: a *short* AGENTS.md section that points at a *long* document, rather than inlining
the long document. The AGENTS.md snippet is four lines:
```
# ExecPlans
When writing complex features or significant refactors, use an ExecPlan (as described in
.agent/PLANS.md) from design to implementation.
```
Everything else lives in `.agent/PLANS.md`, loaded only when relevant.
→ *Exactly the routing-not-inlining pattern the audit should recommend. Also note the term
"ExecPlan" is called out as arbitrary and untrained — the doc explicitly says jargon must be
defined: "Every ExecPlan must define every term of art in plain language or do not use it."*

Notable inversions worth flagging (this doc deliberately breaks the terseness rules above):
- "Every ExecPlan must be fully self-contained ... Repeat any assumption you rely on."
- "Do not point to external blogs or docs; if knowledge is required, embed it in the plan
  itself in your own words."
- "Write in plain prose. Prefer sentences over lists. Avoid checklists, tables, and long
  enumerations."
→ i.e. **a document loaded on demand can afford to repeat itself; an always-on prefix cannot.**
That distinction is a good organizing principle for the skill's recommendations.

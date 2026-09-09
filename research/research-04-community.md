# Research 04 — Established Community Practice on Agent Context Quality & Bloat

Current as of 2026-09-08. Prioritizes 2025–2026 material. Older / superseded items are flagged inline.

---

## 0. TL;DR — what the community actually converged on

1. Agent instruction files are a **per-turn tax**, not free documentation. Every line in an always-loaded file costs tokens on every request.
2. **Longer is not better.** Past a point, more context measurably *reduces* instruction adherence and task accuracy.
3. The canonical failure taxonomy is Breunig's four: **poisoning, distraction, confusion, clash**.
4. Concrete size ceilings have converged: **~200 lines for CLAUDE.md**, **~500 lines for a skill or rule file**, **~2 pages for Copilot instructions**, **~2,000 tokens combined for "always apply" rules**.
5. The two tests that matter: **specificity** ("2-space indent", not "format properly") and **deletability** ("would removing this cause a mistake?").
6. **Link, don't inline.** Anything derivable from the codebase should be derived, not restated — restating it is what goes stale.
7. Advisory text is the weakest enforcement layer. Anything that MUST happen belongs in a **hook / lint / test**, not a bullet point.
8. Duplication across CLAUDE.md / AGENTS.md / README / .cursor/rules is the most common structural bug; the fix is **one source + import or symlink**.

---

## 1. The named failure taxonomy (verbatim)

**Primary source:** Drew Breunig, "How Long Contexts Fail", 2025-06-22
<https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html>

Verbatim definitions:

- **Context Poisoning** — "When a hallucination or other error makes it into the context, where it is repeatedly referenced."
- **Context Distraction** — "When a context grows so long that the model over-focuses on the context, neglecting what it learned during training."
- **Context Confusion** — "When superfluous content in the context is used by the model to generate a low-quality response."
- **Context Clash** — "When you accrue new information and tools in your context that conflicts with other information in the context."

Numbers cited in that piece:

- Gemini 2.5 Pro began repeating past actions once context "grew significantly beyond 100k tokens" (distraction onset).
- Databricks: "model correctness began to fall around 32k for Llama 3.1 405b" — distraction ceilings sit far below advertised window sizes.
- GeoEngine benchmark: quantized Llama 3.1 8b **failed with all 46 tools**, **succeeded when limited to 19 tools** (confusion via tool bloat).
- Sharded (multi-turn) vs single-shot prompts: **average 39% drop**; o3 fell **from 98.1 to 64.1** (clash from incrementally accrued, partly stale info).

**Companion piece (fixes):** Breunig, "How to Fix Your Context" — RAG, tool loadout, context quarantine, context pruning, context summarization, context offloading. Simon Willison's write-up: <https://simonwillison.net/2025/Jun/29/how-to-fix-your-context/>

**Independently restated by LangChain** (evidence the taxonomy is now the community standard):
<https://www.langchain.com/blog/context-engineering-for-agents>

- Poisoning: "When a hallucination makes it into the context"
- Distraction: "When the context overwhelms the training"
- Confusion: "When superfluous context influences the response"
- Clash: "When parts of the context disagree"

LangChain's orthogonal taxonomy of *remedies* — **Write / Select / Compress / Isolate**:

- **Write** — save information outside the context window (scratchpads, memories).
- **Select** — pull in only what is needed, when needed.
- **Compress** — "Retaining only the tokens required to perform a task."
- **Isolate** — split context across sub-agents, sandboxes, structured state objects.

Also from that post: multi-agent systems can use "up to 15× more tokens than chat" (Anthropic); Cognition's line that context engineering is "effectively the #1 job of engineers building AI agents."

> **Audit mapping (directly usable in a skill):**
> poisoning → stale or wrong facts asserted as truth in CLAUDE.md/README;
> distraction → total always-on token count;
> confusion → no-op rules, never-invoked skills, dead MCP tools;
> clash → contradictory rules across files.

---

## 2. Empirical evidence on long-context degradation

### 2.1 Chroma — "Context Rot: How Increasing Input Tokens Impacts LLM Performance" (2025)

<https://research.trychroma.com/context-rot> · <https://www.trychroma.com/research/context-rot>
18 models including GPT-4.1, Claude 4, Gemini 2.5, Qwen3.

- Core claim: models do **not** process context uniformly; reliability falls with input length **even on trivial tasks** (retrieval, text replication).
- "Lower similarity needle-question pairs increases the rate of performance degradation."
- **Distractors:** even a *single* distractor degrades vs needle-only; four compounds it. "Distractors do not have uniform impact." Claude family = lowest hallucination rate, more abstention; GPT family = confident but incorrect.
- **Haystack structure:** "Shuffling the haystack and removing local coherence consistently improves performance" across all 18 models — counterintuitively, coherent long documents hurt *more* than shuffled ones.
- **Repeated-words replication:** accuracy degrades from 25 → 10,000 words; under-generation at length; ~2.55% refusal (GPT-4.1) and 2.89% (Claude Opus 4) starting around 2,500 words.
- **LongMemEval:** focused prompt (~300 tokens) vs full prompt (~113k tokens) shows a large gap; Claude Opus 4 showed the most pronounced gap; thinking modes narrow but do not remove it.

**Audit implication:** the "~300 tokens vs ~113k tokens" gap is the single best citation for "trim your always-on context."
Hamel Husain's condensed note on the same paper: <https://hamel.dev/notes/llm/rag/p6-context_rot.html>

### 2.2 "Lost in the Middle" — Liu et al., 2023 — **OLDER; foundational but partly superseded**

<https://arxiv.org/abs/2307.03172> · code/data: <https://github.com/nelson-liu/lost-in-the-middle>

- U-shaped curve: performance highest when relevant information sits at the **beginning or end** of the input, degrading in the middle — even for explicitly long-context models.
- **Flag:** 2023, pre-dates modern long-context models. Chroma (2025) is the current citation and shows degradation is broader than positional. Use Liu for the positional intuition (put critical rules at the top or bottom of an instruction file), Chroma for magnitude.

### 2.3 Anthropic on its own system prompt (2026)

- "We removed over 80% of Claude Code's system prompt for models like Claude Opus 5" with "no measurable loss on our coding evaluations."
  Reported: <https://www.implicator.ai/anthropic-claude-code-skill-doctor-context-audit/>
- Strongest available evidence that large instruction blocks are usually removable without loss.

---

## 3. Primary vendor guidance (2026) — the concrete thresholds

### 3.1 Anthropic — CLAUDE.md

<https://code.claude.com/docs/en/memory>

Hard numbers and verbatim rules:

- **"Size: target under 200 lines per CLAUDE.md file."**
- "Longer files consume more context and reduce adherence."
- Claude Code "loads a CLAUDE.md file of up to 4 MiB in full and skips a larger file. Shorter files produce better adherence."
- Auto-memory `MEMORY.md`: only the **first 200 lines or 25KB** load per session; anything past that is dropped on next load.
- `@path` imports: "maximum depth of four hops"; imported files "still load and enter the context window at launch" — **splitting into imports does NOT reduce context**, only organizes it.
- Precedence / load order: managed policy → user (`~/.claude/CLAUDE.md`) → project (`./CLAUDE.md` or `./.claude/CLAUDE.md`) → local (`CLAUDE.local.md`). Ancestor directories load at launch; **subdirectory CLAUDE.md files load on demand** when Claude reads files there. All discovered files are **concatenated, not overridden**.
- Specificity examples (verbatim):
  - "Use 2-space indentation" instead of "Format code properly"
  - "Run `npm test` before committing" instead of "Test your changes"
  - "API handlers live in `src/api/handlers/`" instead of "Keep files organized"
- **Consistency:** "if two rules contradict each other, Claude may pick one arbitrarily." Explicit instruction to "Review your CLAUDE.md files, nested CLAUDE.md files in subdirectories, and `.claude/rules/` periodically to remove outdated or conflicting instructions."
- CLAUDE.md is **context, not enforced configuration**: "To block an action regardless of what Claude decides, use a PreToolUse hook instead."
- Delivery detail: "CLAUDE.md content is delivered as a user message after the system prompt, not as part of the system prompt itself."
- HTML block comments `<!-- ... -->` in CLAUDE.md are **stripped before injection** — free maintainer notes. Comments inside code blocks are preserved.
- **`/doctor` trim check (v2.1.206+, 2026-07-09):** "it cuts content Claude can derive from the codebase, such as **directory layouts, dependency lists, and architecture overviews**, and keeps **pitfalls, rationale, and conventions that differ from tool defaults**." — effectively Anthropic's official anti-pattern list.
- **AGENTS.md interop:** "Claude Code reads `CLAUDE.md`, not `AGENTS.md`." Recommended fix is a one-line `@AGENTS.md` import or a symlink, explicitly "so both tools read the same instructions without duplicating them." On Windows a symlink needs Admin/Developer Mode, so the import is preferred.
- `claudeMdExcludes` (glob list, any settings layer) exists for monorepos where other teams' CLAUDE.md files get picked up.
- `/init` reads Cursor rules (`.cursor/rules/`, `.cursorrules`) and Copilot rules (`.github/copilot-instructions.md`); with `CLAUDE_CODE_NEW_INIT=1` it also reads `AGENTS.md`, `.devin/rules/`, `.windsurf/rules/` or `.windsurfrules`, and `.clinerules`. **That list is a ready-made glob set for a context audit.**
- `InstructionsLoaded` hook can log exactly which instruction files loaded, when, and why — a real mechanism for auditing what is actually in context.
- Auto memory (Claude-written): `~/.claude/projects/<project>/memory/`, types `user | feedback | project | reference`; Claude "skips anything it can derive from the codebase" and "anything your CLAUDE.md files already say." Files get a `modified` ISO-8601 frontmatter timestamp (v2.1.214+) — **dated entries as a first-class freshness mechanism**.

### 3.2 Anthropic — Best practices for Claude Code

<https://code.claude.com/docs/en/best-practices>

- Framing: "Most best practices are based on one constraint: Claude's context window fills up fast, and performance degrades as it fills."
- **The deletion test (verbatim):** "For each line, ask: *'Would removing this cause Claude to make mistakes?'* If not, cut it."
- **"Bloated CLAUDE.md files cause Claude to ignore your actual instructions!"**
- **Emphasis dilution (verbatim):** "If you emphasize many lines, none of them stands out." (Add IMPORTANT to *one* line, not many.)
- **Symptoms → causes:**
  - "If Claude keeps doing something you don't want despite having a rule against it, the file is probably too long and the rule is getting lost."
  - "If Claude asks you questions that are answered in CLAUDE.md, the phrasing might be ambiguous."
- **"Treat CLAUDE.md like code: review it when things go wrong, prune it regularly, and test changes by observing whether Claude's behavior actually shifts."**
- The include/exclude table — the most directly auditable list in any vendor doc:

| Include | Exclude |
|---|---|
| Bash commands Claude can't guess | Anything Claude can figure out by reading code |
| Code style rules that differ from defaults | Standard language conventions Claude already knows |
| Testing instructions and preferred test runners | Detailed API documentation (link to docs instead) |
| Repository etiquette (branch naming, PR conventions) | Information that changes frequently |
| Architectural decisions specific to your project | Long explanations or tutorials |
| Developer environment quirks (required env vars) | File-by-file descriptions of the codebase |
| Common gotchas or non-obvious behaviors | Self-evident practices like "write clean code" |

- Named **failure patterns**: the kitchen sink session; correcting over and over; **"The over-specified CLAUDE.md"** ("If your CLAUDE.md is too long, Claude ignores half of it because important rules get lost in the noise"); the trust-then-verify gap; the infinite exploration.
- Fix for over-specification (verbatim): "Ruthlessly prune. **If Claude already does something correctly without the instruction, delete it or convert it to a hook.**"
- Hooks vs instructions: "Unlike CLAUDE.md instructions which are advisory, hooks are deterministic and guarantee the action happens."
- Scoping rule: "CLAUDE.md is loaded every session, so only include things that apply broadly. For domain knowledge or workflows that are only relevant sometimes, use skills instead."

### 3.3 Anthropic — Skills

<https://code.claude.com/docs/en/skills>

- **"Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files."**
- Skill **descriptions always load**; bodies load only on invocation: "Unlike CLAUDE.md content, a skill's body loads only when it's used, so long reference material costs almost nothing until you need it."
- **Skill listing budget = 1% of the model's context window** (`skillListingBudgetFraction`, e.g. `0.02` for 2%; or a fixed `CLAUDE_CODE_SLASH_COMMAND_TOOL_CHAR_BUDGET`).
- **Combined `description` + `when_to_use` truncated at 1,536 characters** per skill in the listing (`skillListingMaxDescChars`). "Put the key use case first."
- Overflow behavior: "Claude Code drops descriptions starting with the skills you invoke least, so the skills you use most keep their full text."
- **Skill body is sticky:** "the rendered `SKILL.md` content enters the conversation as a single message and stays there across later turns" — "every line in a skill is a recurring token cost" after invocation. Claude Code does **not** re-read the file on later turns.
- After auto-compaction: keeps the **first 5,000 tokens of each skill**, with a **combined 25,000-token** re-attachment budget, filled from most-recently-invoked backwards.
- Body style: "State what to do rather than narrating how or why, and apply the same conciseness test you would for CLAUDE.md content."
- **Extraction trigger (verbatim):** "Create a skill when you keep pasting the same instructions, checklist, or multi-step procedure into chat, or **when a section of CLAUDE.md has grown into a procedure rather than a fact.**"
- Three-way split the docs codify: **CLAUDE.md** = static facts/conventions, always loaded · **`.claude/rules/`** = modular, optionally path-scoped via `paths:` glob frontmatter, loads only on matching files · **skills** = procedures, loaded on demand.

### 3.4 Anthropic — `/skill-doctor` (shipped 2026-09-04, Claude Code 2.1.261)

<https://www.implicator.ai/anthropic-claude-code-skill-doctor-context-audit/> · <https://ai-tldr.dev/releases/anthropic-claude-code-2-1-261/> · <https://ccleaks.com/news/how-to-use-claude-code-skill-doctor-sep-2026>

- "Every skill in the skill listing adds to your context on every turn, whether or not Claude ever uses it."
- Reports: which loaded skills were **never invoked**, **what each costs in context**, where to turn them off, and plugins not used recently. Requires v2.1.252+.
- Community-reported rule of thumb attributed to Anthropic's playbook: **8–12 skills** before cost shows up; past that, every line is "context tax."
- **Known limitation (flag it):** the tool records usage occurrence, "not whether the skill improved the result." Usage ≠ value.
- Prior art in the same product: `/doctor` became a full setup checkup in v2.1.205 (2026-07-08); CLAUDE.md trim proposal added v2.1.206 (2026-07-09).

### 3.5 Anthropic — "Effective context engineering for AI agents"

<https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>

- "Context must be treated as a finite resource with diminishing marginal returns."
- **Attention budget:** "Every new token introduced depletes this budget by some amount, increasing need for careful curation."
- **Right altitude:** avoid both "complex, brittle logic hardcoded in prompts" (fragile) and "high-level guidance that fails to give concrete signals" (vague). Target: "Specific enough to guide behavior effectively, yet flexible enough to provide strong heuristics."
- "Find the smallest possible set of high-signal tokens maximizing likelihood of desired outcome." Minimal ≠ short: "striving for the minimal set of information fully outlining expected behavior."
- Long-horizon techniques: **compaction**, **structured note-taking** persisted outside the window, **sub-agents** with clean windows returning condensed summaries.

---

## 4. Cross-tool rule-file guidance (Cursor / Copilot / AGENTS.md / Windsurf / Cline)

### 4.1 Cursor `.cursor/rules` (`.mdc`)

<https://cursor.com/docs/rules> (canonical; `docs.cursor.com/en/context/rules` now 308-redirects)

- **"Good rules are focused, actionable, and scoped. Keep rules under 500 lines"** — plus "avoid duplicating existing codebase documentation."
- Process guidance: "start simply and add rules only when you notice repeated mistakes."
- Four application modes: **Always Apply** · **Apply Intelligently** (agent decides from the description) · **Apply to Specific Files** (globs) · **Apply Manually** (`@rule-name`).
- Nested rules supported in subdirectories; Cursor also honours nested `AGENTS.md` with nearest-file precedence.
- **`.cursorrules` (single root file) is the legacy format**, superseded by `.cursor/rules/*.mdc`. **Flag a repo still on `.cursorrules` as stale-by-format, not just stale-by-content.** (`PatrickJS/awesome-cursorrules` is still the largest catalogue of these, but it is a catalogue of the *legacy* format — treat its contents as examples, not current best practice.)
- Community-converged numbers, consistent across several 2026 write-ups:
  - ≤500 lines/file is the ceiling; the practical target is **50–80 lines and one concept per rule**.
  - **All "Always Apply" rules combined should stay under ~2,000 tokens.**
  - A 50-line rule file ≈ **200–400 tokens**; five always-on 50-line rules ≈ 1,000–2,000 tokens of per-turn overhead.
  - An always-on rule "should be a handful of lines, because it is prepended to every unrelated turn."
  <https://www.morphllm.com/cursor-rules-best-practices> · <https://axonbuild.com/blog/cursor-rules-best-practices/>
- Repeated advice worth encoding as checks: "reference files instead of copying their contents — this keeps rules short and prevents them from becoming stale as code changes"; "avoid copying entire style guides, use a linter instead"; "don't document every possible command since Agent knows common tools like npm, git, and pytest"; keep rules to patterns you use frequently, not edge cases.

### 4.2 GitHub Copilot `.github/copilot-instructions.md`

<https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions>

- GitHub's own generation prompt states the limits verbatim: **"Instructions must be no longer than 2 pages."** and **"Instructions must not be task specific."**
- Emphasis on **exact, validated command sequences** — "which commands work and their proper execution order" — plus documented errors and workarounds encountered, and **timing information for commands that time out**. (Notably the *opposite* of Anthropic's "cut anything derivable"; see §7.)
- Path-scoped variant: `.github/instructions/NAME.instructions.md` with `applyTo:` glob frontmatter; can exclude agents with `excludeAgent: "code-review"` or `"cloud-agent"`.
- <https://github.blog/ai-and-ml/github-copilot/5-tips-for-writing-better-custom-instructions-for-copilot/> — five tips: (1) project overview, "just a few sentences to set the stage"; (2) tech stack list; (3) coding guidelines "broadly applicable to the entire project"; (4) project structure map; (5) pointers to scripts/automation/MCP servers. Stance: "something is always better than nothing."
- Code-review-specific guidance: **start with 10–20 specific instructions** addressing your most common review needs, then test whether they change behavior; "Keep instructions concise and actionable, as lengthy instructions can dilute effectiveness." Widely repeated secondary cap: **~1,000 lines max for a single instruction file**.
  <https://docs.github.com/en/copilot/tutorials/customize-code-review>
- `github/awesome-copilot` is the curated catalogue of `.instructions.md`, `.prompt.md`, `.chatmode.md` files — useful as a corpus of what real instruction files look like, not as normative guidance.

### 4.3 AGENTS.md

<https://agents.md/>

- "Think of AGENTS.md as a **README for agents**: a dedicated, predictable place to provide the context and instructions to help AI coding agents work on your project."
- Explicit README split: "README.md files are for humans: quick starts, project descriptions, and contribution guidelines," while AGENTS.md holds "the extra, sometimes detailed context coding agents need."
- **Nesting is the official monorepo answer:** "Place another AGENTS.md inside each package. Agents automatically read the nearest file in the directory tree, so the closest one takes precedence."
- Precedence: "The closest AGENTS.md to the edited file wins; explicit user chat prompts override everything."
- "AGENTS.md is just standard Markdown. Use any headings you like" — **no mandatory sections and no size guidance in the spec**. That deliberate lack of opinion is part of why AGENTS.md files bloat; the spec offers nothing to audit against, so borrow Anthropic's/Cursor's numbers.
- Common sections: project overview, build/test commands, code style, testing instructions, security considerations, commit/PR guidelines, deployment steps.
- Adopted by 20+ tools (OpenAI Codex, Google Jules, Factory, Aider, Cursor, VS Code, GitHub Copilot, Zed, Warp, JetBrains Junie, Devin).

### 4.4 Windsurf / Cline / Devin (present in the wild; thinner guidance)

- `.windsurfrules` / `.windsurf/rules/`, `.clinerules` (file or directory), `.devin/rules/` follow the same shape: root file superseded by a rules *directory* with globs.
- Claude Code's `/init` and `/import` (v2.1.213+) read all of these — the canonical list of "agent instruction file" locations to scan:
  `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/**/*.md`, `AGENTS.md` (root + nested), `.cursor/rules/**/*.mdc`, `.cursorrules`, `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `.windsurf/rules/`, `.windsurfrules`, `.clinerules`, `.devin/rules/`.
  Source: <https://code.claude.com/docs/en/memory>
- **Audit implication:** presence of *several* of these in one repo is the highest-yield duplication signal a scanner can look for. `/import` "appends a one-time copy" — which means repos that ran it likely contain literal duplicated blocks.

---

## 5. Practitioner writing on context engineering (2025–2026)

### 5.1 Manus — "Context Engineering for AI Agents: Lessons from Building Manus" (2025)

<https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus>

- **KV-cache first:** "KV-cache hit rate is the single most important metric for a production-stage AI agent." Cached vs uncached on Claude Sonnet: **$0.30/MTok vs $3/MTok — 10×**. Manus runs a **~100:1 input-to-output token ratio**.
  → *Audit relevance:* anything that changes the **stable prefix** (timestamps, per-session-generated content, reordered rules) silently destroys cache hits. A CLAUDE.md containing a timestamp or a rotating tip is a cost bug, not just a style bug.
- **Mask, don't remove:** "avoid dynamically adding or removing tools mid-iteration" — changes invalidate the KV-cache and leave the model referencing undefined tools. Prefer logit masking / prefill.
- **Filesystem as context:** "Treat the file system as the ultimate context in Manus: unlimited in size, persistent by nature, and directly operable by the agent itself." Compression should be **restorable** (drop page content, keep the URL).
- **Recitation:** rewriting `todo.md` throughout a task "pushes the global plan into the model's recent attention span," countering lost-in-the-middle across ~50 tool calls per task.
- **Keep the wrong stuff in:** "Leave the wrong turns in the context" — erasing failures removes the evidence the model needs to avoid repeating them. **This directly conflicts with naive "prune everything" advice; see §7.**
- **Don't get few-shotted:** uniform context creates brittle pattern mimicry; deliberately "increase diversity" in serialization and phrasing.

### 5.2 Cognition — "Don't Build Multi-Agents" (2025)

<https://cognition.com/blog/dont-build-multi-agents> (note: `cognition.ai` 301-redirects to `cognition.com`)

- **Principle 1:** "Share context, and share full agent traces, not just individual messages."
- **Principle 2:** "Actions carry implicit decisions, and conflicting decisions carry bad results."
- "Context engineering" is "effectively the #1 job of engineers building AI agents."
- Guidance: default to ruling out architectures that violate those two principles.

### 5.3 Dex Horthy / HumanLayer — "Advanced Context Engineering for Coding Agents" (2025)

<https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md> · talk: <https://www.youtube.com/watch?v=VvkhYWFWaKI> · interview: <https://newsletter.pragmaticengineer.com/p/context-engineering-with-dex-horthy>

- **Frequent intentional compaction**; target "keeping utilization in the **40%–60% range** (depends on complexity of the problem)."
- Geoff Huntley's constraint, quoted approvingly: "you only have approximately **170k of context window** to work with."
- **Priority order for context problems (verbatim, in order):** 1. "Incorrect Information" 2. "Missing Information" 3. "Too much Noise".
  → *This is the correct severity ordering for an audit's findings: wrong beats missing beats bloated.*
- Workflow: **Research → Plan → Implement**, with a **~200-line research document** as the compact, human-readable artifact and a "fairly short" plan.
- **Leverage argument (verbatim):** "A bad line of code is… a bad line of code. But a bad line of a **plan** could lead to hundreds of bad lines of code. And a bad line of **research**... could land you with thousands of bad lines of code."
  → *Applies directly to CLAUDE.md: a bad line there is a bad line in every future session.*
- Results claim: 35k LOC of features (cancellation + WASM) added to a 300k-LOC Rust codebase (BAML) in ~7 hours vs 3–5 days/feature estimated.
- Related: Horthy's **12-Factor Agents** (<https://github.com/humanlayer/12-factor-agents>) — factors 3 ("Own your context window") and 10 ("Small, focused agents") are the ones cited in context-hygiene arguments.

### 5.3b HumanLayer — "Writing a good CLAUDE.md" (the instruction-budget argument)

<https://www.humanlayer.dev/blog/writing-a-good-claude-md>
Listed under "Start Here / CLAUDE.md Best Practices" in `hesreallyhim/awesome-claude-code` — i.e. this is the community's canonical essay on the subject.

- **Instruction budget (the single most quotable frame):** frontier LLMs can follow **~150–200 instructions reliably**; "Claude Code's system prompt contains ~50 individual instructions." That leaves roughly **100–150 instructions** for your CLAUDE.md, rules, and user messages *combined*.
  → Reframes the audit unit from *lines/tokens* to **instruction count**. A repo with 300 imperative bullets across its instruction files has already overdrawn the budget regardless of token count.
- **Length target:** "At HumanLayer, our root `CLAUDE.md` file is *less than sixty lines*." General consensus in the piece: **under 300 lines maximum**; shorter is better.
- **Progressive disclosure:** keep CLAUDE.md minimal (WHY / WHAT / HOW that applies to *every* session), push task-specific guidance to an `agent_docs/` directory (`building_the_project.md`, `running_tests.md`, `code_conventions.md`, `service_architecture.md`) and **reference** rather than duplicate.
- **Against code style rules in CLAUDE.md (verbatim):** **"Never send an LLM to do a linter's job."** "LLMs are comparably expensive and *incredibly* slow compared to traditional linters."
- **Against `/init` auto-generation:** "avoid auto-generating it. You should carefully craft its contents" — because "`CLAUDE.md` is the highest leverage point of the harness." **Directly contradicts Anthropic's own `/init` recommendation; see §7.8.**
- **Universal-applicability rule:** include only instructions relevant to *every* session.

Related, same argument with worked numbers: <https://alexop.dev/posts/stop-bloating-your-claude-md-progressive-disclosure-ai-coding-tools/>
- Worked bloat example: 200 lines of style rules + 150 lines of architecture + 300 lines of gotchas ≈ **half the context window consumed before any work begins**.
- Contrasts "two hundred lines about code style" against simply letting ESLint verify it.
- **Counter-evidence worth flagging:** cites Vercel research finding **skills remained uninvoked in 56% of test cases**, producing zero improvement over baseline — which is an argument *against* naive "just move it to a skill" advice. See §7.9.

### 5.4 Simon Willison — context engineering as a term (2025)

<https://simonwillison.net/2025/Jun/27/context-engineering/>

- Tobi Lütke: "The art of providing all the context for the task to be plausibly solvable by the LLM."
- Andrej Karpathy: "The delicate art and science of filling the context window with just the right information."
- Willison's point: "context engineering" better captures the real work than "prompt engineering," which most people now read as "typing into a chatbot."
- His summary of Breunig: <https://simonwillison.net/2025/Jun/29/how-to-fix-your-context/>

### 5.5 Drew Breunig — "Working with Contexts" (O'Reilly Radar, 2026)

<https://www.oreilly.com/radar/working-with-contexts/> — later restatement of the taxonomy for a broader audience; useful as a citable, edited source when the blog post feels too informal.

---

## 6. Existing audit tools & skills (direct prior art)

These are the closest things to a `/context-health` skill that already exist. Worth studying for check lists and report shape; worth differentiating from.

### 6.1 `agent-clinic/claude-md-doctor`

<https://github.com/agent-clinic/claude-md-doctor>
Tagline: audit "size vitals, dead references, drifted claims, and backtest every rule against your own session history to see which rules get followed, ignored, or never used."

Checks it runs:

- **Vitals:** effective file size vs guidance; estimated token cost per session; structure integrity; "pathology markers" — **stock boilerplate**, **emphasis saturation**, **changelog accretion**.
- **Records verification:** dead file paths; unresolvable `@import`s; command scripts that don't match `package.json`/`Makefile`; `.claude/rules/` scope coverage.
- **Checkable claims:** countable assertions tested against repo state (test counts, file counts, component inventories) — catches "drifted claims."
- **Session backtest:** replays each decomposed rule against local transcripts in `~/.claude/projects/…`; per-rule compliance %, verdict (**healthy / ignored / inert / provisional**), cause triage (**defiance-proven, defiance, dilution, absence**), enforcement class (**hook, linter/test, judge**), and git-history dating so pre-rule violations don't count.
- Thresholds: "target under 200 lines per CLAUDE.md file"; proposed new rules gated at **≥2 sessions or ≥3 occurrences**.
- Output: HTML report with grade + "chief complaint", per-finding evidence, adherence table with receipts, prescriptions, optional badge.

**Key idea to steal:** *evidence-backed findings.* Every claim cites a line, a path, or a transcript excerpt. Also the **enforcement class** concept — for each rule, say whether it should be a hook, a lint rule, or an LLM judge.

### 6.2 `alexknowshtml/claude-memory-health`

<https://github.com/alexknowshtml/claude-memory-health> — "audits your MEMORY.md index — size, orphans, broken links, staleness." Narrower scope (auto-memory only) but the four axes — **size, orphans, broken links, staleness** — are a clean minimal check set.

### 6.3 `SomeStay07/claude-doctor-skill`

<https://github.com/SomeStay07/claude-doctor-skill> — "46 automated checks across 6 layers. Project health audit skill for Claude Code. Security first. Zero dependencies."

### 6.4 `hiclaude/health`

<https://github.com/hiclaude/health> — "audit your Claude Code config health across all layers"; reviews **CLAUDE.md → rules → skills → hooks → subagents → verifiers** and outputs a prioritized report. **⚠️ Returned HTTP 404 on two direct fetch attempts (repo root and README) — surfaced only via the search index. Treat as unverified / possibly deleted or renamed; do not cite as existing.** The **six-layer decomposition is the useful part regardless**, and it matches how Claude Code actually loads things.

### 6.4b `agent-docs-audit` (closest prior art to the proposed skill)

<https://buildwithclaude.com/skill/agent-docs-audit> — "Audits AGENTS.md, CLAUDE.md, and nested agent guidance files for quality, staleness, duplication, and **AGENTS/CLAUDE mirror drift**." The mirror-drift check (root AGENTS.md vs root CLAUDE.md having diverged copies of the same content) is the single most valuable idea here.

Adjacent doc-drift skills in the same marketplace, useful for check inventory:
- **Documentation Freshness** — detects "drift—the gap between what your code does and what your docs say", broken internal links, and API/function signatures in docs that don't match source. <https://mcpmarket.com/tools/skills/documentation-freshness>
- **Docs Audit** — markdown/README/docstring sync, inaccurate code examples, broken links, docstring coverage. <https://mcpmarket.com/tools/skills/documentation-audit-accuracy>
- **docs-sync-audit** — read-only drift audit across READMEs, setup guides, API docs, env docs, changelogs, examples, comments, generated docs. <https://skills-hub.ai/skills/github-copilot-docs-sync-audit>

### 6.4c Concrete per-turn token budgets from a self-audit skill writeup

<https://ai-muninn.com/en/blog/claude-code-slim-self-audit-skill> — the most explicit token-budget table anyone publishes:

| File | Budget |
|---|---|
| CLAUDE.md | "< 3,000 tokens (rules + pointers, no procedures)" |
| MEMORY.md | "< 2,000 tokens (index only, each entry < 150 characters)" |
| each `rules/*.md` | "< 500 tokens each" |
| **Total per-turn overhead** | **"< 8,000 tokens"** |

Its five checks: (1) duplicate content across CLAUDE.md and SKILL.md files — delete from the per-turn file since skills load on demand; (2) MEMORY.md entries exceeding one line; (3) **"Step-by-step instructions belong in skills, not rules"**; (4) flag content dated older than **30 days** for staleness review; (5) for every element, ask **"does this need to load every turn?"**.

### 6.4d First-party framing (bundled Anthropic skill)

Anthropic now ships a bundled `context-health` skill whose own description is the clearest statement of scope anyone has written. Verbatim from the skill listing:

> "Audits a repo's agent context — CLAUDE.md, AGENTS.md, cursor and copilot rules, skills, subagents, READMEs, architecture docs, code comments — for stale, contradictory and duplicated instructions and always-on token cost. Reports prioritized findings; **never edits**."

Two design decisions embedded there worth adopting: (a) **read-only by default** — an audit that edits is an audit nobody trusts; (b) **symptom-based triggering**, not just "audit my context" — its stated triggers include "the agent ignores instructions, follows stale guidance, burns too many tokens, or has been getting worse over months on the same repo."

### 6.5 `FlorianBruniaux/claude-code-ultimate-guide`

<https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/tools/context-audit-prompt.md> and `.../audit-prompt.md` — prompt-only (no skill packaging) audit templates. Notes the common starting state: "A basic CLAUDE.md exists but may be monolithic, stale, or mostly vague rules."

### 6.6 First-party: `/doctor` and `/skill-doctor`

Already covered in §3.4. **Any new `/context-health` skill must be positioned against these:** `/doctor` trims one CLAUDE.md, `/skill-doctor` prices the skill listing. Neither does cross-file conflict detection, neither looks at README/docs/code comments, and neither reads the repo's *other* agents' rule files.

### 6.7 Meta-skill authoring standards worth mirroring

**`obra/superpowers`** — <https://github.com/obra/superpowers> (14 skills: brainstorming, writing-plans, executing-plans, subagent-driven-development, systematic-debugging, TDD, verification-before-completion, writing-skills, …). Its `writing-skills` skill is the most rigorous community standard for skill authoring:
<https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md>

- Budgets: **frontmatter ≤1024 chars**; **description ≤500 chars** ("aim for less"); **getting-started workflows <150 words each**; **frequently-loaded skills <200 words total**; **other skills <500 words**.
- **The Description Trap (verbatim):** "When a description summarizes the skill's workflow, an agent may follow the description instead of reading the full skill content." Fix: descriptions must be **trigger-only** ("Use when X"), third person, **never summarize process**.
- Naming: verb-first, active voice — `creating-skills`, not `skill-creation`.
- Anti-patterns: narrative examples tied to specific sessions; multi-language code samples; generic semantic labels (`helper1`, `step3`); flowcharts containing code or linear instructions.
- Flowcharts only for non-obvious decision points, loops with early exits, and A-vs-B decisions — never for reference material or linear instructions.
- **"NO SKILL WITHOUT A FAILING TEST FIRST"** — write a baseline test documenting agent behavior *without* the skill, then verify compliance *with* it; capture rationalizations verbatim; never batch-create untested skills.
- **Avoid `@` link syntax in skills** — "force-loads files, wastes context." Use plain skill names with `**REQUIRED SUB-SKILL:**` markers.
- Its bundled `anthropic-best-practices.md` mirror: **SKILL.md body under 500 lines**; name ≤64 chars; description ≤1024 chars; **"For reference files longer than 100 lines, include a table of contents at the top"**; **"Keep references one level deep from SKILL.md"**; good example ≈50 tokens vs bad ≈150 tokens; always use forward slashes in paths.
  <https://github.com/obra/superpowers/blob/main/skills/writing-skills/anthropic-best-practices.md>

**Catalogues (useful as corpora, weak as normative guidance):** `hesreallyhim/awesome-claude-code`, `wshobson/agents`, `davila7/claude-code-templates`, `PatrickJS/awesome-cursorrules` (legacy format), `github/awesome-copilot`, `GetBindu/awesome-claude-code-and-skills`. Treat these as *what people actually ship*, and note that a large fraction of their entries violate the size guidance above — which is itself a finding.

---

## 7. Where the community DISAGREES

These are real, live disagreements. A `/context-health` skill should **surface the tension and let the user choose**, not silently pick a side.

### 7.1 Big CLAUDE.md vs minimal CLAUDE.md

- **Minimal camp (Anthropic, Cursor, most 2026 practitioners):** "target under 200 lines"; "Ruthlessly prune"; "Bloated CLAUDE.md files cause Claude to ignore your actual instructions!"; Anthropic cut 80% of its own system prompt with no eval loss.
- **Comprehensive camp (GitHub Copilot docs, many enterprise teams):** front-load "comprehensive, validated information" — exact build sequences, environment setup, project layout, known errors and workarounds, command timings — precisely so the agent doesn't have to explore. GitHub's tip #4 is literally "Explain Your Project Structure." Stance: "something is always better than nothing."
- **The crux:** exploration cost vs per-turn cost. Copilot's model assumes exploration is expensive and unreliable; Anthropic's assumes the agent can read the repo cheaply and that stale restatements are worse than no statement. Both agree on **exact, validated commands**; they diverge on **directory maps and architecture overviews** (Anthropic's `/doctor` explicitly *cuts* those).
- **Practical resolution most teams land on:** small always-on root file + path-scoped rules + on-demand skills. Anthropic, Cursor and AGENTS.md all now provide the machinery for exactly this.

### 7.2 Prune failed attempts vs keep them

- **Manus:** "Leave the wrong turns in the context" — error traces are how the model updates its beliefs.
- **Anthropic best practices:** after two failed corrections, `/clear` because "Context is polluted with failed approaches."
- **Reconcilable:** Manus is talking about *within-task* tool-call errors (evidence); Anthropic is talking about *conversational* correction loops (noise). But the distinction is rarely made explicit, and it matters for what an audit says about a `NOTES.md`/`LEARNINGS.md` full of past failures.

### 7.3 One AGENTS.md vs nested per-package

- **agents.md spec + Cursor:** nested, nearest-file-wins, explicitly the monorepo answer.
- **Claude Code:** nested files are **concatenated, not overridden** — ancestors load at launch and subdirectory files load on demand. Same file layout, *different semantics*.
- **Consequence to flag:** a nested layout authored for Cursor/Codex ("this file overrides the parent") can be **actively wrong** under Claude Code, where both are in context simultaneously and can contradict each other. Anthropic ships `claudeMdExcludes` as the escape hatch. **This is a genuinely detectable, genuinely dangerous misconfiguration.**

### 7.4 Comments are a smell vs rationale comments are essential

- **Smell camp (Clean Code lineage, still widely repeated):** a comment explaining *what* code does is a failure to name things well; comments rot because nothing tests them.
- **Rationale camp (dominant in 2025–2026 agent-context writing):** *why* comments are exactly the context an agent cannot recover from the code. Anthropic's `/doctor` heuristic is the same shape — keep "pitfalls, rationale, and conventions," cut anything derivable.
- **Where they agree, and what an audit can safely flag:** **changelog-in-comments** ("2024-03-12: changed by X"), **commented-out code**, and comments that **contradict the code they annotate**. Those are anti-patterns under both camps.

### 7.5 Duplicate the content vs import/symlink it

- **Anthropic:** import (`@AGENTS.md`) or symlink; explicitly "without duplicating them."
- **Reality:** `/import` "appends a one-time copy," and Windows symlinks need Admin/Developer Mode — so real repos end up with divergent copies. **Auditable:** high-similarity blocks across CLAUDE.md / AGENTS.md / .cursorrules / copilot-instructions.
- **Counter-argument some teams make:** each tool interprets instructions differently, so tailored per-tool files beat a shared lowest-common-denominator file. Legitimate, but it must be a *deliberate* choice with an owner, not drift.

### 7.6 Does splitting into imports help?

- **Widely believed:** "split CLAUDE.md into `@docs/*.md` to keep it small."
- **Anthropic, explicitly:** "Splitting into `@path` imports helps organization but **doesn't reduce context**, since imported files load at launch." Only **path-scoped rules** and **skills** actually defer loading.
- **This is the single most common misconception a context audit will encounter.**

### 7.7 Usage as a proxy for value

- `/skill-doctor` flags never-invoked skills, but records "not whether the skill improved the result." `claude-md-doctor` similarly scores "ignored" rules from transcripts.
- A never-invoked skill may be a correctly-scoped rare-emergency skill. **Never-used ≠ useless** — report it as a prompt for a human decision, not as a defect.

### 7.8 Auto-generate CLAUDE.md (`/init`) vs hand-craft it

- **Anthropic:** "Run `/init` to generate a starting CLAUDE.md automatically… then refine over time." With `CLAUDE_CODE_NEW_INIT=1` it becomes an interactive multi-phase flow with a reviewable proposal.
- **HumanLayer:** "avoid auto-generating it. You should carefully craft its contents" — because "`CLAUDE.md` is the highest leverage point of the harness."
- **Auditable consequence:** `/init` output has a recognizable shape (directory-tree dump, dependency inventory, architecture overview) — exactly the content Anthropic's own `/doctor` later proposes cutting. **A CLAUDE.md that still looks `/init`-shaped and has never been pruned is a detectable finding** (`claude-md-doctor` calls it "stock boilerplate").

### 7.9 Does progressive disclosure actually fire?

- **The advice:** move situational content out of always-on files into skills / `agent_docs/` that load on demand.
- **The counter-evidence:** Vercel research cited by alexop.dev found **skills remained uninvoked in 56% of test cases**, producing zero improvement over baseline. Same failure mode reported on HN: relying on Claude to read referenced documentation files is "unreliable."
- **Partial mitigations the community uses:** path-scoped rules (`paths:` frontmatter / `applyTo:` globs) *push* the content in when a matching file is touched rather than hoping the model pulls it; and "if X then Y" trigger syntax in the root file. Both are more reliable than a bare "see `docs/foo.md`" pointer.
- **Audit implication:** flagging "move this to a skill" is not automatically safe advice. Prefer **path-scoped rules** for must-arrive content and reserve skills for genuinely optional procedures — and say so in the finding.

### 7.10 Style rules in instruction files vs in the linter

- **HumanLayer, categorically:** "Never send an LLM to do a linter's job."
- **Cursor docs, same direction:** "avoid copying entire style guides and using a linter instead."
- **Against:** Anthropic's include-list keeps "Code style rules that differ from defaults" — on the grounds that the model has to *write* conforming code, not merely pass the linter afterwards; a lint failure costs a round trip.
- **Synthesizable rule an audit can apply:** keep a style rule in context only if (a) it is not mechanically enforced by a config already in the repo, and (b) it differs from the ecosystem default. If a `.eslintrc` / `ruff.toml` / `.editorconfig` already encodes the rule, the prose copy is pure duplication — **and this is mechanically checkable.**

---

## 8. Freshness / maintenance techniques the community actually uses

- **Ownership and review cadence.** "Treat CLAUDE.md like code: review it when things go wrong, prune it regularly." Practical triggers rather than a calendar: after an incident, after a failed session, at `/init` re-runs.
- **Add-on-second-mistake rule.** Anthropic's explicit add criteria: "Claude makes the same mistake a second time"; a code review catches something Claude should have known; you retype the same correction; a new teammate would need the same context. Cursor's version: "add rules only when you notice repeated mistakes." `claude-md-doctor` operationalizes it as **≥2 sessions or ≥3 occurrences**.
- **Dated entries.** Claude Code stamps a `modified` ISO-8601 field in auto-memory frontmatter (v2.1.214+) so both human and model can see how current a fact is. Manual equivalent: date entries in decision logs and prune on age.
- **ADRs (Architecture Decision Records).** The durable, dated, superseded-aware format for *why*. This is the natural home for "rationale" content that `/doctor` says to keep but that would bloat an always-on file.
  - Role split, verbatim: "ADRs are the durable, reviewed half of that context. They hold the deliberate, stable decisions, as opposed to the throwaway instructions you type into a single session." <https://www.actual.ai/blog/agent-optimized-adrs>
  - The rot mechanism, verbatim and worth quoting in any audit report: **"Context files rot. The same decision gets restated in `CLAUDE.md`, `AGENTS.md`, a README, and a wiki page, and the four copies disagree within a few months."**
  - **Append-only discipline:** "You do not edit an accepted decision, you supersede it with a new one. The log is append-only." Lifecycle: Proposed → Accepted → Deprecated → Superseded; a superseding ADR states "Supersedes ADR-0003."
  - **Agent-optimized ADR format** (differs from classic prose ADRs): scoped file globs, imperative MUST / MUST NOT rules, **stable rule IDs** (e.g. `R-IMG-001`), and a **verify command** per rule. Stable IDs make a rule citable from code comments and from audit findings; verify commands make the rule mechanically checkable.
  - Size: "Keep them short - 1-2 pages maximum"; the lightweight template is under 500 words. MADR sections: Status / Context / Decision Drivers / Considered Options / Decision / Rationale / Consequences / Implementation Notes. Write them for significant choices (framework, database, API pattern, security architecture); skip for version bumps, bug fixes, routine maintenance. <https://github.com/wshobson/agents/blob/main/plugins/documentation-generation/skills/architecture-decision-records/SKILL.md>
  - **The warning that applies to any freshness scheme:** "Do not try to document everything; you will burn out and the log will rot, which is worse than no log."
- **"If you changed X, update Y" links.** Two mechanisms:
  - Path-scoped rules with `paths:` frontmatter — the rule *arrives* when the file is touched, no memory required.
  - Codeowner-style pairing in CI: touching `src/api/**` without touching `docs/api.md` fails a check.
- **Tests and lint for docs.** Executable docs are the only ones that can't rot: doctest-style snippets, `make check-docs` that runs the commands in the README, link checkers for dead paths, and assertions that the commands named in CLAUDE.md exist in `package.json`/`Makefile` (`claude-md-doctor` checks exactly this).
- **Checkable claims.** Prefer assertions a script can verify ("tests live in `tests/`", "run `pnpm test`") over unverifiable prose ("the codebase is well-modularized"). `claude-md-doctor` calls the failure mode "drifted claims."
- **Enforcement escalation.** For each rule ask: hook (deterministic, must-always-happen), linter/test (mechanically checkable), or judge/instruction (genuinely judgement-based). Anything in tier 1 or 2 should *leave* the instruction file. Anthropic: "If Claude already does something correctly without the instruction, delete it or convert it to a hook."
- **Behavioral testing of instructions.** obra's "NO SKILL WITHOUT A FAILING TEST FIRST": document baseline behavior *without* the rule, then verify the rule changes it. Anthropic's lighter version: "test changes by observing whether Claude's behavior actually shifts."
- **Session backtesting.** Replay rules against `~/.claude/projects/<project>/*.jsonl` transcripts to score compliance and find inert rules. Highest-signal freshness technique available today; requires local transcript access.
- **Instrumentation.** `InstructionsLoaded` hook logs exactly which instruction files loaded and why — ground truth for "what is actually in my context," better than guessing from the filesystem.
- **Single-source with an import.** One canonical file; every other agent's file is a symlink or a one-line import. Makes drift structurally impossible rather than merely discouraged.

---

## 9. Anti-patterns repeatedly called out (the audit-detectable list)

Ordered roughly by (frequency × detectability). Severity ordering follows HumanLayer: **incorrect > missing > noisy**.

### Tier A — Incorrect (highest severity: these actively mislead)

1. **Stale setup/build/test commands** — commands in CLAUDE.md/README that no longer exist in `package.json`, `Makefile`, `pyproject.toml`, or CI. *Detect:* cross-reference every fenced command against script manifests. (`claude-md-doctor` "command script matching")
2. **Dead file/directory references** — paths named in instructions that no longer exist. *Detect:* resolve every path-like token. (`claude-md-doctor` "dead file path detection")
3. **Broken `@imports`** — `@path` that resolves to nothing, or exceeds the 4-hop depth limit. *Detect:* resolve the import graph.
4. **Drifted countable claims** — "we have 42 components", "3 services", "tests live in `spec/`" that no longer hold. *Detect:* verify countable assertions against repo state.
5. **Contradictory rules across files** — root vs nested CLAUDE.md, CLAUDE.md vs `.cursor/rules`, README vs AGENTS.md. Anthropic: "Claude may pick one arbitrarily." *Detect:* semantic conflict pass over extracted imperatives.
6. **Docs describing removed features** — sections referencing modules, flags, endpoints or env vars absent from the code. *Detect:* symbol/identifier existence check.
7. **Comments contradicting the code they annotate** — including stale parameter docs and outdated invariants.
8. **Nested-file semantics mismatch** — a nested layout authored on "nearest wins" assumptions running under Claude Code's concatenation. *Detect:* nested instruction files whose content overlaps or conflicts with an ancestor.

### Tier B — Noise with a real per-turn cost

9. **Oversized always-on files** — CLAUDE.md >200 lines; any single rule file >500 lines; combined always-on rules >~2,000 tokens; Copilot instructions >2 pages.
10. **Duplicated instruction blocks across files** — the same paragraphs in CLAUDE.md, AGENTS.md, README, `.cursorrules`, `copilot-instructions.md`. *Detect:* near-duplicate block hashing across the instruction-file glob set.
11. **Content derivable from the codebase** — directory-tree dumps, dependency lists, file-by-file descriptions, architecture overviews. Anthropic's `/doctor` cuts exactly these.
12. **"Be helpful"-tier no-ops** — "write clean code", "follow best practices", "be concise", "use good naming". Anthropic: "Self-evident practices like 'write clean code'." *Detect:* unverifiable-imperative classifier; vague-adjective lexicon (clean, proper, good, appropriate, robust, modern, efficient) with no measurable object.
13. **Standard language conventions the model already knows** — PEP 8, "use `const` not `var`", "prefer `async/await`". Cursor: "avoid copying entire style guides and use a linter instead."
14. **Emphasis saturation** — many lines shouting IMPORTANT / ALWAYS / NEVER / MUST / CRITICAL. Anthropic: "If you emphasize many lines, none of them stands out." *Detect:* ratio of emphasized lines to total lines.
15. **Changelog accretion in instruction files** — "2026-04: switched to pnpm", "Update: we now use X". Instruction files becoming append-only logs. *Detect:* date-stamped lines, "Update:"/"Note:"/"As of" prefixes, monotonically growing sections.
16. **Aspirational rules nobody follows** — "always write tests first", "100% coverage" in a repo whose diff history says otherwise. *Detect:* backtest against transcripts and/or check the claim against the repo (coverage config, test-to-source ratio).
17. **Giant rule dumps / whole style guides pasted inline.** *Detect:* very long unbroken bullet runs, pasted linter configs, tables of every command.
18. **Generated files committed as context** — lockfiles, `dist/`, OpenAPI dumps, `.min.js`, migration snapshots, large fixtures sitting where an agent will read them, or worse, imported. *Detect:* generated-file markers plus size, and any `@import` pointing at one.
19. **Commented-out code and changelog-in-comments** — the two comment anti-patterns both camps agree on. *Detect:* commented lines that parse as code; `// 2024-03-12 changed by` patterns; `git blame` age.
20. **Never-invoked skills and unused MCP servers/tools** — each costs listing tokens every turn (1% of window budget; 1,536 chars/skill cap; GeoEngine 46-vs-19-tools result). *Detect:* skills present but absent from transcripts; MCP servers configured but never called. **Report as a question, not a defect** (§7.7).

### Tier C — Structural / process

21. **Legacy formats still in place** — `.cursorrules` instead of `.cursor/rules/`, root `.windsurfrules`, `.clinerules` file instead of directory.
22. **No path scoping** — everything always-on when `paths:` frontmatter or `applyTo:` globs would defer most of it.
23. **Procedures living in CLAUDE.md** — multi-step workflows that should be skills. Anthropic's explicit trigger: "a section of CLAUDE.md has grown into a procedure rather than a fact."
24. **Rules that should be hooks or lint rules** — mechanically enforceable instructions burning context as advisory prose.
25. **Instability in the cached prefix** — timestamps, per-run generated content, or reordering in always-on files, which kills KV-cache hits (Manus: 10× cost difference).
26. **No owner, no review trigger, no dates** — nothing in the repo says who maintains the instruction files or when they were last verified.

---

## 9b. Consolidated thresholds table (everything numeric, with provenance)

| Thing | Threshold | Source | Confidence |
|---|---|---|---|
| CLAUDE.md length | **< 200 lines** ("target under 200 lines per CLAUDE.md file") | Anthropic docs (memory) | **Vendor, authoritative** |
| CLAUDE.md length (aggressive) | < 60 lines root file; < 300 lines max | HumanLayer essay | Practitioner, widely cited |
| CLAUDE.md token budget | < 3,000 tokens | ai-muninn self-audit | Practitioner, single source |
| CLAUDE.md hard limit | 4 MiB (file skipped entirely above this) | Anthropic docs | **Vendor** |
| Total per-turn instruction overhead | < 8,000 tokens | ai-muninn | Practitioner, single source |
| Instruction *count* budget | ~150–200 total instructions reliably followed; ~50 already used by Claude Code's system prompt → ~100–150 left for you | HumanLayer | Practitioner; the framing is more useful than the exact number |
| SKILL.md body | **< 500 lines** | Anthropic docs (skills) | **Vendor** |
| Skill body (word-count view) | < 200 words for frequently-loaded skills; < 500 words otherwise; < 150 words per getting-started workflow | obra/superpowers writing-skills | Practitioner, rigorous |
| Skill description + when_to_use | **1,536 chars** (hard truncation in the listing) | Anthropic docs | **Vendor, mechanical** |
| Skill frontmatter | ≤ 1024 chars total; description ≤ 500 chars (aim lower); name ≤ 64 chars | obra + Anthropic skill spec | Mixed |
| Skill listing budget | **1% of context window** (configurable via `skillListingBudgetFraction`) | Anthropic docs | **Vendor, mechanical** |
| Skill count before cost bites | 8–12 | Anthropic playbook, via press | Secondary; treat as soft |
| Skill re-attach after compaction | first 5,000 tokens per skill; 25,000 tokens combined | Anthropic docs | **Vendor, mechanical** |
| Cursor rule file | **< 500 lines** ("Keep rules under 500 lines") | Cursor docs | **Vendor** |
| Cursor rule file (practical) | 50–80 lines, one concept per rule | Community consensus | Practitioner |
| All "Always Apply" rules combined | < ~2,000 tokens | Community consensus | Practitioner |
| Rule token estimate | 50-line rule ≈ 200–400 tokens | Community | Rule of thumb |
| Copilot instructions | **"no longer than 2 pages"**; "must not be task specific" | GitHub docs (generation prompt) | **Vendor, verbatim** |
| Copilot instruction file (secondary) | ~1,000 lines max; start with 10–20 instructions | GitHub tutorials / community | Secondary |
| Individual `rules/*.md` | < 500 tokens each | ai-muninn | Practitioner |
| MEMORY.md | **first 200 lines or 25KB** loaded; rest dropped | Anthropic docs | **Vendor, mechanical** |
| MEMORY.md entries | one line each; < 150 chars per entry | ai-muninn + Anthropic error guidance | Mixed |
| `@import` depth | **max 4 hops** | Anthropic docs | **Vendor, mechanical** |
| Reference file needing a TOC | > 100 lines | Anthropic skill best practices | Vendor-adjacent |
| Reference file nesting | "one level deep from SKILL.md" | Anthropic skill best practices | Vendor-adjacent |
| ADR length | 1–2 pages max; lightweight template < 500 words | wshobson/agents ADR skill | Practitioner |
| Staleness review trigger | content dated > 30 days | ai-muninn | Practitioner |
| Rule-worthiness gate | ≥ 2 sessions or ≥ 3 occurrences of the same mistake | claude-md-doctor | Practitioner |
| Context utilization target during work | **40–60%** | HumanLayer / Dex Horthy | Practitioner, well-known |
| Usable context window in practice | ~170k | Geoff Huntley, via HumanLayer | Rule of thumb |
| Distraction onset (observed) | ~32k (Llama 3.1 405b), ~100k (Gemini 2.5 Pro) | Databricks / Breunig | Empirical, model-specific |
| Tool count before confusion | fails at 46 tools, succeeds at 19 (Llama 3.1 8b quantized) | GeoEngine, via Breunig | Empirical, model-specific |

> **How to use this in an audit:** report **vendor-mechanical** numbers as hard failures, **vendor** numbers as warnings, and **practitioner** numbers as advisory with the source named. Never present a community rule of thumb as though it were a spec.

---

## 10. Source list (primary first)

**Vendor / primary**
- <https://code.claude.com/docs/en/memory> — CLAUDE.md, rules, auto memory, imports, precedence, 200-line target
- <https://code.claude.com/docs/en/best-practices> — deletion test, include/exclude table, named failure patterns
- <https://code.claude.com/docs/en/skills> — 500-line SKILL.md, 1% listing budget, 1,536-char cap, stickiness, compaction budgets
- <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents> — attention budget, right altitude
- <https://cursor.com/docs/rules> — "focused, actionable, and scoped… under 500 lines"
- <https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions> — "no longer than 2 pages", "must not be task specific"
- <https://docs.github.com/en/copilot/tutorials/customize-code-review> — 10–20 instructions, iterate
- <https://github.blog/ai-and-ml/github-copilot/5-tips-for-writing-better-custom-instructions-for-copilot/>
- <https://agents.md/> — README-for-agents, nesting, nearest-wins

**Research**
- <https://research.trychroma.com/context-rot> — Context Rot, 18 models (2025)
- <https://arxiv.org/abs/2307.03172> — Lost in the Middle (2023, **older**)
- <https://hamel.dev/notes/llm/rag/p6-context_rot.html> — Hamel Husain's note on Context Rot

**Practitioner**
- <https://www.humanlayer.dev/blog/writing-a-good-claude-md> — instruction budget, <60 lines, "never send an LLM to do a linter's job"
- <https://alexop.dev/posts/stop-bloating-your-claude-md-progressive-disclosure-ai-coding-tools/> — worked bloat example; Vercel 56%-uninvoked counter-evidence
- <https://www.actual.ai/blog/agent-optimized-adrs> — "the four copies disagree within a few months"; append-only ADRs; stable rule IDs
- <https://github.com/wshobson/agents/blob/main/plugins/documentation-generation/skills/architecture-decision-records/SKILL.md> — MADR format, superseding, 1–2 page limit
- <https://ai-muninn.com/en/blog/claude-code-slim-self-audit-skill> — explicit per-turn token budget table
- <https://news.ycombinator.com/item?id=46098838> — HN "Writing a good Claude.md" thread; practitioner reports of adherence decay
- <https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html> — the four failure modes
- <https://www.oreilly.com/radar/working-with-contexts/> — Breunig, edited restatement (2026)
- <https://simonwillison.net/2025/Jun/29/how-to-fix-your-context/> · <https://simonwillison.net/2025/Jun/27/context-engineering/>
- <https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus>
- <https://cognition.com/blog/dont-build-multi-agents>
- <https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md>
- <https://github.com/humanlayer/12-factor-agents> — 12 factors; factor 3 "Own your context window", factor 9 "Compact Errors into Context Window", factor 10 "Small, Focused Agents"
- <https://www.langchain.com/blog/context-engineering-for-agents> — write/select/compress/isolate

**Tools & skills (prior art)**
- <https://github.com/agent-clinic/claude-md-doctor>
- <https://github.com/alexknowshtml/claude-memory-health>
- <https://github.com/SomeStay07/claude-doctor-skill>
- <https://github.com/hiclaude/health> (**404 on direct fetch — verify**)
- <https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/tools/context-audit-prompt.md>
- <https://www.implicator.ai/anthropic-claude-code-skill-doctor-context-audit/> — /skill-doctor coverage
- <https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md> — skill authoring standard
- <https://github.com/obra/superpowers/blob/main/skills/writing-skills/anthropic-best-practices.md>

**Catalogues (corpora, not normative)**
- `hesreallyhim/awesome-claude-code` · `wshobson/agents` · `davila7/claude-code-templates` · `PatrickJS/awesome-cursorrules` (legacy `.cursorrules` format) · `github/awesome-copilot` · `GetBindu/awesome-claude-code-and-skills`

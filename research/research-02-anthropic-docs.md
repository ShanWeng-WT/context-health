# Research 02 — Anthropic Official Documentation & Engineering Blog

Source material for the `/context-health` skill. All claims below were fetched live (Sept 2026), not recalled.

**IMPORTANT URL NOTE:** Anthropic moved Claude Code docs. `https://docs.claude.com/en/docs/claude-code/*` now 301/308-redirects to `https://code.claude.com/docs/en/*`. The famous `anthropic.com/engineering/claude-code-best-practices` post 308-redirects to `https://code.claude.com/docs/en/best-practices` — it is now a doc page, not a blog post, and has been substantially rewritten. API/Skills docs live at `https://platform.claude.com/docs/en/...`.

---

## 1. CLAUDE.md / memory files

### 1.1 Canonical sources
- https://code.claude.com/docs/en/memory ("How Claude remembers your project")
- https://code.claude.com/docs/en/best-practices ("Write an effective CLAUDE.md")
- https://code.claude.com/docs/en/features-overview ("Extend Claude Code")
- https://code.claude.com/docs/en/large-codebases (monorepo layering)
- https://code.claude.com/docs/en/costs ("Move instructions from CLAUDE.md to skills")
- https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more

### 1.2 The hard size number: 200 lines

Stated in **four separate places**, consistently:

| Source | Wording |
|---|---|
| memory | "**Size**: target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." |
| memory (troubleshooting) | "Files over 200 lines consume more context and may reduce adherence." |
| features-overview | "**Rule of thumb:** Keep CLAUDE.md under 200 lines." / "Keep CLAUDE.md under 200 lines. Move reference material to skills" |
| costs | "Aim to keep CLAUDE.md under 200 lines by including only essentials." |
| steering blog | "Keep under 200 lines" |

Hard technical limits (memory doc):
- "Claude Code loads a CLAUDE.md file of up to **4 MiB** in full and **skips a larger file**." (silent failure mode — a >4MiB CLAUDE.md loads NOTHING)
- "Shorter files produce better adherence."

### 1.3 What to include / exclude (best-practices, verbatim table)

| ✅ Include | ❌ Exclude |
|---|---|
| Bash commands Claude can't guess | Anything Claude can figure out by reading code |
| Code style rules that differ from defaults | Standard language conventions Claude already knows |
| Testing instructions and preferred test runners | Detailed API documentation (link to docs instead) |
| Repository etiquette (branch naming, PR conventions) | Information that changes frequently |
| Architectural decisions specific to your project | Long explanations or tutorials |
| Developer environment quirks (required env vars) | File-by-file descriptions of the codebase |
| Common gotchas or non-obvious behaviors | Self-evident practices like "write clean code" |

### 1.4 The per-line test (best-practices) — DIRECTLY ACTIONABLE AS AN AUDIT CHECK

> "Keep it concise. For each line, ask: *'Would removing this cause Claude to make mistakes?'* If not, cut it. **Bloated CLAUDE.md files cause Claude to ignore your actual instructions!**"

> "Treat CLAUDE.md like code: review it when things go wrong, prune it regularly, and test changes by observing whether Claude's behavior actually shifts."

### 1.5 Named diagnostic symptoms → causes (best-practices) — GOLD FOR A SYMPTOM-DRIVEN AUDIT

> "If Claude keeps doing something you don't want despite having a rule against it, **the file is probably too long and the rule is getting lost**."

> "If Claude asks you questions that are answered in CLAUDE.md, **the phrasing might be ambiguous**."

### 1.6 Emphasis dilution (best-practices) — AUDIT CHECK

> "If Claude keeps skipping one instruction, add emphasis such as 'IMPORTANT' to that line alone. **If you emphasize many lines, none of them stands out.**"

Corroborated by the steering blog on `--append-system-prompt`: "the more instructions you provide using this method, the less strictly Claude will follow them."

Also corroborated by prompt-engineering docs (https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices):
> "Where you might have said 'CRITICAL: You MUST use this tool when...', you can use more normal prompting like 'Use this tool when...'." (Opus 4.5/4.6 overtrigger on aggressive language)

**This is a real tension / shift**: Claude Code best-practices still recommends "IMPORTANT" emphasis; the platform prompting guide says newer models overtrigger on it and to dial it back. See §7 (Disagreements).

### 1.7 Consistency / contradiction (memory) — AUDIT CHECK

> "**Consistency**: if two rules contradict each other, **Claude may pick one arbitrarily**. Review your CLAUDE.md files, nested CLAUDE.md files in subdirectories, and `.claude/rules/` **periodically to remove outdated or conflicting instructions**."

Troubleshooting section repeats it:
> "Look for conflicting instructions across CLAUDE.md files. If two files give different guidance for the same behavior, Claude may pick one arbitrarily."

Layering rule (features-overview):
> "**CLAUDE.md files** are additive: all levels contribute content to Claude's context simultaneously... When instructions conflict, Claude uses judgment to reconcile them, with more specific instructions typically taking precedence."

### 1.8 Specificity (memory) — verbatim good/bad pairs, usable as audit exemplars

> "**Specificity**: write instructions that are concrete enough to verify."
> - "Use 2-space indentation" instead of "Format code properly"
> - "Run `npm test` before committing" instead of "Test your changes"
> - "API handlers live in `src/api/handlers/`" instead of "Keep files organized"

### 1.9 Structure (memory)

> "**Structure**: use markdown headers and bullets to group related instructions. Claude scans structure the same way readers do: organized sections are easier to follow than dense paragraphs."

### 1.10 Hierarchy / load order (memory)

Load order, **broadest to most specific** (later = read last = closer to the prompt):

| Scope | Location | Shared with |
|---|---|---|
| Managed policy | macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`; Linux/WSL `/etc/claude-code/CLAUDE.md`; Windows `C:\Program Files\ClaudeCode\CLAUDE.md` | All users in org |
| User instructions | `~/.claude/CLAUDE.md` | Just you, all projects |
| Project instructions | `./CLAUDE.md` **or** `./.claude/CLAUDE.md` | Team, via source control |
| Local instructions | `./CLAUDE.local.md` (gitignore it) | Just you, this project |

Resolution details:
- "Claude Code loads `CLAUDE.md` and `CLAUDE.local.md` from your current working directory and **every directory above it**."
- "All discovered files are **concatenated into context rather than overriding each other**."
- "Across the directory tree, content is ordered from the filesystem root down to your working directory" — so instructions closest to cwd are read LAST.
- "Within each directory, `CLAUDE.local.md` is appended after `CLAUDE.md`."
- Subdirectory CLAUDE.md files "are included when Claude reads files in those subdirectories" — i.e. lazily, not at launch.
- `claudeMd` key in `managed-settings.json` can inline managed CLAUDE.md content. Managed policy CLAUDE.md **cannot be excluded**.
- `claudeMdExcludes` setting (glob against absolute paths, arrays merge across settings layers) skips other teams' files in monorepos.

**Note: `CLAUDE.local.md` is NOT deprecated** in the current docs (contrary to older guidance) — it's a first-class scope again: "For private per-project preferences that shouldn't be checked into version control, create a `CLAUDE.local.md` at the project root."

Worktree gotcha: "a gitignored `CLAUDE.local.md` only exists in the worktree where you created it. To share personal instructions across worktrees, import a file from your home directory instead."

### 1.11 Imports (`@path`) — AUDIT CHECK, KEY GOTCHA

- Syntax: `@path/to/import`. Relative paths resolve **relative to the file containing the import**, not cwd.
- "Imported files can recursively import other files, with a **maximum depth of four hops**."
- "Import parsing **skips Markdown code spans and fenced code blocks**." Wrap in backticks (`` `@README` ``) to mention a path without importing.
- **CRITICAL for a bloat audit:** "Imported files are expanded and **loaded into context at launch** alongside the CLAUDE.md that references them." And: "Splitting into `@path` imports helps organization but **doesn't reduce context**, since imported files load at launch."
- External imports (path resolving outside cwd) trigger a one-time approval dialog in project-level memory files; declining disables them permanently and silently.

### 1.12 AGENTS.md — EXPLICIT ANSWER

> "**Claude Code reads `CLAUDE.md`, not `AGENTS.md`.**"

Supported bridges:
1. `@AGENTS.md` import at the top of CLAUDE.md, then Claude-specific additions below.
2. Symlink: `ln -s AGENTS.md CLAUDE.md` (Windows needs Admin/Developer Mode — use the import instead).
3. `/init` reads Cursor rules (`.cursor/rules/`, `.cursorrules`) and Copilot rules (`.github/copilot-instructions.md`) and incorporates them. With `CLAUDE_CODE_NEW_INIT=1`, `/init` also reads `AGENTS.md`, `.devin/rules/`, `.windsurf/rules/`/`.windsurfrules`, `.clinerules`.
4. `/import` (v2.1.213+) appends a one-time copy of `AGENTS.md` etc. into the matching CLAUDE.md and carries over MCP servers, commands, subagents, skills.

**Audit implication:** an `AGENTS.md` with no CLAUDE.md bridge is dead weight for Claude Code — it costs nothing but delivers nothing. A repo with BOTH, unlinked, is a duplication/divergence risk.

### 1.13 HTML comments are free

> "Block-level HTML comments (`<!-- maintainer notes -->`) in CLAUDE.md files are **stripped before the content is injected into Claude's context**. Use them to leave notes for human maintainers without spending context tokens on them. Comments inside code blocks are preserved."

### 1.14 CLAUDE.md is advisory, not enforcement — NAMED FAILURE MODE

> "Claude treats them as context, **not enforced configuration**. To block an action regardless of what Claude decides, use a PreToolUse hook instead."

> "CLAUDE.md content is **delivered as a user message after the system prompt**, not as part of the system prompt itself. Claude reads it and tries to follow it, but **there's no guarantee of strict compliance, especially for vague or conflicting instructions**."

From features-overview (Hook vs Skill tab):
> "**Put guardrails in hooks.** An instruction like 'never edit `.env`' in CLAUDE.md or a skill is a **request, not a guarantee**. A `PreToolUse` hook that blocks the edit is enforcement. If a rule must hold every time, make it a hook rather than a prompt instruction."

From the steering blog anti-patterns:
> - "Every time X, always do Y" → use **hooks**
> - "Never do this" → use **hooks** (PreToolUse) or **managed settings**
> - 30-line procedures → use **skills**; "**Procedures belong in skills. CLAUDE.md is for facts Claude should hold all the time.**"
> - "A real guardrail needs to be deterministic, and the enforcement methods are hooks and permissions."

**AUDIT CHECK:** grep CLAUDE.md for "always", "never", "every time", "before every commit", "after each edit" → these are candidates for hooks, not memory.

### 1.15 When to ADD to CLAUDE.md (memory)

> "Add to it when:
> - Claude makes the same mistake a second time
> - A code review catches something Claude should have known about this codebase
> - You type the same correction or clarification into chat that you typed last session
> - A new teammate would need the same context to be productive"

> "Keep it to facts Claude should hold in every session: build commands, conventions, project layout, 'always do X' rules. **If an entry is a multi-step procedure or only matters for one part of the codebase, move it to a skill or a path-scoped rule instead.**"

### 1.16 `/doctor` trim proposals — DIRECT PRECEDENT FOR THE `/context-health` SKILL

> "The `/doctor` checkup proposes trims for a checked-in CLAUDE.md: it **cuts content Claude can derive from the codebase, such as directory layouts, dependency lists, and architecture overviews, and keeps pitfalls, rationale, and conventions that differ from tool defaults.** The trim check requires Claude Code v2.1.206 or later."

This is Anthropic's own explicit heuristic for what to cut vs keep. Use it verbatim as the core rubric.

### 1.17 Compaction survival (memory + context-window)

> "Project-root CLAUDE.md survives compaction: after `/compact`, Claude re-reads it from disk and re-injects it into the session."

> "If an instruction disappeared after compaction, it was given only in conversation, lives in a nested CLAUDE.md that hasn't reloaded yet, or is a path-scoped rule that hasn't matched a file since."

### 1.18 Auto memory (a second, Claude-written memory system)

- Location: `~/.claude/projects/<project>/memory/`, keyed off the git repo (all worktrees share one).
- Contains `MEMORY.md` index + one topic file per memory.
- **"The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at the start of every conversation. Content beyond that threshold is not loaded at session start."**
- If MEMORY.md exceeds the limit, "the write still succeeds, but Claude Code returns an error telling Claude to rewrite the index, **because everything past the limit is dropped on the next load**."
- Four memory types recorded in frontmatter `type`: `user`, `feedback`, `project`, `reference`.
- "Claude **skips anything it can derive from the codebase**, such as architecture, file paths, or debugging fixes. It also **skips anything your CLAUDE.md files already say**." ← explicit de-duplication rule.
- Topic files are NOT loaded at startup; read on demand.
- Frontmatter `modified` ISO-8601 timestamp (v2.1.214+): "The timestamp shows how current the fact is, both to you and to Claude when it reads the memory back." ← **staleness signal built into the format**.
- Main conversation's auto memory is NOT loaded into subagents (except forks).
- Toggle: `autoMemoryEnabled`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `autoMemoryDirectory`.

### 1.19 `.claude/rules/` — the path-scoping escape valve

- Files in `.claude/rules/*.md`, discovered recursively; subdirectories allowed.
- "Rules without `paths` frontmatter are loaded at launch with the same priority as `.claude/CLAUDE.md`." ← **unscoped rules are always-on context, same cost as CLAUDE.md**.
- `paths:` YAML frontmatter with globs scopes a rule to matching files: "**Path-scoped rules trigger when Claude reads files matching the pattern, not on every tool use.**"
- Brace expansion budget: "a rule's whole `paths` list shares one budget of **1,000 expanded patterns and 4 MiB**". Over budget → pattern used unexpanded → literal braces match nothing (silent failure).
- Invalid `[` bracket expression → matches nothing, silently (other patterns still work).
- User-level rules `~/.claude/rules/` load **before** project rules (project rules win).
- Symlinks supported; circular symlinks detected.
- Rules vs skills: "Rules load into context every session or when matching files are opened. For task-specific instructions that **don't need to be in context all the time, use skills instead**."

### 1.20 Debugging which instructions loaded
- `/context` → "Memory files" list = what actually loaded.
- `/memory` → browse/edit all memory locations.
- `InstructionsLoaded` hook → "log exactly which instruction files are loaded, when they load, and why."

---

## 2. Context engineering

### 2.1 "Effective context engineering for AI agents"
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

**The core framing:**
> Context engineering is finding "the **smallest possible set of high-signal tokens** that maximize the likelihood of some desired outcome."

Distinction:
> Prompt engineering = "methods for writing/organizing LLM instructions"; context engineering = "strategies for **curating and maintaining the optimal set of tokens during inference**." Context engineering is the "natural progression" as systems move to multi-turn, long-horizon agents.

**Context rot / attention budget:**
> "As the number of tokens increases, the model's ability to accurately recall information **decreases**." (context rot)
- LLMs have a finite "**attention budget**" with diminishing marginal returns, analogous to human working memory.
- "**Every new token introduced depletes this budget by some amount.**"
- Degradation is "a **gradient rather than a hard cliff**" — models stay capable but show "reduced precision for information retrieval."
- Architectural cause: transformer n² pairwise token relationships get stretched thin at scale.

**System prompts — "the right altitude":**
Two failure modes at the extremes:
- "Complex, brittle logic hardcoded in prompts" → fragile, high maintenance.
- "Vague, high-level guidance" that falsely assumes shared context.
Sweet spot: "**specific enough to guide behavior effectively, yet flexible enough to provide strong heuristics.**"
- Use structured sections: `<background_information>`, `<instructions>`, `## Tool guidance`, `## Output description`.
- XML tags or Markdown headers to delineate.
- "Start with a minimal prompt on the best available model, then add instructions iteratively based on failures."
- "**Minimal does not necessarily mean short**; sufficient information is needed upfront."

**Tools:**
- Tools should return "token efficient" information and encourage "efficient agent behaviors."
- "Self-contained, robust to error, extremely clear" about intended use.
- Named failure mode: "**Bloated tool sets covering too much functionality or ambiguous decision points.**"
- The heuristic: "**If a human engineer can't definitively say which tool to use, an AI agent can't do better.**"
- Recommends a "minimal viable set of tools."

**Just-in-time retrieval vs pre-loading:**
- JIT: maintain "lightweight identifiers" (file paths, queries, links); "dynamically load data into context at runtime using tools."
- Mirrors human cognition: "we don't memorize corpuses but use external organization and indexing."
- Metadata (folder hierarchy, naming, timestamps) is itself signal — "a mechanism to refine behavior."
- Enables "**progressive disclosure**" — agents "incrementally discover relevant context through exploration" and "assemble understanding layer by layer, maintaining only what's necessary in working memory."
- Trade-off acknowledged: "Runtime exploration is slower than retrieving pre-computed data" and requires "opinionated engineering" to prevent "misusing tools, chasing dead-ends."
- **Hybrid is recommended**: "retrieve some data upfront for speed, pursue autonomous exploration at discretion." Claude Code is the named example: **CLAUDE.md files pre-loaded; glob/grep for just-in-time navigation.** Guidance: "the simplest thing that works."

**Compaction:**
- "Taking a conversation nearing the context limit, summarizing its contents, and reinitiating with the summary."
- Preserve "architectural decisions, unresolved bugs, implementation details"; discard "redundant tool outputs or messages."
- Continue with compressed context + "**five most recently accessed files**."
- Tuning: "maximize recall first to capture every relevant piece," then "iterate to improve precision by eliminating superfluous content."
- "**Tool result clearing** [is] the safest, lightest-touch compaction."

**Structured note-taking / external memory:**
- Agent "regularly writes notes persisted to memory outside the context window" and pulls them back later — "persistent memory with minimal overhead."
- Examples: Claude Code to-do lists and `NOTES.md`; Claude playing Pokémon tracking tallies across thousands of steps.
- "After context resets, the agent reads its own notes and continues."

**Sub-agent context isolation:**
- Specialized sub-agents with "**clean context windows**"; main agent coordinates with a high-level plan.
- Each sub-agent explores extensively but "returns only a condensed, distilled summary (**1,000–2,000 tokens**)."
- "Clear separation of concerns — detailed search context isolated within sub-agents."
- "Multi-agent systems showed substantial improvement over single-agent systems on complex research."

**Only explicit number in the post:** the 1,000–2,000-token sub-agent summary.

### 2.2 Context management on the platform
https://claude.com/blog/context-management (redirect from anthropic.com/news/context-management)

- Framing: "**Context windows have limits, but real work doesn't.**"
- **Context editing** = automatic clearing of stale tool calls/results near the limit.
- **Memory tool** = file-based store outside the context window, persists across conversations.
- Numbers:
  - Memory tool + context editing combined: **39% performance improvement** on complex multi-step agentic tasks.
  - Context editing alone: **29% improvement**.
  - **84% token reduction** in a 100-turn web search evaluation.
- Sonnet 4.5+ has built-in **context awareness** (tracks remaining tokens).

### 2.3 Claude Code's own context accounting
https://code.claude.com/docs/en/context-window

Illustrative startup budget against a **200,000-token** window (Anthropic's own representative numbers):

| Component | Tokens |
|---|---|
| System prompt | 4,200 |
| Auto memory (MEMORY.md) | 680 |
| Environment info | 280 |
| MCP tool names (deferred) | 120 |
| **Skill descriptions** | **450** |
| `~/.claude/CLAUDE.md` | 320 |
| **Project CLAUDE.md** | **1,800** |
| (user's first prompt) | 45 |

So ~7,850 tokens load before the user types — of which CLAUDE.md is ~2,120 (≈27% of startup context), skill descriptions ~450.

Other numbers from the same page:
- `ENABLE_TOOL_SEARCH=auto` loads MCP schemas upfront "when they fit within **10% of the context window**"; `=false` loads everything.
- Subagent example: "The subagent read **6,100 tokens** of files. You got a **420-token** result. **That's the context savings.**"
- Compaction summary ≈ **12%** of the summarized token volume (`sumTokens * 0.12` in the simulation).
- **Invoked skill bodies are re-injected after compaction, capped at 5,000 tokens per skill and 25,000 tokens total; oldest dropped first.**
- "Truncation keeps the start of the file, so **put the most important instructions near the top of `SKILL.md`**."
- After compaction, "Claude Code re-reads up to **five** of the files Claude has read or edited... choosing the ones modified most recently. **A file over 5,000 tokens comes back as a path reference without its content.**"
- "The **skill listing does not reload**" after compaction — "Only skills you actually invoked get preserved."
- 1M-token context available on Fable 5.1/5, Sonnet 5, Opus 4.6+, Sonnet 4.6.

**What survives compaction (verbatim table):**
| Mechanism | After compaction |
|---|---|
| System prompt and output style | Unchanged; not part of message history |
| Project-root CLAUDE.md and unscoped rules | Re-injected from disk |
| Auto memory | Re-injected from disk |
| Plan written in plan mode | Re-injected from disk |
| Rules with `paths:` frontmatter | Reloaded as Claude reads matching files |
| Nested CLAUDE.md in subdirectories | Reloaded as Claude reads files there |
| Files Claude read or edited | Re-reads up to five, most recently modified first |
| Invoked skill bodies | Re-injected, capped 5,000/skill and 25,000 total |
| Context hooks added earlier | Summarized with the rest |
| SessionStart hooks matching `compact` | Run again, output added |

> "If a rule must persist across compaction, drop the `paths:` frontmatter or move it to the project-root CLAUDE.md."

### 2.4 The single constraint framing (best-practices)

> "**Most best practices are based on one constraint: Claude's context window fills up fast, and performance degrades as it fills.**"

> "LLM performance degrades as context fills. When the context window is getting full, Claude may start 'forgetting' earlier instructions or making more mistakes. **The context window is the most important resource to manage.**"

### 2.5 The five named session failure patterns (best-practices) — DIRECTLY REUSABLE

> - "**The kitchen sink session.** You start with one task, then ask Claude something unrelated, then go back to the first task. Context is full of irrelevant information." → Fix: `/clear` between unrelated tasks.
> - "**Correcting over and over.** ... Context is polluted with failed approaches." → Fix: after two failed corrections, `/clear` and write a better prompt.
> - "**The over-specified CLAUDE.md.** If your CLAUDE.md is too long, **Claude ignores half of it because important rules get lost in the noise**." → Fix: "Ruthlessly prune. If Claude already does something correctly without the instruction, delete it or convert it to a hook."
> - "**The trust-then-verify gap.** Claude produces a plausible-looking implementation that doesn't handle edge cases." → Fix: always provide verification.
> - "**The infinite exploration.** You ask Claude to 'investigate' something without scoping it. Claude reads hundreds of files, filling the context." → Fix: scope narrowly or use subagents.

Also: "If you've corrected Claude more than twice on the same issue in one session, the context is cluttered with failed approaches."

### 2.6 Context cost by feature (features-overview, verbatim table)

| Feature | When it loads | What loads | Context cost |
|---|---|---|---|
| CLAUDE.md | Session start | Full content | **Every request** |
| Skills | Session start + when used | Descriptions at start, full content when used | Low (descriptions every request) |
| MCP servers | Session start | Tool names; full schemas on demand | Low until a tool is used |
| Code intelligence | After edits / on demand | Diagnostics, symbol locations | Low; reduces file reads elsewhere |
| Subagents | When spawned | Fresh context | Isolated from main session |
| Hooks | On trigger | Nothing (runs externally) | **Zero, unless hook returns output** |

> "Every feature you add consumes some of Claude's context. Too much can fill up your context window, but **it can also add noise that makes Claude less effective; skills may not trigger correctly, or Claude may lose track of your conventions**."

### 2.7 Reduce token usage (costs)
- "**Move instructions from CLAUDE.md to skills**... If it contains detailed instructions for specific workflows (like PR reviews or database migrations), **those tokens are present even when you're doing unrelated work**."
- "**Prefer CLI tools when available**: Tools like `gh`, `aws`, `gcloud`, and `sentry-cli` are still more context-efficient than MCP servers because they don't add any per-tool listing."
- "**Disable unused servers**: Run `/mcp` to see configured servers and disable any you're not actively using."
- Hooks as preprocessors: "Instead of Claude reading a 10,000-line log file to find errors, a hook can grep for `ERROR` and return only matching lines, **reducing context from tens of thousands of tokens to hundreds**."
- Cost benchmarks: "**~\$13 per developer per active day and \$150–250 per developer per month**, with costs remaining **below \$30 per active day for 90% of users**."
- Background token usage "typically under **\$0.04 per session**".
- "**Agent teams use approximately 7x more tokens** than standard sessions when teammates run in plan mode."
- `/usage` "**Behavior flags**: behaviors such as long context or cache misses, flagged when one accounts for **10% or more** of recent usage."
- Cache miss definition: "a request as a miss when the request re-processed **more than 5% and at least 2,000 tokens** of what it could have read from cache."
- Cache lifetime: 1 hour on subscription, drops to 5 minutes on usage credits / API key.

---

## 3. Agent Skills authoring

### 3.1 Progressive disclosure — the three levels with token costs
https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview

| Level | When loaded | **Token cost** | Content |
|---|---|---|---|
| **Level 1: Metadata** | Always (at startup) | **~100 tokens per Skill** | `name` and `description` from YAML frontmatter |
| **Level 2: Instructions** | When Skill is triggered | **Under 5k tokens** | SKILL.md body |
| **Level 3+: Resources** | As needed | **None until accessed** | Bundled files; scripts run via bash, only output enters context |

> "This lightweight approach means you can install many Skills **without context penalty**: until a Skill is triggered, only its name and description occupy context."

> "**No practical limit on bundled content**: Files don't consume context until accessed."

> "When Claude runs `validate_form.py`, **the script's code never loads into the context window**. Only its output consumes tokens."

Engineering post version (https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills):
> "the amount of context that can be bundled into a skill is **effectively unbounded**" when agents have filesystem + code execution.
> "By moving the form-filling instructions to a separate file, the skill author is able to keep the core of the skill lean."
Authoring principles named there: "Start with evaluation", "Structure for scale", "Think from Claude's perspective", "Iterate with Claude".

### 3.2 The 500-line rule
https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

> "**Keep SKILL.md body under 500 lines for optimal performance.** If your content exceeds this, split it into separate files using the progressive disclosure patterns."

Stated in the "Token budgets" section AND in the checklist AND in the Claude Code skills doc ("**Keep `SKILL.md` under 500 lines.** Move large reference material to separate files.").

> "Supporting files load only when Claude needs them, so **every line in `SKILL.md` is a recurring token cost**." (Claude Code skills doc)

### 3.3 Hard frontmatter limits

| Field | Limit | Source |
|---|---|---|
| `name` | **Max 64 characters**; lowercase letters/numbers/hyphens only; no XML tags; **cannot contain "anthropic" or "claude"** | platform best-practices + overview |
| `description` | **Max 1,024 characters**, non-empty, no XML tags | platform overview + best-practices |
| `description` + `when_to_use` combined (Claude Code) | **Capped at 1,536 characters** in skill listings | code.claude.com/docs/en/skills |
| `compatibility` | Max 500 characters | code.claude.com/docs/en/skills |

**Note a real discrepancy:** platform docs say `description` max 1,024 chars; Claude Code docs say `description` + `when_to_use` combined cap of 1,536 chars in listings (`skillListingMaxDescChars`, default 1,536). Different layers, different numbers.

### 3.4 Skill listing budget (Claude Code)
- "Skill listing budget: **scales at 1% of the model's context window**." (≈2,000 tokens at 200k)
- "When overflowed, Claude Code **drops descriptions starting with least-invoked skills**."
- Configurable: `skillListingBudgetFraction` (e.g. `0.02` = 2%) or `SLASH_COMMAND_TOOL_CHAR_BUDGET`.
- `skillOverrides` can set a skill to `"name-only"` (no description in listing).
- **AUDIT CHECK:** "Names always load, but **descriptions are shortened when there are many, which can strip the keywords Claude uses to decide whether a skill applies.** Keep descriptions short and lead with words a request would contain." (large-codebases doc)
- "**Put key use case first** — text may be truncated to fit context budgets."

### 3.5 Writing descriptions — verbatim guidance

> "**Always write in third person**. The description is injected into the system prompt, and inconsistent point-of-view can cause discovery problems."
> - Good: "Processes Excel files and generates reports"
> - Avoid: "I can help you process Excel files"
> - Avoid: "You can use this to process Excel files"

> "The description is critical for skill selection: Claude uses it to choose the right Skill from **potentially 100+ available Skills**."

> "The `description` field ... should include **both what the Skill does and when to use it**."

Good examples:
```
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
description: Analyze Excel spreadsheets, create pivot tables, generate charts. Use when analyzing Excel files, spreadsheets, tabular data, or .xlsx files.
description: Generate descriptive commit messages by analyzing git diffs. Use when the user asks for help writing commit messages or reviewing staged changes.
```

Bad examples (verbatim): `Helps with documents`, `Processes data`, `Does stuff with files`

Claude Code doc adds: "**Include trigger phrases** — words users naturally say when they need this skill" and "**Match user language** — don't use internal jargon if external terms are clearer."

From features-overview: "**If descriptions are vague or overlap, Claude may load the wrong skill or miss one that would help.**"

### 3.6 Naming conventions
> "Consider using **gerund form** (verb + -ing)": `processing-pdfs`, `analyzing-spreadsheets`, `managing-databases`, `testing-code`, `writing-documentation`.
> Acceptable: noun phrases (`pdf-processing`), action-oriented (`process-pdfs`).
> **Avoid**: "Vague names: `helper`, `utils`, `tools`"; "Overly generic: `documents`, `data`, `files`"; reserved words; "**Inconsistent patterns within your skill collection**".

### 3.7 Reference depth — AUDIT CHECK

> "**Keep references one level deep from SKILL.md.** All reference files should link directly from SKILL.md to ensure Claude reads complete files when needed."

Why: "Claude may **partially read files** when they're referenced from other referenced files. When encountering nested references, Claude might use commands like `head -100` to preview content rather than reading entire files, **resulting in incomplete information**."

> "For reference files **longer than 100 lines**, include a **table of contents** at the top. This ensures Claude can see the full scope of available information even when previewing with partial reads."

### 3.8 Concision — "the context window is a public good"

> "**The context window is a public good.** Your Skill shares the context window with everything else Claude needs to know."

> "**Default assumption: Claude is already very smart.** Only add context Claude doesn't already have. Challenge each piece of information:
> - 'Does Claude really need this explanation?'
> - 'Can I assume Claude knows this?'
> - '**Does this paragraph justify its token cost?**'"

Worked example: a concise PDF-extraction section is "~50 tokens"; the verbose version is "~150 tokens" — a 3x cost for zero added signal.

### 3.9 Degrees of freedom — the narrow-bridge/open-field analogy

> "Match the level of specificity to the task's **fragility and variability**."
- **High freedom** (text instructions): multiple valid approaches, context-dependent decisions.
- **Medium freedom** (pseudocode/parameterized scripts): a preferred pattern exists.
- **Low freedom** (specific scripts, few/no parameters): fragile/error-prone ops, consistency critical, exact sequence required.

> "**Narrow bridge with cliffs on both sides:** There's only one safe way forward. Provide specific guardrails and exact instructions."
> "**Open field with no hazards:** Many paths lead to success. Give general direction and trust Claude."

### 3.10 Anti-patterns (verbatim section)
- **Avoid Windows-style paths**: "Always use forward slashes in file paths, even on Windows."
- **Avoid offering too many options**: "'You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image, or...'" → "**Provide a default** (with escape hatch)."
- **Avoid assuming tools are installed.**
- **No "voodoo constants"** (Ousterhout's law): "`TIMEOUT = 47  # Why 47?`" → "**If you don't know the right value, how will Claude determine it?**"
- **MCP tool references must be fully qualified**: `ServerName:tool_name`. "Without the server prefix, Claude may fail to locate the tool, especially when multiple MCP servers are available."

### 3.11 Consistent terminology — AUDIT CHECK
> "Choose one term and use it throughout the Skill."
> Good — consistent: always "API endpoint", always "field", always "extract".
> Bad — inconsistent: mix "API endpoint"/"URL"/"API route"/"path"; mix "field"/"box"/"element"/"control"; mix "extract"/"pull"/"get"/"retrieve".
> "**Consistency helps Claude parse and follow instructions.**"

### 3.12 Evaluation-first
> "**Create evaluations BEFORE writing extensive documentation.** This ensures your Skill solves real problems rather than documenting imagined ones."
Five steps: identify gaps → create **three** scenarios → establish baseline → write minimal instructions → iterate.
> "Test with **Haiku, Sonnet, and Opus**." / "**At least three evaluations created.**"

### 3.13 The Claude A / Claude B loop
> "Work with one instance of Claude ('Claude A') to create a Skill that is used by other instances ('Claude B')."
Observation signals to watch (verbatim):
- "**Unexpected exploration paths:** Does Claude read files in an order you didn't anticipate?"
- "**Missed connections:** Does Claude fail to follow references to important files?"
- "**Overreliance on certain sections:** If Claude repeatedly reads the same file, consider whether that content should be in the main SKILL.md instead."
- "**Ignored content:** If Claude never accesses a bundled file, it might be unnecessary or poorly signaled."

### 3.14 The official checklist (verbatim) — REUSABLE AS AUDIT ITEMS

Core quality:
- [ ] Description is specific and includes key terms
- [ ] Description includes both what the Skill does and when to use it
- [ ] SKILL.md body is under 500 lines
- [ ] Additional details are in separate files (if needed)
- [ ] No time-sensitive information (or in "old patterns" section)
- [ ] Consistent terminology throughout
- [ ] Examples are concrete, not abstract
- [ ] File references are one level deep
- [ ] Progressive disclosure used appropriately
- [ ] Workflows have clear steps

Code and scripts:
- [ ] Scripts solve problems rather than defer to Claude
- [ ] Error handling is explicit and helpful
- [ ] No "voodoo constants" (all values justified)
- [ ] Required packages listed in instructions and verified as available
- [ ] Scripts have clear documentation
- [ ] No Windows-style paths (all forward slashes)
- [ ] Validation/verification steps for critical operations
- [ ] Feedback loops included for quality-critical tasks

Testing:
- [ ] At least three evaluations created
- [ ] Tested with Haiku, Sonnet, and Opus
- [ ] Tested with real usage scenarios
- [ ] Team feedback incorporated (if applicable)

### 3.15 Skill content lifecycle (Claude Code)
- "Content enters conversation as a **single message**" and "**Stays in context across later turns**".
- "**Not re-read** on subsequent turns — write **standing instructions, not one-time steps**." ← IMPORTANT AUTHORING RULE.
- Re-invocation with identical rendered content → short "already loaded" note; different content → full content appended again.
- `allowed-tools` permission grant **clears on next user message**.
- `disable-model-invocation: true` → description not in context at all; zero cost until `/name` invoked.
- `user-invocable: false` → hidden from `/` menu, Claude-only.

---

## 4. All concrete numeric thresholds found (consolidated)

| Number | What it governs | Source |
|---|---|---|
| **200 lines** | Target max per CLAUDE.md file | memory, features-overview, costs, steering blog |
| **4 MiB** | CLAUDE.md hard limit — larger files are **skipped entirely** | memory |
| **200 lines or 25 KB** | Auto-memory `MEMORY.md` startup load cutoff (whichever first) | memory, sub-agents |
| **4 hops** | Max recursive `@import` depth in CLAUDE.md | memory |
| **1,000 patterns / 4 MiB** | Brace-expansion budget for a rule's `paths:` list | memory |
| **500 lines** | Max SKILL.md body | platform best-practices, code skills doc |
| **~100 tokens** | Level-1 skill metadata cost per skill | platform overview |
| **Under 5k tokens** | Level-2 SKILL.md body target | platform overview |
| **64 chars** | Max skill `name` | platform overview/best-practices |
| **1,024 chars** | Max skill `description` (platform) | platform overview |
| **1,536 chars** | Max `description` + `when_to_use` in Claude Code listings (`skillListingMaxDescChars`) | code skills doc |
| **1% of context window** | Skill listing budget (`skillListingBudgetFraction`) | code skills doc |
| **5,000 tokens/skill, 25,000 total** | Skill body re-injection cap after compaction | context-window, code skills doc |
| **15,000 tokens** | Combined subagent descriptions before a startup warning | sub-agents |
| **20** | Max concurrent subagents (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`) | sub-agents |
| **3 layers** | Max subagent nesting depth below main | sub-agents |
| **5 files** | Files re-read after compaction (most recently modified) | context-window, effective-context-engineering |
| **5,000 tokens** | File size above which post-compaction re-read returns a path reference only | context-window |
| **1,000–2,000 tokens** | Target sub-agent summary size | effective-context-engineering |
| **10%** | Context-window fraction under which `ENABLE_TOOL_SEARCH=auto` preloads MCP schemas | context-window |
| **10%** | Share of recent usage at which `/usage` flags a behavior | costs |
| **25,000 tokens** | Default Claude Code tool-response truncation limit | writing-tools-for-agents |
| **100 lines** | Reference-file length above which a table of contents is required | platform best-practices |
| **3–5 examples** | For few-shot prompting | prompting best practices |
| **~30%** | Response-quality gain from putting queries at the END of long-context prompts | prompting best practices |
| **20k+ tokens** | Threshold for "long context prompting" techniques | prompting best practices |
| **200,000 tokens** | Default context window in Claude Code's own simulation | context-window |
| **39% / 29% / 84%** | Memory+context-editing gain / context-editing-alone gain / token reduction | claude.com/blog/context-management |
| **90.2%** | Multi-agent (Opus lead + Sonnet subagents) over single-agent Opus 4 | multi-agent-research-system |
| **80% / 95%** | Variance in browsing tasks explained by token usage / by tokens+tool calls+model | multi-agent-research-system |
| **4x / 15x** | Agents vs chat token use / multi-agent vs chat token use | multi-agent-research-system |
| **~7x** | Agent-team token use vs standard session (plan mode) | costs |
| **150,000 → 2,000 tokens (98.7%)** | Token saving from code execution vs preloading all MCP tool defs | code-execution-with-mcp |
| **50,000 tokens** | Extra tokens from a 2-hour transcript flowing through the model twice | code-execution-with-mcp |
| **8** | Consecutive Stop-hook blocks before Claude Code overrides and ends the turn | best-practices |
| **~$13/day, $150–250/month, <$30/day for 90%** | Enterprise per-developer cost | costs |

---

## 5. Tool descriptions, instruction conflicts, ambiguity as root cause

### 5.1 "Writing effective tools for agents"
https://www.anthropic.com/engineering/writing-tools-for-agents

- "**More tools don't always lead to better outcomes.**" Build "a few thoughtful tools targeting specific high-impact workflows" rather than wrapping every API endpoint.
- **The ambiguity failure mode, stated directly:** "**When tools overlap in function or have a vague purpose, agents can get confused about which ones to use.**"
- Namespacing: prefix by service (`asana_search`, `jira_search`) or resource (`asana_projects_search`). "Selecting between prefix- and suffix-based namespacing [has] non-trivial effects on tool-use evaluations."
- "Return only high signal information back to agents"; prioritize "contextual relevance over flexibility."
- Semantic identifiers: "merely resolving arbitrary alphanumeric UUIDs to more semantically meaningful and interpretable language... **significantly improves Claude's precision in retrieval tasks by reducing hallucinations**."
- `response_format` enum (`"concise"` vs `"detailed"`): example Slack response 206 tokens detailed vs **72 tokens** concise.
- "For Claude Code, tool responses [are restricted] to **25,000 tokens by default**." Truncation should carry steering text toward "many small and targeted searches."
- "**Tool descriptions are one of the most effective methods for improving tools**" since they load into context. Claude Sonnet 3.5 hit SOTA on SWE-bench after "precise refinements to tool descriptions."
- Eval metrics to collect: "total runtime of individual tool calls and tasks, the total number of tool calls, the total token consumption, and tool errors."

### 5.2 "Building effective agents"
https://www.anthropic.com/engineering/building-effective-agents

- Workflows = "LLMs and tools orchestrated through predefined code paths"; agents = "LLMs dynamically direct their own processes and tool usage."
- "**Find the simplest solution possible, and only increase complexity when needed.**"
- Agents "trade latency and cost for better task performance"; add complexity only "when it demonstrably improves outcomes."
- Three principles: **simplicity**, **transparency** ("explicitly showing the agent's planning steps"), and **ACI** — "**carefully craft your agent-computer interface through thorough tool documentation and testing**"; "invest just as much effort in creating good agent-computer interfaces [as human-computer interfaces]."
- Appendix (prompt-engineering your tools):
  - "Give the model enough tokens to 'think' before it writes itself into a corner."
  - "Keep the format close to what the model has seen naturally occurring in text on the internet."
  - **Poka-yoke**: change "arguments so that it is harder to make mistakes" (absolute filepaths eliminated relative-path errors on SWE-bench).
  - Write descriptions like "**a great docstring for a junior developer**" — example usage, edge cases, input requirements, **clear boundaries between tools**.
  - "Run many example inputs in our workbench to see what mistakes the model makes, and iterate."

### 5.3 The "brilliant but new employee" framing
https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

> "Think of Claude as a **brilliant but new employee who lacks context on your norms and workflows**. The more precisely you explain what you want, the better the result."

> "**Golden rule:** Show your prompt to a colleague with minimal context on the task and ask them to follow it. **If they'd be confused, Claude will be too.**"
← **This is THE test for an instruction-quality audit.**

Other relevant items:
- "Provide instructions as sequential steps using numbered lists or bullet points when the order or completeness of steps matters."
- "Providing context or motivation behind your instructions... can help Claude better understand your goals." Example: `NEVER use ellipses` (less effective) vs `Your response will be read aloud by a text-to-speech engine, so never use ellipses since the text-to-speech engine will not know how to pronounce them.` (more effective). "**Claude is smart enough to generalize from the explanation.**"
- XML tags: "help Claude parse complex prompts unambiguously, especially when your prompt mixes instructions, context, examples, and variable inputs... **reduces misinterpretation**." Use "consistent, descriptive tag names."
- Examples: "3–5 examples for best results", wrapped in `<example>`/`<examples>` tags; "Relevant, Diverse, Structured."
- Long context: "**Put longform data at the top**... Queries at the end can improve response quality by **up to 30 percent** in tests."
- Tool triggering: "If you say 'can you suggest some changes,' Claude will sometimes provide suggestions rather than implementing them."
- **Overtriggering warning** (see §7): "Claude Opus 4.5 and Claude Opus 4.6 are also more responsive to the system prompt than previous models. If your prompts were designed to reduce undertriggering on tools or skills, **these models may now overtrigger. The fix is to dial back any aggressive language.**"
- Overeagerness / overengineering damping prompt provided verbatim (scope, documentation, defensive coding, abstractions).
- Subagent overuse: "Claude Opus 4.6 has a **strong predilection for subagents** and may spawn them in situations where a simpler, direct approach would suffice... Claude Opus 5 also delegates to subagents more readily than prior models."

### 5.4 Multi-agent research system failure modes
https://www.anthropic.com/engineering/multi-agent-research-system

Named early failure modes:
- Spawning excessive subagents for simple queries
- Endless web searching for nonexistent sources
- Agent distraction through excessive updates
- "**Duplicated work due to vague task descriptions**" ← ambiguity as root cause again
- Selection of SEO-optimized content over authoritative sources

Delegation requirement: "Each subagent needs **an objective, an output format, guidance on the tools and sources to use, and clear task boundaries**."

Effort scaling: simple queries = 1 agent, 3–10 tool calls; direct comparisons = 2–4 subagents, 10–15 calls each; complex research = 10+ subagents.

"Agents maintain state across many turns; **minor system failures can be catastrophic**."
"Agents save plans to memory when context approaches 200,000 tokens."
Self-improvement: Claude identifying its own failures and suggesting tool-description improvements gave a "**40% decrease in task completion time**."

---

## 6. Documentation staleness / keeping instructions in sync

### 6.1 The explicit staleness playbook (large-codebases) — BEST SINGLE SOURCE
https://code.claude.com/docs/en/large-codebases

> "A few ways to **keep the files current** as the codebase and models change:
> - **Review in pull requests**: treat CLAUDE.md edits like any other documentation change so conventions track the code
> - **Revisit after major model releases**: **instructions that worked around an older model's limitation may become overhead once a newer model handles the case on its own.** For example, a rule that forces single-file refactors can be deleted once the limitation is gone
> - **Add a Stop hook that proposes updates**: a `Stop` hook receives the path to the session transcript when Claude finishes responding, so a script can review the session and propose CLAUDE.md updates while the gap it exposed is fresh"

### 6.2 Governance decay in monorepos (large-codebases)
> "Per-directory CLAUDE.md files can become hard to govern as the codebase grows. **Conventions drift, files go stale, and no one owns the root.**"
Fix: move conventions out of always-loaded CLAUDE.md into skills / plugins / MCP servers.

### 6.3 Root-file dilemma (large-codebases)
> "a single CLAUDE.md at the repository root tends to **either grow to cover every subsystem's conventions**, costing context on instructions unrelated to the current task, **or stay too generic to be useful**."

### 6.4 Time-sensitive content in skills (platform best-practices)
> "**Avoid time-sensitive information.** Don't include information that will become outdated."
Bad: "If you're doing this before August 2025, use the old API. After August 2025, use the new API."
Good: a `## Current method` section plus a collapsed `## Old patterns` `<details>` block. "The old patterns section provides historical context without cluttering the main content."

### 6.5 Finding unused skills — TELEMETRY-BASED STALENESS DETECTION (large-codebases)
> "To find which skills go unused, enable the OpenTelemetry logs exporter and set `OTEL_LOG_TOOL_DETAILS=1` so skill names are recorded verbatim instead of redacted. The `skill_activated` event records every invocation in its `skill.name` attribute, and `invocation_trigger` records whether a command, Claude, or a nested skill invoked it, **which tells you what to consolidate or retire**."

### 6.6 The auto-memory `modified` timestamp (memory)
> "When Claude writes a memory file that begins with YAML frontmatter, Claude Code records the write time in a `modified` frontmatter field as an ISO 8601 timestamp. **The timestamp shows how current the fact is, both to you and to Claude** when it reads the memory back."

### 6.7 The consolidation instruction Claude Code gives itself (memory)
When MEMORY.md nears the 200-line / 25KB limit: "Claude Code reminds Claude to shorten it: **keep one line per entry, move detail into topic files, and merge or drop stale entries.**"

---

## 7. Where Anthropic disagrees with itself / has shifted

1. **"IMPORTANT"/"YOU MUST" emphasis.**
   - `code.claude.com/docs/en/best-practices` (current): "If Claude keeps skipping one instruction, **add emphasis such as 'IMPORTANT'** to that line alone."
   - `platform.claude.com/.../claude-prompting-best-practices` (current): "Where you might have said '**CRITICAL: You MUST use this tool when...**', you can use **more normal prompting** like 'Use this tool when...'" because Opus 4.5/4.6 **overtrigger**.
   - The original 2025 `claude-code-best-practices` blog post recommended tuning CLAUDE.md with "IMPORTANT" and "YOU MUST" to improve adherence; that language has been softened in the doc rewrite to "add emphasis... to that line alone" plus the dilution warning. **Net shift: emphasis is now a scalpel, not a hammer, and overuse is itself the failure.**

2. **CLAUDE.local.md deprecation.**
   Earlier docs deprecated `CLAUDE.local.md` in favor of imports. The current memory doc restores it as a first-class scope with its own row in the location table and explicit `/init` support (`CLAUDE_CODE_NEW_INIT=1` "personal option"). **Any audit that flags CLAUDE.local.md as deprecated is out of date.**

3. **Imports as a size fix.**
   Splitting via `@path` is presented as an organizational tool in one place and explicitly disclaimed as a context fix in another: "**Splitting into `@path` imports helps organization but doesn't reduce context**, since imported files load at launch." Path-scoped rules and skills are the real fix. Easy for an auditor to get wrong.

4. **JIT retrieval vs pre-loading.**
   The context-engineering post argues hard for just-in-time retrieval and progressive disclosure, then concedes the hybrid: "Claude Code... CLAUDE.md files pre-loaded; glob/grep for just-in-time navigation" and "**the simplest thing that works**." So pre-loading is not condemned — the guidance is about *what* is worth pre-loading.

5. **Subagents: universally good vs overused.**
   - best-practices/features-overview/costs: use subagents aggressively for investigation and verbose ops.
   - prompting best practices: "Claude Opus 4.6 has a strong predilection for subagents and **may spawn them in situations where a simpler, direct approach would suffice**"; Opus 5 "also delegates to subagents more readily." Provides a damping prompt.
   - Cost side: subagents/agent teams cost ~7x–15x more tokens. So "use a subagent" is a context-window optimization that is a token-cost *pessimization*.

6. **Skill description limits differ by surface.** Platform: `description` ≤ 1,024 chars. Claude Code: `description` + `when_to_use` ≤ 1,536 chars in listings, with further dynamic truncation under the 1% listing budget. An author hitting the platform limit can still be silently truncated in Claude Code.

7. **"Minimal does not necessarily mean short."** (context-engineering post) sits in tension with the blunt "under 200 lines" / "under 500 lines" rules elsewhere. The reconciliation Anthropic actually offers is the `/doctor` rubric: cut what's derivable from the codebase, keep pitfalls/rationale/conventions-that-differ-from-defaults. **Length is a proxy; derivability is the real test.**

8. **Blog post → doc page migration.** "Claude Code best practices" is no longer an engineering blog post; it is a doc. Its content has been substantially rewritten (e.g., the old "tune your CLAUDE.md files" / "prompt improver" advice is gone; new material on `/goal`, Stop hooks, auto mode, `/batch`, adversarial review). Any skill quoting the 2025 blog post is quoting a superseded source.

---

## 8. Directly actionable audit checks distilled

### CLAUDE.md / memory
1. **Line count** > 200 per file → flag. Report per-file and aggregate across the whole loaded hierarchy (root + ancestors + `.claude/CLAUDE.md` + CLAUDE.local.md + unscoped `.claude/rules/*.md` + all `@` imports transitively to depth 4).
2. **File size** > 4 MiB → CRITICAL, file is silently skipped entirely.
3. **Derivable content**: directory layouts / file trees, dependency lists, architecture overviews, file-by-file descriptions, restatements of `package.json` scripts → cut (the `/doctor` rubric).
4. **Self-evident content**: "write clean code", standard language conventions, generic best practices → cut.
5. **Contradictions** across CLAUDE.md, nested CLAUDE.md, `.claude/rules/`, AGENTS.md, `.cursorrules`, `.github/copilot-instructions.md` → "Claude may pick one arbitrarily."
6. **Emphasis dilution**: count `IMPORTANT`/`CRITICAL`/`YOU MUST`/`NEVER`/`ALWAYS`/bold/caps lines. More than a handful → none stands out.
7. **Enforcement mismatch**: "always X" / "never Y" / "every time" / "before every commit" → should be a hook or a permissions deny rule, not memory.
8. **Procedures in memory**: numbered multi-step runbooks > ~10 lines → should be a skill.
9. **Path-specific content in a global file**: instructions that only apply to one directory → per-directory CLAUDE.md or a path-scoped rule.
10. **Vagueness**: unverifiable instructions ("format properly", "keep it organized", "test your changes") → rewrite concretely.
11. **Imports**: count transitive `@` imports and their line totals — they all load at launch; imports are NOT a size fix. Check depth ≤ 4. Check for `@path` mentions inside backticks that were meant to import (or vice versa).
12. **AGENTS.md present without a CLAUDE.md bridge** (import or symlink) → Claude Code never reads it.
13. **Duplication between AGENTS.md and CLAUDE.md** (copied rather than imported) → divergence risk.
14. **HTML comments**: maintainer notes can be moved into `<!-- -->` for free.
15. **Frequently-changing facts** (version numbers, dates, "as of X", team member names, ticket IDs) → time-sensitive, will go stale.
16. **Unscoped `.claude/rules/*.md`** cost the same as CLAUDE.md every session → candidates for `paths:` frontmatter.
17. **`MEMORY.md`** > 200 lines or > 25 KB → everything past the cutoff is silently dropped.

### Skills
18. **SKILL.md body** > 500 lines → split.
19. **`name`** > 64 chars, contains uppercase/underscores, contains "claude" or "anthropic", or is vague (`helper`, `utils`, `tools`, `data`) → flag.
20. **`description`** missing, > 1,024 chars, written in first/second person, missing a "Use when..." trigger clause, or lacking natural trigger keywords → flag.
21. **Overlapping descriptions** across skills → Claude "may load the wrong skill or miss one."
22. **Skill-listing budget**: total description bytes across all discoverable skills vs 1% of context window (~2,000 tokens at 200k) → over budget means silent truncation of the least-invoked skills' descriptions.
23. **Reference depth** > 1 hop from SKILL.md → partial reads.
24. **Reference files** > 100 lines without a table of contents.
25. **Most important instructions not near the top of SKILL.md** → post-compaction truncation keeps only the first 5,000 tokens.
26. **Time-sensitive content** not quarantined in an "Old patterns" section.
27. **Inconsistent terminology** within a skill.
28. **One-time steps written as if the skill will be re-read** — skills are not re-read on later turns.
29. **Windows-style backslash paths.**
30. **MCP tool names without a `ServerName:` prefix.**

### Subagents
31. **Combined subagent descriptions** > 15,000 tokens → startup warning.
32. Subagent `description` without clear delegation triggers; missing objective/output-format/tool-guidance/boundaries.

### Cross-cutting
33. **The colleague test**: "Show your prompt to a colleague with minimal context... If they'd be confused, Claude will be too."
34. **The deletion test**: "For each line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it."
35. **The token-cost test**: "Does this paragraph justify its token cost?"
36. **Model-workaround rot**: rules written to compensate for older-model limitations.
37. **Always-on token budget**: sum CLAUDE.md + unscoped rules + skill descriptions + MCP tool names and express as a % of the 200k window (Anthropic's own reference session is ~7,850 tokens ≈ 3.9%, with CLAUDE.md ≈ 2,120).

---

## 9. Full source URL list

**Engineering blog**
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://www.anthropic.com/engineering/writing-tools-for-agents
- https://www.anthropic.com/engineering/building-effective-agents
- https://www.anthropic.com/engineering/multi-agent-research-system
- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- https://www.anthropic.com/engineering/code-execution-with-mcp
- https://www.anthropic.com/engineering/claude-code-best-practices → **308 → https://code.claude.com/docs/en/best-practices**

**Claude blog**
- https://claude.com/blog/context-management (← anthropic.com/news/context-management)
- https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more
- https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start (referenced, not fetched)

**Claude Code docs (code.claude.com/docs/en/...)**
- /memory · /best-practices · /context-window · /skills · /sub-agents · /features-overview · /costs · /large-codebases · /mcp
- Index: https://code.claude.com/docs/llms.txt

**Platform docs (platform.claude.com/docs/en/...)**
- /agents-and-tools/agent-skills/overview
- /agents-and-tools/agent-skills/best-practices
- /build-with-claude/prompt-engineering/claude-prompting-best-practices (← .../be-clear-and-direct redirects here)

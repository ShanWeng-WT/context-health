# Sources and design provenance

Why this skill checks what it checks. Every principle below traces to a source, so
when agent practice moves on you can find the load-bearing claim and change it rather
than guessing what the skill was for.

**Researched:** 2026-09-08, by five parallel agents covering Anthropic artifacts on
disk, Anthropic documentation and engineering blog, OpenAI documentation and cookbook,
community practice current to 2026, and detection mechanics.

**Verification status.** Claims marked ✅ were confirmed directly against a primary
source during research or tested in code here. Claims marked ⚠️ come from a single
secondary source and are used only as soft guidance, never as the sole basis for a
finding. Numbers change faster than principles — re-check §4 first.

---

## 1. Principles adopted

### From Anthropic

**Context is a finite attention budget, not a container.** The goal is "the smallest
possible set of high-signal tokens that maximize the likelihood of some desired
outcome"; recall degrades as tokens grow, on a gradient rather than a cliff. ✅
→ *Drives:* the always-on ledger as the report's headline number.
[effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

**Bloat causes rule-ignoring, not just cost.** Over-specified instruction files mean
"Claude ignores half of it because important rules get lost in the noise"; the stated
diagnostic is that a rule being repeatedly disobeyed usually means the file is too
long. ✅
→ *Drives:* the framing that dilution is a **correctness** problem, and the skill's
symptom-based triggers ("the agent ignores my instructions").
[best-practices](https://code.claude.com/docs/en/best-practices)

**The deletion test.** For each line, ask whether removing it would cause mistakes. ✅
→ *Drives:* the load-bearing test, probe 1.

**The derivability rubric.** Cut what Claude can derive from the codebase — directory
layouts, dependency lists, architecture overviews; keep pitfalls, rationale, and
conventions that differ from tool defaults. ✅
→ *Drives:* catalogue D1 and the protect list. This is the single most useful
keep/cut rule found anywhere, and it is Anthropic's own trim rubric.
[memory](https://code.claude.com/docs/en/memory)

**Imports do not reduce context.** Imported files load at launch. ✅
→ *Drives:* ledger import resolution; catalogue T2. Widely believed otherwise, which
makes it a high-value check.

**Instruction files are advisory, not enforcement.** A rule in CLAUDE.md is a request,
not a guarantee; guardrails belong in hooks and permissions. ✅
→ *Drives:* catalogue S2, flagged as the highest-leverage recommendation available.

**Emphasis dilutes.** "If you emphasize many lines, none of them stands out." ✅
→ *Drives:* the emphasis-ratio detector.

**Contradictions resolve arbitrarily.** Claude "may pick one arbitrarily." ✅
→ *Drives:* the whole Conflicting harm class.

**Progressive disclosure.** Skill bodies cost nothing until used; only name and
description are always-on. ✅ → *Drives:* the two-tier model and "move down a tier".

**Re-check after model releases.** Instructions written around an older model's
limitation become overhead once a newer model handles the case natively. ✅
→ *Drives:* catalogue D5, the model-cruft detector. Rarely checked by anyone.
[large-codebases](https://code.claude.com/docs/en/large-codebases)

**Ambiguity is the root cause of agent failure.** If a human engineer cannot say which
of two tools applies, an agent cannot do better. ✅ → *Drives:* catalogue D8.

### From OpenAI

**Contradiction costs more than under-specification.** GPT-5-class models expend
reasoning "searching for a way to reconcile the contradictions rather than picking one
instruction at random"; conflicting rules "create more instability than missing
detail." ✅
→ *Drives:* Conflicting ranked second only to Misleading, above all dilution.
[gpt-5_prompting_guide](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide)

**Diagnose and patch as separate steps.** OpenAI's audit protocol: first name the
failure mode, quote the exact offending lines, and explain the causal link; only then
patch, and "do not redesign the agent from scratch — prefer small, explicit edits." ✅
→ *Drives:* the report-never-repair rule, the required quote-plus-evidence fields, and
"surgical edits over rewrites". Adopted with one departure: the causal link is *held*
rather than written. A finding's claim, quote and evidence carry the mechanism for a
reader who already knows the repo, and spelling it out turned every P1 into four
paragraphs. The reader who wants it asks, and the answer is better for being scoped to
what they asked.
[gpt-5-1_prompting_guide](https://cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide)

**Audit your instruction files — vendor advice, not just ours.** "We strongly recommend
auditing skills and other files accessible to your model for instructions that could
influence its behavior," because "unclear or conflicting guidance in a skill file may
cause the model to pause and block work early." ✅
→ *Drives:* the skill's existence, and the inclusion of skills and subagent prompts in
scope rather than only CLAUDE.md.
[gpt-6-astra](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra)

**Trim/keep lists.** Trim repeated statements of a rule, examples that don't change
behavior, and process instructions for behavior the model already does reliably. Keep
success criteria, stopping conditions, safety and permission constraints, and routing
rules that depend on context. ✅ → *Drives:* the cut list and protect list.

**Absolutes should be true invariants.** Reserve ALWAYS/NEVER/must for real invariants;
repeated caution language causes over-pausing — a behavioral harm, not just token
cost. ✅ → *Drives:* catalogue D3.

**Lean prompts measurably win.** OpenAI's internal coding-agent evals report 10–15%
score gains with 41–66% fewer tokens from simplification. ⚠️ (single source; used as
motivation, never as a finding.)

**Commands in instruction files are executed, not just read.** ✅
→ *Drives:* dead commands (M1) rated Misleading rather than merely stale.

**Prefix stability matters.** Dynamic content near the top of an always-on file busts
the cached prefix for everything after it. ✅ → *Drives:* catalogue S6.

**Do not flag terseness as under-specification.** OpenAI recommends *less* specification
for reasoning models and warns examples can hurt; Anthropic leans example-rich. ✅
→ *Drives:* an explicit non-finding in the calibration list.

### From community practice (2026)

**The long-context failure taxonomy** — poisoning, distraction, confusion, clash. ✅
→ *Drives:* the four harm classes, renamed to be actionable (Misleading, Diluting,
Costly, Conflicting).
[dbreunig.com](https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html)

**Severity ordering: incorrect > missing > noisy.** ✅
→ *Drives:* the P1/P2/P3 scheme, and the inclusion of a Missing section so the audit
is not purely subtractive. **Deviation:** the ordering is kept for *correctness*
harms, but "noisy" is not floored at P3 here — a measured, recoverable cut of ≥2k
always-on tokens reaches P1, because the source ranks harm *kinds* and says nothing
about magnitude, and a per-turn tax paid forever is not a footnote.
[humanlayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md)

**Context rot is empirically measured**, across 18 models, and even a single distractor
degrades retrieval. ✅ [research.trychroma.com/context-rot](https://research.trychroma.com/context-rot)

**Specificity is verifiability.** "Use 2-space indentation", not "format code
properly." ✅ → *Drives:* catalogue D2 and the vague-imperative check.

**Never send an LLM to do a linter's job.** ⚠️ → *Drives:* catalogue D6, softened by
Anthropic's carve-out for conventions that differ from defaults.

**Usage is not value.** Invocation counts do not say whether a skill improved the
result. ✅ → *Drives:* T5 reported as a question, not a defect.

### From software-design literature

**Comments should say what the code cannot, in different words.** Interface behaviour,
data-structure meaning, cross-module dependencies. ✅ (Ousterhout)
→ *Drives:* probe 3 and the protect list.
[Ousterhout on comments](https://web.stanford.edu/~ouster/cgi-bin/cs190-spring15/lecture.php?topic=comments)

**Comment/code inconsistency correlates with bug-introducing commits** (~1.5×). ⚠️
(single paper) → *Drives:* M7's severity. [arXiv 2409.10781](https://arxiv.org/abs/2409.10781)

**Both comment camps agree on the same four cases** — restating comments,
commented-out code, changelog comments, contradicting comments. ✅
→ *Drives:* confining comment findings to that overlap, so the audit does not take a
side in a live debate.

---

## 2. Design decisions and their reasons

| Decision | Why |
|---|---|
| Report, never edit | OpenAI's two-call protocol; and a context file's lines usually encode reasons invisible from inside the repo |
| Always-on vs on-demand as the organizing axis | A doc loaded on demand can repeat itself; an always-on prefix cannot. Makes severity derivable rather than asserted |
| Scripts first, reading second | An audit that reads the whole repo to find bloat *is* the bloat |
| Every finding needs a re-runnable command | Prevents the plausible-sounding hallucinated finding, the main failure mode of a prose-judging audit |
| Traps co-located with detectors | The FP trap is only useful at the moment of judging that finding |
| Explicit "leave this alone" section | Without it an audit reads as a mandate to delete, and users prune rationale along with noise |
| Token cost as a peer harm, ranked by size | Reduction is a stated goal of the audit, and cost is the one harm that arrives with a number attached — so it ranks on magnitude rather than sitting below the correctness harms. Bounded by the load-bearing test: a cut is *recoverable* only when every line in it fails that test, and the default recommendation is *salvage* (compress, move a tier, merge copies) so the tokens come back without the knowledge going with them |
| Comment sweep on by default | Code comments are part of the agent-facing prose the audit exists to judge; leaving them behind a flag meant the comment half of the rubric usually went unused. Cost is bounded — tracked source files only, capped at 4000 |
| Confidence separate from severity | A high-severity finding you are 60% sure of is still worth reporting — but say so |
| Missing section | Sources agree missing information outranks noise, yet every audit tool found was purely subtractive |
| Disagreements surfaced, not resolved | Several debates are genuinely open; a repo on the far side of one may be there deliberately |

---

## 3. Deliberate non-goals

- **Code quality, architecture, naming, formatting.** Different review. Code is
  evidence here, never subject.
- **Auto-fixing.** Diagnosis only.
- **Optimizing for shorter.** The target is useful information per token, which
  sometimes means recommending *more* context.
- **Runtime transcript backtesting.** Session transcripts could prove a rule was
  violated in N of the last M sessions — the strongest possible evidence for an
  unenforced instruction. Not implemented; the most promising extension.

---

## 4. Numeric constants — check these first when updating

Used in `scripts/ledger.py`. All vendor-published and therefore perishable.

| Constant | Value | Source |
|---|---|---|
| `@import` depth limit | 4 hops | code.claude.com/docs/en/memory |
| CLAUDE.md line target | 200 | code.claude.com/docs/en/memory |
| CLAUDE.md hard limit | 4 MiB (file skipped **entirely**) | code.claude.com/docs/en/memory |
| MEMORY.md cutoff | first 200 lines or 25 KB | code.claude.com/docs/en/memory |
| Skill listing budget | 1% of context window | code.claude.com/docs/en/skills |
| Skill entry cap | 1,536 chars (name+description) | code.claude.com/docs/en/skills |
| SKILL.md body target | 500 lines | code.claude.com/docs/en/skills |
| AGENTS.md merged chain cap | 32 KiB (`project_doc_max_bytes`) | learn.chatgpt.com config reference |
| Token estimate | chars / 4 | standard heuristic; ±15% prose, under-counts code and CJK |

**Documentation has moved.** Claude Code docs are now at `code.claude.com/docs/en/*`
(was `docs.claude.com/en/docs/claude-code/*`), and the 2025 "Claude Code best
practices" blog post now redirects to `code.claude.com/docs/en/best-practices` with
substantially rewritten content. OpenAI's `developers.openai.com/codex/*` redirects to
`learn.chatgpt.com/docs/*`. Any guidance quoting the old URLs is quoting a superseded
source.

---

## 5. Detector calibration record

Precision was tuned against a real production monorepo; recall against a fixture with
planted defects. Numbers worth keeping because they show how noisy the naive versions
were:

| Detector | Naive | Tuned | What fixed it |
|---|---|---|---|
| `refs` | 132 findings, ~0 true | 0 on that repo, 4/4 on fixture | strip URLs; exclude vendored docs and changelogs; require a multi-segment path whose parent exists |
| `commands` | 30, ~24 false | 4 | match only inside code spans and fences, command must start the line — `make` matches English prose otherwise |
| `conflicts` | 32, mostly TOC-vs-heading | 1 | skip headings, TOC entries and tables; exclude files inside skill folders from the always-on set |
| `external` | 5 findings, 4 false | 1, the true positive | require the fetch verb and a live URL in the same few lines; exclude placeholder hosts, pinned URLs, and negated lines — "NEVER fetch raw files from GitHub" is advice *against* the defect |
| whole sweep | 233 candidates | 15 | the above, combined |

The lesson generalizes: **a detector that fires on a well-maintained repo is broken.**
Tune against a repo you believe is healthy, then confirm recall against planted
defects.

And its converse, learned the harder way in iteration 3: **a check with no detector
behind it will produce a confident false negative.** Iteration 2 added the fetch-and-obey
question as prose guidance in the process. All three runs dutifully reported on it, and
the one run facing a real instance declared the category benign — a 1 KB stub reads as
trivial, so it got skimmed. Prose told the agent to look; it did not give it anything to
look *with*. The `external` detector exists because of that failure. A clean verdict
carries authority, so a check that can only be performed by skimming is worse than no
check at all.

---

## 5b. Evaluation record

Three cases, each run with and without the skill: an explicit audit of a real
production monorepo, a symptom-led request ("Claude keeps ignoring my CLAUDE.md") on a
fixture with planted defects, and a deliberately healthy repo whose *code* is ugly, to
test restraint and the scope boundary.

Iteration 1: **100% with skill, 91.7% baseline.** The baseline was strong — a capable
agent finds most planted defects unaided — so the interesting result is *where* the
conditions separated:

- **Token accounting.** The word "token" appeared zero times in the baseline's
  production-repo report; all sizing was in bytes. Only the skill produced a tiered
  ledger and a percentage of the window.
- **Scope discipline.** Both runs noticed a stale dependency pin. The skill filed it
  under Out of scope; the baseline made it a work item and additionally performed an
  uninvited dead-code review. Same observation, opposite handling.
- **Factual precision.** Skill: 25 symlinks, correct line numbers, emphasis ratio
  exactly right. Baseline: 26 symlinks (wrong), wrong line number, wrong ratio.
- **Loading-model correctness.** The baseline claimed unscoped `.claude/rules/*.md`
  "probably never loads" and recommended adding an `@` import — wrong, and it
  propagated into a bad recommendation. This is the class of error the ledger exists
  to prevent.

What the baseline caught and the skill missed — all fixed in iteration 2 by adding
catalogue M9, T6, T7, S7, S8 and the on-demand ownership questions in step 1: a stub
file instructing the agent to fetch and obey unpinned remote content; vendored context
outweighing authored context 4.4x, including generated build artifacts; an orphaned
lockfile; and the team's own skills sitting where the tool never scans.

Also fixed in iteration 2: the report ran long on a healthy repo because P3s got both
a table row and a prose section, so the proportionality rule was made binding; and one
run reported the *session's* git HEAD instead of the audited repo's, so the skill now
requires `git -C <repo>`.

**Method note.** Baseline runs need the skill genuinely uninstalled, not merely
unmentioned — otherwise the control auto-triggers it and the comparison is worthless.

**Iteration 3 changed the deliverable, so the scores above predate the current
assertions.** The report became a file with a summary in chat, and the per-finding
mechanism paragraph was dropped, leaving four fields. Three assertions moved with it:
the no-edit rule now permits the report file itself and forbids only edits to existing
ones; the "explains the mechanism" assertion on the rotted-repo case became a
severity-ranking assertion, since the skill now scores worse for satisfying the old
wording; and both contract rules are asserted across all three cases. Re-run before
citing 0.97 against the current suite.

## 6. Full source list

**Anthropic** — [effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) ·
[writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) ·
[building effective agents](https://www.anthropic.com/engineering/building-effective-agents) ·
[multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) ·
[agent skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) ·
docs: [memory](https://code.claude.com/docs/en/memory) ·
[best-practices](https://code.claude.com/docs/en/best-practices) ·
[skills](https://code.claude.com/docs/en/skills) ·
[context-window](https://code.claude.com/docs/en/context-window) ·
[sub-agents](https://code.claude.com/docs/en/sub-agents) ·
[large-codebases](https://code.claude.com/docs/en/large-codebases) ·
[agent skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

**OpenAI** — [agents.md](https://agents.md/) ·
[AGENTS.md guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md) ·
[customization overview](https://learn.chatgpt.com/docs/customization/overview) ·
[config reference](https://learn.chatgpt.com/docs/config-file/config-reference) ·
[GPT-5 prompting guide](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide) ·
[GPT-5.1 prompting guide](https://cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide) ·
[Codex prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) ·
[Sol prompt guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6) ·
[GPT-6 Astra](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra) ·
[prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching) ·
[function calling](https://developers.openai.com/api/docs/guides/function-calling) ·
[ExecPlans](https://cookbook.openai.com/articles/codex_exec_plans)

**Research** — [Context Rot, Chroma](https://research.trychroma.com/context-rot) ·
[Lost in the Middle](https://arxiv.org/abs/2307.03172) (2023, partly superseded) ·
[comment-code inconsistency](https://arxiv.org/abs/2010.01625) ·
[inconsistent changes and bugs](https://arxiv.org/abs/2409.10781)

**Practitioner** — [how contexts fail](https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html) ·
[writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md) ·
[advanced context engineering](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents) ·
[12-factor agents](https://github.com/humanlayer/12-factor-agents) ·
[Manus context engineering](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) ·
[don't build multi-agents](https://cognition.com/blog/dont-build-multi-agents) ·
[LangChain context engineering](https://www.langchain.com/blog/context-engineering-for-agents) ·
[Simon Willison](https://simonwillison.net/2025/Jun/27/context-engineering/) ·
[progressive disclosure / bloat](https://alexop.dev/posts/stop-bloating-your-claude-md-progressive-disclosure-ai-coding-tools/) ·
[agent-optimized ADRs](https://www.actual.ai/blog/agent-optimized-adrs)

**Other tools** — [Cursor rules](https://cursor.com/docs/rules) ·
[Copilot repository instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)

**Design literature** — [Ousterhout on comments](https://web.stanford.edu/~ouster/cgi-bin/cs190-spring15/lecture.php?topic=comments) ·
[Google eng-practices](https://google.github.io/eng-practices/review/reviewer/looking-for.html) ·
[Necessary Comments](https://blog.cleancoder.com/uncle-bob/2017/02/23/NecessaryComments.html)

**Prior art reviewed** — Anthropic's bundled `context-health` skill (read via its
SKILL.md; its reference files were not retrievable on this machine), `prompt-audit`
(from `anthropics/skills`, `skills/claude-api/shared/prompt-audit.md`), the
`comment-analyzer` subagent from the pr-review-toolkit plugin, `claude-md-improver`,
`consolidate-memory`, [claude-md-doctor](https://github.com/agent-clinic/claude-md-doctor),
[claude-memory-health](https://github.com/alexknowshtml/claude-memory-health).

---

## 7. Updating this skill

1. Re-check §4 constants against vendor docs — they change most often.
2. Re-check catalogue D5 (model cruft) after each major model release; entries retire
   as models improve, and new scaffolding habits appear.
3. Re-run the calibration in §5 against a repo you consider healthy. A detector that
   starts firing on it has drifted.
4. When adding a principle, record its source here in the same form, or the next person
   cannot tell a researched decision from a guess.

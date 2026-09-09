# Research 05 — Code comments, documentation rot, and detection mechanics

Source material for the `/context-health` skill. Target environment: **Windows 11, Git Bash
(GNU awk 5.3.2, git 2.52) + PowerShell 7**. Every command in Part B was executed against real
repos (`D:\Projects\open-slide`, 597 commits; `D:\Projects\anthropic-skills`, 112 markdown files)
and the output is reproduced or described.

---

# PART A — What makes a comment / doc valuable vs noise

## A1. Ousterhout, *A Philosophy of Software Design* (ch. 12–16)

The load-bearing idea: **a comment's job is to add information that is not in the code.** Everything
else follows from it.

| Claim | Quote (verbatim, <15 words) | Source |
|---|---|---|
| Core test for a comment | "Comments should describe things that aren't obvious from the code." | [danlebrero notes](https://danlebrero.com/2021/02/24/philosophy-of-software-design-summary/), [Pragmatic Engineer review](https://blog.pragmaticengineer.com/a-philosophy-of-software-design-review/) |
| The value a comment adds | "Comments should add precision or intuition." | [danlebrero](https://danlebrero.com/2021/02/24/philosophy-of-software-design-summary/) |
| The book's own red flag | "Comment Repeats Code: all of the information in a comment is immediately obvious" | [Portebois' red-flag list](https://sportebois.medium.com/software-design-red-flags-wisdom-nuggets-from-john-ousterhout-8a9b0045e2bb) |
| The "different words" test | "use different words in the comment from those in the name of the entity" | same |
| Anti-duplication rule | "Document each thing exactly once: don't duplicate documentation" | [Ousterhout's own Stanford lecture](https://web.stanford.edu/~ouster/cgi-bin/cs190-spring15/lecture.php?topic=comments) |
| Interface leakage | "Implementation Documentation Contaminates Interface" (red flag) | [Portebois](https://sportebois.medium.com/software-design-red-flags-wisdom-nuggets-from-john-ousterhout-8a9b0045e2bb) |
| Long docs = design smell | "Hard to Describe: … the documentation for a variable or method must be long" | same |
| Where comments live | "Comments belong to the code, not the commit log" | [danlebrero](https://danlebrero.com/2021/02/24/philosophy-of-software-design-summary/) |

**Four kinds of comment** (Ousterhout's taxonomy — the backbone of any audit rubric):

1. **Interface comments** — go with the declaration of a class/function; describe behaviour,
   arguments, return values, side effects, exceptions, caller obligations. Fill in what the
   signature *cannot* say: units, null-permitted, inclusive/exclusive boundaries.
2. **Data-structure member comments** — next to a field declaration; what it represents.
   Ousterhout says to "be very specific" here (units, invariants, meaning of null/zero).
3. **Implementation comments** — inside a method; describe *how* it works, at a higher level of
   abstraction than the code itself.
4. **Cross-module comments** — describe dependencies that cross module boundaries. These are the
   hardest to place and the most valuable, because nothing else in the codebase records them.

Mixing 1 and 3 is the "information leakage" failure: an interface comment that leaks implementation
adds complexity for every caller. Source:
<https://web.stanford.edu/~ouster/cgi-bin/cs190-spring15/lecture.php?topic=comments>

**The two ways comments fail** (same lecture): "comments duplicate code" and "non-obvious info is
not described". These are the *only two* failure axes an auditor needs; everything in Part B is a
detector for one or the other.

**Chapter 15, "Write the comment first"** — comments as a design tool: if the interface comment is
hard to write or must be long, the interface is wrong. This gives the audit a *design* reading of a
bloated docstring, not just a style reading. Pragmatic Engineer calls this "solid" advice for
juniors while noting he'd first ask whether refactoring removes the need.

**Chapter 16** relevance: keep documentation *near* the code so it gets updated in the same edit.
This is the theoretical justification for the git-proximity staleness signal in Part B: comments far
from their subject (a `docs/` tree, a root README) rot faster than a docstring on the function,
because they are not in the diff the developer is already editing.

## A2. Anthropic / Claude Code guidance on comments

- **Anthropic's positive framing** (Writing Code Comments skill, PostHog-authored, widely
  distributed for Claude Code): before adding any comment ask *"What does this tell a future reader
  that the code itself doesn't?"* If it restates functionality, delete it.
  Rule: "Explain why, not what. The what is in the code; the why usually is not."
  Source: <https://www.getclaudeskills.com/skills/writing-code-comments-posthog>
- **Four delete-on-sight categories** from that skill — the best ready-made taxonomy for the
  audit's comment section:
  1. **Narration restating the code** — `# increment the counter` above `counter += 1`.
  2. **Change history and chat context** — `# previously used a set here`, `// per PR #1234`,
     `# AI: generated this helper`.
  3. **Perishable measurements** — `# skip the ~20 min build`, `# no story currently opts into
     webkit`. The word *currently* is a literal grep-able rot marker.
  4. **Commented-out code** — "Version control tracks deleted code; remove it entirely".
- Good examples it gives: `# ATOMIC_REQUESTS is off, so wrap the two writes that must commit
  together`; `// Stripe sends the amount in cents; the rest of our system uses dollars`.
  Note both name an *external* fact (a framework setting, a third-party API's units) — i.e.
  Ousterhout's cross-module category.
- A second widely-mirrored framing: "a comment earns its place only when it tells a reader
  something the code cannot", across file headers / function docs / inline / architectural notes.
  Source: <https://mcpmarket.com/tools/skills/writing-code-comments>

**Real-world production instance worth citing in the skill.** `open-slide`'s `AGENTS.md:43` (a
public repo shipping an agent instruction file) states the minimal-comment position for AI agents
in operational terms:

> "**Default to writing no comments.** Only add one when the WHY is non-obvious … don't reference
> tasks/PRs/callers ("added for X", "used by Y"), don't write section-divider banners
> (`// ── Section ──`) or module-header descriptions, and don't leave commented-out code. If
> removing a comment wouldn't confuse a future reader, don't write it."

Useful because it converts the philosophy into four *detectable* patterns: task/PR references,
banner comments, module-header descriptions, commented-out code.

## A3. Google engineering practices

From <https://google.github.io/eng-practices/review/reviewer/looking-for.html>:

- Reviewer prompt: "Did the developer write clear comments in understandable English? Are all of the
  comments actually necessary?" — note the second question; Google explicitly treats *excess*
  comments as a review finding, not just missing ones.
- Comments should "explain why" rather than what; if code can't explain itself, simplify the code.
  Explicit exceptions: regular expressions and complex algorithms.
- The strongest formulation of comment value: comments should convey "information that the code
  itself can't possibly contain, like the reasoning behind a decision."
- **Directly actionable for an audit:** reviewers should examine *pre-existing* comments for
  outdated TODOs or notes that advise against the change being made. This legitimises auditing
  comments that no recent PR touched.
- **Docs vs comments are different artifacts**: documentation should "express the purpose of a piece
  of code, how it should be used, and how it behaves when used"; comments carry reasoning. An audit
  that finds *purpose/usage* prose inside inline comments has found misplaced content, and vice
  versa.
- **Deletion rule**: when code is deprecated or deleted, consider whether its documentation should
  be deleted too. This is the mirror image of "stale doc" and is much easier to detect (see B4:
  docs referencing deleted paths).

## A4. Comment–code inconsistency research: which SIGNALS the models use

This literature matters mostly because it tells you **which cheap features actually carry signal**,
so a shell-and-LLM audit can approximate a trained model.

**Deep JIT Inconsistency Detection** (Panthaplackel et al., AAAI 2021) — arXiv
[2010.01625](https://arxiv.org/abs/2010.01625), artifact
<https://github.com/panthap2/deep-jit-inconsistency-detection>. Framing: detect that a comment
*became* inconsistent as a result of a code change, "before they are committed". Its inputs:

| Signal | What it is | Cheap shell/LLM analogue |
|---|---|---|
| `Medit` — sequential edit | token-level edit script of the code change (replace/delete/add ops) | `git diff -U0` hunks for the function, fed to the model |
| `Tedit` — tree edit | AST diff of the change | tree-sitter node compare (see Fiberplane, B1.5) |
| comment/code token overlap features | hand-crafted lexical similarity between comment text and code identifiers | grep the comment's nouns against the current identifiers |
| variants | `SEQ(C,Medit)+features`, `GRAPH(C,Tedit)+features`, `HYBRID+features` | — |

**Key takeaway: token overlap between the comment and the identifiers it names is a real, published
feature.** If a comment names `userCache` and no such symbol exists in the enclosing scope any more,
that is exactly the feature the SOTA models learned. That check is a two-line grep (B4.3).

Related work decomposing changes into ordered "replacing / deleting / adding" activities reports up
to **+13.54% F1** over prior SOTA — reinforcing that *the shape of the edit*, not just the final
text, is where the signal lives. A doc audit therefore gets more from `git log --diff-filter=AD`
(files added/deleted since the doc was written) than from a plain content diff.

**Bug impact — the "so what" number.** *Investigating the Impact of Code Comment Inconsistency on
Bug Introducing* (arXiv [2409.10781](https://arxiv.org/abs/2409.10781), 2024): inconsistent changes
are **~1.5× more likely** to lead to a bug-introducing commit than consistent ones. Use this to
justify severity ranking: a stale comment is not cosmetic.

Other entries worth naming: **DocChecker** (arXiv [2306.06347](https://arxiv.org/pdf/2306.06347)),
bootstrapping a code LLM to both detect *and rectify* inconsistencies; **confidence-learning based
detection** (IEEE TSE 2024, <https://www.computer.org/csdl/journal/ts/2024/03/10416264/1U6HPkFeLL2>),
which treats the training labels themselves as noisy — a warning that "the comment doesn't match" is
a *fuzzy* label even for humans, so the audit should report suspicion with evidence, never a verdict.

## A5. The minimal-comments camp, in its strongest form

Present this fairly; the audit will otherwise read as pro-comment bias.

- **Robert C. Martin, *Clean Code* ch. 4.** The maximal claim: "comments are always failures" —
  "the proper use of comments is to compensate for our failure to express ourself in code."
  Corollaries: "a long descriptive name is better than a long descriptive comment"; don't comment
  bad code, rewrite it. Source:
  <https://www.goodreads.com/work/quotes/3779106-clean-code-a-handbook-of-agile-software-craftsmanship-robert-c-martin>
- **The steel-man, stated properly:** every comment is an unverified assertion. The compiler does
  not check it, the tests do not check it, the type system does not check it, CI does not check it.
  Code is the only artifact continuously validated against reality. So each comment is a liability
  with a maintenance cost and a nonzero probability of becoming a lie — and a lie is *worse* than
  silence, because a reader who distrusts a comment must re-derive the truth anyway, having already
  paid to read the comment. The 1.5× bug-introduction figure in A4 is, ironically, ammunition here too.
- **Martin's own carve-outs** (the position is not absolutist): TODO, caution/warning of
  consequences, statements of intent, clarification of an opaque API, and legal comments are
  "necessary". See *Necessary Comments*:
  <https://blog.cleancoder.com/uncle-bob/2017/02/23/NecessaryComments.html>
- **Where the camps actually agree** — and this is what the skill should say: *no one defends the
  restating comment.* Ousterhout, Google, Martin and Anthropic's skill all delete
  `// increment counter`. The disagreement is only about the residue: Ousterhout says a large
  residue of non-obvious information exists and must be written down; Martin says the residue is
  small and usually indicates code that should be refactored instead.
- **The strongest counter to Martin** (from the *Clean Code* critique at <https://qntm.org/clean>
  and others): code can only show what *is* there. It cannot show what was deliberately excluded,
  what was tried and rejected, which external contract forced the shape, or what invariant a caller
  must uphold. Those four categories are unrepresentable in code, so they are unrepresentable in
  "self-documenting code" too.
- **Reconciliation rule the audit can apply mechanically:** if a comment could be deleted and its
  information recovered by reading the code, it is noise (Martin wins). If deleting it destroys
  information that exists nowhere in the repository, it is load-bearing (Ousterhout wins).

## A6. Doc-level value taxonomy for agent context

From Claude Code's own guidance at <https://code.claude.com/docs/en/memory>:

- **Keep**: "facts Claude should hold in every session: build commands, conventions, project layout,
  'always do X' rules." Pitfalls, rationale, conventions that differ from tool defaults.
- **Cut**: anything derivable from the codebase. The `/doctor` trim check "cuts content Claude can
  derive from the codebase, such as directory layouts, dependency lists, and architecture
  overviews".
- **Move, don't delete**: "If an entry is a multi-step procedure or only matters for one part of the
  codebase, move it to a skill or a path-scoped rule instead." That is the audit's main
  recommendation type — relocation beats deletion, because it preserves content and removes the
  always-on cost.
- **Contradiction is a first-class defect**: "if two rules contradict each other, Claude may pick one
  arbitrarily." Also: "Look for conflicting instructions across CLAUDE.md files."
- **Size target**: "target under 200 lines per CLAUDE.md file. Longer files consume more context and
  reduce adherence." Hard limit: a CLAUDE.md over **4 MiB** is skipped entirely.
- **Imports do not save context**: "Splitting into @path imports helps organization but doesn't
  reduce context, since imported files load at launch." Max import depth: **four hops**.
- Block-level HTML comments (`<!-- ... -->`) in CLAUDE.md **are stripped before injection** — free
  maintainer notes, and something the audit's token math must exclude.

---

# PART B — Detection mechanics

## B0. Windows / Git Bash preflight (do this first — two of these bit during testing)

```bash
# 1. LOCALE. Without this, awk emits "Invalid multibyte data" warnings and `sort` HARD-FAILS
#    ("string comparison failed") on any repo containing UTF-8 punctuation or CJK. Not cosmetic:
#    the pipeline silently produced 0 rows instead of 7404.
export LC_ALL=C

# 2. Non-ASCII paths: make git print raw UTF-8 instead of \NNN escapes
git -c core.quotepath=false log ...

# 3. CRLF: if core.autocrlf=true, every line ends with \r and hashes/regexes drift.
#    Strip it in every text pipeline:  | tr -d '\r'
git config core.autocrlf

# 4. Tool inventory actually present in Git Bash on this machine:
#    awk (GNU 5.3.2), sed, sort, uniq, md5sum, sha1sum, perl, comm, join, tr, xargs, jq, python
#    NOT present: rg, fd, python3 (use `python`)
```

## B1. Git staleness: doc last-touched vs subject churn

### B1.1 Last-touch date for one path

```bash
git log -1 --format=%ad --date=short -- path/to/README.md   # 2026-08-18
git log -1 --format=%at -- path/to/README.md                # 1787022766  (epoch, for arithmetic)
git log -1 --format=%H  -- path/to/README.md                # the doc's own commit SHA
```

Traps:
- `git log -- <path>` follows the *current* path only. Use `--follow` for a single renamed file;
  `--follow` cannot be combined with multiple paths.
- History simplification hides commits where the file's content ended up unchanged on a merge.
  Add `--no-merges` for author-intent dates.
- A repo-wide reformat / license-header sweep resets every file's "last touched" date. **Always
  sanity-check for a single commit that touched hundreds of files** before trusting freshness:
  `git log --format='%h %ad %s' --date=short --shortstat | grep -B2 -E '[0-9]{3,} files changed'`

### B1.2 Last-touch for EVERY tracked file in one pass (O(history), not O(files) git calls)

Spawning `git log` per file is the naive approach and is unusably slow on Windows (process creation
cost). One pass instead — **verified: 584 rows on a 584-file repo, exact match**:

```bash
#!/usr/bin/env bash
# lastmod.sh — emit "<epoch>\t<path>" for every TRACKED file
set -e; export LC_ALL=C; cd "${1:-.}"
git ls-files | tr -d '\r' | sort > /tmp/_tracked.$$
git -c core.quotepath=false log --no-merges --format='@%at' --name-only \
  | tr -d '\r' \
  | awk '/^@[0-9]+$/ {t=substr($0,2); next} NF {if(!($0 in s)){s[$0]=t; print t"\t"$0}}' \
  | sort -k2,2 > /tmp/_hist.$$
awk -F'\t' 'NR==FNR{keep[$0]=1; next} ($2 in keep)' /tmp/_tracked.$$ /tmp/_hist.$$
rm -f /tmp/_tracked.$$ /tmp/_hist.$$
```

Why the `@` sentinel: a bare `%at` line is indistinguishable from a filename that is all digits.
Why the `git ls-files` intersection: without it you also get every **deleted** file. That is not
useless — it is its own finding. On the test repo the un-intersected version surfaced
`.claude/skills/apply-comments/SKILL.md` as "141 days old" when the file no longer exists at all.
Run both: intersected = freshness; the difference = *ghost paths that docs may still reference*.

### B1.3 Docs untouched for N months while their subject churned — the core rot metric

```bash
export LC_ALL=C
DOC=AGENTS.md
SHA=$(git log -1 --format=%H -- "$DOC")          # baseline: the doc's own last commit

# commits to the code area STRICTLY AFTER the doc's last edit
git rev-list --count "$SHA"..HEAD -- packages/            # -> 195

# churn volume since then
git log "$SHA"..HEAD --numstat --format='' -- packages/ \
  | awk '{a+=$1; d+=$2} END {printf "+%d / -%d over %d file-touches\n", a, d, NR}'
# -> +26503 / -8600 over 904 file-touches

# STRONGEST signal: files ADDED or DELETED under the subject since the doc was written.
# A doc cannot describe a file that did not exist when it was written, and it is probably
# still describing files that have since been deleted.
git log "$SHA"..HEAD --diff-filter=AD --name-status --format='' -- packages/ | sort -u
```

**Prefer the `SHA..HEAD` range over `--since`.** Verified drift: `--since="@$(git log -1
--format=%at -- AGENTS.md)"` returned **196** commits where `SHA..HEAD` returned **195** — `--since`
is inclusive of the boundary second and re-counts the doc's own commit (and anything else committed
in that same second, which on a squash-merge repo can be a whole PR).

Batch form, one line per doc:

```bash
export LC_ALL=C; now=$(date +%s)
git ls-files '*.md' | grep -vE 'CHANGELOG|node_modules|\.changeset' | while IFS= read -r d; do
  sha=$(git log -1 --format=%H -- "$d"); t=$(git log -1 --format=%at -- "$d"); [ -z "$t" ] && continue
  dir=$(dirname "$d")
  n=$(git rev-list --count "$sha"..HEAD -- "$dir")
  printf '%5dd  %4d commits since  %s\n' $(( (now-t)/86400 )) "$n" "$d"
done | sort -rn
```

**Rot score.** `rot = commits_to_subject_since_doc_edit × log(1 + doc_age_days)`. Rank on that, not
on age alone: a 400-day-old doc for a directory nobody has touched in 400 days is *fine*, and saying
otherwise is the fastest way to lose the reader's trust in the whole report.

Thresholds that behaved sensibly in testing:
- **Critical**: doc ≥ 180 days old **and** ≥ 30 commits to its subject since **and** ≥ 1 file
  added-or-deleted under the subject.
- **Warn**: doc ≥ 90 days old and ≥ 10 commits since.
- **Ignore**: subject commits since = 0, at any age. Also ignore `CHANGELOG.md`, `LICENSE`,
  `CODE_OF_CONDUCT.md`, ADRs and anything under `docs/adr/` or `decisions/` — **historical records
  are supposed to be old.** This is the single biggest false-positive class.

### B1.4 Comment-level staleness with `git blame`

```bash
# age of every TODO, oldest first
export LC_ALL=C; now=$(date +%s)
git grep -n -E '\b(TODO|FIXME|HACK|XXX)\b' -- '*.ts' '*.py' '*.cs' | while IFS=: read -r f l rest; do
  t=$(git blame -L "$l,$l" --porcelain -- "$f" 2>/dev/null | awk '/^author-time /{print $2}')
  [ -n "$t" ] && printf '%5dd  %s:%s  %s\n' $(( (now-t)/86400 )) "$f" "$l" "$(echo "$rest" | cut -c1-70)"
done | sort -rn
```

Then the *real* comment-rot signal — **comment older than the code it sits in**:

```bash
# For a comment at FILE:LINE, compare its blame date to the newest blame date in the body below.
# If the comment's commit is much older, the code moved on without the comment.
# This is the shell approximation of the JIT-inconsistency feature.
f=src/foo.ts; c=42; body_start=43; body_end=70
ct=$(git blame -L "$c,$c"                 --porcelain -- "$f" | awk '/^author-time /{print $2}')
bt=$(git blame -L "$body_start,$body_end" --porcelain -- "$f" | awk '/^author-time /{print $2}' | sort -rn | head -1)
[ "$bt" -gt "$ct" ] && echo "STALE?  comment $(( (bt-ct)/86400 )) days older than newest body line"
```

Traps: `git blame` attributes to the *last* commit that touched the line, so a reformat, a rename
sweep, or a `git mv` makes everything look fresh. Mitigate with `git blame -w -C -M --ignore-rev <sha>`
(or a checked-in `.git-blame-ignore-revs` + `git config blame.ignoreRevsFile`). Also: blame is
expensive; cap it to the top N candidates from a cheap grep, never run it repo-wide.

### B1.5 The Fiberplane "drift" model — the rigorous version, worth stealing

<https://fiberplane.com/blog/drift-documentation-linter/> ships a linter for exactly this problem.
Its mechanics are the best-designed prior art found:

- An **anchor** is "a small piece of markdown frontmatter you add to your spec file", with three
  parts: `path` (required), `symbol` (optional declaration name), `provenance` (optional git SHA).
- **Provenance** records "which commit last addressed this anchor". Without it, it falls back to the
  last commit that touched the spec file — i.e. exactly the B1.3 heuristic.
- Staleness test: get the baseline commit, extract the file/symbol at that baseline with
  `git show <baseline>:<file>`, compare to current, report if different.
- To avoid reformat false positives it "hashes a normalized AST fingerprint (node kinds + token
  text, no whitespace or position data)" via tree-sitter, and for supported languages
  (TS, Python, Rust, Go, Zig, Java) "only tracks changes to that symbol".
- Acknowledged failure mode: it cannot verify the human actually re-read the code when re-linking.

**For `/context-health`, use `git show <baseline>:<file>` as the poor-man's version even without
tree-sitter** — no parser needed, and it is exact:

```bash
SHA=$(git log -1 --format=%H -- docs/api.md)
git show "$SHA":src/api.ts > /tmp/then.ts
diff -u /tmp/then.ts src/api.ts | head -50    # what changed under this doc since it was written
# whitespace-insensitive, to kill reformat noise:
diff -uwB /tmp/then.ts src/api.ts | grep -cE '^[+-][^+-]'
```

## B2. Duplicated prose across files at scale

Ousterhout's justification is one sentence: "Document each thing exactly once: don't duplicate
documentation (it won't get maintained)."

### B2.1 Normalized-line hashing (start here — cheap, exact, explainable)

**Verified on `anthropic-skills`: 7,404 normalized lines from 112 markdown files.**

```bash
export LC_ALL=C
git ls-files '*.md' '*.mdc' '*.txt' | while IFS= read -r f; do
  awk -v F="$f" '{
    line=tolower($0);
    gsub(/[^a-z0-9 ]/," ",line); gsub(/  +/," ",line); gsub(/^ | $/,"",line);
    if (length(line) >= 40) print line "\t" F ":" FNR
  }' "$f"
done 2>/dev/null | sort > /tmp/norm.tsv
```

The metric that matters is **not** "which line repeats" but **how much prose two files share**:

```bash
# duplicated-line VOLUME per file pair
awk -F'\t' '{split($2,parts,":"); f=parts[1];
             if (!(($1 SUBSEP f) in s)) {s[$1 SUBSEP f]=1; files[$1]=files[$1] " " f}}
 END {for (k in files) {n=split(files[k],a," ");
        for(i=1;i<=n;i++) for(j=i+1;j<=n;j++) if(a[i]<a[j]) pair[a[i]"\t"a[j]]++}
      for (pk in pair) if (pair[pk] >= 4) print pair[pk]"\t"pk}' /tmp/norm.tsv | sort -rn
```

Real output (anthropic-skills):

```
49  skills/mcp-builder/reference/node_mcp_server.md   skills/mcp-builder/reference/python_mcp_server.md
44  skills/claude-api/python/claude-api/README.md     skills/claude-api/typescript/claude-api/README.md
34  skills/claude-api/php/managed-agents/README.md    skills/claude-api/ruby/managed-agents/README.md
23  skills/claude-api/python/managed-agents/README.md skills/claude-api/typescript/managed-agents/README.md
```

A correct find: per-language guides sharing 44–49 identical prose lines.

**awk gotchas that cost real time here** — both produced fatal errors, both are easy to hit:
- `split(str, arr, sep)` — the array is the **second** argument. `split(s," ",a)` fatals with
  *"second argument is not an array"*.
- Never reuse a name as both a `split()` array and a `for (k in arr)` loop variable →
  *"attempt to use array `p` in a scalar context"*.

**Thresholds.** `>= 4` shared 40-char lines between two files = worth reporting. `>= 15` = one of
the two should import or link the other. `>= 40` = near-clone; recommend deleting one.

**False-positive traps for line hashing:**
- License headers, code-of-conduct boilerplate, generated tables of contents, frontmatter keys, and
  identical fenced code blocks. Filter fenced code before hashing if you only care about prose:
  `awk '/^```/{inb=!inb; next} !inb'`.
- Templated repos where duplication is *intended* (`packages/*/README.md` scaffolds).
- Short bullets — hence the `length >= 40` floor. Below ~40 chars, "Run the tests." collides across
  unrelated files.

### B2.2 Shingling / n-gram overlap (catches paraphrase; line hashing does not)

Word-level w-shingles + Jaccard: split each doc into overlapping word sequences, compare shingle
sets, threshold the Jaccard estimate (τ ≈ 0.8 for "same document", far lower for "shares a
section"). MinHash+LSH is the scale-up when pairwise comparison is too expensive; for a repo audit
(hundreds of files, not millions) **pairwise is fine and exact — skip MinHash.** References:
<https://blog.nelhage.com/post/fuzzy-dedup/>, <https://yorko.github.io/2023/practical-near-dup-detection/>

```bash
export LC_ALL=C
sh5() { tr -d '\r' < "$1" | tr 'A-Z' 'a-z' | tr -cs 'a-z0-9' '\n' | grep -v '^$' \
        | awk 'BEGIN{n=5}{w[NR%n]=$0; if(NR>=n){s="";for(i=NR-n+1;i<=NR;i++)s=s w[i%n]"_";print s}}' \
        | sort -u; }
sh5 a.md > /tmp/a.sh; sh5 b.md > /tmp/b.sh
inter=$(comm -12 /tmp/a.sh /tmp/b.sh | wc -l)
uni=$(cat /tmp/a.sh /tmp/b.sh | sort -u | wc -l)
awk -v i="$inter" -v u="$uni" 'BEGIN{printf "Jaccard %.3f\n", (u?i/u:0)}'
```

Interpretation for docs (not for web-page dedup — thresholds differ):
- **J ≥ 0.7** — the two files are the same document. Delete one.
- **0.35 ≤ J < 0.7** — substantial shared sections; extract a shared file and link it.
- **0.15 ≤ J < 0.35** — same topic, differently worded. Feed *these* to the LLM for a contradiction
  check (B5) — near-paraphrases are where contradictions hide.
- **J < 0.15** — ignore.

Use **containment**, not Jaccard, when files differ wildly in size (a 2,000-line guide vs a 30-line
CLAUDE.md section): `containment(small, big) = |A ∩ B| / |A|`. Jaccard reports ~0.02 for a section
that is 100% copied into a large file; containment reports 1.0. **This is the most common way a
duplication audit misses the real finding.**

## B3. Token cost, cheaply

```bash
# chars/4 heuristic, per file, largest first  (verified on anthropic-skills)
export LC_ALL=C
git ls-files '*.md' | while IFS= read -r f; do printf '%s\t%s\n' "$(wc -c < "$f")" "$f"; done \
  | sort -rn | awk -F'\t' '{printf "%8d chars  ~%6d tok  %s\n", $1, int($1/4), $2}' | head -20
```

Real output: `175868 chars  ~43967 tok  skills/claude-api/shared/model-migration.md`.

Accuracy of `chars/4`: good to roughly ±15% for English prose; it **under-counts** code, JSON, paths
and CJK (CJK can approach 1 token/char) and **over-counts** long runs of whitespace. For an audit
that only needs ranking and order of magnitude it is fine — but write "≈" in the report. Cheap
cross-check: `wc -w` × 1.3 is a second estimate; if the two disagree by >30% the file is code-heavy,
not prose. An exact count needs Anthropic's count-tokens endpoint, and a repo audit should not
require network access.

### B3.1 The always-on ledger (the headline number of the whole audit)

What Claude Code actually loads **at launch, every session** (sources:
<https://code.claude.com/docs/en/memory>, <https://code.claude.com/docs/en/context-window>,
<https://code.claude.com/docs/en/skills>):

| Loaded every session | Notes |
|---|---|
| Managed policy CLAUDE.md | `C:\Program Files\ClaudeCode\CLAUDE.md` on Windows; cannot be excluded |
| `~/.claude/CLAUDE.md` | user scope, all projects (~320 tok in the docs' worked example) |
| `./CLAUDE.md` **or** `./.claude/CLAUDE.md` | project (~1,800 tok in that example) |
| `./CLAUDE.local.md` | appended after CLAUDE.md at each level |
| **every ancestor directory's** CLAUDE.md / CLAUDE.local.md | root→cwd order |
| **all `@path` imports, recursively, up to 4 hops** | "imported files still load and enter the context window at launch" |
| `.claude/rules/*.md` **without** `paths:` frontmatter | "loaded at launch with the same priority as `.claude/CLAUDE.md`" |
| `~/.claude/rules/*.md` without `paths:` | user scope |
| Auto-memory `MEMORY.md` | first 200 lines / 25 KB, whichever first (~680 tok) |
| **Skill name + description listing** | ~450 tok in the example; budget "scales at 1% of the model's context window"; each entry capped at 1,536 chars |
| System prompt, env info, tool schemas | ~4,200 / ~280 / varies |

**Loaded on demand (weight these ~0 in the ledger):**
- Skill *bodies* — "a skill's body loads only when it's used, so long reference material costs almost
  nothing until you need it." Skills with `disable-model-invocation: true` are not even in the listing.
- `.claude/rules/*.md` **with** `paths:` frontmatter — load when Claude reads a matching file.
- CLAUDE.md files in **subdirectories below cwd** — "included when Claude reads files in those
  subdirectories", not at launch.
- Auto-memory topic files (`user_role.md` etc.).
- `AGENTS.md` — **Claude Code does not read it** unless a CLAUDE.md imports it or symlinks to it.

Competitors, for a cross-tool audit:
- **Cursor**: `.cursor/rules/*.mdc` with `alwaysApply: true` load in every conversation; `globs:`
  scope them. Community guidance: keep always-apply rules under ~200 words.
  <https://techsy.io/en/blog/cursor-rules-guide>
- **GitHub Copilot**: `.github/copilot-instructions.md` is repo-wide and always-on, and it "does
  **not** use the `applyTo` frontmatter". `.github/instructions/*.instructions.md` are path-scoped
  via `applyTo` globs.
  <https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot>

Ledger script (verified; prints per-file and subtotal):

```bash
export LC_ALL=C; cd "$REPO"; tot=0
add() { [ -f "$1" ] || return; c=$(wc -c < "$1"); printf '  %-52s %7d chars  ~%6d tok\n' "$1" "$c" "$((c/4))"; tot=$((tot+c)); }
for f in CLAUDE.md .claude/CLAUDE.md CLAUDE.local.md \
         .github/copilot-instructions.md .cursorrules .windsurfrules .clinerules; do add "$f"; done
while IFS= read -r f; do [ -n "$f" ] || continue
  head -20 "$f" | grep -qE '^paths:|^globs:|alwaysApply:[[:space:]]*false' && continue   # path-scoped: on demand
  add "$f"
done < <(git ls-files '.claude/rules/*.md' '.cursor/rules/*.mdc' '.github/instructions/*.md' 2>/dev/null)
echo "  ---- ALWAYS-ON SUBTOTAL: ~$((tot/4)) tokens"

# skill DESCRIPTIONS only (bodies are on-demand): frontmatter name+description per SKILL.md
find . -name SKILL.md -not -path './node_modules/*' | while read -r s; do
  awk '/^---/{n++; next} n==1' "$s" | grep -E '^(name|description):' | wc -c
done | awk '{s+=$1} END {printf "  skill descriptions: ~%d tok\n", s/4}'
```

Resolve `@imports` too — they are launch-time cost:

```bash
# @path imports, EXCLUDING code spans (Claude Code skips backticked paths and fenced blocks)
awk '/^```/{inb=!inb; next} !inb' CLAUDE.md | sed 's/`[^`]*`//g' \
  | grep -oE '(^|[[:space:]])@[A-Za-z0-9_./~@-]+' | tr -d ' @' | sort -u
```

**Traps in the ledger:**
- A **symlinked** `CLAUDE.md -> AGENTS.md` shows as a 9-byte file. Verified on `open-slide`:
  `CLAUDE.md` = 9 chars, `AGENTS.md` = 3,149 chars. Naively summing both double-counts *and*
  under-counts. Test with `[ -L CLAUDE.md ]` and resolve.
- The import extractor must strip code spans, or a package name like `` `@open-slide/cli` `` is
  reported as an import. Verified false positive.
- Ancestor CLAUDE.md files above the repo root also load. `git ls-files` will never see them: walk
  up from cwd separately.
- HTML comments in CLAUDE.md are stripped before injection — subtract them from the token estimate.
- Don't count `.claude/skills/**/SKILL.md` bodies in the always-on total. Counting them is the most
  common way to produce a wildly wrong (and instantly discreditable) headline number.

## B4. Broken / stale references in docs

### B4.1 File paths — tested, tuned to zero false positives on real docs

The naive `grep -oE '[\w/.-]+\.\w+'` produces garbage: `Next.js`, `dev/build`, `fixes/polish`,
`tasks/PRs/callers` all matched during testing. The tuned version calibrates against the repo's own
extension set and basename set:

```bash
#!/usr/bin/env bash
# brokenrefs.sh <repo> <doc>...
# HIGH = has an extension the repo actually uses, and does not exist.
# MED  = no extension, contains a slash, and its parent directory exists.
export LC_ALL=C; REPO="${1:?}"; shift; cd "$REPO" || exit 1
git ls-files > /tmp/_ls.$$
sed -nE 's/.*\.([A-Za-z0-9]{1,6})$/\1/p' /tmp/_ls.$$ | sort -u > /tmp/_ext.$$
awk -F/ '{print $NF}' /tmp/_ls.$$ | sort -u > /tmp/_base.$$
STOP='^(Next|Node|Vue|React|Express|Socket|D3|Three|Chart|Nuxt|Ember|jQuery)\.(js|io|ts)$'
for doc in "$@"; do
  [ -f "$doc" ] || { echo "MISS  $doc: doc itself does not exist"; continue; }
  grep -oE '[A-Za-z0-9_.@-]+(/[A-Za-z0-9_.@-]+)+|[A-Za-z0-9_.-]+\.[A-Za-z0-9]{1,6}\b' "$doc" \
  | grep -vE '^(https?://|www\.|@[a-z])' | grep -vE "$STOP" \
  | sed -E 's#^\./##; s#/$##' | sort -u \
  | while IFS= read -r c; do
      [ -e "$c" ] && continue
      grep -qxF "$c" /tmp/_ls.$$ && continue
      case "$c" in */*) hasslash=1;; *) hasslash=0; grep -qxF "$c" /tmp/_base.$$ && continue;; esac
      ext="${c##*.}"
      if [ "$ext" != "$c" ] && grep -qxF "$ext" /tmp/_ext.$$; then echo "HIGH  $doc: $c"
      elif [ "$hasslash" = 1 ] && [ -d "${c%/*}" ]; then echo "MED   $doc: $c"; fi
    done
done
rm -f /tmp/_ls.$$ /tmp/_ext.$$ /tmp/_base.$$
```

Verified result — planted 2 broken paths + 1 renamed dir into a test doc alongside two real
instruction files:

```
HIGH  _tmp_testdoc.md: docs/nope/thing.md
HIGH  _tmp_testdoc.md: packages/core/src/gone.ts
MED   _tmp_testdoc.md: packages/core/src/oldname
(zero output for the real AGENTS.md and CLAUDE.md)
```

Bonus signal: cross-reference broken paths against **deleted** files from B1.2. If the path exists in
history but not in HEAD, you can name the deleting commit — far more actionable than "path not found":

```bash
git log --diff-filter=D --format='%h %ad' --date=short --name-only -- 'packages/core/src/gone.ts' | head -3
```

### B4.2 Commands (`npm run x`, `make y`, script names)

```bash
export LC_ALL=C
grep -ohE '(npm|pnpm|yarn|bun) run [a-zA-Z0-9:_-]+' *.md .claude/**/*.md 2>/dev/null \
  | awk '{print $NF}' | sort -u > /tmp/cmds.txt
jq -r '.scripts | keys[]' package.json | sort -u > /tmp/scripts.txt
comm -23 /tmp/cmds.txt /tmp/scripts.txt          # -> referenced but NOT defined  (the finding)
comm -13 /tmp/cmds.txt /tmp/scripts.txt          # -> defined but never documented (weaker)
```

Verified on `open-slide`: zero orphans (correct — docs and `package.json` agree). Equivalents:
`make` targets → `grep -oE '^[a-zA-Z0-9_-]+:' Makefile`; Python → `pyproject.toml
[project.scripts]`; .NET → `dotnet run --project` paths.

### B4.3 Symbols

```bash
# every backticked identifier in a doc that appears nowhere in the code
export LC_ALL=C
grep -ohE '`[A-Za-z_][A-Za-z0-9_]{3,}`' docs/*.md | tr -d '`' | sort -u | while read -r sym; do
  git grep -qw -- "$sym" -- '*.ts' '*.tsx' '*.py' '*.cs' '*.go' || echo "ORPHAN SYMBOL: $sym"
done
```

This is the same feature the JIT-inconsistency models use (comment/code token overlap). Traps: it
fires on prose words in backticks, on symbols that live in `node_modules`/vendored code, and on
renamed-but-equivalent symbols. Require length ≥ 4, require camelCase/snake_case/PascalCase shape
(`grep -E '[a-z][A-Z]|_'`), and cap the report at the top ~20.

### B4.4 URLs

```bash
export LC_ALL=C
git ls-files '*.md' | xargs grep -ohE 'https?://[A-Za-z0-9._~:/?#@!$&()*+,;=%-]+' \
  | sed 's/[.,)]*$//' | sort -u > /tmp/urls.txt
while read -r u; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 8 -L "$u" 2>/dev/null)
  case "$code" in 200|301|302|000) ;; *) echo "$code  $u" ;; esac
done < /tmp/urls.txt
```

Traps: **network access may be unavailable or disallowed** — make this opt-in and never block the
audit on it. Rate-limit (GitHub returns 429), many sites 403 a bare curl (send `-A 'Mozilla/5.0'`),
`000` means connection failure, not a dead link. Higher-signal and offline: flag internal-wiki /
ticket URLs whose host appears nowhere else in the repo, and flag URLs into the repo's own GitHub
tree pinned at a `blob/<sha>` that is no longer reachable.

## B5. Contradictions between instruction files

Claude Code's docs make this a first-class defect: "if two rules contradict each other, Claude may
pick one arbitrarily." Three tractable signals, ascending in cost:

### B5.1 Same setting key, different value (near-zero false positives — do this first)

```bash
export LC_ALL=C
for f in CLAUDE.md AGENTS.md .cursorrules .github/copilot-instructions.md .claude/rules/*.md; do
  [ -f "$f" ] || continue
  grep -oiE '(indent(ation)?|line[ -]?length|max[ -]?line|timeout|port|node version|python version|coverage|max[ -]?tokens)[^0-9a-z]{0,12}([0-9]+)' "$f" \
    | sed "s#^#$f: #"
done | sort -t: -k2
```

Verified output on planted fixtures:

```
CLAUDE.md: Line length limit: 100
AGENTS.md: Line length limit: 120
```

### B5.2 Tool/command divergence (also near-zero FP)

```bash
grep -ohE '\b(npm|pnpm|yarn|bun)\b' CLAUDE.md AGENTS.md .claude/rules/*.md 2>/dev/null | sort -u
# more than one package manager named across always-on files == a conflict, full stop
```

Verified: returned `npm pnpm yarn` on the fixtures. Generalize to test runners
(`jest|vitest|pytest`), formatters (`prettier|biome|black|ruff`), and branch policy
(`main|master|develop`).

### B5.3 Same topic, opposite polarity or different object (the general case)

Pair every directive-shaped line with every other, score word-set Jaccard, flag pairs that are
*near*-identical but not identical — those either contradict or duplicate. **Tested: found all four
planted contradictions, zero false positives on a real 8-directive instruction file.**

```awk
# contradict.awk — usage: awk -f contradict.awk CLAUDE.md AGENTS.md .claude/rules/*.md
BEGIN{ split("always never must should shall may can do does not dont don t avoid prefer use \
using used the a an of for to and or before after when you we it is are be run runs running with \
without our your please ensure only just all any this that in on at as if then else directly",S," ");
       for(i in S) stop[S[i]]=1 }
{ raw=$0; l=tolower(raw);
  if (l !~ /(always|never|must|should|do not|don'?t|avoid|prefer|may |can |use |run |only )/) next;
  pol=(l ~ /(never|do not|don'?t|avoid|no longer|must not|should not)/)?"NEG":"POS";
  t=l; gsub(/[^a-z0-9]+/," ",t); n=split(t,w," "); words="";
  for(i=1;i<=n;i++) if(!(w[i] in stop) && length(w[i])>1) words=words w[i] " ";
  N++; P[N]=pol; SRC[N]=FILENAME ":" FNR; TXT[N]=substr(raw,1,72); W[N]=words }
END{ for(a=1;a<=N;a++) for(b=a+1;b<=N;b++){
    split(W[a],x," "); split(W[b],y," ");
    delete sa; delete sb; na=0; nb=0; inter=0;
    for(i in x) if(!(x[i] in sa)){sa[x[i]]=1; na++}
    for(i in y) if(!(y[i] in sb)){sb[y[i]]=1; nb++}
    for(k in sa) if(k in sb) inter++;
    uni=na+nb-inter; if(uni==0) continue; j=inter/uni;
    if ((j>=0.45 && j<1.0) || (inter>=1 && (na-inter)<=1 && (nb-inter)<=1 && j<1.0))
      printf "J=%.2f  %s [%s] %s\n         %s [%s] %s\n", j, SRC[a],P[a],TXT[a], SRC[b],P[b],TXT[b];
    else if (j==1.0 && P[a]!=P[b]) printf "POLARITY FLIP  %s / %s\n", SRC[a], SRC[b]; } }
```

Verified output (4/4 planted conflicts, no misses, no FPs):

```
J=0.33  CLAUDE.md:2 [POS] - Always use `pnpm` for installs.
         AGENTS.md:2 [POS] - Always use `yarn` for installs.
J=0.60  CLAUDE.md:3 [POS] - Run tests with `npm test` before committing.
         AGENTS.md:3 [POS] - Run tests with `pnpm test` before committing.
J=0.67  CLAUDE.md:4 [NEG] - Never commit directly to main.
         AGENTS.md:4 [POS] - You may commit directly to main for hotfixes.
J=0.33  CLAUDE.md:7 [POS] - Prefer named exports.
         AGENTS.md:7 [POS] - Prefer default exports.
```

**Why the `differs-by-one-token` clause matters:** short directives ("Prefer named exports" vs
"Prefer default exports") have only two content words, so their Jaccard is 0.33 and a plain
threshold of 0.45 misses them. The extra clause — intersection ≥ 1 and each side has ≤ 1 unique
token — catches exactly the "same sentence, one word swapped" case, which is what a real
contradiction looks like.

**Traps:** a conditional exception is not a contradiction ("never commit to main" + "except for
release automation" is coherent), and scope-qualified rules in path-scoped files are *meant* to
differ from the global rule. The mechanical detector cannot tell these apart — so treat its output
as a **candidate list to hand to the model**, one pair at a time, with 5 lines of surrounding
context from each file. That two-stage design (cheap recall in the shell, precision from the LLM) is
the right architecture for the whole contradiction section. Also: `.claude/rules/*.md` with `paths:`
frontmatter is *scoped*; only flag cross-scope pairs when the path-scoped rule contradicts a rule
that also applies to those same paths.

## B6. Comment smells — patterns that actually work

All run against `open-slide` (TypeScript, well maintained); counts and FP rates are real.

### B6.1 Commented-out code

The obvious regex over-fires badly. **Tightened version, verified: 2 false positives across a whole
TS monorepo, both prose sentences that happen to end in a semicolon.**

```bash
export LC_ALL=C
git grep -n -E '^[[:space:]]*//' -- '*.ts' '*.tsx' '*.js' '*.cs' '*.java' | \
awk -F: '{ file=$1; ln=$2; $1=""; $2=""; sub(/^::/,""); c=$0;
   sub(/^[[:space:]]*\/\/[[:space:]]?/,"",c);
   if (c ~ /^(const|let|var|if|for|while|return|import|export|function|class|await|try|catch|switch|case|throw|new|public|private|def)\b.*[;{)=]/)
      { print "KW    " file ":" ln ":" substr(c,1,80); next }
   if (c ~ /[;{}]$/ && c ~ /[=(]/ && c !~ /[.,][[:space:]]*$/)
      { n=split(c,w," "); if (n<=12) print "PUNCT " file ":" ln ":" substr(c,1,80) } }'
```

Python/shell variant: swap the marker to `^[[:space:]]*#` and the keyword list to
`def|class|import|from|if|for|while|return|try|except|with|print`.

Traps: prose ending in `;` (the observed FP); commented-out *examples* in a docstring or a
`# Usage:` block, which are legitimate; disabled config lines in `.env.example`/`Dockerfile`, which
are conventional and correct. **Confidence rises steeply with run length** — 3+ consecutive matching
lines is almost always real dead code; a lone match is usually prose.

### B6.2 Long comment blocks (banner / changelog / essay detector)

```bash
export LC_ALL=C
git grep -n -E '^[[:space:]]*(//|#)' -- '*.ts' '*.py' | awk -F: '{print $1":"$2}' \
| awk -F: 'NR==1{f=$1;p=$2;run=1;start=$2;next}
  {if($1==f && $2==p+1) run++; else {if(run>=6) print "  "run" comment lines at "f":"start; f=$1;start=$2;run=1} p=$2; f=$1}
  END{if(run>=6) print "  "run" comment lines at "f":"start}'
```

Verified: found five 6–7 line blocks. This is a *neutral* signal — a long block is either a valuable
cross-module comment (Ousterhout's most valuable kind) or an essay/changelog. Escalate to the model;
never auto-flag.

### B6.3 Banner comments

```bash
git grep -n -E '^[[:space:]]*(//|#|\*)[[:space:]]*[-=*_#─═]{6,}' -- . | head -40
```

Verified: zero hits on `open-slide` (correct — its own AGENTS.md forbids them). Traps: file-header
license blocks and generated-file markers use the same divider glyphs; exclude anything with
`@generated` / `DO NOT EDIT` within 3 lines.

### B6.4 TODO / FIXME with dates, tickets, and age

```bash
# inline dates and ticket refs
git grep -nE '(TODO|FIXME|HACK|XXX)[^a-zA-Z]{0,4}(\(?[A-Za-z.]+\)?)?[^a-zA-Z0-9]{0,3}([0-9]{4}-[0-9]{2}-[0-9]{2}|[A-Z]{2,10}-[0-9]+)'
# bare markers with no owner and no ticket — the worst kind
git grep -nE '(TODO|FIXME|HACK|XXX)[^(:]*$' -- '*.ts' '*.py' '*.cs'
# age: see B1.4
```

Escalation rule: TODO older than **365 days** with no linked ticket ⇒ "decide: do it, file it, or
delete it". A TODO whose inline date has *passed* is an automatic finding.

### B6.5 `@deprecated` and abandonment markers

```bash
git grep -nE '@deprecated|\[Obsolete|DeprecationWarning|@Deprecated' -- .
# then: is the deprecated thing still referenced?
sym=oldFunction; git grep -w -- "$sym" | grep -v '@deprecated' | wc -l
# and: how long has it been deprecated?  (blame the @deprecated line, B1.4)
```

Verified: 1 hit on `open-slide` (`packages/core/src/config.ts:17`). Finding shape: "deprecated N days
ago, still referenced in M places" or "deprecated N days ago, zero references — delete".

### B6.6 Redundant docstrings that restate the signature

```bash
# @param whose description is just the param name (with or without "the")
git grep -nE '@param[[:space:]]+\{?[A-Za-z<>\[\],. ]*\}?[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]+(the[[:space:]]+)?\1\b' \
  -- '*.ts' '*.js' '*.java'
# one-line docstrings that are just Get/Set/Return + the member name
git grep -nE '/\*\*[[:space:]]*(Gets?|Sets?|Returns?)[[:space:]]+the[[:space:]]+[a-zA-Z ]+\.?[[:space:]]*\*/' -- '*.ts' '*.cs' '*.java'
```

The **general, language-agnostic version is Ousterhout's "different words" test**, and it is easy to
mechanise: take the identifier, split camelCase/snake_case into words, lowercase both it and the
first line of its doc comment, drop stopwords, compute overlap. **Overlap ≥ 0.8 with no additional
content words = the comment adds nothing.** This is the single highest-yield comment check, because
it is exactly the book's stated red flag:

```bash
# identifier -> doc-first-line word overlap.  stdin lines: "file:line:::identifier:::doc first line"
python - <<'PY'
import re, sys
STOP = set("the a an of to for and or is are be this that it with in on at returns return gets get sets set".split())
for raw in sys.stdin:
    try: loc, ident, doc = raw.rstrip("\n").split(":::")
    except ValueError: continue
    iw = {w.lower() for w in re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+', ident)} - STOP
    dw = {w.lower() for w in re.findall(r"[A-Za-z]+", doc)} - STOP
    if not iw or not dw: continue
    if dw <= iw or (len(iw & dw) / len(dw)) >= 0.8:
        print(f"REDUNDANT {loc}  {ident}  <-  {doc.strip()[:60]}")
PY
```

(Note: `python3` is **not** on PATH in Git Bash on this machine; use `python`.)

### B6.7 Changelog-in-comments and perishable measurements

```bash
# dated history lines inside comments
git grep -nE '^[[:space:]]*(\*|//|#)[[:space:]]*(v?[0-9]+\.[0-9]+([.0-9]*)?|\[?[0-9]{4}-[0-9]{2}-[0-9]{2}\]?|Changed|Added|Updated|Modified|Revision)[[:space:]:—-]'
# "added for X" / "used by Y" / PR and ticket references inside comments
git grep -nE '(//|#|\*)[^\n]*\b(added (for|in)|per PR|see PR|as of|introduced in|used by)\b'
# perishable measurements and hedges — the "currently" tell
git grep -nEi '(//|#|\*)[^\n]*\b(currently|for now|at the moment|as of (today|now|20[0-9]{2})|temporar(y|ily)|takes (about|~)?[0-9]+ ?(ms|s|sec|min))\b'
```

`currently` / `for now` / `temporarily` are high-yield: Anthropic's comment guidance names them
explicitly as perishable, and they age into lies **without any code change at all** — the one comment
smell that git-based staleness detection cannot find, which is exactly why the grep earns its place.

## B7. PowerShell equivalents (verified on PowerShell 7)

```powershell
# doc age in days + rough token count
Set-Location 'D:/Projects/open-slide'
$t = git log -1 --format=%at -- AGENTS.md
$age = [int]((([DateTimeOffset]::UtcNow.ToUnixTimeSeconds()) - $t) / 86400)
"AGENTS.md age: $age days"                                  # -> 127 days
"approx tokens: $([int]((Get-Item AGENTS.md).Length / 4))"  # -> 787
```

```powershell
# always-on ledger
$files = @('CLAUDE.md','.claude/CLAUDE.md','CLAUDE.local.md','AGENTS.md',
           '.github/copilot-instructions.md','.cursorrules') +
         (Get-ChildItem -Recurse -Filter *.md -Path .claude/rules -EA SilentlyContinue).FullName
$files | Where-Object { $_ -and (Test-Path $_) } |
  ForEach-Object { [pscustomobject]@{ File=$_; Tokens=[int]((Get-Item $_).Length/4) } } |
  Sort-Object Tokens -Descending | Format-Table -AutoSize
```

```powershell
# staleness sweep: each markdown file vs commits to its directory since it was last edited
git ls-files '*.md' | ForEach-Object {
  $sha = git log -1 --format=%H -- $_
  $dir = Split-Path $_ -Parent; if (-not $dir) { $dir = '.' }
  $n = (git rev-list --count "$sha..HEAD" -- $dir)
  [pscustomobject]@{ Doc=$_; CommitsSince=[int]$n }
} | Sort-Object CommitsSince -Descending | Select-Object -First 20
```

PowerShell caveats: `Select-String` defaults to case-**insensitive** (unlike grep) — pass
`-CaseSensitive`; `Get-Content` splits on `\n` and keeps `\r` on CRLF files; `git` writes progress to
stderr, which PowerShell surfaces as errors under `$ErrorActionPreference='Stop'`. **For anything
involving text normalization, hashing, or n-grams, prefer Git Bash** — the awk/sort pipelines above
are an order of magnitude shorter and were all verified there.

## B8. Suggested audit pipeline (cheap → expensive)

1. **Inventory + always-on ledger** (B3.1). One number: always-on tokens. Everything else is context
   for it.
2. **Cheap greps**: broken refs (B4.1–B4.2), setting-value conflicts (B5.1), tool divergence (B5.2),
   comment smells (B6). Pure `git grep`, seconds.
3. **Staleness sweep** (B1.3), ranked by `commits_since × log(1+age)`. One `git rev-list` per doc.
4. **Duplication**: normalized-line volume per pair (B2.1); shingle-Jaccard/containment only on the
   pairs that survive (B2.2).
5. **Model pass — the only expensive step**: hand the model *only* the candidate pairs and top-N
   stale docs, with surrounding scope, and ask for a verdict plus evidence. Never let the model read
   every file; that reproduces the bloat the audit exists to find.
6. **Report**: findings with `file:line`, the evidence command that produced them, and a severity
   that is *derived*. Never assert "this is stale"; assert "this doc has not changed in 210 days
   while 47 commits and 3 file deletions landed under the directory it documents."

---

## Sources

- https://web.stanford.edu/~ouster/cgi-bin/cs190-spring15/lecture.php?topic=comments
- https://sportebois.medium.com/software-design-red-flags-wisdom-nuggets-from-john-ousterhout-8a9b0045e2bb
- https://danlebrero.com/2021/02/24/philosophy-of-software-design-summary/
- https://blog.pragmaticengineer.com/a-philosophy-of-software-design-review/
- https://google.github.io/eng-practices/review/reviewer/looking-for.html
- https://www.getclaudeskills.com/skills/writing-code-comments-posthog
- https://mcpmarket.com/tools/skills/writing-code-comments
- https://arxiv.org/abs/2010.01625 · https://github.com/panthap2/deep-jit-inconsistency-detection
- https://arxiv.org/abs/2409.10781
- https://arxiv.org/pdf/2306.06347
- https://www.computer.org/csdl/journal/ts/2024/03/10416264/1U6HPkFeLL2
- https://blog.cleancoder.com/uncle-bob/2017/02/23/NecessaryComments.html
- https://qntm.org/clean
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/context-window
- https://code.claude.com/docs/en/skills
- https://fiberplane.com/blog/drift-documentation-linter/
- https://understandingdata.com/posts/doc-drift-detection-ci/
- https://blog.nelhage.com/post/fuzzy-dedup/
- https://yorko.github.io/2023/practical-near-dup-detection/
- https://techsy.io/en/blog/cursor-rules-guide
- https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot

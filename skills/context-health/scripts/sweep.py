#!/usr/bin/env python
"""Mechanical detectors for context rot. Produces CANDIDATES, not verdicts.

Every detector here is cheap, explainable and reproducible. None of them decide
whether something is a problem - they surface a line plus the evidence that makes
it suspicious, so the model can judge a short list instead of reading the repo.
That order matters: an audit that reads everything reproduces the bloat it exists
to find.

Each detector documents its false-positive trap in `TRAPS`. Report the trap
alongside the finding; a finding whose trap has not been checked is not a finding.

Usage:
    python sweep.py [REPO] [--json] [--comments] [--only NAME,NAME]

Detectors:
    refs        paths named in docs that do not exist
    commands    commands in docs missing from package.json / Makefile / pyproject
    dupes       near-duplicate prose across instruction files
    stale       docs whose subject changed long after the doc did
    emphasis    ALL-CAPS / MUST / NEVER saturation
    conflicts   same setting with two values; rival tools; opposite directives
    perishable  "currently", "as of <date>", changelog accretion in instructions
    cruft       instructions written for models that no longer need them
    external    context telling the agent to fetch remote content and obey it
    comments    commented-out code, changelog comments, stale TODOs (--comments)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", ".venv", "venv",
    "__pycache__", ".next", "target", "bin", "obj", ".cache", "coverage",
}
INSTRUCTION_NAMES = {
    "CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", ".cursorrules",
    "copilot-instructions.md", ".windsurfrules", ".clinerules", "GEMINI.md",
}
VENDORED = re.compile(r"/(?:\.agents|node_modules|third_party|external|vendor|"
                      r"examples?|fixtures?|templates?)/")
CODE_EXT = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".cs", ".rb",
    ".php", ".c", ".h", ".cpp", ".hpp", ".swift", ".kt", ".scala", ".sh",
}

TRAPS = {
    "refs": "Illustrative or planned paths, and paths inside code fences, are not "
            "broken references. Check whether the doc is describing what exists or "
            "what someone should create.",
    "commands": "Commands can be defined outside a manifest - in CI, a justfile, a "
                "shell alias, or a global tool. Confirm the command really is gone.",
    "dupes": "Deliberate mirroring for two different audiences can be correct. The "
             "finding is only real when the copies have DRIFTED, so diff them.",
    "stale": "Changelogs, licences, ADRs and post-mortems are supposed to be old. "
             "And one repo-wide reformat resets every file's date - check for a "
             "commit touching 100+ files before trusting any freshness signal.",
    "emphasis": "A handful of genuine invariants deserve emphasis. The finding is "
                "the RATIO, not any single line.",
    "conflicts": "Scoped rules legitimately differ from global ones, and a rule may "
                 "carry an unstated exception. Ask whether an agent could satisfy "
                 "both at once; if it could, this is scope refinement, not conflict.",
    "perishable": "A dated entry inside an explicitly historical section (ADR, "
                  "migration log) is doing its job.",
    "cruft": "Some of these phrases are still load-bearing in a specific workflow. "
             "Ask whether the current model already does this unprompted.",
    "external": "A documentation link is fine. The finding is an instruction to "
                "TREAT fetched content as rules. Check whether the URL is pinned to a "
                "commit or tag - a pinned fetch is a vendoring choice, not this defect.",
    "comments": "Prose ending in a semicolon, and commented-out code kept as a "
                "documented alternative, both read as false positives. Confidence "
                "rises steeply with 3+ consecutive lines.",
}


# ---------------------------------------------------------------------------
# infrastructure
# ---------------------------------------------------------------------------

def git(repo: Path, *args: str) -> str:
    try:
        r = subprocess.run(
            ["git", "-c", "core.quotepath=false", *args],
            cwd=repo, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120,
        )
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    except OSError:
        return ""


def strip_fences(text: str) -> list[tuple[int, str]]:
    """Numbered lines with fenced code blocks removed. 1-indexed."""
    out, in_fence = [], False
    for i, line in enumerate(text.split("\n"), 1):
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((i, line))
    return out


class Finding:
    def __init__(self, detector, path, line, text, evidence, confidence="medium"):
        self.detector, self.path, self.line = detector, path, line
        self.text, self.evidence, self.confidence = text.strip()[:300], evidence, confidence

    def as_dict(self):
        return {
            "detector": self.detector, "file": self.path, "line": self.line,
            "text": self.text, "evidence": self.evidence,
            "confidence": self.confidence, "trap": TRAPS.get(self.detector, ""),
        }


class Sweep:
    def __init__(self, repo: Path, want_comments: bool):
        self.repo = repo.resolve()
        self.want_comments = want_comments
        self.findings: list[Finding] = []
        self.notes: list[str] = []
        self.tracked = self._tracked()
        self.docs = [p for p in self.tracked if p.suffix.lower() in (".md", ".mdc", ".mdx")]
        self.instructions = [
            p for p in self.tracked
            if (p.name in INSTRUCTION_NAMES
                or "/.claude/rules/" in self.rel(p)
                or "/.cursor/rules/" in self.rel(p))
            and not VENDORED.search(self.rel(p))
            # A file inside a skill folder is that skill's body: it loads on
            # demand, so it is not part of the always-on instruction set.
            and "/skills/" not in self.rel(p)
        ]
        self.reformats = self._mass_reformat_commits()

    def _tracked(self) -> list[Path]:
        out = git(self.repo, "ls-files")
        if out:
            paths = [self.repo / line for line in out.splitlines() if line]
        else:
            self.notes.append("not a git repo (or git unavailable): walking the tree; "
                              "staleness detection is disabled")
            paths = [p for p in self.repo.rglob("*") if p.is_file()]
        return [p for p in paths if not SKIP_DIRS & set(p.parts) and p.is_file()]

    def _mass_reformat_commits(self) -> set[str]:
        """Commits touching 100+ files reset every file's date. Exclude them."""
        out = git(self.repo, "log", "--format=%H", "--name-only", "-n", "400")
        big, sha, count = set(), None, 0
        for line in out.splitlines():
            if re.fullmatch(r"[0-9a-f]{40}", line):
                if sha and count >= 100:
                    big.add(sha)
                sha, count = line, 0
            elif line.strip():
                count += 1
        if sha and count >= 100:
            big.add(sha)
        return big

    def rel(self, p: Path) -> str:
        try:
            return "/" + str(p.resolve().relative_to(self.repo)).replace("\\", "/")
        except ValueError:
            return str(p)

    def r(self, p: Path) -> str:
        return self.rel(p).lstrip("/")

    def add(self, *a, **kw):
        self.findings.append(Finding(*a, **kw))

    # -----------------------------------------------------------------------
    # detectors
    # -----------------------------------------------------------------------

    def owned_docs(self) -> list[Path]:
        """Docs this repo authors about itself.

        Vendored third-party documentation (a copied-in skill, a bundled style
        guide) describes someone else's project, so its paths are supposed not
        to resolve here. Auditing those paths produces pure noise - on one real
        repo it was 132 findings, none of them true.
        """
        vendored = re.compile(r"(?:^|/)(?:\.agents|node_modules|third_party|external|"
                              r"examples?|fixtures?|templates?|\.github/ISSUE_TEMPLATE)/")
        historical = re.compile(r"(?:^|/)(?:CHANGELOG|HISTORY|RELEASES?|MIGRATION|"
                                r"NEWS|UPGRADING)[^/]*\.mdx?$", re.I)
        out = []
        for d in self.docs:
            rel = "/" + self.r(d)
            if vendored.search(rel) or historical.search(rel):
                continue
            out.append(d)
        return out

    def refs(self):
        """Paths named in a repo's own docs that do not exist.

        Calibrated against the repo's own extension set: a naive path regex
        matches `Next.js`, `dev/build` and `and/or`, and slices URLs into
        fake paths, so it is worse than useless.
        """
        exts = {p.suffix.lower() for p in self.tracked if p.suffix}
        basenames = {p.name for p in self.tracked}
        dirs = {str(Path(self.r(p)).parent).replace("\\", "/") for p in self.tracked}
        url = re.compile(r"https?://\S+|\b[\w.\-]+\.(?:com|org|net|io|dev|sh|app)\b")
        pat = re.compile(r"`([A-Za-z0-9_.\-/]{3,90})`"
                         r"|(?<![\w/.])((?:[A-Za-z0-9_.\-]+/){1,6}[A-Za-z0-9_.\-]+)")
        targets = self.owned_docs() + [p for p in self.instructions if p not in self.docs]
        for doc in dict.fromkeys(targets):
            hits: dict[str, int] = {}
            for lineno, line in strip_fences(read(doc)):
                line = url.sub(" ", line)          # kill URLs before path matching
                for m in pat.finditer(line):
                    tok = (m.group(1) or m.group(2) or "").strip().rstrip(".,;:)")
                    tok = tok.lstrip("./")
                    if not tok or " " in tok or tok.startswith(("@", "#", "-")):
                        continue
                    suffix = Path(tok).suffix.lower()
                    if suffix and suffix not in exts:
                        continue                   # a file type this repo never uses
                    if Path(tok).name in basenames:
                        continue                   # exists somewhere: moved, not gone
                    if (self.repo / tok).exists():
                        continue
                    parent = str(Path(tok).parent).replace("\\", "/")
                    if "/" not in tok.rstrip("/"):
                        # A bare name is only evidence inside an instruction file,
                        # where every path is meant to be actionable right now.
                        # Elsewhere it is usually a folder the READER creates.
                        if doc not in self.instructions or not suffix:
                            continue
                    elif parent == "." or parent not in dirs:
                        # Root-relative single segments (`slides/`, `dist/`) are
                        # nearly always instructions to the reader, not claims
                        # about this tree. Absent subtrees are prose.
                        continue
                    hits.setdefault(tok, lineno)
            for tok, lineno in hits.items():
                parent = str(Path(tok).parent).replace("\\", "/")
                conf = "high" if parent != "." and parent in dirs else "medium"
                self.add("refs", self.r(doc), lineno, tok,
                         f"`{tok}` is named as a path; it does not exist in the working "
                         f"tree" + (f" (its parent `{parent}/` does)" if conf == "high" else ""),
                         conf)

    def commands(self):
        """Documented commands that no longer exist in any manifest.

        These are the worst kind of stale context, because agents run them.
        """
        defined: set[str] = set()
        pkg = self.repo / "package.json"
        if pkg.is_file():
            try:
                defined |= set(json.loads(read(pkg)).get("scripts", {}))
            except (ValueError, TypeError):
                pass
        for mk in ("Makefile", "makefile", "GNUmakefile"):
            f = self.repo / mk
            if f.is_file():
                defined |= set(re.findall(r"^([A-Za-z0-9_.\-]+):(?!=)", read(f), re.M))
        pyproj = self.repo / "pyproject.toml"
        if pyproj.is_file():
            defined |= set(re.findall(r"^([A-Za-z0-9_\-]+)\s*=\s*[\"']", read(pyproj), re.M))
        just = self.repo / "justfile"
        if just.is_file():
            defined |= set(re.findall(r"^([A-Za-z0-9_\-]+):", read(just), re.M))
        if not defined:
            return
        # An explicit `run` verb is required. Bare `pnpm`/`yarn` swallows the next
        # word, so "use pnpm to install deps" reports a missing script called `to`.
        runner = re.compile(r"\b(?:npm run|pnpm run|yarn run|bun run|make)\s+"
                            r"([A-Za-z0-9_:.\-]+)")
        reserved = {"install", "test", "start", "build", "run", "ci", "add", "-C",
                    "to", "the", "a", "all", "clean", "help"}
        for doc in dict.fromkeys(self.docs + self.instructions):
            for lineno, line in self.command_lines(read(doc)):
                for name in runner.findall(line):
                    if name in defined or name in reserved:
                        continue
                    self.add("commands", self.r(doc), lineno, line,
                             f"`{name}` is not a script in package.json / Makefile / "
                             f"pyproject.toml / justfile", "high")

    def command_lines(self, text: str):
        """Lines where a command could plausibly appear: code spans and fences.

        Scanning prose instead makes `make` match "make it work", "make software"
        and "make translucent surfaces frostier" - 24 false positives on one real
        repo, every one of them looking confident.
        """
        in_fence = False
        for i, line in enumerate(text.split("\n"), 1):
            if re.match(r"^\s*```", line):
                in_fence = not in_fence
                continue
            # Even inside a fence the command must START the line. Fences also
            # hold conversation transcripts, where "You: make this smaller"
            # otherwise reports a missing make target called `this`.
            if re.match(r"^\s*\$?\s*(?:npm|pnpm|yarn|bun|make)\b", line):
                yield i, line
            elif in_fence:
                continue
            else:
                for span in re.findall(r"`([^`]+)`", line):
                    yield i, span

    def dupes(self):
        """Near-duplicate prose across instruction files.

        Containment, not Jaccard: a short file wholly copied into a long one
        scores badly on Jaccard and is exactly the case worth catching.
        """
        targets = list(dict.fromkeys(self.instructions + [
            d for d in self.docs if d.name.upper() in {"README.MD", "CONTRIBUTING.MD"}
        ]))
        norm: dict[Path, set[str]] = {}
        for p in targets:
            lines = set()
            for _, line in strip_fences(read(p)):
                s = re.sub(r"[^a-z0-9 ]", "", line.lower()).strip()
                if len(s) >= 40:
                    lines.add(s)
            if lines:
                norm[p] = lines
        seen = set()
        for a in norm:
            for b in norm:
                if a is b or (b, a) in seen:
                    continue
                seen.add((a, b))
                shared = norm[a] & norm[b]
                if len(shared) < 3:
                    continue
                containment = len(shared) / min(len(norm[a]), len(norm[b]))
                conf = "high" if len(shared) >= 15 else "medium"
                if len(shared) < 5 and containment < 0.25:
                    continue
                self.add("dupes", self.r(a), 0, next(iter(shared))[:120],
                         f"{len(shared)} identical normalized lines shared with "
                         f"{self.r(b)} ({containment:.0%} of the smaller file). "
                         f"Both load; the agent pays twice and they can drift apart.",
                         conf)

    def stale(self):
        """Docs whose subject changed long after the doc last did."""
        if not git(self.repo, "rev-parse", "--git-dir"):
            return
        now = time.time()
        for doc in self.docs:
            rel = self.r(doc)
            # These are meant to be old, or sit in a directory that churns by
            # design (.changeset adds and deletes a file per release).
            if re.search(r"changelog|licen[cs]e|adr|decisions?/|history|postmortem|"
                         r"\.changeset/|migrations?/|releases?\.md", rel, re.I):
                continue
            sha_date = git(self.repo, "log", "-1", "--format=%H %at", "--", rel).split()
            if len(sha_date) != 2:
                continue
            sha, at = sha_date[0], int(sha_date[1])
            age_days = (now - at) / 86400
            if age_days < 120:
                continue
            subject = str(Path(rel).parent).replace("\\", "/")
            subject = "." if subject in (".", "") else subject
            churn = git(self.repo, "rev-list", "--count", f"{sha}..HEAD", "--", subject)
            n = int(churn.strip() or 0)
            if n < 5:
                continue
            addel = git(self.repo, "log", f"{sha}..HEAD", "--diff-filter=AD",
                        "--name-status", "--format=", "--", subject)
            moved = len([l for l in addel.splitlines() if l.strip()])
            score = n * (1 + (age_days / 365))
            if score < 15:
                continue
            ev = (f"last edited {age_days:.0f} days ago; {n} commits have landed under "
                  f"`{subject}/` since")
            if moved:
                ev += f", including {moved} file additions or deletions"
            self.add("stale", rel, 1, f"(whole file, {len(read(doc).splitlines())} lines)",
                     ev, "high" if moved else "medium")

    def emphasis(self):
        """Emphasis saturation. If everything is critical, nothing is."""
        pat = re.compile(r"\b(IMPORTANT|CRITICAL|ALWAYS|NEVER|MUST|REQUIRED|MANDATORY|"
                         r"DO NOT|YOU MUST)\b")
        for p in self.instructions:
            body = [(n, l) for n, l in strip_fences(read(p)) if l.strip()]
            if len(body) < 12:
                continue
            hits = [(n, l) for n, l in body if pat.search(l)]
            ratio = len(hits) / len(body)
            if ratio > 0.15 and len(hits) >= 5:
                self.add("emphasis", self.r(p), hits[0][0],
                         f"{len(hits)} emphasized lines of {len(body)}",
                         f"{ratio:.0%} of lines shout. Emphasis works by contrast; at "
                         f"this density none of them stands out, and the genuine "
                         f"invariants are indistinguishable from the preferences.",
                         "high" if ratio > 0.3 else "medium")

    def conflicts(self):
        """Three conflict shapes, cheapest and most reliable first."""
        files = self.instructions
        # 1. same setting key, two values - near-zero false positives
        settings: dict[str, set] = defaultdict(set)
        where: dict[tuple, tuple] = {}
        kv = re.compile(r"\b([A-Za-z][A-Za-z0-9_\-]{3,30})\s*(?:=|:|\bto\b)\s*"
                        r"[`\"']?(\d+(?:\.\d+)?[a-zA-Z%]{0,4})[`\"']?")
        for p in files:
            for n, line in strip_fences(read(p)):
                for key, val in kv.findall(line):
                    k = key.lower()
                    settings[k].add(val)
                    where[(k, val)] = (self.r(p), n, line)
        for k, vals in settings.items():
            if len(vals) > 1:
                locs = [where[(k, v)] for v in vals]
                if len({l[0] for l in locs}) < 2 and len(vals) < 3:
                    continue
                detail = "; ".join(f"{v} at {where[(k, v)][0]}:{where[(k, v)][1]}" for v in vals)
                self.add("conflicts", locs[0][0], locs[0][1], locs[0][2],
                         f"`{k}` is given {len(vals)} different values across always-on "
                         f"instructions: {detail}. The agent has no rule for choosing.",
                         "high")

        # 2. rival tools named across always-on files
        families = {
            "package manager": ["npm", "yarn", "pnpm", "bun"],
            "test runner": ["jest", "vitest", "pytest", "mocha", "unittest", "rspec"],
            "formatter": ["prettier", "black", "ruff format", "gofmt", "dotnet format"],
            "linter": ["eslint", "ruff", "flake8", "pylint", "biome"],
        }
        blob = {p: read(p).lower() for p in files}
        for family, tools in families.items():
            seen = {}
            for p, text in blob.items():
                for t in tools:
                    if re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", text):
                        seen.setdefault(t, []).append(self.r(p))
            if len(seen) > 1:
                detail = "; ".join(f"{t} in {', '.join(sorted(set(v)))}" for t, v in seen.items())
                first = sorted(seen.values())[0][0]
                self.add("conflicts", first, 0, family,
                         f"{len(seen)} rival {family}s are named in always-on "
                         f"instructions: {detail}. Unless the repo genuinely uses both, "
                         f"the agent will sometimes pick the wrong one.",
                         "medium")

        # 3. opposite directives - Jaccard OR differ-by-one-token
        directives = []
        dpat = re.compile(r"\b(always|never|prefer|avoid|use|do not|don't|must|should)\b", re.I)
        for p in files:
            for n, line in strip_fences(read(p)):
                s = line.strip(" -*\t")
                # A heading and the table-of-contents entry pointing at it are
                # the same words by design. Pairing them yields 100%-overlap
                # "contradictions" that are confident and entirely spurious.
                if line.lstrip().startswith("#") or "](" in s or s.startswith("|"):
                    continue
                if 20 < len(s) < 200 and dpat.search(s):
                    words = set(re.findall(r"[a-z]+", s.lower()))
                    directives.append((self.r(p), n, s, words))
        for i in range(len(directives)):
            for j in range(i + 1, len(directives)):
                fa, na, sa, wa = directives[i]
                fb, nb, sb, wb = directives[j]
                if sa == sb:
                    continue
                inter, union = wa & wb, wa | wb
                if not union:
                    continue
                jac = len(inter) / len(union)
                one_off = len(union - inter) == 2 and abs(len(wa) - len(wb)) <= 1
                if jac >= 0.6 or one_off:
                    self.add("conflicts", fa, na, sa,
                             f"reads as a near-restatement or a polarity flip of "
                             f"{fb}:{nb} — \"{sb}\" (word overlap {jac:.0%}). Either "
                             f"one is redundant, or they disagree.",
                             "high" if one_off else "low")

    def perishable(self):
        """Content that rots with no code change at all - the hardest kind to catch."""
        pats = [
            (re.compile(r"\b(currently|at the moment|for now|right now|temporarily|"
                        r"at present|as of (?:now|today|writing))\b", re.I),
             "a time-relative claim with no date - it can rot without any code changing"),
            (re.compile(r"\b(?:as of|since|updated?)\s+"
                        r"(?:\d{4}-\d{2}|\w+ \d{4}|Q[1-4] \d{4}|\d{4})\b", re.I),
             "a dated claim in an always-on file - verify it still holds"),
            (re.compile(r"^\s*[-*]?\s*(?:\d{4}-\d{2}-\d{2}|update|note|edit)\s*[:\-]", re.I),
             "changelog accretion: an instruction file used as an append-only log"),
            (re.compile(r"\b(?:we (?:now )?(?:use|have|are)|recently (?:moved|switched|migrated))\b", re.I),
             "narrates a transition; once the transition is old this only confuses"),
            (re.compile(r"\b\d+\s+(?:components?|services?|packages?|modules?|endpoints?|tables?)\b", re.I),
             "a countable claim about the repo - verify the count, it drifts silently"),
            # An undated deadline never becomes checkably stale, so no future audit
            # and no reader can tell whether it is upcoming or years overdue.
            (re.compile(r"\b(?:in |by |before |until )?Q[1-4]\b(?!\s*\d{4})|"
                        r"\b(?:next|this|last) (?:quarter|sprint|release|month|year)\b|"
                        r"\b(?:soon|shortly|in the near future|eventually|"
                        r"by end of (?:the )?(?:quarter|month|year))\b", re.I),
             "an undated deadline - it can never be caught as stale, because there is "
             "no date to compare against"),
        ]
        for p in self.instructions:
            for n, line in strip_fences(read(p)):
                for pat, why in pats:
                    if pat.search(line):
                        self.add("perishable", self.r(p), n, line, why, "medium")
                        break

    def cruft(self):
        """Instructions aimed at a model generation that no longer needs them.

        Prompt scaffolding that helped older models is now either inert (paying
        tokens for nothing) or actively harmful - documented cases exist of
        intensifier language causing repetitive tool use.
        """
        pats = [
            (r"\bthink step[- ]by[- ]step\b", "reasoning models already do this; inert"),
            (r"\btake a deep breath\b", "a retired prompt-engineering trick; inert"),
            (r"\byou are an? (?:expert|world[- ]class|senior|10x)\b",
             "role-priming has little effect on current models and costs tokens"),
            (r"\b(?:do not be lazy|don't be lazy|be thorough|work hard|no shortcuts)\b",
             "pressure language; documented to cause over-searching, not better work"),
            (r"</?(?:scratchpad|thinking)>", "manual scratchpad tags conflict with native reasoning"),
            (r"\bread the (?:file|code) before (?:editing|changing)\b",
             "current agents do this natively"),
            (r"\b(?:always )?(?:output|provide|start with) an? (?:upfront )?plan\b",
             "vendor guidance now advises removing this; it can stop work early"),
            (r"\btake your time\b|\bdo not rush\b", "inert on reasoning models"),
            (r"\bI will tip\b|\bmy job depends\b|\bor (?:I|you) will be (?:fired|penali[sz]ed)\b",
             "incentive framing; no measured benefit on current models"),
        ]
        for p in self.instructions:
            for n, line in strip_fences(read(p)):
                for pat, why in pats:
                    if re.search(pat, line, re.I):
                        self.add("cruft", self.r(p), n, line, why, "medium")
                        break

    def external(self):
        """Context that tells the agent to fetch remote content and obey it.

        Judgment alone misses this: a 1KB stub reads as trivial, so an auditor
        skims it and pronounces the repo clean - which is worse than not looking,
        because the clean verdict now carries authority. Hence a detector.

        Skill bodies are in scope even though they load on demand: when the skill
        fires, the fetch fires with it.
        """
        url = re.compile(r"https?://[^\s`'\")>\]]+")
        # Placeholder hosts appear in code samples, not in fetch instructions.
        placeholder = re.compile(r"^(?:localhost|127\.|0\.0\.0\.0|.*\bexample\.(?:com|org|net)$"
                                 r"|.*\byour-|.*\bmy-app|.*\.local$|.*\.test$)", re.I)
        fetching = re.compile(r"\b(?:fetch|curl|wget|download|retrieve|WebFetch|web_fetch)\b", re.I)
        # "NEVER fetch raw files from GitHub" is guidance AGAINST this defect.
        negated = re.compile(r"\b(?:never|do not|don't|avoid|instead of|rather than|no need to)\b"
                             r"[^.]{0,40}\b(?:fetch|curl|wget|download|retrieve)\b", re.I)
        obeying = re.compile(r"\b(?:follow|obey|apply|adhere|comply|enforce|use|treat)\b"
                             r"[^.]{0,80}\b(?:rule|guideline|instruction|standard|"
                             r"convention|polic|checklist|spec)", re.I)
        latest = re.compile(r"\b(?:latest|fresh|current|up[- ]to[- ]date|newest)\b", re.I)
        pinned = re.compile(r"/(?:blob|raw|tree)/(?:[0-9a-f]{7,40}|v?\d+\.\d+)", re.I)

        targets = list(self.instructions)
        for root in (self.repo / ".claude/skills", self.repo / ".agents/skills",
                     self.repo / ".claude/agents"):
            if root.is_dir():
                targets += sorted(root.rglob("*.md"))

        for p in dict.fromkeys(targets):
            lines = read(p).split("\n")
            for n, line in enumerate(lines, 1):
                if not fetching.search(line) or negated.search(line):
                    continue
                # The URL may sit on the next line or two ("fetch the guidelines
                # from the source URL below"), so look in a small window.
                window = "\n".join(lines[max(0, n - 2):n + 3])
                live = [u for u in url.findall(window)
                        if "/" in u and not placeholder.match(u.split("/")[2])]
                if not live:
                    continue
                if not (obeying.search(window) or latest.search(line)):
                    continue
                if all(pinned.search(u) for u in live):
                    continue          # pinned to a commit or tag: vendoring, not this
                hosts = sorted({u.split("/")[2] for u in live})[:3]
                self.add("external", self.r(p), n, line.strip(),
                         f"instructs the agent to fetch from {', '.join(hosts)} and "
                         f"treat the result as rules. Whatever is at that URL today "
                         f"becomes agent behaviour - unversioned, unreviewed, and "
                         f"silent when it changes",
                         "high")
                break                 # one finding per file is enough to act on

    def comments(self):
        """Comment smells. Opt-in: this walks source files."""
        code = [p for p in self.tracked if p.suffix.lower() in CODE_EXT]
        cpat = re.compile(r"^\s*(?://|#)\s?(.*)$")
        codeish = re.compile(r"[;{}()\[\]=]|^\s*(?:if|for|while|return|def|function|"
                             r"const|let|var|import|from|class|public|private)\b")
        for p in code[:4000]:
            lines = read(p).split("\n")
            run = []
            for n, line in enumerate(lines, 1):
                m = cpat.match(line)
                body = m.group(1).strip() if m else None
                if body and codeish.search(body) and len(body.split()) <= 12 \
                        and not body.rstrip().endswith((".", ",")):
                    run.append((n, body))
                    continue
                if len(run) >= 3:
                    self.add("comments", self.r(p), run[0][0], run[0][1],
                             f"{len(run)} consecutive commented-out code lines "
                             f"({run[0][0]}-{run[-1][0]}); git already remembers this",
                             "high")
                run = []
            text = "\n".join(lines)
            for n, line in enumerate(lines, 1):
                m = cpat.match(line)
                if not m:
                    continue
                b = m.group(1)
                if re.search(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b.*\b(?:added|changed|fixed|"
                             r"removed|updated|by)\b", b, re.I):
                    self.add("comments", self.r(p), n, b,
                             "changelog inside a comment; git blame carries this already",
                             "high")
                elif re.search(r"\b(?:currently|for now|temporarily|takes about|"
                               r"~\d+\s*(?:min|sec|hour|ms))\b", b, re.I):
                    self.add("comments", self.r(p), n, b,
                             "a perishable measurement or hedge; nothing will ever "
                             "update it when the fact changes", "medium")
            del text

    # -----------------------------------------------------------------------

    ALL = ["refs", "commands", "dupes", "stale", "emphasis", "conflicts",
           "perishable", "cruft", "external"]

    def run(self, only: list[str] | None) -> None:
        names = only or list(self.ALL)
        if self.want_comments and "comments" not in names:
            names.append("comments")
        for name in names:
            fn = getattr(self, name, None)
            if not fn:
                self.notes.append(f"unknown detector: {name}")
                continue
            try:
                fn()
            except Exception as exc:  # a broken detector must not kill the sweep
                self.notes.append(f"detector `{name}` failed: {exc!r}")

    def render(self) -> str:
        order = {"high": 0, "medium": 1, "low": 2}
        buckets: dict[str, list[Finding]] = defaultdict(list)
        for f in self.findings:
            buckets[f.detector].append(f)
        out = [f"# Detector sweep - {self.repo.name}", ""]
        out.append(f"{len(self.findings)} candidates across {len(buckets)} detectors. "
                   "These are leads, not verdicts - each carries the trap that would "
                   "make it a false positive.")
        for name in self.ALL + ["comments"]:
            fs = buckets.get(name)
            if not fs:
                continue
            fs.sort(key=lambda f: order.get(f.confidence, 3))
            out += ["", f"## {name}  ({len(fs)})", "", f"_Trap: {TRAPS[name]}_", ""]
            for f in fs[:40]:
                loc = f"{f.path}:{f.line}"
                out.append(f"- **{loc}** [{f.confidence}] `{f.text}`")
                out.append(f"  - {f.evidence}")
            if len(fs) > 40:
                out.append(f"- _... and {len(fs) - 40} more_")
        if self.notes:
            out += ["", "## Notes", ""] + [f"- {n}" for n in self.notes]
        return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--comments", action="store_true", help="also scan source comments")
    ap.add_argument("--only", default="", help="comma-separated detector names")
    args = ap.parse_args()

    repo = Path(args.repo)
    if not repo.is_dir():
        print(f"not a directory: {repo}", file=sys.stderr)
        return 2

    sweep = Sweep(repo, args.comments)
    sweep.run([s.strip() for s in args.only.split(",") if s.strip()] or None)
    if args.json:
        print(json.dumps({
            "repo": str(sweep.repo),
            "findings": [f.as_dict() for f in sweep.findings],
            "notes": sweep.notes,
        }, indent=2))
    else:
        print(sweep.render())
    return 0


if __name__ == "__main__":
    sys.exit(main())

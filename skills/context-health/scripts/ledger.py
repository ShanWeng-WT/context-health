#!/usr/bin/env python
"""Always-on context ledger.

Measures what an agent loads at launch of EVERY session, versus what it loads on
demand. The always-on total is the headline number of a context-health audit:
it is a per-turn tax, paid before the user types anything.

Deliberately deterministic and judgment-free. It reports what loads and what it
costs. Deciding whether a line deserves its tokens is the model's job, not this
script's.

Usage:
    python ledger.py [REPO] [--json] [--window 200000]

Notes on accuracy:
  - Token counts are chars/4, the standard rough estimate. Accurate to about
    +/-15% on English prose; it UNDER-counts code, JSON and CJK text. Treat the
    numbers as a budget, not a measurement.
  - HTML comments are stripped before counting: Claude Code removes them before
    injection, so they are genuinely free.
  - Symlinks are resolved, so a CLAUDE.md -> AGENTS.md bridge is counted once.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Constants sourced from vendor documentation. See SOURCES.md for provenance.
# --------------------------------------------------------------------------

MAX_IMPORT_DEPTH = 4  # code.claude.com/docs/en/memory
MEMORY_LINE_CAP = 200  # MEMORY.md: first 200 lines OR 25 KB, whichever first
MEMORY_BYTE_CAP = 25 * 1024
CLAUDE_MD_HARD_LIMIT = 4 * 1024 * 1024  # larger files are silently skipped
SKILL_ENTRY_CAP = 1536  # name+description bytes per skill in the listing
SKILL_LISTING_FRACTION = 0.01  # listing budget scales at 1% of the window
CLAUDE_MD_LINE_TARGET = 200  # documented target, not a hard limit
AGENTS_MD_BYTE_CAP = 32 * 1024  # Codex project_doc_max_bytes

HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
CODE_FENCE = re.compile(r"^\s*```")
CODE_SPAN = re.compile(r"`[^`]*`")
IMPORT_RE = re.compile(r"(?:^|\s)@([A-Za-z0-9_./~\\-][A-Za-z0-9_./~\\@-]*)")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Files that other agent tools load on every request.
FOREIGN_ALWAYS_ON = [
    (".github/copilot-instructions.md", "GitHub Copilot"),
    (".cursorrules", "Cursor (legacy format)"),
    (".windsurfrules", "Windsurf"),
    (".clinerules", "Cline"),
    (".aider.conf.yml", "Aider"),
]


def tokens(n_chars: int) -> int:
    return round(n_chars / 4)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def billable_chars(text: str) -> int:
    """Chars that actually reach the model: HTML comments are stripped first."""
    return len(HTML_COMMENT.sub("", text))


def strip_code(text: str) -> str:
    """Remove fenced blocks and inline code spans.

    Import extraction must run on this. Without it a package name written as
    `@scope/pkg` is reported as a broken import - the single most common false
    positive in this whole script.
    """
    out, in_fence = [], False
    for line in text.splitlines():
        if CODE_FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(CODE_SPAN.sub("", line))
    return "\n".join(out)


def parse_frontmatter(text: str) -> dict:
    """Minimal YAML frontmatter reader: flat scalar keys only.

    Deliberately not a YAML parser. It needs name, description, paths, globs and
    alwaysApply, all of which are flat scalars in practice.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    data, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^\s+", line) and key:
            data[key] += " " + line.strip()
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            data[key] = val.strip().strip("'\"")
    return data


class Entry:
    __slots__ = ("path", "label", "chars", "note")

    def __init__(self, path, label, chars, note=""):
        self.path, self.label, self.chars, self.note = path, label, chars, note


class Ledger:
    def __init__(self, repo: Path, window: int):
        self.repo = repo.resolve()
        self.window = window
        self.always_on: list[Entry] = []
        self.on_demand: list[Entry] = []
        self.warnings: list[str] = []
        self._seen: set[Path] = set()

    # -- helpers -----------------------------------------------------------

    def rel(self, p: Path) -> str:
        try:
            return str(p.resolve().relative_to(self.repo)).replace("\\", "/")
        except ValueError:
            return str(p)

    def add(self, path: Path, label: str, bucket: list, note: str = "") -> bool:
        """Add a file once. Returns False if already counted (symlink/alias)."""
        try:
            real = path.resolve()
        except OSError:
            return False
        if not real.is_file():
            return False
        if real in self._seen:
            return False
        self._seen.add(real)
        text = read(real)
        ghost = self.unmaterialized_symlink(path, text)
        if ghost:
            self.warnings.append(
                f"{self.rel(path)} is a git symlink that was never materialized - on this "
                f"checkout it is a {len(text)}-byte text file whose entire content is the "
                f"literal string `{text.strip()}`. The agent loads that string, not "
                f"{ghost.name}. Replace it with a real `@{text.strip()}` import, which works "
                "on every platform."
            )
            note = note or "DEAD - unmaterialized symlink"
        bucket.append(Entry(self.rel(path), label, billable_chars(text), note))
        return True

    def unmaterialized_symlink(self, path: Path, text: str) -> Path | None:
        """A git symlink checked out on a filesystem without symlink support.

        Git stores a symlink as a blob containing the target path. Without
        core.symlinks (the Windows default when the user lacks the privilege),
        checkout writes that blob as a plain file. The result is an always-on
        file whose whole content is a filename - the agent reads the string,
        not the target, and the bridge silently does nothing.
        """
        candidate = text.strip()
        if not candidate or "\n" in candidate or len(candidate) > 200:
            return None
        if not re.fullmatch(r"[A-Za-z0-9_./\\-]+\.[A-Za-z0-9]+", candidate):
            return None
        target = (path.parent / candidate).resolve()
        return target if target.is_file() else None

    # -- discovery ---------------------------------------------------------

    def walk_imports(self, path: Path, depth: int = 1) -> None:
        """Follow @path imports. They load at launch - imports are not a size fix."""
        if depth > MAX_IMPORT_DEPTH:
            self.warnings.append(
                f"import chain from {self.rel(path)} exceeds {MAX_IMPORT_DEPTH} hops; "
                "deeper files are never loaded"
            )
            return
        for raw in IMPORT_RE.findall(strip_code(read(path))):
            target = (
                Path(os.path.expanduser("~")) / raw[2:]
                if raw.startswith("~/")
                else (path.parent / raw)
            )
            if not target.exists():
                self.warnings.append(
                    f"broken import `@{raw}` in {self.rel(path)} - resolves to nothing"
                )
                continue
            if self.add(target, f"@import (depth {depth})", self.always_on):
                self.walk_imports(target, depth + 1)

    def collect_memory_files(self) -> None:
        """CLAUDE.md at every level, plus ancestors above the repo root."""
        home = Path(os.path.expanduser("~"))
        for name, label in (
            ("CLAUDE.md", "user memory"),
            (".claude/CLAUDE.md", "user memory"),
        ):
            p = home / name
            if self.add(p, label, self.always_on):
                self.walk_imports(p)

        for rules_dir, scope in ((home / ".claude/rules", "user"), (self.repo / ".claude/rules", "project")):
            if rules_dir.is_dir():
                for rule in sorted(rules_dir.glob("*.md")):
                    fm = parse_frontmatter(read(rule))
                    if "paths" in fm:
                        self.add(rule, f"{scope} rule (path-scoped)", self.on_demand)
                    else:
                        self.add(rule, f"{scope} rule (unscoped)", self.always_on,
                                 "no `paths:` - loads every session")

        # Repo root and every ancestor directory up to the filesystem root.
        chain = [self.repo] + list(self.repo.parents)
        for d in chain:
            for name in ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md"):
                p = d / name
                where = "project" if d == self.repo else f"ancestor {self.rel(d)}"
                if self.add(p, f"{where} memory", self.always_on):
                    self.walk_imports(p)

        mem = self.repo / ".claude/MEMORY.md"
        if mem.is_file():
            text = read(mem)
            lines = text.splitlines()
            loaded = "\n".join(lines[:MEMORY_LINE_CAP])[:MEMORY_BYTE_CAP]
            self.always_on.append(Entry(self.rel(mem), "auto-memory", len(loaded)))
            if len(lines) > MEMORY_LINE_CAP or len(text) > MEMORY_BYTE_CAP:
                self.warnings.append(
                    f"{self.rel(mem)} exceeds the {MEMORY_LINE_CAP}-line / 25 KB cutoff; "
                    "everything past it is silently dropped"
                )

    def collect_skills(self) -> None:
        """Only name+description load at launch. Bodies are on demand."""
        roots = [self.repo / ".claude/skills", Path(os.path.expanduser("~")) / ".claude/skills"]
        listing = 0
        for root in roots:
            if not root.is_dir():
                continue
            for skill in sorted(root.glob("*/SKILL.md")):
                text = read(skill)
                fm = parse_frontmatter(text)
                if fm.get("disable-model-invocation", "").lower() == "true":
                    self.on_demand.append(
                        Entry(self.rel(skill), "skill (user-invoked)", billable_chars(text),
                              "not in the listing - zero always-on cost")
                    )
                    continue
                entry = len(f"{fm.get('name', '')}{fm.get('description', '')}")
                if entry > SKILL_ENTRY_CAP:
                    self.warnings.append(
                        f"{self.rel(skill)}: name+description is {entry} chars, over the "
                        f"{SKILL_ENTRY_CAP}-char cap - it is truncated in the listing"
                    )
                listing += min(entry, SKILL_ENTRY_CAP)
                body = billable_chars(text)
                self.on_demand.append(Entry(self.rel(skill), "skill body", body))
                for ref in sorted(skill.parent.rglob("*.md")):
                    if ref != skill:
                        self.on_demand.append(
                            Entry(self.rel(ref), "skill reference", billable_chars(read(ref)))
                        )
        if listing:
            self.always_on.append(Entry("(skill listing)", "skill name+description", listing))
            budget = self.window * SKILL_LISTING_FRACTION
            if tokens(listing) > budget:
                self.warnings.append(
                    f"skill listing is ~{tokens(listing)} tokens, over the "
                    f"{budget:.0f}-token budget ({SKILL_LISTING_FRACTION:.0%} of window); "
                    "least-used descriptions get dropped silently"
                )

    def collect_foreign(self) -> None:
        for rel, tool in FOREIGN_ALWAYS_ON:
            self.add(self.repo / rel, f"{tool} (always-on)", self.always_on)

        cursor = self.repo / ".cursor/rules"
        if cursor.is_dir():
            for rule in sorted(cursor.glob("*.mdc")):
                fm = parse_frontmatter(read(rule))
                always = fm.get("alwaysApply", "").lower() == "true"
                bucket = self.always_on if always else self.on_demand
                self.add(rule, f"Cursor rule ({'always' if always else 'scoped'})", bucket)

        gh = self.repo / ".github/instructions"
        if gh.is_dir():
            for rule in sorted(gh.glob("*.md")):
                self.add(rule, "Copilot rule (path-scoped)", self.on_demand)

    def collect_agents_md(self) -> None:
        """AGENTS.md is invisible to Claude Code unless a CLAUDE.md bridges to it."""
        skip = {".git", "node_modules", "vendor", "dist", "build", ".venv"}
        found = sorted(
            p for p in self.repo.rglob("AGENTS.md") if not skip & set(p.parts)
        )
        if not found:
            return
        sizes = {p: billable_chars(read(p)) for p in found}
        for p in found:
            if p.resolve() not in self._seen:
                self.on_demand.append(
                    Entry(self.rel(p), "AGENTS.md", sizes[p],
                          "read by Codex, not by Claude Code")
                )

        root_claude = self.repo / "CLAUDE.md"
        bridged = False
        if root_claude.is_file():
            text = read(root_claude)
            if root_claude.is_symlink() and "AGENTS" in str(root_claude.resolve()):
                bridged = True
            elif "@AGENTS.md" in strip_code(text):
                bridged = True
            elif self.unmaterialized_symlink(root_claude, text):
                bridged = True  # intent is clear; the broken-symlink warning already fired
        total = sum(sizes.values())
        if not bridged:
            where = "and no CLAUDE.md exists" if not root_claude.is_file() else \
                    "and CLAUDE.md neither imports nor symlinks to them"
            self.warnings.append(
                f"{len(found)} AGENTS.md file(s) (~{tokens(total)} tokens) {where} - "
                "Claude Code never reads them. That guidance is dead weight for Claude "
                "and live for Codex, so the two agents behave differently on this repo."
            )

        # Codex's 32 KiB cap applies to one root-to-leaf chain, not the repo total.
        worst, worst_chain = 0, ()
        for p in found:
            chain = tuple(
                q for q in found
                if q.parent == self.repo or q.parent in p.parents or q.parent == p.parent
            )
            size = sum(sizes[q] for q in chain)
            if size > worst:
                worst, worst_chain = size, chain
        if worst > AGENTS_MD_BYTE_CAP:
            names = ", ".join(self.rel(q) for q in worst_chain)
            self.warnings.append(
                f"the merged AGENTS.md chain [{names}] is {worst:,} bytes, over Codex's "
                f"{AGENTS_MD_BYTE_CAP:,}-byte cap - Codex silently truncates the overflow, "
                "so the guidance at the end of the chain never reaches the model"
            )

    def collect_harness_config(self) -> None:
        """Settings, hooks, output styles and slash commands.

        Hooks and settings do not enter the context window as prose, but a hook
        that injects text does, and they change what the agent is permitted to
        do - so an audit that ignores them misreads why an instruction is or is
        not being followed.
        """
        for rel, label in (
            (".claude/settings.json", "project settings"),
            (".claude/settings.local.json", "local settings"),
        ):
            p = self.repo / rel
            if p.is_file():
                self.on_demand.append(
                    Entry(self.rel(p), label, 0, "governs permissions and hooks, not context")
                )
        for d, label in (
            (self.repo / ".claude/commands", "slash command"),
            (self.repo / ".claude/output-styles", "output style"),
        ):
            if d.is_dir():
                for f in sorted(d.glob("*.md")):
                    self.add(f, label, self.on_demand)

    def check_limits(self) -> None:
        for e in self.always_on:
            if e.chars > CLAUDE_MD_HARD_LIMIT:
                self.warnings.append(
                    f"{e.path} exceeds 4 MiB - the file is skipped ENTIRELY, not truncated"
                )
        root = self.repo / "CLAUDE.md"
        if root.is_file():
            n = len(read(root).splitlines())
            if n > CLAUDE_MD_LINE_TARGET:
                self.warnings.append(
                    f"CLAUDE.md is {n} lines against a documented {CLAUDE_MD_LINE_TARGET}-line "
                    "target - past this, rules start getting lost in the noise"
                )

    def run(self) -> None:
        self.collect_memory_files()
        self.collect_skills()
        self.collect_foreign()
        self.collect_agents_md()
        self.collect_harness_config()
        self.check_limits()

    # -- output ------------------------------------------------------------

    def totals(self) -> tuple[int, int]:
        return (sum(e.chars for e in self.always_on), sum(e.chars for e in self.on_demand))

    def to_dict(self) -> dict:
        a, o = self.totals()
        return {
            "repo": str(self.repo),
            "window": self.window,
            "always_on_tokens": tokens(a),
            "always_on_pct": round(100 * tokens(a) / self.window, 2),
            "on_demand_tokens": tokens(o),
            "always_on": [
                {"path": e.path, "label": e.label, "tokens": tokens(e.chars), "note": e.note}
                for e in sorted(self.always_on, key=lambda e: -e.chars)
            ],
            "on_demand": [
                {"path": e.path, "label": e.label, "tokens": tokens(e.chars), "note": e.note}
                for e in sorted(self.on_demand, key=lambda e: -e.chars)
            ],
            "warnings": self.warnings,
        }

    def render(self) -> str:
        a, o = self.totals()
        out = [f"# Always-on ledger - {self.repo.name}", ""]
        out.append("Loaded at the start of every session, before the user types anything.")
        out.append("")
        out.append("| Tokens | % window | File | Kind |")
        out.append("|---:|---:|---|---|")
        for e in sorted(self.always_on, key=lambda e: -e.chars):
            if not e.chars:
                continue
            pct = 100 * tokens(e.chars) / self.window
            note = f" — {e.note}" if e.note else ""
            out.append(f"| {tokens(e.chars):,} | {pct:.2f}% | `{e.path}` | {e.label}{note} |")
        out.append(f"| **{tokens(a):,}** | **{100 * tokens(a) / self.window:.2f}%** | "
                   f"**ALWAYS-ON TOTAL** | |")
        out.append("")
        out.append(f"On-demand context (costs nothing until used): ~{tokens(o):,} tokens "
                   f"across {len(self.on_demand)} files.")
        if self.warnings:
            out.append("")
            out.append("## Mechanical limits breached")
            out.append("")
            for w in self.warnings:
                out.append(f"- {w}")
        out.append("")
        out.append("_Token counts are chars/4 (~±15% on prose, under-counts code and CJK)._")
        return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    ap.add_argument("--window", type=int, default=200_000, help="context window size")
    args = ap.parse_args()

    repo = Path(args.repo)
    if not repo.is_dir():
        print(f"not a directory: {repo}", file=sys.stderr)
        return 2

    ledger = Ledger(repo, args.window)
    ledger.run()
    if args.json:
        print(json.dumps(ledger.to_dict(), indent=2))
    else:
        print(ledger.render())
    return 0


if __name__ == "__main__":
    sys.exit(main())

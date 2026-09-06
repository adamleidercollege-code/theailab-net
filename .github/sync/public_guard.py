#!/usr/bin/env python3
"""Audit a repo tree for the dev-to-public sync invariants (Phase 2, plan Sec 5.4).

CLI contract (depended on by other phases -- keep exact):

    python3 .github/sync/public_guard.py <repo_root> [--allow FILE] [--deny FILE] [--skip-gitleaks]

Defaults: --allow and --deny default to public.allow / private.deny sitting
next to this script (i.e. <script_dir>/public.allow, <script_dir>/private.deny).

Exit codes: 0 when clean, 1 when any violation is found.

Output: one line per violation, in the form

    VIOLATION <rule-id>: <path-or-detail>

where rule-id is one of:
    denylisted, not-allowlisted, marker, gitleaks, oversize, week-state, week-md

On success (possibly after WARNING lines), prints:

    OK <n> files audited

Rules implemented:
    1. No tracked path matches the denylist.                    -> denylisted
    2. Every tracked path is allowlisted OR matches
       weeks/week-??.html.                                       -> not-allowlisted
    3. No file contains the private-content marker (see MARKER
       below -- deliberately not spelled out as a contiguous
       literal in this docstring, so the guard's own source never
       trips its own rule).                                       -> marker
    4. `gitleaks detect --no-git --source <root>` is clean
       (skipped with a WARNING if gitleaks is missing or
       --skip-gitleaks is passed).                                -> gitleaks
    5. No tracked file is larger than 5 MB.                       -> oversize
    6. Week invariant: every weeks/week-??.html contains
       "<!-- sync:state (live|pending)" and, if
       weeks/manifest.json exists, its recorded state agrees.     -> week-state
    7. No weeks/*.md is tracked.                                  -> week-md

"Tracked" means `git -C <root> ls-files`. Stdlib only -- no third-party deps.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

WEEK_HTML_RE = re.compile(r"^weeks/week-\d\d\.html$")
WEEK_MD_RE = re.compile(r"^weeks/.*\.md$")
SYNC_STATE_RE = re.compile(r"<!--\s*sync:state\s+(live|pending)")
# Built by concatenation, never as a contiguous literal: this file is
# itself published to B (it's part of .github/sync/**), and the literal
# form of this marker is exactly what rule 3 / push.sh's marker sweep
# scans for. A contiguous literal here would make the guard flag its own
# source as a violation, and would make push.sh's marker sweep delete the
# guard from B right after copying it.
MARKER = "sync:" + "private"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def parse_glob_list(path: Path) -> list[str]:
    """Parse a rsync-include-style or plain glob list file.

    Lines starting with '#' are comments (also supports trailing inline
    comments after whitespace + '#'). Blank lines are skipped.

    Lines may carry an rsync-style '+' (include) or '-' (exclude) prefix.
    For the purposes of "is this path allow/deny-listed", only '+' lines
    (and bare, unprefixed lines) are meaningful membership patterns; a
    '-' line (e.g. the catch-all "- *" at the end of public.allow, or
    "- /tests/sync/**") is an rsync-only exclusion and is NOT added to the
    returned pattern list -- otherwise a trailing "- *" would make every
    path match "allowlisted" via the stripped pattern "*". private.deny
    has no +/- prefixes and is parsed the same way (every line is a bare
    pattern, so all of them are kept).

    A leading '/' (repo-root anchor) is stripped from each kept pattern,
    so the remaining text is a plain glob matched against repo-relative
    tracked paths. A pattern ending in '/' is treated as "this directory
    and everything under it" (see _single_match).
    """
    patterns: list[str] = []
    if not path.exists():
        return patterns
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Strip inline comments (whitespace followed by '#')
        line = re.split(r"\s+#", line, maxsplit=1)[0].strip()
        if not line:
            continue
        # rsync-style prefix: '-' lines are exclusions, not membership
        # patterns -- drop them entirely (see docstring).
        if line[0] == "-":
            continue
        if line[0] == "+":
            line = line[1:].strip()
        if not line:
            continue
        # Strip leading root anchor
        if line.startswith("/"):
            line = line[1:]
        if not line:
            continue
        patterns.append(line)
    return patterns


def path_matches_any(rel_path: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if _single_match(rel_path, pat):
            return True
    return False


def _single_match(rel_path: str, pat: str) -> bool:
    # Directory rule: "core/" or "core/**" or "core/**.html" all mean
    # "under this directory". A bare "core/" should also match the
    # directory prefix itself but paths are files so this is moot; what
    # matters is matching any file under it.
    if pat.endswith("/"):
        prefix = pat
        return rel_path.startswith(prefix)
    if fnmatch.fnmatch(rel_path, pat):
        return True
    # For patterns like "core/**.html" fnmatch's '**' behaves like '*'
    # (no special recursive semantics), which already matches
    # "core/about.html" via '*' since fnmatch treats '**' as '*' repeated
    # -- but to be safe for deeper nesting (core/sub/about.html), also
    # try converting "**" to "*" recursively-equivalent by testing with
    # a regex translation.
    if "**" in pat:
        regex = fnmatch.translate(pat).replace(re.escape("**"), ".*")
        # fnmatch.translate already escapes '*' region; simplest robust
        # approach: build our own regex from the pattern directly.
        regex2 = _glob_to_regex(pat)
        if re.match(regex2, rel_path):
            return True
    return False


def _glob_to_regex(pat: str) -> str:
    # Translate a limited glob syntax to regex:
    #   **  -> match anything including '/'
    #   *   -> match anything except '/'
    #   ?   -> match a single non-'/' char
    out = []
    i = 0
    while i < len(pat):
        c = pat[i]
        if pat[i : i + 2] == "**":
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return "^" + "".join(out) + "$"


def git_ls_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def check_denylisted(tracked: list[str], deny_patterns: list[str]) -> list[str]:
    violations = []
    for rel_path in tracked:
        if path_matches_any(rel_path, deny_patterns):
            violations.append(f"VIOLATION denylisted: {rel_path}")
    return violations


def check_not_allowlisted(tracked: list[str], allow_patterns: list[str]) -> list[str]:
    violations = []
    for rel_path in tracked:
        if WEEK_HTML_RE.match(rel_path):
            continue
        if path_matches_any(rel_path, allow_patterns):
            continue
        violations.append(f"VIOLATION not-allowlisted: {rel_path}")
    return violations


def check_marker(root: Path, tracked: list[str]) -> list[str]:
    violations = []
    for rel_path in tracked:
        full = root / rel_path
        try:
            if not full.is_file():
                continue
            data = full.read_bytes()
        except OSError:
            continue
        if MARKER.encode() in data:
            violations.append(f"VIOLATION marker: {rel_path}")
    return violations


def check_gitleaks(root: Path, skip: bool) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    violations: list[str] = []
    if skip:
        warnings.append("WARNING gitleaks skipped (--skip-gitleaks)")
        return violations, warnings
    import shutil

    if shutil.which("gitleaks") is None:
        warnings.append("WARNING gitleaks not found on PATH; skipping scan")
        return violations, warnings
    result = subprocess.run(
        ["gitleaks", "detect", "--no-git", "--source", str(root)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stdout.strip() + "\n" + result.stderr.strip()).strip()
        detail = detail.replace("\n", " | ") if detail else "gitleaks reported findings"
        violations.append(f"VIOLATION gitleaks: {detail}")
    return violations, warnings


def check_oversize(root: Path, tracked: list[str]) -> list[str]:
    violations = []
    for rel_path in tracked:
        full = root / rel_path
        try:
            size = full.stat().st_size
        except OSError:
            continue
        if size > MAX_BYTES:
            violations.append(f"VIOLATION oversize: {rel_path} ({size} bytes)")
    return violations


def check_week_state(root: Path, tracked: list[str]) -> list[str]:
    violations = []
    week_html = [p for p in tracked if WEEK_HTML_RE.match(p)]
    manifest_path = root / "weeks" / "manifest.json"
    manifest: dict | None = None
    if "weeks/manifest.json" in tracked and manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            violations.append(f"VIOLATION week-state: weeks/manifest.json unreadable ({exc})")
            manifest = None

    for rel_path in week_html:
        full = root / rel_path
        try:
            text = full.read_text(errors="replace")
        except OSError as exc:
            violations.append(f"VIOLATION week-state: {rel_path} unreadable ({exc})")
            continue
        m = SYNC_STATE_RE.search(text)
        if not m:
            violations.append(f"VIOLATION week-state: {rel_path} missing sync:state comment")
            continue
        html_state = m.group(1)
        if manifest is not None:
            # week number from filename weeks/week-NN.html
            week_num = rel_path.split("week-")[1].split(".html")[0]
            entry = manifest.get(week_num)
            manifest_state = entry.get("state") if isinstance(entry, dict) else None
            if manifest_state is not None and manifest_state != html_state:
                violations.append(
                    f"VIOLATION week-state: {rel_path} sync:state={html_state} "
                    f"but manifest.json state={manifest_state}"
                )
    return violations


def check_week_md(tracked: list[str]) -> list[str]:
    violations = []
    for rel_path in tracked:
        if WEEK_MD_RE.match(rel_path):
            violations.append(f"VIOLATION week-md: {rel_path}")
    return violations


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", type=Path)
    parser.add_argument("--allow", type=Path, default=None)
    parser.add_argument("--deny", type=Path, default=None)
    parser.add_argument("--skip-gitleaks", action="store_true")
    args = parser.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    allow_path = args.allow if args.allow is not None else script_dir / "public.allow"
    deny_path = args.deny if args.deny is not None else script_dir / "private.deny"

    root = args.repo_root.resolve()
    if not root.is_dir():
        print(f"VIOLATION oversize: repo_root does not exist: {root}")
        return 1

    allow_patterns = parse_glob_list(allow_path)
    deny_patterns = parse_glob_list(deny_path)

    try:
        tracked = git_ls_files(root)
    except subprocess.CalledProcessError as exc:
        print(f"VIOLATION denylisted: git ls-files failed: {exc}")
        return 1

    violations: list[str] = []
    warnings: list[str] = []

    violations += check_denylisted(tracked, deny_patterns)
    violations += check_not_allowlisted(tracked, allow_patterns)
    violations += check_marker(root, tracked)
    gitleaks_violations, gitleaks_warnings = check_gitleaks(root, args.skip_gitleaks)
    violations += gitleaks_violations
    warnings += gitleaks_warnings
    violations += check_oversize(root, tracked)
    violations += check_week_state(root, tracked)
    violations += check_week_md(tracked)

    for w in warnings:
        print(w)
    for v in violations:
        print(v)

    if violations:
        return 1

    print(f"OK {len(tracked)} files audited")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

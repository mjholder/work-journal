#!/usr/bin/env python3
"""Repoint the webby plugin's daily-note skills at this vault's layout.

Webby 2.1.0 assumes a numbered PARA layout (10_Daily/, 20_Work/,
80_System/Templates/, _AGENT_MANIFEST.md). This vault uses the legacy layout
(Daily/, Work/, Projects/, templates/). Any skill that hardcodes 10_Daily/
writes to the wrong folder and silently recreates it.

This script is idempotent and safe to re-run after a plugin update.

Usage:  python3 .claude/scripts/fix-webby-paths.py [--plugin-dir DIR]

Scope: only the daily-note paths. vault-save and vault-query additionally
depend on _AGENT_MANIFEST.md and the id-based naming scheme, which this
script deliberately does not fake.
"""

import argparse
import sys
from pathlib import Path

DEFAULT_PLUGIN = Path.home() / ".claude-enmaas/plugins/cache/ducky/webby/2.1.0"

# Applied to every skill file and the plugin CLAUDE.md, in order.
GLOBAL_REPLACEMENTS = [
    # Longest-first: the slash and filename variants must be consumed before
    # the bare forms below, or "10_Daily/" would become "Daily//".
    ("10_Daily/", "Daily/"),
    ("10_Daily", "Daily"),
    ("80_System/Templates/Daily-Template.md", "templates/daily.md"),
    ("80_System/Templates/", "templates/"),
]

# Applied only to skills/todo/SKILL.md. The vault template carries a
# Drawing Prompt section and a {date} placeholder, so read it directly
# instead of the plugin's pre-rendered copy.
TODO_OLD = (
    "read `${CLAUDE_PLUGIN_ROOT}/skills/_shared/daily-template.md`, "
    "replace `YYYY-MM-DD` with today's date and `DayOfWeek, Month D, YYYY` "
    'with the output of `date +"%A, %B %-d, %Y"`, then write it with '
    "`mcp__obsidian__write_note`"
)
TODO_NEW = (
    "read `templates/daily.md` with `mcp__obsidian__read_note`, replace "
    "`{date}` with today's date, then write the result to "
    "`Daily/YYYY-MM-DD.md` with `mcp__obsidian__write_note`"
)

# The trailing sentence still called the plugin's shared copy the source of
# truth, which contradicts reading the vault template directly.
SOT_OLD = (
    "Do not inline the template here; the shared file is the single source of "
    "truth and must match the vault's `templates/daily.md`."
)
SOT_NEW = (
    "Do not inline the template here; `templates/daily.md` in the vault is the "
    "single source of truth."
)

TODO_REPLACEMENTS = [(TODO_OLD, TODO_NEW), (SOT_OLD, SOT_NEW)]


def patch_file(path: Path, replacements, report):
    try:
        text = original = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        report.append(f"  ! skipped {path}: {exc}")
        return 0

    hits = 0
    for old, new in replacements:
        if old in text:
            hits += text.count(old)
            text = text.replace(old, new)

    if text != original:
        path.write_text(text, encoding="utf-8")
        report.append(f"  patched {path.relative_to(plugin_dir)} ({hits} replacement(s))")
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-dir", type=Path, default=DEFAULT_PLUGIN)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    global plugin_dir
    plugin_dir = args.plugin_dir

    if not plugin_dir.is_dir():
        print(f"error: plugin directory not found: {plugin_dir}", file=sys.stderr)
        print("Pass --plugin-dir if the plugin version changed.", file=sys.stderr)
        return 1

    targets = sorted(plugin_dir.glob("skills/*/SKILL.md"))
    targets += [plugin_dir / "skills/_shared/README.md", plugin_dir / "CLAUDE.md"]

    report, total = [], 0
    for path in targets:
        if not path.is_file():
            continue
        if args.dry_run:
            text = path.read_text(encoding="utf-8")
            n = sum(text.count(old) for old, _ in GLOBAL_REPLACEMENTS)
            if n:
                report.append(f"  would patch {path.relative_to(plugin_dir)} ({n})")
            total += n
        else:
            total += patch_file(path, GLOBAL_REPLACEMENTS, report)

    todo = plugin_dir / "skills/todo/SKILL.md"
    if todo.is_file():
        todo_text = todo.read_text(encoding="utf-8")
        if any(old in todo_text for old, _ in TODO_REPLACEMENTS):
            if args.dry_run:
                report.append("  would patch skills/todo/SKILL.md (template source)")
            else:
                patch_file(todo, TODO_REPLACEMENTS, report)
        total += 1

    print("\n".join(report) if report else "  already patched — nothing to do")

    if not args.dry_run:
        leftover = []
        for path in targets:
            if path.is_file() and "10_Daily" in path.read_text(encoding="utf-8"):
                leftover.append(str(path.relative_to(plugin_dir)))
        if leftover:
            print(f"\nwarning: '10_Daily' still present in: {', '.join(leftover)}", file=sys.stderr)
            return 2
        print("\nNo '10_Daily' references remain in the patched files.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

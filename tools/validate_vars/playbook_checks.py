from __future__ import annotations

import re
from pathlib import Path


SELF_REFERENTIAL_VAR_RE = re.compile(
    r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*"\{\{\s*\1(?:\s*\|[^}]*)?\s*\}\}"\s*$'
)
INCLUDE_TASK_RE = re.compile(r"^\s*ansible\.builtin\.(?:import_tasks|include_tasks):")
TASK_START_RE = re.compile(r"^\s*-\s")


def find_self_referential_task_vars(playbooks_root: Path) -> list[str]:
    """Scan playbook task imports/includes for recursive var handoffs.

    Purpose:
        Detect self-referential variable forwarding inside `vars:` blocks that
        belong to `ansible.builtin.import_tasks` or `ansible.builtin.include_tasks`
        statements. These assignments can trigger recursive templating failures
        when the imported task references the same variable in task names or
        expressions.

    Inputs:
        playbooks_root (Path): Repository `playbooks/` directory to scan.

    Returns:
        list[str]: Human-readable validation errors with file and line context.

    Constraints:
        - This is a structural guard for repo-authored task files, not a full YAML parser.
        - Only `vars:` blocks attached to task includes/imports are checked.
    """
    errors: list[str] = []
    for path in sorted(playbooks_root.rglob("*.yml")):
        errors.extend(_scan_playbook_file(path))
    return errors


def _scan_playbook_file(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    errors: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if not TASK_START_RE.match(line):
            index += 1
            continue

        task_indent = _indent(line)
        block_end = _find_task_end(lines, index + 1, task_indent)
        include_line_index = _find_include_line(lines, index, block_end)
        if include_line_index is None:
            index = block_end
            continue

        vars_line_index = _find_vars_line(lines, include_line_index + 1, block_end, task_indent)
        if vars_line_index is None:
            index = block_end
            continue

        vars_indent = _indent(lines[vars_line_index])
        child_start = vars_line_index + 1
        child_end = _find_child_block_end(lines, child_start, block_end, vars_indent)
        for child_index in range(child_start, child_end):
            child_line = lines[child_index]
            if SELF_REFERENTIAL_VAR_RE.match(child_line):
                errors.append(
                    f"{path.as_posix()}:{child_index + 1}: "
                    f"self-referential task var handoff under include/import vars: `{child_line.strip()}`"
                )

        index = block_end

    return errors


def _find_task_end(lines: list[str], start: int, task_indent: int) -> int:
    index = start
    while index < len(lines):
        line = lines[index]
        if TASK_START_RE.match(line) and _indent(line) <= task_indent:
            return index
        index += 1
    return len(lines)


def _find_include_line(lines: list[str], start: int, end: int) -> int | None:
    for index in range(start, end):
        if INCLUDE_TASK_RE.match(lines[index]):
            return index
    return None


def _find_vars_line(lines: list[str], start: int, end: int, task_indent: int) -> int | None:
    for index in range(start, end):
        line = lines[index]
        if _indent(line) <= task_indent:
            return None
        if re.match(r"^\s*vars:\s*$", line):
            return index
    return None


def _find_child_block_end(lines: list[str], start: int, end: int, parent_indent: int) -> int:
    index = start
    while index < end:
        line = lines[index]
        if line.strip() and _indent(line) <= parent_indent:
            return index
        index += 1
    return end


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))

"""Deterministic plumbing for test generation: find coverage gaps, summarise results.

Used by the generate-tests skill and by .github/workflows/test-generation.yml, so the
local run and CI split the work the same way. Standard library only.

    python coverage_gaps.py plan <base-ref> <coverage.json>
        Prints a JSON array with one object per target test module with coverage gaps
        in changed route handlers: {"slug", "module", "test_file", "gaps"}.

    python coverage_gaps.py summary <plan.json> <coverage-before.json> <coverage-after.json> [notes.md ...]
        Prints the PR summary in Markdown.
"""

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)


def changed_app_files(base_ref: str) -> list[str]:
    out = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=AM",
            f"{base_ref}...HEAD",
            "--",
            "app",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [path for path in out.split() if path.endswith(".py")]


def changed_lines(base_ref: str, module: str) -> set[int]:
    # New-side line numbers added or modified in the diff. A pure deletion (count 0)
    # adds no lines, but it still changed whatever handler it sits in, so it counts
    # as touching line c, the line before the deletion point.
    out = subprocess.run(
        [
            "git",
            "diff",
            "--unified=0",
            "--diff-filter=AM",
            f"{base_ref}...HEAD",
            "--",
            module,
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    lines = set()
    for start, count in HUNK.findall(out):
        start, count = int(start), int(count) if count else 1
        lines.update(range(start, start + count) if count else [start])
    return lines


def route_handlers(source: str) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    # Only route handlers are in scope: startup code and dependencies such as
    # lifespan and get_session are replaced in tests by design.
    handlers = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            func = decorator.func if isinstance(decorator, ast.Call) else decorator
            if isinstance(func, ast.Attribute) and func.attr in HTTP_METHODS:
                handlers.append(node)
                break
    return handlers


def plan(base_ref: str, coverage_path: str) -> list[dict]:
    files = json.loads(Path(coverage_path).read_text())["files"]
    modules = []
    for module in changed_app_files(base_ref):
        report = files.get(module)
        if report is None:
            continue
        missing = set(report["missing_lines"])
        missing_branches = report.get("missing_branches", [])
        changed = changed_lines(base_ref, module)
        gaps = []
        for handler in route_handlers(Path(module).read_text()):
            # Decorators sit above handler.lineno; include them in the span.
            first = min([d.lineno for d in handler.decorator_list] + [handler.lineno])
            span = range(first, handler.end_lineno + 1)
            if changed.isdisjoint(span):
                continue
            lines = sorted(line for line in missing if line in span)
            branches = [branch for branch in missing_branches if branch[0] in span]
            if lines or branches:
                gaps.append(
                    {"function": handler.name, "lines": lines, "branches": branches}
                )
        if gaps:
            slug = Path(module).stem
            modules.append(
                {
                    "slug": slug,
                    "module": module,
                    "test_file": f"tests/test_{slug}.py",
                    "gaps": gaps,
                }
            )
    return modules


def collect_test_names(source: str) -> set[str]:
    return {
        node.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }


def added_tests(test_file: str) -> list[str]:
    path = Path(test_file)
    if not path.exists():
        return []
    head = subprocess.run(
        ["git", "show", f"HEAD:{test_file}"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout
    return sorted(collect_test_names(path.read_text()) - collect_test_names(head or ""))


def percent(coverage: dict, module: str) -> str:
    report = coverage.get(module)
    return f"{report['summary']['percent_covered_display']}%" if report else "—"


def summary(plan_path: str, before_path: str, after_path: str, notes: list[str]) -> str:
    modules = json.loads(Path(plan_path).read_text())
    before = json.loads(Path(before_path).read_text())["files"]
    after = json.loads(Path(after_path).read_text())["files"]

    added = {m["test_file"]: added_tests(m["test_file"]) for m in modules}
    total = sum(len(names) for names in added.values())
    files = sum(1 for names in added.values() if names)

    lines = ["## Test Generation", ""]
    lines.append(
        f"Added {total} tests across {files} files" if total else "No tests added"
    )
    lines += ["", "| File | Coverage before | Coverage after |", "|---|---|---|"]
    for m in modules:
        lines.append(
            f"| {m['module']} | {percent(before, m['module'])} | {percent(after, m['module'])} |"
        )
    for m in modules:
        if added[m["test_file"]]:
            lines += [
                "",
                f"`{m['test_file']}`: "
                + ", ".join(f"`{n}`" for n in added[m["test_file"]]),
            ]
    for note in notes:
        path = Path(note)
        if path.exists() and path.read_text().strip():
            lines += ["", path.read_text().strip()]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    command, *args = sys.argv[1:]
    if command == "plan":
        print(json.dumps(plan(*args)))
    elif command == "summary":
        print(summary(args[0], args[1], args[2], args[3:]), end="")
    else:
        sys.exit(f"unknown command: {command}")

---
name: generate-tests
description: Generates pytest tests for coverage gaps in app code changed on the current branch, without duplicating existing tests. Use when asked to fill test coverage gaps or generate tests for a branch or PR.
allowed-tools: [Read, Edit(tests/**), Edit(reports/**), Bash(uv run pytest *), Bash(uv run python .claude/skills/generate-tests/scripts/coverage_gaps.py *)]
disallowed-tools: [Edit(app/**), Bash(git commit *), Bash(git push *), Bash(uv add *)]
argument-hint: [base-ref] [report-path] # defaults: origin/main reports/test-gen-summary.md
---

# Generate Tests

Runs test generation locally, the same way as `.github/workflows/test-generation.yml`, but
one module at a time. In CI each module is a separate parallel job.

Arguments: `$ARGUMENTS`. The first is the base ref (default `origin/main`). The second is the
report path (default `reports/test-gen-summary.md`).

## Instructions

1. Measure the baseline, from the repo root:
   `uv run pytest -q --cov --cov-report=json:reports/coverage-before.json`.
   If any test fails, write the failures to the report and stop. Don't fix existing tests.
2. Plan:
   `uv run python .claude/skills/generate-tests/scripts/coverage_gaps.py plan <base-ref> reports/coverage-before.json`.
   Save the output to `reports/plan.json`. It's a list of modules with gaps. If it's empty (`[]`),
   write `No coverage gaps in changed route handlers.` to the report and stop.
3. For each module in the plan:
   - Write its `gaps` array to `reports/gaps-<slug>.json`.
   - Follow `.claude/skills/write-tests/SKILL.md` with these arguments:
     `<test_file> reports/gaps-<slug>.json reports/notes-<slug>.md`.
4. Run `uv run pytest -q --cov --cov-report=json:reports/coverage-after.json`. If the full suite
   fails, fix or delete the failing new tests and re-run.
5. Write the report:
   `uv run python .claude/skills/generate-tests/scripts/coverage_gaps.py summary reports/plan.json reports/coverage-before.json reports/coverage-after.json reports/notes-*.md`.
   Save the output to the report path.

Only edit files under `tests/` and `reports/`. Never edit app code, even to fix a bug.

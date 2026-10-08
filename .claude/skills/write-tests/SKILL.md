---
name: write-tests
description: Writes pytest tests for a given list of coverage gaps in one test module. Used by generate-tests and by each fan-out leg of the test-generation workflow.
allowed-tools: [Read, Edit(tests/**), Edit(reports/**), Bash(uv run pytest *)]
disallowed-tools: [Edit(app/**), Edit(tests/conftest.py), Bash(git *), Bash(uv add *)]
argument-hint: <test-file> <gaps-json> <notes-path> # e.g. tests/test_users.py reports/gaps-users.json reports/notes-users.md
---

# Write Tests

Writes tests for one test module. It runs on its own, in parallel with other modules,
so it must stay inside its target file.

Arguments: `$ARGUMENTS`
1. the target test file
2. a JSON file listing the gaps. Each entry has `function`, `lines` and `branches` (as `[from, to]`
   line pairs).
3. where to write notes

## Instructions

1. Read `tests/conftest.py`, the gaps file, the app module behind each gap and the target test file. If the target doesn't exist yet, create it with the imports and layout of `tests/routers/test_users.py`.
2. For each gap, check whether an existing test already asserts that behaviour. If one does, skip the gap and note it. Don't write a near-copy.
3. Append tests to the end of the target file. Write the fewest tests that cover the gaps, one behaviour each, following the testing rule (`.claude/rules/testing.md`). In CI it's appended to the system prompt; interactively it loads when you work under `tests/`.
4. Run `uv run pytest <target file> -q` and fix your tests until they pass. If a test fails because the app's behaviour looks wrong, delete the test and note it as a suspected bug. Don't change the assertion to match. Then check each new test against the review standard and remove any that fail it.
5. Edit only the target file and the notes file. Never touch `tests/conftest.py` or app code. If you need a fixture that `conftest.py` doesn't have, define it in the target file.
6. Only write the notes file if there is something to report. If there is, use this layout:

   ```
   ### Notes: <target file>
   - Skipped: <gap>, <reason>
   - Suspected bug: <endpoint>, <what looks wrong>
   - Local fixture: <name>, <why conftest didn't cover it>
   ```

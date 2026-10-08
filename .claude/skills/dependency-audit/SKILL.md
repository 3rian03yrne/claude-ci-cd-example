---
name: dependency-audit
description: Audits the project python dependencies. Use to determine if the current python dependencies are pinned, contain known vulnerabilities, or adverse statuses. 
allowed-tools: [Bash(uv tree *), Bash(uv audit *), Write(reports/**), Edit(reports/**)]
disallowed-tools: [Bash(uv lock *), Bash(uv sync *), Bash(uv add *)]
argument-hint: [dependency-audit.md] # filename 
context: fork
---

# Dependency Skill

Audits the project python dependencies and make recommendations as needed.

## Instructions

1. Confirm a `uv.lock` exists in the repo root. If it does not, write a report saying the audit was skipped because there is no lockfile, and stop.
2. Review `pyproject.toml`, and `.python-version` for pinned versions of python and dependencies. 
3. Run from the repo root: `uv audit`. A non-zero exit code usually means vulnerabilities were found; that is a result to report, not a failure to retry.
4. Check for current and outdated dependency versions by running from the repo root: `uv tree --outdated --depth 1`
5. Write the audit report to reports/$ARGUMENTS in the repo root using this layout:
  * A Heading: `## Dependency Audit`
  * A one-line verdict: either `No known vulnerabilities found` or `N vulnerabilities found in M packages`.
  * If there are findings, a table with columns: Package | Installed | Advisory ID | Severity (if given) | Fixed in
  * For each finding with a fix available, a short "Suggested fix" line, e.g. uv lock --upgrade-package <name>.
  * The raw uv audit output inside a collapsed <details> block.
  * If unpinned dependencies or python versions are found include a subheading: `### Warning: unpinned dependencies found`
  * Create a table ONLY if there are unpinned dependencies with columns: Package | Dependency Group | Suggested Pin
  * For each unpinned dependencies suggest pinning to the current version taken from the uv tree output.
  * For outdated dependencies, do not create a table, but suggest the user review the raw uv tree results with either: `Dependencies are up to date` or `Review optional dependency upgrades`.
  * Include the raw uv tree output inside a collapsed <details> block
6. Report only what uv audit printed. Do not invent advisory IDs, severities, or fixed versions. If a field is missing from the output, write "—".
7. Do not modify pyproject.toml, uv.lock, or any other project file.

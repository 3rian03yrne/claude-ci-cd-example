# Claude CI/CD Example

Claude CI/CD examples for a minimal FastAPI project.

## Example Covered

* Automated Dependency Reporting
* Automated Test Generation

## How it works

* A Pull Request will kick off the GitHub Action Workflows: dependency-audit and test-generation
* The dependency-audit workflow installs dependencies needed for the audit (i.e. `uv`) and then runs Claude non-interactively with a custom skill triggered with a simple backslash command as the prompt: `/dependency-audit`. 
* The test-generation workflow runs a script that identifies test coverage gaps, and then uses a matrix strategey that runs Claude non-interactively in parallel per module with a custom `/write-tests` skill.

## Commands

Start local dev

```
uv run fastapi dev
```

Run tests

```
uv run pytest
```

Run coverage report

```
uv run pytest --cov
```

## Project Structure

The project has the structure of a typical FastAPI project.

```
├── app
│   ├── routers
│   │   ├── orders.py
│   │   └── users.py
│   ├── database.py
│   ├── main.py
│   └── models.py
├── tests
│   ├── routers
│   │   ├── test_orders.py
│   │   └── test_users.py
│   ├── conftest.py
│   └── test_main.py
├── pyproject.toml
└── uv.lock
```

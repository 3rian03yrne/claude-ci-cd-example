# Claude CI/CD Example

Claude CI/CD examples for a minimal FastAPI project.

## Example Covered

* Automated Dependency Reporting
* Automated Test Generation

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

---
paths: ["tests/**"]
---

# Testing

How to write tests in this repo. 

## Standards

- One behaviour per test. Name it `test_<endpoint>_<case>`, e.g. `test_get_user_not_found`.
- Arrange / act / assert, separated by blank lines (see `tests/test_users.py`).
- Assert the status code and the whole JSON body, not individual keys, unless a value
  is non-deterministic (e.g. `created_at`: pop it and check it separately).
- Decimals come back as strings: assert `"9.90"`, not `9.9`.
- No sleeps, no network, no reliance on test order.
- Test through the HTTP API with `client`. Don't call router functions directly.

A new test is accepted when all of these hold:

1. It covers a line or branch that was previously missed, or a distinct behaviour (status code, error message, validation rule) that no existing test asserts.
2. It doesn't repeat an existing test's arrangement and assertions.
3. It passes, deterministically, with the full suite.
4. It asserts current behaviour. If the behaviour looks wrong, report it as a suspected bug instead of writing a test that locks it in.

## Fixtures

- Use the fixtures in `tests/conftest.py`:
  - `client`: a `TestClient` bound to a fresh in-memory DB per test
  - `make_user` / `make_order`: factories that arrange data
- Don't build `Session`s, engines or model rows by hand in a test; extend a factory instead.
- Add a new fixture to `conftest.py` only when two or more test modules need it.
  Otherwise keep it in the module that uses it.
- One test module per router: `app/routers/x.py` → `tests/routers/test_x.py`.

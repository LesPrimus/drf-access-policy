# Project handoff / TODO

Working notes so this can be picked up on another machine (by a human or another
Claude Code agent). Read this top to bottom before continuing.

## What this is

A fork of [`drf-access-policy`](https://github.com/rsinger86/drf-access-policy)
(upstream is unmaintained — last release `1.5.0`, March 2023). We are
modernizing it and republishing it under a new name.

## Decisions already made (do not re-litigate without the owner)

| Topic | Decision |
| --- | --- |
| PyPI distribution name | **`drf-access-policy2`** (available on PyPI; original name is taken) |
| Import / package name | **stays `rest_access_policy`** — keeps it a drop-in replacement (`from rest_access_policy import ...`) |
| Python support | **3.12+** |
| Statements API | **strict dataclass-only**: `Statement(...)` instances required; passing a `dict` raises `AccessPolicyException` |
| `field_permissions` dict | **removed**; replaced by `read_only_fields` on `Statement`, matched **principal-only**, applied by `FieldAccessMixin` on write requests (POST/PUT/PATCH) |
| Test framework | **port to pytest** (full idiom: functions + fixtures, `assert`, `pytest.raises`, `@pytest.mark.django_db`) via `pytest-django` |
| Test runner | **pytest becomes canonical**; replace the old `tox.ini` / `manage.py test` flow |

## Branch

All work is on **`feat/dataclass-only-statements`** (off `master`). The only git
remote is `origin` → the fork (`github.com/LesPrimus/drf-access-policy`). There
is no `upstream` remote.

## Status

### Done
- [x] `rest_access_policy/access_policy.py` — `Statement` self-normalizes scalars
      to lists + validates `effect` in `__post_init__`; added `read_only_fields`
      field. Engine is dataclass-only: attribute access everywhere,
      `_validate_statements` rejects non-`Statement` items, new
      `_get_user_principals` helper (set-based principal matching, resolves group
      values once), removed `asdict`/dict normalization.
- [x] `rest_access_policy/field_access_mixin.py` — dropped the `field_permissions`
      dict path; new `_apply_read_only_fields` reads `Statement.read_only_fields`,
      matches by principal via `_get_user_principals`, applies on write methods.
- [x] `test_project/testapp/access_policies.py` — fixtures converted to `Statement(...)`.
- [x] `test_project/testapp/tests/test_statement.py` — updated for normalized
      fields + new `read_only_fields`.

### In progress / next up
- [ ] **Rewrite `test_project/testapp/tests/test_access_policy.py`** — still the
      OLD dict-based version; it will FAIL against the refactored engine. Convert
      all dict statements to `Statement(...)`, switch assertions to attribute
      access (`result[0].action` not `result[0]["action"]`), and replace
      `test_normalize_statements` with tests for `_validate_statements`
      (pass-through for `Statement`s; raises `AccessPolicyException` for a dict).
      A drafted version exists in the chat history but was not written to disk
      because we pivoted to pytest first — write it directly in **pytest style**.
- [ ] **Port all tests to pytest** (full idiom). Files: `test_access_policy.py`,
      `test_statement.py`, `test_views.py`, `test_view_set.py`,
      `test_view_set_mixin.py`, `test_fields.py`. Add a `conftest.py` with
      fixtures (`api_client` → DRF `APIClient`, user/group factories replacing
      `setUp`). Mark DB tests with `@pytest.mark.django_db`.
- [ ] **Add pytest config + deps**: `pytest`, `pytest-django` as dev deps;
      `[tool.pytest.ini_options]` in `pyproject.toml` with
      `DJANGO_SETTINGS_MODULE = "test_project.settings"` and test path globs.
      Replace/retire `tox.ini`.
- [ ] **Fix Python 3.12+ blocker**: `test_project/settings.py` imports
      `from distutils.version import StrictVersion` (line ~14) and has a Django
      1.8 block — `distutils` was removed in Python 3.12. Delete both.
- [ ] **Packaging for PyPI** (was the original goal): port `setup.py` metadata
      into a real `pyproject.toml` (hatchling backend; `name = "drf-access-policy2"`,
      `requires-python = ">=3.12"`, deps `djangorestframework` + `pyparsing`,
      package `rest_access_policy`, include `py.typed`). Remove `setup.py`.
      Note: current `pyproject.toml`/`uv.lock` on disk are throwaway `uv init`
      stubs (`version 0.1.0`, `requires-python >=3.14`, no deps) and are NOT
      committed — recreate them properly.
- [ ] Update `README.md` badges + source URL for the fork; rewrite the dict-based
      statement examples to `Statement(...)`; document `read_only_fields` and the
      removal of `field_permissions`. Same for the `docs/` site.
- [ ] Run the full suite green, then build (`uv build`) and verify wheel/sdist
      contents (must include `rest_access_policy` + `py.typed`). Do NOT upload to
      PyPI without explicit owner go-ahead.

## Gotchas / notes
- `pyparsing` API used (`infixNotation`, `opAssoc`, `Keyword`, `Word`) is fine on
  pyparsing 3.x — no code change needed.
- `read_only_fields` matching is **principal-only** by design (action/effect/
  condition are intentionally NOT considered for field read-only).
- Local `.venv`/`venv` and `.idea/` are gitignored; don't commit them.
- Tests can't run yet on this machine: needs a Django/DRF env (and the distutils
  fix above) — set that up as part of the pytest task.
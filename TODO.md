# Fork modernization + PyPI rebrand

Working notes so this can be picked up on another machine (by a human or another
Claude Code agent). Read this top to bottom before continuing.

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development`
> (recommended) or `superpowers:executing-plans` to implement the plan
> task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the modernization of this fork and republish it on PyPI as
`drf-access-policy2`. Import name stays `rest_access_policy` — drop-in
replacement for the unmaintained upstream.

**Architecture:** Python 3.12+, dataclass-only `Statement` API, pytest test
suite, `pyproject.toml` (hatchling backend). No tox, no `setup.py`, no
`requirements.{in,txt}`.

**Tech stack:** Django, DRF, pyparsing, pytest, pytest-django, hatchling, uv.

---

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
| Test framework | **pytest** (full idiom: functions + fixtures, `assert`, `pytest.raises`, `@pytest.mark.django_db`) via `pytest-django` |
| Test runner | **pytest is canonical**; retire `tox.ini` / `manage.py test` flow |
| Build backend | **hatchling** via `pyproject.toml` |
| Dep/runner tool | **uv** (`uv run pytest`, `uv build`) |

### Decisions to confirm before Task 2 lands

| Topic | Suggested default | Note |
| --- | --- | --- |
| First release version | **`2.0.0`** | Breaking from upstream `1.5.0` (dataclass-only, removed `field_permissions`, Py 3.12+ required). Override in `pyproject.toml` if you'd rather signal "same code, new name" with `1.5.0`. |
| Author metadata | `LesPrimus <amerigo.armentano@hotmail.it>` | Change in `pyproject.toml` `[project.authors]` if you don't want the email exposed. |

## Branch

All work is on **`feat/dataclass-only-statements`** (off `master`). The only git
remote is `origin` → the fork (`github.com/LesPrimus/drf-access-policy`). There
is no `upstream` remote.

## Done

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
      fields + new `read_only_fields` (still `APITestCase` style — Task 4 below
      ports it to pytest idiom).

---

## Implementation plan

Tasks are ordered to fail fast on environment issues, then build the test
runner, then port tests file-by-file (smallest → largest), then package +
publish prep. Commit after each task.

> Run all `pytest` / `uv` commands from the repo root.

### Task 1: Unblock Python 3.12 (`distutils` removal)

**Files:**
- Modify: `test_project/settings.py:13-17, 45-47`

Python 3.12 removed `distutils`. The `StrictVersion` branch only existed to
toggle a Django 1.8 special-case that no longer applies (Django 3.1 is the
floor in current `requirements.in` and we're moving to modern Django anyway).
Delete both the import and the conditional `INSTALLED_APPS` append.

- [ ] **Step 1: Remove the `distutils` import and the Django 1.8 block**

Edit `test_project/settings.py`. Delete line 14 (`from distutils.version import StrictVersion`) and lines 45-47 (the `# Django 1.8 requires...` comment plus the `if StrictVersion(...)` block).

After the edit, the top of the file should look like:

```python
import os

import django

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
```

…and `INSTALLED_APPS` should end right after the `test_project.testapp` line — no conditional append below it.

- [ ] **Step 2: Sanity-check the file imports clean**

Run: `python -c "import ast; ast.parse(open('test_project/settings.py').read())"`
Expected: no output (syntax OK).

- [ ] **Step 3: Commit**

```bash
git add test_project/settings.py
git commit -m "chore: drop distutils.version usage (Py3.12+ blocker)"
```

---

### Task 2: Replace `setup.py` / `tox.ini` / `requirements.*` with `pyproject.toml`

**Files:**
- Create: `pyproject.toml`
- Delete: `setup.py`, `tox.ini`, `requirements.in`, `requirements.txt`, `pypi_submit.py`

`pyproject.toml` carries both packaging metadata (for `drf-access-policy2` on
PyPI) and pytest config. We collapse the four legacy files into it.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "drf-access-policy2"
version = "2.0.0"
description = "Declarative access policies/permissions for Django REST Framework, modeled after AWS IAM. Maintained fork of drf-access-policy."
readme = "README.md"
requires-python = ">=3.12"
license = { file = "LICENSE.md" }
authors = [{ name = "LesPrimus", email = "amerigo.armentano@hotmail.it" }]
keywords = ["django", "restframework", "drf", "access", "policy", "authorization", "declarative"]
classifiers = [
    "License :: OSI Approved :: MIT License",
    "Framework :: Django",
    "Framework :: Django :: 4.2",
    "Framework :: Django :: 5.0",
    "Framework :: Django :: 5.1",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
dependencies = [
    "djangorestframework",
    "pyparsing",
]

[project.optional-dependencies]
dev = [
    "django",
    "pytest",
    "pytest-django",
]

[project.urls]
Homepage = "https://github.com/LesPrimus/drf-access-policy"
Source = "https://github.com/LesPrimus/drf-access-policy"

[tool.hatch.build.targets.wheel]
packages = ["rest_access_policy"]

[tool.hatch.build.targets.sdist]
include = [
    "rest_access_policy",
    "README.md",
    "LICENSE.md",
]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "test_project.settings"
python_files = ["test_*.py"]
testpaths = ["test_project/testapp/tests"]
addopts = "-ra"
```

Notes:
- `version` defaults to `2.0.0` per the "Decisions to confirm" table. Change to `1.5.0` if you prefer the "same code, new name" framing.
- `[project.authors]` email is exposed in package metadata. Drop the `email = ...` key if you don't want it indexed.

- [ ] **Step 2: Delete the superseded files**

```bash
git rm setup.py tox.ini requirements.in requirements.txt pypi_submit.py
```

- [ ] **Step 3: Bootstrap the environment with uv and install dev deps**

```bash
uv venv
uv pip install -e ".[dev]"
```

Expected: `uv venv` creates `.venv/`; `uv pip install` resolves and installs `django`, `djangorestframework`, `pyparsing`, `pytest`, `pytest-django`, and the project itself in editable mode. No errors.

- [ ] **Step 4: Confirm pytest discovers the suite (collection only)**

Run: `uv run pytest --collect-only -q`
Expected: collection succeeds (no import errors). Some old tests may still appear as `unittest.TestCase`-style; that's fine — they'll be ported in Tasks 4-9. Failures here usually mean `DJANGO_SETTINGS_MODULE` isn't being picked up — re-check `[tool.pytest.ini_options]`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "build: replace setup.py/tox/requirements with pyproject.toml (drf-access-policy2)"
```

---

### Task 3: Add `conftest.py` with shared fixtures

**Files:**
- Create: `test_project/testapp/tests/conftest.py`

Tests share these patterns: an `APIClient`, creating `User` and `Group` rows,
optionally force-authenticating. Replace per-class `setUp` with fixtures.

- [ ] **Step 1: Write the conftest**

```python
import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_group(db):
    def _make_group(name):
        group, _ = Group.objects.get_or_create(name=name)
        return group

    return _make_group


@pytest.fixture
def make_user(db, make_group):
    """
    Factory for a Django ``User`` optionally placed in the given group names.
    """

    def _make_user(username="user", group_names=()):
        user = User.objects.create(username=username)
        for name in group_names:
            user.groups.add(make_group(name))
        return user

    return _make_user


@pytest.fixture
def auth_client(api_client, make_user):
    """
    Returns (client, user) with ``force_authenticate`` already applied.
    """

    def _auth(username="user", group_names=()):
        user = make_user(username=username, group_names=group_names)
        api_client.force_authenticate(user=user)
        return api_client, user

    return _auth
```

- [ ] **Step 2: Smoke-test the fixture wiring**

Run: `uv run pytest --collect-only test_project/testapp/tests/conftest.py -q`
Expected: collection passes (no errors).

- [ ] **Step 3: Commit**

```bash
git add test_project/testapp/tests/conftest.py
git commit -m "test: add pytest conftest with api_client/make_user fixtures"
```

---

### Task 4: Port `test_statement.py` to pytest

**Files:**
- Modify: `test_project/testapp/tests/test_statement.py` (full rewrite)

No DB, no client — pure dataclass behaviour. Drop `APITestCase`, switch to
module-level functions and plain `assert`.

- [ ] **Step 1: Rewrite the file**

```python
from dataclasses import asdict

import pytest

from rest_access_policy import Statement


def test_should_raise_error_if_invalid_effect():
    with pytest.raises(ValueError, match="effect must be one of"):
        Statement(principal="*", action="build", effect="veto")


def test_scalar_values_are_normalized_to_lists():
    statement = Statement(
        principal="*",
        action="build",
        effect="allow",
        condition="is_sunny",
        condition_expression="is_sunny or is_cloudy",
        read_only_fields="status",
    )

    assert statement.principal == ["*"]
    assert statement.action == ["build"]
    assert statement.condition == ["is_sunny"]
    assert statement.condition_expression == ["is_sunny or is_cloudy"]
    assert statement.read_only_fields == ["status"]


def test_to_dict():
    statement = Statement(
        principal="*",
        action="build",
        effect="allow",
        condition_expression=["method1"],
    )

    assert asdict(statement) == {
        "principal": ["*"],
        "action": ["build"],
        "effect": "allow",
        "condition": [],
        "condition_expression": ["method1"],
        "read_only_fields": [],
    }
```

Note: the original test used `Exception` + substring match; the engine actually raises `ValueError` (see `Statement.__post_init__`). `pytest.raises(ValueError, match=...)` is the precise form.

- [ ] **Step 2: Run the file**

Run: `uv run pytest test_project/testapp/tests/test_statement.py -v`
Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
git add test_project/testapp/tests/test_statement.py
git commit -m "test: port test_statement to pytest"
```

---

### Task 5: Port `test_view_set_mixin.py` to pytest

**Files:**
- Modify: `test_project/testapp/tests/test_view_set_mixin.py` (full rewrite)

No DB. Verifies `AccessViewSetMixin` enforces `access_policy` and composes
`permission_classes` without mutating the class attribute.

- [ ] **Step 1: Rewrite the file**

```python
import pytest
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ViewSet

from rest_access_policy import AccessPolicy, AccessViewSetMixin


def test_should_raise_error_if_no_access_policy_set():
    class MyViewSet(AccessViewSetMixin, ViewSet):
        pass

    with pytest.raises(Exception, match="you must assign an AccessPolicy "):
        MyViewSet()


def test_should_not_raise_error_if_access_policy_set():
    class MyViewSet(AccessViewSetMixin, ViewSet):
        access_policy = AccessPolicy

    MyViewSet()  # no exception


def test_prepend_policy_to_permissions_without_modifying_class_attribute():
    class MyViewSet(AccessViewSetMixin, ViewSet):
        access_policy = AccessPolicy

    v = MyViewSet()
    assert v.permission_classes == [AccessPolicy, AllowAny]
    assert MyViewSet.permission_classes == [AllowAny]
```

- [ ] **Step 2: Run the file**

Run: `uv run pytest test_project/testapp/tests/test_view_set_mixin.py -v`
Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
git add test_project/testapp/tests/test_view_set_mixin.py
git commit -m "test: port test_view_set_mixin to pytest"
```

---

### Task 6: Port `test_view_set.py` to pytest

**Files:**
- Modify: `test_project/testapp/tests/test_view_set.py` (full rewrite)

Uses the DB. `setUp` deletes are replaced by `@pytest.mark.django_db`'s
per-test transaction rollback.

- [ ] **Step 1: Rewrite the file**

```python
import pytest
from rest_framework.reverse import reverse

from test_project.testapp.models import UserAccount


@pytest.mark.django_db
def test_create_allowed(auth_client):
    client, _ = auth_client(username="admin_user", group_names=["admin"])

    for name in ["account-mixin-test-list", "account-list"]:
        url = reverse(name)
        response = client.post(
            url,
            {"username": "fred", "first_name": "Fred", "last_name": "Rogers"},
            format="json",
        )
        assert response.status_code == 201


@pytest.mark.django_db
def test_retrieve_denied(auth_client):
    account = UserAccount.objects.create(
        username="fred", first_name="Fred", last_name="Rogers"
    )
    client, _ = auth_client(username="banned_user", group_names=["banned"])

    url = reverse("account-detail", args=[account.id])
    response = client.get(url, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_set_password_should_be_allowed(auth_client):
    account = UserAccount.objects.create(
        username="fred", first_name="Fred", last_name="Rogers"
    )
    client, _ = auth_client(username="regular", group_names=["regular_users"])

    url = reverse("account-set-password", args=[account.id])
    response = client.post(url, format="json")
    assert response.status_code == 200


@pytest.mark.django_db
def test_set_password_should_be_denied(auth_client):
    account = UserAccount.objects.create(
        username="fred", first_name="Fred", last_name="Rogers"
    )
    client, _ = auth_client(username="unprivileged")

    url = reverse("account-set-password", args=[account.id])
    response = client.post(url, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_partial_update_should_not_update_status_for_dev_group(auth_client):
    account = UserAccount.objects.create(
        username="fred", first_name="Fred", last_name="Rogers"
    )
    client, _ = auth_client(username="dev_user", group_names=["dev"])

    url = reverse("account-detail", args=[account.id])
    response = client.patch(
        url, data={"last_name": "Mercury", "status": "inactive"}, format="json"
    )
    assert response.data["last_name"] == "Mercury"
    assert response.data["status"] == "active"
```

- [ ] **Step 2: Run the file**

Run: `uv run pytest test_project/testapp/tests/test_view_set.py -v`
Expected: 5 passed.

- [ ] **Step 3: Commit**

```bash
git add test_project/testapp/tests/test_view_set.py
git commit -m "test: port test_view_set to pytest"
```

---

### Task 7: Port `test_views.py` to pytest

**Files:**
- Modify: `test_project/testapp/tests/test_views.py` (full rewrite)

- [ ] **Step 1: Rewrite the file**

```python
import pytest
from rest_framework.reverse import reverse


@pytest.mark.django_db
def test_admin_can_do_anything_with_logs(auth_client):
    client, _ = auth_client(username="admin", group_names=["admin"])

    response = client.get(reverse("get-logs"), format="json")
    assert response.status_code == 200

    response = client.delete(reverse("delete-logs"), format="json")
    assert response.status_code == 200


@pytest.mark.django_db
def test_dev_can_only_get_logs(auth_client):
    client, _ = auth_client(username="dev", group_names=["dev"])

    response = client.get(reverse("get-logs"), format="json")
    assert response.status_code == 200

    response = client.delete(reverse("delete-logs"), format="json")
    assert response.status_code == 403


def test_anonymous_user_can_view_landing_page(api_client):
    response = api_client.get(reverse("get-landing-page"), format="json")
    assert response.status_code == 200


@pytest.mark.django_db
def test_authenticated_user_can_view_landing_page(auth_client):
    client, _ = auth_client(username="someone")
    response = client.get(reverse("get-landing-page"), format="json")
    assert response.status_code == 200
```

- [ ] **Step 2: Run the file**

Run: `uv run pytest test_project/testapp/tests/test_views.py -v`
Expected: 4 passed.

- [ ] **Step 3: Commit**

```bash
git add test_project/testapp/tests/test_views.py
git commit -m "test: port test_views to pytest"
```

---

### Task 8: Port `test_fields.py` to pytest

**Files:**
- Modify: `test_project/testapp/tests/test_fields.py` (full rewrite)

Two test classes (`FieldsTestCase`, `SlugFieldsTestCase`) become two
module-level test groups. Each test creates a real `User` so it needs DB
access. `FakeRequest` remains as a local helper.

- [ ] **Step 1: Rewrite the file**

```python
from typing import Optional

import pytest
from django.contrib.auth.models import User
from rest_framework.serializers import Serializer

from rest_access_policy import (
    AccessPolicy,
    PermittedPkRelatedField,
    PermittedSlugRelatedField,
)


class FakeRequest:
    def __init__(self, user: Optional[User], method: str = "GET"):
        self.user = user
        self.method = method


@pytest.mark.django_db
def test_pk_field_include_in_scope_object():
    class TestPolicy(AccessPolicy):
        @classmethod
        def scope_queryset(cls, request, queryset):
            return queryset

    class TestSerializer(Serializer):
        user = PermittedPkRelatedField(
            access_policy=TestPolicy, queryset=User.objects.all()
        )

    request_user = User.objects.create(username="Requester")
    user = User.objects.create(username="Test user")

    serializer = TestSerializer(
        data={"user": user.pk},
        context={"request": FakeRequest(user=request_user)},
    )

    assert serializer.is_valid()
    assert serializer.validated_data["user"] == user


@pytest.mark.django_db
def test_pk_field_exclude_out_of_scope_object():
    request_user = User.objects.create(username="Requester")
    user = User.objects.create(username="Test user")

    class TestPolicy(AccessPolicy):
        @classmethod
        def scope_queryset(cls, request, queryset):
            if request.user == request_user:
                return queryset.none()
            return queryset

    class TestSerializer(Serializer):
        user = PermittedPkRelatedField(
            access_policy=TestPolicy, queryset=User.objects.all()
        )

    serializer = TestSerializer(
        data={"user": user.pk},
        context={"request": FakeRequest(user=request_user)},
    )

    assert not serializer.is_valid()
    assert "object does not exist" in str(serializer.errors)


@pytest.mark.django_db
def test_slug_field_include_in_scope_object():
    class TestPolicy(AccessPolicy):
        @classmethod
        def scope_queryset(cls, request, queryset):
            return queryset

    class TestSerializer(Serializer):
        user = PermittedSlugRelatedField(
            access_policy=TestPolicy,
            queryset=User.objects.all(),
            slug_field="username",
        )

    request_user = User.objects.create(username="Requester")
    user = User.objects.create(username="Test user")

    serializer = TestSerializer(
        data={"user": "Test user"},
        context={"request": FakeRequest(user=request_user)},
    )

    assert serializer.is_valid()
    assert serializer.validated_data["user"] == user


@pytest.mark.django_db
def test_slug_field_exclude_out_of_scope_object():
    request_user = User.objects.create(username="Requester")
    user = User.objects.create(username="Test user")

    class TestPolicy(AccessPolicy):
        @classmethod
        def scope_queryset(cls, request, queryset):
            if request.user == request_user:
                return queryset.none()
            return queryset

    class TestSerializer(Serializer):
        user = PermittedSlugRelatedField(
            access_policy=TestPolicy,
            queryset=User.objects.all(),
            slug_field="username",
        )

    serializer = TestSerializer(
        data={"user": "Test user"},
        context={"request": FakeRequest(user=request_user)},
    )

    assert not serializer.is_valid()
    assert "Object with username=Test user does not exist" in str(serializer.errors)
```

- [ ] **Step 2: Run the file**

Run: `uv run pytest test_project/testapp/tests/test_fields.py -v`
Expected: 4 passed.

- [ ] **Step 3: Commit**

```bash
git add test_project/testapp/tests/test_fields.py
git commit -m "test: port test_fields to pytest"
```

---

### Task 9: Rewrite `test_access_policy.py` (dict → `Statement`, unittest → pytest)

**Files:**
- Modify: `test_project/testapp/tests/test_access_policy.py` (full rewrite — 704 lines)

This is the biggest task. The existing file is still dict-based and will fail
against the refactored engine (`_validate_statements` now rejects dicts). It
also uses `unittest.TestCase`. Both must change. Because the file is large, the
rewrite is described as a guided conversion rather than a single inline blob.

**Conversion rules (apply to every test):**

| Old | New |
| --- | --- |
| `class XTestCase(TestCase):` | (delete class; promote methods to module-level functions) |
| `def setUp(self): User.objects.all().delete(); Group.objects.all().delete()` | (delete — `@pytest.mark.django_db` handles DB isolation) |
| `def test_x(self):` | `def test_x():` (or with fixtures, e.g. `def test_x(make_user, make_group):`) |
| `self.assertEqual(a, b)` | `assert a == b` |
| `self.assertTrue(x)` / `self.assertFalse(x)` | `assert x` / `assert not x` |
| `self.assertIn(x, y)` | `assert x in y` |
| `with self.assertRaises(Exception) as ctx:` … `str(ctx.exception)` | `with pytest.raises(Exception, match="..."):` |
| Any test that creates `User`/`Group` rows | add `@pytest.mark.django_db` |
| Tests using only `FakeRequest` + `AccessPolicy()` (no ORM) | no marker needed |
| Statement dicts inside `statements = [{...}, {...}]` | `statements = [Statement(...), Statement(...)]` |
| Result inspection `result[0]["action"]` | `result[0].action` (Statement attr access) |

**Statement-shape patterns (these appear repeatedly in the file):**

```python
# OLD
{"principal": "*", "action": "create", "effect": "allow"}

# NEW
Statement(principal="*", action="create", effect="allow")
```

```python
# OLD
{
    "principal": ["group:admin"],
    "action": ["destroy"],
    "condition": "is_nice_day",
    "effect": "deny",
}

# NEW
Statement(
    principal=["group:admin"],
    action=["destroy"],
    condition="is_nice_day",
    effect="deny",
)
```

**The `test_normalize_statements` test must be replaced**, not converted. The
method `_normalize_statements` no longer exists; `_validate_statements` is its
replacement and has different semantics (validates instead of normalizing):

```python
def test_validate_statements_returns_input_unchanged_for_statement_list():
    policy = AccessPolicy()
    statements = [
        Statement(principal="user:1", action="create", effect="allow"),
        Statement(principal="group:admin", action="destroy", effect="deny"),
    ]
    assert policy._validate_statements(statements) is statements


def test_validate_statements_raises_for_dict_statement():
    policy = AccessPolicy()
    with pytest.raises(
        AccessPolicyException,
        match="Statements must be 'Statement' instances",
    ):
        policy._validate_statements(
            [{"principal": "*", "action": "create", "effect": "allow"}]
        )
```

**Worked conversion example** (one of the existing tests, end-to-end):

```python
# OLD (unittest, dict statements)
class AccessPolicyTests(TestCase):
    def setUp(self):
        User.objects.all().delete()
        Group.objects.all().delete()

    def test_get_user_group_values(self):
        group1 = Group.objects.create(name="admin")
        group2 = Group.objects.create(name="ceo")
        user = User.objects.create(username="mr user")
        user.groups.add(group1, group2)

        policy = AccessPolicy()
        result = sorted(policy.get_user_group_values(user))
        self.assertEqual(result, ["admin", "ceo"])

# NEW (pytest, fixtures)
@pytest.mark.django_db
def test_get_user_group_values(make_user):
    user = make_user(username="mr user", group_names=["admin", "ceo"])

    policy = AccessPolicy()
    result = sorted(policy.get_user_group_values(user))
    assert result == ["admin", "ceo"]
```

**Top-of-file imports for the new module:**

```python
import unittest.mock as mock
from typing import Optional

import pytest
from django.contrib.auth.models import AnonymousUser, Group, User
from rest_framework.decorators import api_view
from rest_framework.viewsets import ModelViewSet

from rest_access_policy import AccessPolicy, AccessPolicyException
from rest_access_policy.access_policy import Statement
```

The `FakeRequest` / `FakeViewSet` helpers at the top of the existing file
stay as module-level classes (they're used pervasively).

- [ ] **Step 1: Read the existing file**

Run: open `test_project/testapp/tests/test_access_policy.py` and skim its 704 lines so you know what you're translating.

- [ ] **Step 2: Rewrite the file end-to-end**

Apply the rules + patterns + worked example above to every test in the file. Replace `test_normalize_statements` with the two `_validate_statements` tests shown above.

- [ ] **Step 3: Run the file**

Run: `uv run pytest test_project/testapp/tests/test_access_policy.py -v`
Expected: every test passes.

If any test fails because the old assertion encoded a dict-shape expectation that no longer makes sense (e.g. inspecting a `result[0]["action"]` shape), fix the test to use attribute access (`result[0].action`). If a test was specifically validating the old dict-input path of the engine, delete it — that path is gone, and `_validate_statements` already covers the rejection case.

- [ ] **Step 4: Commit**

```bash
git add test_project/testapp/tests/test_access_policy.py
git commit -m "test: port test_access_policy to pytest + Statement API"
```

---

### Task 10: Run the full suite green

**Files:** none — verification step.

- [ ] **Step 1: Run all tests**

Run: `uv run pytest -v`
Expected: every test in `test_project/testapp/tests/` passes. No errors, no warnings about deprecated `unittest.TestCase` patterns leaking through.

- [ ] **Step 2: If anything fails, fix the failing test file first**

Don't paper over engine bugs. If a real regression surfaces (engine behaviour changed during the refactor in a way the old test caught), open it as a separate fix and add a focused regression test before continuing.

- [ ] **Step 3: Confirm the legacy entrypoints are gone**

Run: `ls setup.py tox.ini requirements.in requirements.txt pypi_submit.py 2>&1 | grep -v "No such file"`
Expected: no output (all five files are deleted).

- [ ] **Step 4: Commit (only if Step 2 produced fixes)**

```bash
git add <changed files>
git commit -m "fix: <description>"
```

---

### Task 11: Update `README.md` for the rebrand + new API

**Files:**
- Modify: `README.md`

The README is what PyPI renders on the package page, so it has to reflect the
new name, the dataclass-only `Statement` API, and the removal of
`field_permissions`. Minimum scope:

1. Replace the two badges at the top (`drf-access-policy` → `drf-access-policy2`):

```markdown
[![Package version](https://badge.fury.io/py/drf-access-policy2.svg)](https://pypi.python.org/pypi/drf-access-policy2)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-access-policy2.svg)](https://pypi.python.org/pypi/drf-access-policy2)
```

2. Replace every dict-based `statements = [...]` example with `Statement(...)` instances. The two examples currently in the README (lines ~10-24 and ~30-42) must change. Example:

```python
from rest_access_policy import AccessPolicy, Statement


class ArticleAccessPolicy(AccessPolicy):
    statements = [
        Statement(action=["list", "retrieve"], principal="*", effect="allow"),
        Statement(
            action=["publish", "unpublish"],
            principal=["group:editor"],
            effect="allow",
        ),
    ]
```

3. Replace the `field_permissions = {...}` example (around line 41-42) with the new `read_only_fields` on `Statement`:

```python
class UserAccountAccessPolicy(AccessPolicy):
    statements = [
        Statement(principal="group:admin", action=["create", "update"], effect="allow"),
        Statement(
            principal="group:dev",
            action=["update", "partial_update"],
            effect="allow",
            read_only_fields=["status"],
        ),
    ]
```

4. Replace the upstream source-code link (around line 62) with the fork:

```markdown
**Source Code**: <a href="https://github.com/LesPrimus/drf-access-policy" target="_blank">https://github.com/LesPrimus/drf-access-policy</a>
```

5. Replace the "Testing" section at the bottom (around line 186-188) with the pytest flow:

```markdown
# Testing

```bash
uv venv
uv pip install -e ".[dev]"
uv run pytest
```
```

6. Add a `## 2.0` changelog entry at the top of the changelog block, summarising: drop-in fork of `drf-access-policy`; Python 3.12+; dataclass-only `Statement` API; `field_permissions` replaced by `read_only_fields` on `Statement`.

- [ ] **Step 1: Apply edits 1-6 above**

- [ ] **Step 2: Sanity-check that no dict-shaped `statements = [{...}]` examples remain**

Run: `grep -n '"action"' README.md`
Expected: no matches (or only inside `Statement(...)` kwargs, which use bare identifiers — there should genuinely be nothing).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README for drf-access-policy2 (dataclass Statement API)"
```

---

### Task 12: Update the `docs/` site + `mkdocs.yml`

**Files:**
- Modify: `mkdocs.yml`
- Modify: every file under `docs/` that still shows dict-based statements or references upstream URLs

- [ ] **Step 1: Update `mkdocs.yml`**

Change `repo_name` and `repo_url`:

```yaml
repo_name: LesPrimus/drf-access-policy
repo_url: https://github.com/LesPrimus/drf-access-policy
```

(Optional: change `site_name` if you want the rendered docs to say something other than the original "Django REST - Access Policy".)

- [ ] **Step 2: Find all docs files that need rewriting**

Run: `grep -rln 'rsinger86\|"action"\|field_permissions' docs/`
Expected: a list of files. Walk each one and:
- Replace `rsinger86/drf-access-policy` URLs with `LesPrimus/drf-access-policy`.
- Replace dict statement examples with `Statement(...)`.
- Replace `field_permissions` docs with `read_only_fields` on `Statement`.

- [ ] **Step 3: Verify nothing dict-shaped or upstream-referencing remains**

Run: `grep -rln 'rsinger86\|"action"\|field_permissions' docs/ mkdocs.yml`
Expected: no matches.

- [ ] **Step 4: Commit**

```bash
git add docs/ mkdocs.yml
git commit -m "docs: update mkdocs site for fork + dataclass Statement API"
```

---

### Task 13: Build wheel/sdist and verify contents

**Files:** none — verification step.

- [ ] **Step 1: Clean any prior build artifacts**

```bash
rm -rf dist/ build/ *.egg-info
```

- [ ] **Step 2: Build**

Run: `uv build`
Expected: `dist/drf_access_policy2-2.0.0.tar.gz` and `dist/drf_access_policy2-2.0.0-py3-none-any.whl` are produced (filename version matches `pyproject.toml`).

- [ ] **Step 3: Inspect the wheel**

Run: `unzip -l dist/drf_access_policy2-2.0.0-py3-none-any.whl`
Expected: contains `rest_access_policy/__init__.py`, `rest_access_policy/access_policy.py`, `rest_access_policy/py.typed`, and the rest of the package. Does NOT contain `test_project/`, `docs/`, or `tox.ini`.

- [ ] **Step 4: Inspect the sdist**

Run: `tar tzf dist/drf_access_policy2-2.0.0.tar.gz`
Expected: contains `rest_access_policy/`, `README.md`, `LICENSE.md`, `pyproject.toml`. Does NOT contain `.venv/`, `.idea/`, or test data.

- [ ] **Step 5: Do NOT upload to PyPI without explicit owner go-ahead**

This is the final gate before publishing. Stop here. The PyPI upload step
(`uv publish` or `twine upload`) requires an owner decision — `2.0.0` is
irreversible once published.

---

## Optional follow-up (decoupled, do not block 13)

- **GitHub repo rename** `LesPrimus/drf-access-policy` → `LesPrimus/drf-access-policy2` for consistency with the PyPI name. NOT required for PyPI (only the `name` in `pyproject.toml` matters). If done:
  1. Rename on GitHub (web UI or `gh repo rename drf-access-policy2`).
  2. `git remote set-url origin https://github.com/LesPrimus/drf-access-policy2.git`
  3. Re-edit the URLs in `pyproject.toml`, `README.md`, and `mkdocs.yml`.
  4. Commit and push.

## Gotchas / notes

- `pyparsing` API used (`infixNotation`, `opAssoc`, `Keyword`, `Word`) is fine on pyparsing 3.x — no code change needed.
- `read_only_fields` matching is **principal-only** by design (action/effect/condition are intentionally NOT considered for field read-only).
- Local `.venv`/`venv` and `.idea/` are gitignored; don't commit them.
- `Statement.__post_init__` raises `ValueError` (not a custom exception) for invalid `effect`. Tests asserting on the exception type should expect `ValueError`.
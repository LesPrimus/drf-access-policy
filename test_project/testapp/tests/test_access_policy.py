import unittest.mock as mock
from typing import Optional

import pytest
from django.contrib.auth.models import AnonymousUser, Group, User
from rest_framework.decorators import api_view
from rest_framework.viewsets import ModelViewSet

from rest_access_policy import AccessPolicy, AccessPolicyException
from rest_access_policy.access_policy import Statement


class FakeRequest:
    def __init__(self, user: Optional[User], method: str = "GET"):
        self.user = user
        self.method = method


class FakeViewSet:
    def __init__(self, action: str = "create"):
        self.action = action


def test_get_invoked_action_from_function_based_view():
    @api_view(["GET"])
    def my_view(request):
        return ""

    policy = AccessPolicy()
    view_instance = my_view.cls()

    result = policy._get_invoked_action(view_instance)
    assert result == "my_view"


def test_get_invoked_action_from_class_based_view():
    class UserViewSet(ModelViewSet):
        pass

    policy = AccessPolicy()
    view_instance = UserViewSet()
    view_instance.action = "create"

    result = policy._get_invoked_action(view_instance)
    assert result == "create"


@pytest.mark.django_db
def test_get_user_group_values(make_user):
    user = make_user(username="mr user", group_names=["admin", "ceo"])

    policy = AccessPolicy()
    result = sorted(policy.get_user_group_values(user))

    assert result == ["admin", "ceo"]


def test_get_user_group_values_empty_if_user_is_anonymous():
    user = AnonymousUser()
    policy = AccessPolicy()
    result = sorted(policy.get_user_group_values(user))
    assert result == []


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


@pytest.mark.django_db
def test_get_statements_matching_principal_if_user_is_authenticated():
    user = User.objects.create(id=5)
    user.groups.add(Group.objects.create(name="cooks"))

    statements = [
        Statement(principal=["id:5"], action=["create"]),
        Statement(principal=["group:dev"], action=["destroy"]),
        Statement(principal=["group:cooks"], action=["do_something"]),
        Statement(principal=["*"], action=["*"]),
        Statement(principal=["id:79"], action=["vote"]),
        Statement(principal=["anonymous"], action=["anonymous_action"]),
        Statement(principal=["authenticated"], action=["authenticated_action"]),
        Statement(principal=["staff"], action=["staff_action"]),
        Statement(principal=["admin"], action=["admin_action"]),
    ]

    policy = AccessPolicy()
    result = policy._get_statements_matching_principal(FakeRequest(user), statements)

    assert len(result) == 4
    assert result[0].action == ["create"]
    assert result[1].action == ["do_something"]
    assert result[2].action == ["*"]
    assert result[3].action == ["authenticated_action"]


@pytest.mark.django_db
def test_get_statements_matching_principal_if_user_is_staff():
    user = User.objects.create(id=5, is_staff=True)
    user.groups.add(Group.objects.create(name="cooks"))

    statements = [
        Statement(principal=["id:5"], action=["create"]),
        Statement(principal=["group:dev"], action=["destroy"]),
        Statement(principal=["group:cooks"], action=["do_something"]),
        Statement(principal=["*"], action=["*"]),
        Statement(principal=["id:79"], action=["vote"]),
        Statement(principal=["anonymous"], action=["anonymous_action"]),
        Statement(principal=["authenticated"], action=["authenticated_action"]),
        Statement(principal=["staff"], action=["staff_action"]),
        Statement(principal=["admin"], action=["admin_action"]),
    ]

    policy = AccessPolicy()
    result = policy._get_statements_matching_principal(FakeRequest(user), statements)

    assert len(result) == 5
    assert result[0].action == ["create"]
    assert result[1].action == ["do_something"]
    assert result[2].action == ["*"]
    assert result[3].action == ["authenticated_action"]
    assert result[4].action == ["staff_action"]


@pytest.mark.django_db
def test_get_statements_matching_principal_if_user_is_admin():
    user = User.objects.create(id=5, is_staff=True, is_superuser=True)
    user.groups.add(Group.objects.create(name="cooks"))

    statements = [
        Statement(principal=["id:5"], action=["create"]),
        Statement(principal=["group:dev"], action=["destroy"]),
        Statement(principal=["group:cooks"], action=["do_something"]),
        Statement(principal=["*"], action=["*"]),
        Statement(principal=["id:79"], action=["vote"]),
        Statement(principal=["anonymous"], action=["anonymous_action"]),
        Statement(principal=["authenticated"], action=["authenticated_action"]),
        Statement(principal=["staff"], action=["staff_action"]),
        Statement(principal=["admin"], action=["admin_action"]),
    ]

    policy = AccessPolicy()
    result = policy._get_statements_matching_principal(FakeRequest(user), statements)

    assert len(result) == 6
    assert result[0].action == ["create"]
    assert result[1].action == ["do_something"]
    assert result[2].action == ["*"]
    assert result[3].action == ["authenticated_action"]
    assert result[4].action == ["staff_action"]
    assert result[5].action == ["admin_action"]


def test_get_statements_matching_principal_if_user_is_anonymous():
    user = AnonymousUser()

    statements = [
        Statement(principal=["id:5"], action=["create"]),
        Statement(principal=["*"], action=["list"]),
        Statement(principal=["anonymous"], action=["anonymous_action"]),
        Statement(principal=["authenticated"], action=["authenticated_action"]),
        Statement(principal=["staff"], action=["staff_action"]),
        Statement(principal=["admin"], action=["admin_action"]),
    ]

    policy = AccessPolicy()
    result = policy._get_statements_matching_principal(FakeRequest(user), statements)

    assert len(result) == 2
    assert result[0].action == ["list"]
    assert result[1].action == ["anonymous_action"]


def test_get_statements_matching_action_when_method_unsafe():
    statements = [
        Statement(principal=["id:5"], action=["create"]),
        Statement(principal=["group:dev"], action=["destroy"]),
        Statement(principal=["group:cooks"], action=["do_something"]),
        Statement(principal=["*"], action=["*"]),
        Statement(principal=["id:79"], action=["vote"]),
        Statement(principal=["id:900"], action=["<safe_methods>"]),
    ]

    policy = AccessPolicy()
    result = policy._get_statements_matching_action(
        FakeRequest(None, method="DELETE"), "destroy", statements
    )

    assert len(result) == 2
    assert result[0].action == ["destroy"]
    assert result[1].action == ["*"]


def test_get_statements_matching_action_when_method_safe():
    statements = [
        Statement(principal=["*"], action=["list"]),
        Statement(principal=["id:5"], action=["*"]),
        Statement(principal=["group:cooks"], action=["<safe_methods>"]),
        Statement(principal=["group:devs"], action=["destroy"]),
    ]

    policy = AccessPolicy()
    result = policy._get_statements_matching_action(
        FakeRequest(None, method="GET"), "list", statements
    )

    assert len(result) == 3
    assert result[0].principal == ["*"]
    assert result[1].principal == ["id:5"]
    assert result[2].principal == ["group:cooks"]


def test_get_statements_matching_action_when_using_http_method_placeholder():
    statements = [
        Statement(principal=["*"], action=["create"]),
        Statement(principal=["group:cooks"], action=["<method:post>"]),
        Statement(principal=["group:devs"], action=["destroy"]),
    ]

    policy = AccessPolicy()
    result = policy._get_statements_matching_action(
        FakeRequest(None, method="POST"), "an action that won't match", statements
    )

    assert len(result) == 1
    assert result[0].principal == ["group:cooks"]


def test_get_statements_matching_conditions():
    class TestPolicy(AccessPolicy):
        def is_true(self, request, view, action):
            return True

        def is_false(self, request, view, action):
            return False

        def is_cloudy(self, request, view, action):
            return True

        def is_arg_true(self, request, view, action, arg):
            return eval(arg)

    statements = [
        Statement(principal=["id:1"], action=["create"]),
        Statement(principal=["id:2"], action=["create"], condition=["is_true"]),
        Statement(principal=["id:4"], action=["create"], condition=["is_false"]),
        Statement(
            principal=["id:5"],
            action=["create"],
            condition_expression=["is_cloudy", "is_false and is_true"],
        ),
        Statement(
            principal=["id:6"],
            action=["create"],
            condition_expression=["is_false and is_true", "is_cloudy"],
        ),
        Statement(
            principal=["id:7"],
            action=["create"],
            condition_expression=["is_true or is_false"],
        ),
        Statement(
            principal=["id:8"],
            action=["create"],
            condition_expression=["is_true and not is_false"],
        ),
        Statement(
            principal=["id:9"],
            action=["create"],
            condition_expression=["not not is_true"],
        ),
        Statement(
            principal=["id:10"],
            action=["create"],
            condition_expression=["not (is_true and is_false)"],
        ),
        Statement(
            principal=["id:11"],
            action=["create"],
            condition_expression=["is_false or not is_true and is_cloudy"],
        ),
        Statement(
            principal=["id:12"],
            action=["create"],
            condition_expression=["is_false or not is_true or not is_cloudy"],
        ),
        Statement(
            principal=["id:13"],
            action=["create"],
            condition_expression=["is_false or not (is_true and is_cloudy)"],
        ),
        Statement(
            principal=["id:14"],
            action=["create"],
            condition_expression=["is_true or is_false or is_cloudy"],
        ),
        Statement(
            principal=["id:15"],
            action=["create"],
            condition_expression=["is_false or is_arg_true:True"],
        ),
        Statement(
            principal=["id:16"],
            action=["create"],
            condition_expression=["is_false or is_arg_true:False"],
        ),
    ]

    policy = TestPolicy()

    result = policy._get_statements_matching_conditions(
        None, None, action=None, statements=statements, is_expression=True
    )
    result = policy._get_statements_matching_conditions(
        None, None, action=None, statements=result, is_expression=False
    )

    assert [s.principal for s in result] == [
        ["id:1"],
        ["id:2"],
        ["id:7"],
        ["id:8"],
        ["id:9"],
        ["id:10"],
        ["id:14"],
        ["id:15"],
    ]


@mock.patch("rest_access_policy.access_policy.BoolOperand")
def test_complex_condition_parser_not_called_for_simple_condition(op_mock):
    op_mock.setParseAction = mock.MagicMock()

    class TestPolicy(AccessPolicy):
        def is_cloudy(self, request, view, action):
            return True

    statements = [
        Statement(principal=["id:1"], action=["create"], condition=["is_cloudy"]),
    ]

    policy = TestPolicy()
    result = policy._get_statements_matching_conditions(
        None, None, action=None, statements=statements, is_expression=False
    )

    assert result == statements
    op_mock.setParseAction.assert_not_called()


def test_check_condition_throws_error_if_no_method():
    class TestPolicy(AccessPolicy):
        pass

    policy = TestPolicy()

    with pytest.raises(
        AccessPolicyException,
        match="condition 'is_sunny' must be a method on the access policy",
    ):
        policy._check_condition("is_sunny", None, None, "action")


def test_check_condition_throws_error_if_returns_non_boolean():
    class TestPolicy(AccessPolicy):
        def is_sunny(self, request, view, action):
            return "yup"

    policy = TestPolicy()

    with pytest.raises(
        AccessPolicyException,
        match="condition 'is_sunny' must return true/false, not",
    ):
        policy._check_condition("is_sunny", None, None, "action")


def test_check_condition_is_called():
    class TestPolicy(AccessPolicy):
        def is_sunny(self, request, view, action):
            return True

    policy = TestPolicy()

    assert policy._check_condition("is_sunny", None, None, "action")


def test_check_condition_is_called_with_custom_arg():
    class TestPolicy(AccessPolicy):
        def user_is(self, request, view, action, field_name: str):
            return field_name == "owner"

    policy = TestPolicy()

    assert policy._check_condition("user_is:owner", None, None, "action")
    assert not policy._check_condition("user_is:staff", None, None, "action")


def test_check_condition_in_reusable_module_is_called():
    class TestPolicy(AccessPolicy):
        pass

    policy = TestPolicy()

    assert policy._check_condition("is_a_cat:Garfield", None, None, "action")
    assert not policy._check_condition("is_a_cat:Snoopy", None, None, "action")


def test_get_condition_method_from_self():
    class TestPolicy(AccessPolicy):
        def is_a_cat(self, request, view, action):
            return False

    policy = TestPolicy()

    assert policy._get_condition_method("is_a_cat") == policy.is_a_cat


def test_get_condition_method_from_reusable_module():
    class TestPolicy(AccessPolicy):
        pass

    policy = TestPolicy()
    from test_project import global_access_conditions

    assert policy._get_condition_method("is_a_cat") == global_access_conditions.is_a_cat


def test_get_condition_method_throw_error():
    class TestPolicy(AccessPolicy):
        pass

    policy = TestPolicy()

    with pytest.raises(
        AccessPolicyException,
        match="must be a method on the access policy or be defined in the 'reusable_conditions' module",
    ):
        policy._get_condition_method("is_a_dog")


@pytest.mark.django_db
def test_evaluate_statements_false_if_no_statements(make_user):
    class TestPolicy(AccessPolicy):
        def is_sunny(self, request, view, action):
            return True

    policy = TestPolicy()
    user = make_user(username="mr user")

    result = policy._evaluate_statements([], FakeRequest(user), None, "create")
    assert result is False


@pytest.mark.django_db
def test_evaluate_statements_false_any_deny(make_user):
    policy = AccessPolicy()
    user = make_user(username="mr user")

    statements = [
        Statement(principal="*", action="*", effect="deny"),
        Statement(principal="*", action="*", effect="allow"),
    ]

    result = policy._evaluate_statements(
        statements, FakeRequest(user), None, "create"
    )
    assert result is False


@pytest.mark.django_db
def test_evaluate_statements_true_if_any_allow_and_none_deny(make_user):
    policy = AccessPolicy()
    user = make_user(username="mr user")

    statements = [
        Statement(principal="*", action="create", effect="allow"),
        Statement(principal="*", action="take_out_the_trash", effect="allow"),
    ]

    result = policy._evaluate_statements(
        statements, FakeRequest(user), None, "create"
    )
    assert result is True


@pytest.mark.django_db
def test_has_permission(make_user):
    class TestPolicy(AccessPolicy):
        statements = [Statement(principal="*", action="create", effect="allow")]

        def is_sunny(self, request, view, action):
            return True

    policy = TestPolicy()
    view = FakeViewSet(action="create")
    request = FakeRequest(user=make_user(username="fred"))

    with mock.patch.object(
        policy, "_evaluate_statements", wraps=policy._evaluate_statements
    ) as monkey:
        policy.has_permission(request, view)
        monkey.assert_called_with(
            [Statement(principal="*", action="create", effect="allow")],
            request,
            view,
            "create",
        )


@pytest.mark.django_db
def test_has_permission_with_custom_condition_and_star_character(make_user):
    class TestPolicy(AccessPolicy):
        statements = [
            Statement(
                action="*",
                principal="group:hr",
                effect="allow",
                condition=["check_permissions:*"],
            ),
            Statement(
                action="*",
                principal="group:admin",
                effect="allow",
                condition=["check_permissions:reboot"],
            ),
        ]

        def check_permissions(self, request, view, action, permissions: str):
            return permissions == "*"

    policy = TestPolicy()
    view = FakeViewSet(action="create")

    fred = make_user(username="fred", group_names=["admin"])
    jane = make_user(username="jane", group_names=["hr"])

    assert policy.has_permission(FakeRequest(user=fred), view) is False
    assert policy.has_permission(FakeRequest(user=jane), view) is True


def test_has_permission_is_true_when_user_is_none():
    class TestPolicy(AccessPolicy):
        statements = [Statement(action="*", principal="anonymous", effect="allow")]

    view = FakeViewSet(action="create")
    policy = TestPolicy()

    assert policy.has_permission(FakeRequest(user=None), view) is True


def test_has_permission_is_false_when_user_is_none():
    class TestPolicy(AccessPolicy):
        statements = [Statement(action="*", principal="authenticated", effect="allow")]

    view = FakeViewSet(action="create")
    policy = TestPolicy()

    assert policy.has_permission(FakeRequest(user=None), view) is False
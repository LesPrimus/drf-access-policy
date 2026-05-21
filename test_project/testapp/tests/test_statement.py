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
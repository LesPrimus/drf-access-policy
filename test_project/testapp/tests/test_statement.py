from dataclasses import asdict
from rest_framework.test import APITestCase

from rest_access_policy import AccessPolicy, Statement


class StatementTestCase(APITestCase):
    def test_should_raise_error_if_invalid_effect(self):
        with self.assertRaises(Exception) as context:
            Statement(principal="*", action="build", effect="veto")

        self.assertTrue("effect must be one of" in str(context.exception))

    def test_scalar_values_are_normalized_to_lists(self):
        statement = Statement(
            principal="*",
            action="build",
            effect="allow",
            condition="is_sunny",
            condition_expression="is_sunny or is_cloudy",
            read_only_fields="status",
        )

        self.assertEqual(statement.principal, ["*"])
        self.assertEqual(statement.action, ["build"])
        self.assertEqual(statement.condition, ["is_sunny"])
        self.assertEqual(statement.condition_expression, ["is_sunny or is_cloudy"])
        self.assertEqual(statement.read_only_fields, ["status"])

    def test_to_dict(self):
        statement = Statement(
            principal="*",
            action="build",
            effect="allow",
            condition_expression=["method1"],
        )

        self.assertEqual(
            asdict(statement),
            {
                "principal": ["*"],
                "action": ["build"],
                "effect": "allow",
                "condition": [],
                "condition_expression": ["method1"],
                "read_only_fields": [],
            },
        )
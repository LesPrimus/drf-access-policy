from rest_framework.request import Request

from .access_policy import AccessPolicy


class FieldAccessMixin(object):
    def __init__(self, *args, **kwargs):
        self.serializer_context = kwargs.get("context", {})
        super().__init__(*args, **kwargs)
        self._apply_fields_access()
        self._apply_read_only_fields()

    @property
    def access_policy(self) -> AccessPolicy:
        meta = getattr(self, "Meta", None)

        if not meta:
            raise Exception("Must set access_policy inside Meta for FieldAccessMixin")

        access_policy = getattr(meta, "access_policy", None)

        if not access_policy:
            raise Exception("Must set access_policy inside Meta for FieldAccessMixin")

        if getattr(access_policy, "scope_fields", None) is None:
            raise Exception("Must define scope_fields method on access_policy")

        return access_policy

    @property
    def request(self) -> Request:
        request = self.serializer_context.get("request")

        if not request:
            raise Exception("Must pass context with request to FieldAccessMixin")

        return request

    def _apply_fields_access(self):
        if self.read_only is True:
            return

        fields = self.access_policy.scope_fields(
            self.request, self.fields, instance=self.instance
        )

        if fields is None:
            raise Exception("scope_fields method must return fields variable")

        self.fields = fields

    def _apply_read_only_fields(self):
        """
        Force fields listed in a statement's ``read_only_fields`` to read-only
        on write requests when the requesting user matches the statement's
        principal. Matching is principal-only (action/effect/condition are not
        considered here).
        """
        if self.read_only is True:
            return

        if self.request.method not in ("POST", "PUT", "PATCH"):
            return

        policy = self.access_policy
        view = self.serializer_context.get("view")
        statements = policy().get_policy_statements(self.request, view)
        user_principals = policy._get_user_principals(self.request)

        for statement in statements:
            if not statement.read_only_fields:
                continue

            principals = statement.principal

            if "*" not in principals and user_principals.isdisjoint(principals):
                continue

            if "*" in statement.read_only_fields:
                for field in self.fields.values():
                    field.read_only = True
                break

            for field_name in statement.read_only_fields:
                if self.fields.get(field_name, None) is not None:
                    self.fields[field_name].read_only = True
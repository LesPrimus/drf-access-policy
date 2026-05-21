from rest_access_policy import AccessPolicy, Statement


class UserAccountAccessPolicy(AccessPolicy):
    statements = [
        Statement(principal="group:admin", action=["create", "update"], effect="allow"),
        Statement(
            principal="group:dev",
            action=["update", "partial_update"],
            effect="allow",
        ),
        Statement(principal="group:banned", action="retrieve", effect="deny"),
        Statement(
            principal="group:regular_users",
            action="set_password",
            effect="allow",
        ),
    ]

    @classmethod
    def scope_fields(cls, request, fields: dict, instance=None):
        if request.user.groups.filter(name="dev"):
            fields["status"].read_only = True
        return fields


class LogsAccessPolicy(AccessPolicy):
    statements = [
        Statement(principal="group:admin", action="*", effect="allow"),
        Statement(principal="group:dev", action="get_logs", effect="allow"),
        Statement(principal="group:dev", action="delete_logs", effect="deny"),
    ]


class LandingPageAccessPolicy(AccessPolicy):
    statements = [
        Statement(principal=["anonymous", "authenticated"], action="*", effect="allow"),
    ]
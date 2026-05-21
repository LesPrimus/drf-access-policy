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
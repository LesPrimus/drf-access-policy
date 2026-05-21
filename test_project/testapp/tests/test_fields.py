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
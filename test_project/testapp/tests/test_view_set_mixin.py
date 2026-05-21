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

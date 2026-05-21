from django.urls import include, path
from rest_framework import routers
from test_project.testapp.views import (
    UserAccountViewSet,
    UserAccountViewSetWithMixin,
    delete_logs,
    get_logs,
    get_landing_page,
)

# Standard viewsets
router = routers.DefaultRouter()
router.register(r"accounts", UserAccountViewSet, basename="account")
router.register(r"accounts-mixin-test", UserAccountViewSetWithMixin, basename="account-mixin-test")


urlpatterns = [
    path("", include(router.urls)),
    path("delete-logs/", delete_logs, name="delete-logs"),
    path("get-logs/", get_logs, name="get-logs"),
    path("get-landing-page/", get_landing_page, name="get-landing-page"),
]

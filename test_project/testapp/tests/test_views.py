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
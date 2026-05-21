import pytest
from rest_framework.reverse import reverse

from test_project.testapp.models import UserAccount


@pytest.mark.django_db
def test_create_allowed(auth_client):
    client, _ = auth_client(username="admin_user", group_names=["admin"])

    for name in ["account-mixin-test-list", "account-list"]:
        url = reverse(name)
        response = client.post(
            url,
            {"username": "fred", "first_name": "Fred", "last_name": "Rogers"},
            format="json",
        )
        assert response.status_code == 201


@pytest.mark.django_db
def test_retrieve_denied(auth_client):
    account = UserAccount.objects.create(
        username="fred", first_name="Fred", last_name="Rogers"
    )
    client, _ = auth_client(username="banned_user", group_names=["banned"])

    url = reverse("account-detail", args=[account.id])
    response = client.get(url, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_set_password_should_be_allowed(auth_client):
    account = UserAccount.objects.create(
        username="fred", first_name="Fred", last_name="Rogers"
    )
    client, _ = auth_client(username="regular", group_names=["regular_users"])

    url = reverse("account-set-password", args=[account.id])
    response = client.post(url, format="json")
    assert response.status_code == 200


@pytest.mark.django_db
def test_set_password_should_be_denied(auth_client):
    account = UserAccount.objects.create(
        username="fred", first_name="Fred", last_name="Rogers"
    )
    client, _ = auth_client(username="unprivileged")

    url = reverse("account-set-password", args=[account.id])
    response = client.post(url, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_partial_update_should_not_update_status_for_dev_group(auth_client):
    account = UserAccount.objects.create(
        username="fred", first_name="Fred", last_name="Rogers"
    )
    client, _ = auth_client(username="dev_user", group_names=["dev"])

    url = reverse("account-detail", args=[account.id])
    response = client.patch(
        url, data={"last_name": "Mercury", "status": "inactive"}, format="json"
    )
    assert response.data["last_name"] == "Mercury"
    assert response.data["status"] == "active"

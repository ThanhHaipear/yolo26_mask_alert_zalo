from app.models import ZaloUser


def test_webhook_saves_new_zalo_user(client, db_session):
    response = client.post(
        "/webhook/zalo",
        json={
            "sender": {
                "id": "user-123",
                "display_name": "Test User",
                "is_following": True,
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["saved"] is True

    user = db_session.query(ZaloUser).one()
    assert user.zalo_user_id == "user-123"
    assert user.display_name == "Test User"
    assert user.is_following is True


def test_webhook_updates_existing_zalo_user(client, db_session):
    db_session.add(ZaloUser(zalo_user_id="user-123", display_name="Old Name", is_following=True))
    db_session.commit()

    response = client.post(
        "/webhook/zalo",
        json={
            "data": {
                "sender": {
                    "id": "user-123",
                    "name": "New Name",
                    "is_following": False,
                }
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["saved"] is True

    user = db_session.query(ZaloUser).one()
    assert user.display_name == "New Name"
    assert user.is_following is False

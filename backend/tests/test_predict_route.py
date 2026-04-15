from types import SimpleNamespace

from app.models import Alert
from app.routes import predict as predict_route


def test_predict_rejects_non_image_file(client):
    response = client.post(
        "/predict",
        files={"file": ("notes.txt", b"plain-text", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only image files are supported"


def test_predict_returns_no_violation_when_model_finds_no_issue(client, image_bytes, monkeypatch):
    monkeypatch.setattr(
        predict_route,
        "model_service",
        SimpleNamespace(
            predict=lambda image: [
                {
                    "class_id": 0,
                    "class_name": "with_mask",
                    "confidence": 0.98,
                    "x1": 1,
                    "y1": 2,
                    "x2": 10,
                    "y2": 12,
                }
            ]
        ),
    )

    response = client.post(
        "/predict",
        files={"file": ("image.jpg", image_bytes, "image/jpeg")},
        data={"camera_name": "gate-cam"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["violation_count"] == 0
    assert payload["zalo_sent"] is False
    assert payload["alert_id"] is None
    assert payload["message"] == "No violations detected"


def test_predict_creates_alert_and_updates_delivery(client, db_session, image_bytes, monkeypatch):
    monkeypatch.setattr(
        predict_route,
        "model_service",
        SimpleNamespace(
            predict=lambda image: [
                {
                    "class_id": 1,
                    "class_name": "without_mask",
                    "confidence": 0.93,
                    "x1": 3,
                    "y1": 4,
                    "x2": 20,
                    "y2": 24,
                }
            ]
        ),
    )
    monkeypatch.setattr(
        predict_route,
        "gcs_storage_service",
        SimpleNamespace(upload_image=lambda image, camera_name, alert_id=None: f"gs://bucket/{camera_name}-{alert_id}.jpg"),
    )
    monkeypatch.setattr(
        predict_route,
        "zalo_service",
        SimpleNamespace(
            is_ready=lambda: True,
            build_alert_message=lambda camera_name, violation_count: f"Alert from {camera_name}: {violation_count}",
            send_alert=lambda message, image_url=None, chat_id=None: (True, "sent"),
        ),
    )

    response = client.post(
        "/predict",
        files={"file": ("image.jpg", image_bytes, "image/jpeg")},
        data={"camera_name": "lobby-cam"},
    )

    payload = response.json()
    alert = db_session.query(Alert).one()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["violation_count"] == 1
    assert payload["zalo_sent"] is True
    assert payload["alert_id"] == alert.id
    assert payload["image_url"] == f"gs://bucket/lobby-cam-{alert.id}.jpg"
    assert alert.camera_name == "lobby-cam"
    assert alert.alert_type == "mask_violation"
    assert alert.zalo_sent is True
    assert alert.image_url == payload["image_url"]
    assert alert.zalo_response == "sent"


def test_predict_skips_alert_during_cooldown(client, db_session, image_bytes, monkeypatch):
    detections = [
        {
            "class_id": 1,
            "class_name": "without_mask",
            "confidence": 0.91,
            "x1": 1,
            "y1": 1,
            "x2": 8,
            "y2": 8,
        }
    ]
    monkeypatch.setattr(predict_route, "model_service", SimpleNamespace(predict=lambda image: detections))
    monkeypatch.setattr(
        predict_route,
        "gcs_storage_service",
        SimpleNamespace(upload_image=lambda image, camera_name, alert_id=None: "gs://bucket/test.jpg"),
    )
    monkeypatch.setattr(
        predict_route,
        "zalo_service",
        SimpleNamespace(
            is_ready=lambda: False,
            build_alert_message=lambda camera_name, violation_count: "message",
            send_alert=lambda message, image_url=None, chat_id=None: (False, "disabled"),
        ),
    )

    first = client.post(
        "/predict",
        files={"file": ("image.jpg", image_bytes, "image/jpeg")},
        data={"camera_name": "cam-1"},
    )
    second = client.post(
        "/predict",
        files={"file": ("image.jpg", image_bytes, "image/jpeg")},
        data={"camera_name": "cam-1"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["message"] == "Violation detected but skipped by cooldown"
    assert db_session.query(Alert).count() == 1


def test_predict_frame_waits_until_threshold_then_creates_alert(client, db_session, image_bytes, monkeypatch):
    monkeypatch.setattr(
        predict_route.settings,
        "continuous_violation_seconds",
        2,
        raising=False,
    )
    monkeypatch.setattr(
        predict_route.settings,
        "violation_grace_seconds",
        5,
        raising=False,
    )
    monkeypatch.setattr(
        predict_route,
        "model_service",
        SimpleNamespace(
            predict=lambda image: [
                {
                    "class_id": 1,
                    "class_name": "without_mask",
                    "confidence": 0.95,
                    "x1": 3,
                    "y1": 4,
                    "x2": 20,
                    "y2": 24,
                }
            ]
        ),
    )
    monkeypatch.setattr(
        predict_route,
        "gcs_storage_service",
        SimpleNamespace(upload_image=lambda image, camera_name, alert_id=None: None),
    )
    monkeypatch.setattr(
        predict_route,
        "zalo_service",
        SimpleNamespace(
            is_ready=lambda: False,
            build_alert_message=lambda camera_name, violation_count: f"Alert from {camera_name}: {violation_count}",
            send_alert=lambda message, image_url=None, chat_id=None: (False, "disabled"),
        ),
    )
    predict_route.realtime_state_service.clear(session_id="session-1", camera_name="cam-rt")

    first = client.post(
        "/predict-frame",
        files={"file": ("frame.jpg", image_bytes, "image/jpeg")},
        data={"camera_name": "cam-rt", "session_id": "session-1", "captured_at": "2026-04-10T10:00:00Z"},
    )
    second = client.post(
        "/predict-frame",
        files={"file": ("frame.jpg", image_bytes, "image/jpeg")},
        data={"camera_name": "cam-rt", "session_id": "session-1", "captured_at": "2026-04-10T10:00:03Z"},
    )

    assert first.status_code == 200
    assert first.json()["alert_armed"] is False
    assert "Waiting to reach 2s" in first.json()["message"]

    assert second.status_code == 200
    assert second.json()["alert_armed"] is True
    assert second.json()["alert_id"] is not None
    assert db_session.query(Alert).count() == 1

    predict_route.realtime_state_service.clear(session_id="session-1", camera_name="cam-rt")

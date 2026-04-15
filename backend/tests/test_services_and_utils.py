from datetime import datetime, timedelta

from app.models import Alert
from app.services.alert_service import alert_service
from app.services.realtime_state_service import realtime_state_service
from app.utils.image_utils import apply_nms, count_violations


def test_count_violations_counts_only_violation_classes():
    detections = [
        {"class_name": "with_mask"},
        {"class_name": "without_mask"},
        {"class_name": "mask_weared_incorrect"},
    ]

    assert count_violations(detections) == 2


def test_alert_service_respects_cooldown_window(db_session):
    db_session.add(
        Alert(
            camera_name="cam-1",
            alert_type="mask_violation",
            violation_count=1,
            message="Recent alert",
            zalo_recipient_uid=None,
            created_at=datetime.utcnow(),
        )
    )
    db_session.commit()

    assert alert_service.should_create_alert(db_session, camera_name="cam-1", alert_type="mask_violation") is False


def test_alert_service_allows_new_alert_after_cooldown(db_session):
    db_session.add(
        Alert(
            camera_name="cam-1",
            alert_type="mask_violation",
            violation_count=1,
            message="Old alert",
            zalo_recipient_uid=None,
            created_at=datetime.utcnow() - timedelta(hours=1),
        )
    )
    db_session.commit()

    assert alert_service.should_create_alert(db_session, camera_name="cam-1", alert_type="mask_violation") is True


def test_apply_nms_removes_overlapping_lower_confidence_box():
    detections = [
        {"class_name": "without_mask", "confidence": 0.9, "x1": 10, "y1": 10, "x2": 110, "y2": 110},
        {"class_name": "mask_weared_incorrect", "confidence": 0.7, "x1": 15, "y1": 15, "x2": 105, "y2": 105},
        {"class_name": "with_mask", "confidence": 0.6, "x1": 200, "y1": 200, "x2": 260, "y2": 260},
    ]

    filtered = apply_nms(detections, iou_threshold=0.45)

    assert len(filtered) == 2
    assert filtered[0]["confidence"] == 0.9
    assert filtered[1]["confidence"] == 0.6


def test_realtime_state_arms_alert_after_continuous_violation_window():
    session_id = "session-test"
    camera_name = "cam-rt"
    realtime_state_service.clear(session_id=session_id, camera_name=camera_name)


def test_realtime_state_keeps_timer_during_short_grace_gap():
    session_id = "session-grace"
    camera_name = "cam-grace"
    realtime_state_service.clear(session_id=session_id, camera_name=camera_name)

    start = datetime.utcnow()
    realtime_state_service.update(
        session_id=session_id,
        camera_name=camera_name,
        has_violation=True,
        observed_at=start,
        threshold_seconds=15,
        grace_seconds=3,
    )
    status = realtime_state_service.update(
        session_id=session_id,
        camera_name=camera_name,
        has_violation=False,
        observed_at=start + timedelta(seconds=2),
        threshold_seconds=15,
        grace_seconds=3,
    )

    assert status["within_grace_period"] is True
    assert status["active_violation_seconds"] == 0.0

    realtime_state_service.clear(session_id=session_id, camera_name=camera_name)

    start = datetime.utcnow()
    first = realtime_state_service.update(
        session_id=session_id,
        camera_name=camera_name,
        has_violation=True,
        observed_at=start,
        threshold_seconds=15,
        grace_seconds=3,
    )
    second = realtime_state_service.update(
        session_id=session_id,
        camera_name=camera_name,
        has_violation=True,
        observed_at=start + timedelta(seconds=16),
        threshold_seconds=15,
        grace_seconds=20,
    )

    assert first["alert_armed"] is False
    assert second["alert_armed"] is True
    assert second["active_violation_seconds"] >= 15

    realtime_state_service.clear(session_id=session_id, camera_name=camera_name)

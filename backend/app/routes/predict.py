import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.schemas import PredictResponse
from app.services.alert_service import alert_service
from app.services.model_service import model_service
from app.services.realtime_state_service import realtime_state_service
from app.services.storage_service import gcs_storage_service
from app.services.zalo_service import zalo_service
from app.utils.image_utils import count_violations, decode_image_bytes, draw_detections

router = APIRouter(tags=["predict"])
logger = logging.getLogger(__name__)


def parse_observed_at(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)

    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_prediction_response(
    *,
    detections: list[dict],
    message: str,
    violation_count: int,
    image_url: str | None = None,
    annotated_image_base64: str | None = None,
    zalo_sent: bool = False,
    alert_id: int | None = None,
    mode: str = "image",
    session_id: str | None = None,
    current_violation: bool | None = None,
    active_violation_seconds: float | None = None,
    threshold_seconds: int | None = None,
    alert_armed: bool | None = None,
    backend_connected: bool | None = True,
) -> PredictResponse:
    return PredictResponse(
        success=True,
        violation_count=violation_count,
        detections=detections,
        image_url=image_url,
        annotated_image_base64=annotated_image_base64,
        zalo_sent=zalo_sent,
        message=message,
        alert_id=alert_id,
        mode=mode,
        session_id=session_id,
        current_violation=current_violation,
        active_violation_seconds=active_violation_seconds,
        threshold_seconds=threshold_seconds,
        alert_armed=alert_armed,
        backend_connected=backend_connected,
    )


def process_alert_flow(
    *,
    db: Session,
    camera_name: str,
    detections: list[dict],
    image,
    mode: str,
    session_id: str | None = None,
    current_violation: bool | None = None,
    active_violation_seconds: float | None = None,
    threshold_seconds: int | None = None,
    alert_armed: bool | None = None,
    backend_connected: bool | None = True,
) -> PredictResponse:
    violation_count = count_violations(detections)

    if violation_count <= 0:
        return build_prediction_response(
            detections=detections,
            violation_count=0,
            message="No violations detected",
            mode=mode,
            session_id=session_id,
            current_violation=current_violation,
            active_violation_seconds=active_violation_seconds,
            threshold_seconds=threshold_seconds,
            alert_armed=alert_armed,
            backend_connected=backend_connected,
        )

    if mode == "realtime" and not alert_armed:
        message = f"Violation observed for {active_violation_seconds:.2f}s. Waiting to reach {threshold_seconds}s."
        return build_prediction_response(
            detections=detections,
            violation_count=violation_count,
            message=message,
            mode=mode,
            session_id=session_id,
            current_violation=current_violation,
            active_violation_seconds=active_violation_seconds,
            threshold_seconds=threshold_seconds,
            alert_armed=False,
            backend_connected=backend_connected,
        )

    if not alert_service.should_create_alert(db, camera_name=camera_name, alert_type="mask_violation"):
        return build_prediction_response(
            detections=detections,
            violation_count=violation_count,
            message="Violation detected but skipped by cooldown",
            mode=mode,
            session_id=session_id,
            current_violation=current_violation,
            active_violation_seconds=active_violation_seconds,
            threshold_seconds=threshold_seconds,
            alert_armed=alert_armed,
            backend_connected=backend_connected,
        )

    message = zalo_service.build_alert_message(camera_name=camera_name, violation_count=violation_count)
    alert = alert_service.create_alert(
        db,
        camera_name=camera_name,
        alert_type="mask_violation",
        violation_count=violation_count,
        message=message,
        zalo_recipient_uid=settings.zalo_chat_id or None,
    )

    image_url = None
    try:
        annotated = draw_detections(image, detections)
        image_url = gcs_storage_service.upload_image(annotated, camera_name=camera_name, alert_id=alert.id)
    except Exception:
        logger.exception("Failed to upload annotated image")

    zalo_sent = False
    zalo_response = "Zalo alert disabled"
    if zalo_service.is_ready():
        zalo_sent, zalo_response = zalo_service.send_alert(
            message=message,
            image_url=image_url,
            chat_id=alert.zalo_recipient_uid,
        )

    alert = alert_service.update_alert_delivery(
        db,
        alert,
        image_url=image_url,
        zalo_sent=zalo_sent,
        zalo_response=zalo_response,
    )

    return build_prediction_response(
        detections=detections,
        violation_count=violation_count,
        image_url=alert.image_url,
        zalo_sent=alert.zalo_sent,
        message="Violation detected and alert recorded",
        alert_id=alert.id,
        mode=mode,
        session_id=session_id,
        current_violation=current_violation,
        active_violation_seconds=active_violation_seconds,
        threshold_seconds=threshold_seconds,
        alert_armed=alert_armed,
        backend_connected=backend_connected,
    )


@router.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(...),
    camera_name: str = Form(default=settings.default_camera_name),
    db: Session = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    content = await file.read()
    try:
        image = decode_image_bytes(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    detections = model_service.predict(image)
    return process_alert_flow(
        db=db,
        camera_name=camera_name,
        detections=detections,
        image=image,
        mode="image",
    )


@router.post("/predict-frame", response_model=PredictResponse)
async def predict_frame(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    camera_name: str = Form(default=settings.default_camera_name),
    captured_at: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    content = await file.read()
    try:
        image = decode_image_bytes(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    detections = model_service.predict(image)
    violation_count = count_violations(detections)
    observed_at = parse_observed_at(captured_at)
    realtime_status = realtime_state_service.update(
        session_id=session_id,
        camera_name=camera_name,
        has_violation=violation_count > 0,
        observed_at=observed_at,
        threshold_seconds=settings.continuous_violation_seconds,
        grace_seconds=settings.violation_grace_seconds,
    )

    return process_alert_flow(
        db=db,
        camera_name=camera_name,
        detections=detections,
        image=image,
        mode="realtime",
        session_id=session_id,
        current_violation=realtime_status["current_violation"],
        active_violation_seconds=realtime_status["active_violation_seconds"],
        threshold_seconds=realtime_status["threshold_seconds"],
        alert_armed=realtime_status["alert_armed"],
        backend_connected=True,
    )

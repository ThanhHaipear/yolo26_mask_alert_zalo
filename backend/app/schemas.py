from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DetectionItem(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int


class PredictResponse(BaseModel):
    success: bool
    violation_count: int
    detections: list[DetectionItem]
    image_url: str | None = None
    annotated_image_base64: str | None = None
    zalo_sent: bool
    message: str
    alert_id: int | None = None
    mode: str = "image"
    session_id: str | None = None
    current_violation: bool | None = None
    active_violation_seconds: float | None = None
    threshold_seconds: int | None = None
    alert_armed: bool | None = None
    backend_connected: bool | None = None


class AlertRead(BaseModel):
    id: int
    camera_name: str
    alert_type: str
    violation_count: int
    message: str
    image_url: str | None
    zalo_recipient_uid: str | None
    zalo_sent: bool
    zalo_response: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ZaloUserRead(BaseModel):
    id: int
    zalo_user_id: str
    display_name: str | None
    is_following: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

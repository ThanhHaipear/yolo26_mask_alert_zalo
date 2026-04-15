from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Alert


class AlertService:
    def should_create_alert(self, db: Session, camera_name: str, alert_type: str) -> bool:
        cooldown_start = datetime.utcnow() - timedelta(seconds=settings.alert_cooldown_seconds)
        stmt = (
            select(Alert)
            .where(Alert.camera_name == camera_name)
            .where(Alert.alert_type == alert_type)
            .where(Alert.created_at >= cooldown_start)
            .order_by(Alert.created_at.desc())
        )
        return db.execute(stmt).scalar_one_or_none() is None

    def create_alert(
        self,
        db: Session,
        camera_name: str,
        alert_type: str,
        violation_count: int,
        message: str,
        zalo_recipient_uid: str | None,
    ) -> Alert:
        alert = Alert(
            camera_name=camera_name,
            alert_type=alert_type,
            violation_count=violation_count,
            message=message,
            zalo_recipient_uid=zalo_recipient_uid,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def update_alert_delivery(
        self,
        db: Session,
        alert: Alert,
        *,
        image_url: str | None = None,
        zalo_sent: bool | None = None,
        zalo_response: str | None = None,
    ) -> Alert:
        if image_url is not None:
            alert.image_url = image_url
        if zalo_sent is not None:
            alert.zalo_sent = zalo_sent
        if zalo_response is not None:
            alert.zalo_response = zalo_response

        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert


alert_service = AlertService()

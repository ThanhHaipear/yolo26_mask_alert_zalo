from datetime import datetime

import requests

from app.config import settings


class ZaloBotService:
    def __init__(self) -> None:
        self.base_url = "https://bot-api.zaloplatforms.com"

    def is_ready(self) -> bool:
        return bool(settings.enable_zalo_alert and settings.zalo_bot_token and settings.zalo_chat_id)

    def send_text_alert(self, message: str, chat_id: str | None = None) -> tuple[bool, str]:
        if not self.is_ready():
            return False, "Zalo alert is disabled or not configured"

        entrypoint = f"{self.base_url}/bot{settings.zalo_bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id or settings.zalo_chat_id,
            "text": message,
        }

        try:
            response = requests.post(
                entrypoint,
                json=payload,
                timeout=settings.request_timeout_seconds,
            )
            return response.ok, response.text
        except requests.RequestException as exc:
            return False, str(exc)

    def send_photo_alert(self, caption: str, photo_url: str, chat_id: str | None = None) -> tuple[bool, str]:
        if not self.is_ready():
            return False, "Zalo alert is disabled or not configured"

        entrypoint = f"{self.base_url}/bot{settings.zalo_bot_token}/sendPhoto"
        payload = {
            "chat_id": chat_id or settings.zalo_chat_id,
            "caption": caption,
            "photo": photo_url,
        }

        try:
            response = requests.post(
                entrypoint,
                json=payload,
                timeout=settings.request_timeout_seconds,
            )
            return response.ok, response.text
        except requests.RequestException as exc:
            return False, str(exc)

    def send_alert(self, message: str, image_url: str | None = None, chat_id: str | None = None) -> tuple[bool, str]:
        if image_url:
            ok, response_text = self.send_photo_alert(caption=message, photo_url=image_url, chat_id=chat_id)
            if ok:
                return ok, response_text
        return self.send_text_alert(message=message, chat_id=chat_id)

    @staticmethod
    def build_alert_message(camera_name: str, violation_count: int) -> str:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        return (
            "MASK VIOLATION ALERT\n"
            f"Camera: {camera_name}\n"
            f"Time: {timestamp}\n"
            f"Violation count: {violation_count}"
        )


zalo_service = ZaloBotService()

from datetime import datetime
from datetime import timedelta
from uuid import uuid4

from google.cloud import storage

from app.config import settings
from app.utils.image_utils import encode_image_to_jpeg_bytes


class GCSStorageService:
    def __init__(self) -> None:
        self.enabled = bool(settings.enable_gcs_upload and settings.gcs_bucket_name)
        self.client = storage.Client() if self.enabled else None

    def upload_image(self, image, camera_name: str, alert_id: int | None = None) -> str | None:
        if not self.enabled or self.client is None:
            return None

        blob_name = (
            f"alerts/{datetime.utcnow().strftime('%Y%m%d')}/"
            f"{camera_name}-{alert_id or 'na'}-{uuid4().hex}.jpg"
        )
        bucket = self.client.bucket(settings.gcs_bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(encode_image_to_jpeg_bytes(image), content_type="image/jpeg")
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=settings.gcs_signed_url_minutes),
            method="GET",
        )


gcs_storage_service = GCSStorageService()

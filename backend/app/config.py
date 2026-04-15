from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mask Detection Backend"
    app_version: str = "1.0.0"
    app_env: str = "development"
    cors_origins: str = "*"
    db_url: str = "sqlite:///./mask_alerts.db"
    instance_connection_name: str = ""
    db_user: str = ""
    db_pass: str = ""
    db_name: str = ""
    private_ip: bool = False

    model_path: str = "best_mask.onnx"
    input_size: int = 640
    conf_threshold: float = 0.5
    iou_threshold: float = 0.45
    class_names: str = "with_mask,without_mask,mask_weared_incorrect"
    onnx_providers: str = "CPUExecutionProvider"
    alert_cooldown_seconds: int = 30
    continuous_violation_seconds: int = 15
    violation_grace_seconds: int = 3
    default_camera_name: str = "default-camera"

    zalo_bot_token: str = ""
    zalo_chat_id: str = ""
    enable_zalo_alert: bool = False

    gcs_bucket_name: str = ""
    enable_gcs_upload: bool = False
    gcs_signed_url_minutes: int = 15

    webhook_verify_token: str = "change-me"

    request_timeout_seconds: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def backend_dir(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def resolved_model_path(self) -> Path:
        model_path = Path(self.model_path)
        if model_path.is_absolute():
            return model_path
        return self.backend_dir / model_path

    @property
    def cors_origins_list(self) -> list[str]:
        value = self.cors_origins.strip()
        if value == "*":
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def class_names_list(self) -> list[str]:
        return [item.strip() for item in self.class_names.split(",") if item.strip()]

    @property
    def onnx_providers_list(self) -> list[str]:
        return [item.strip() for item in self.onnx_providers.split(",") if item.strip()]

    @property
    def sqlalchemy_connect_args(self) -> dict:
        if self.db_url.startswith("sqlite"):
            return {"check_same_thread": False}
        return {}


settings = Settings()

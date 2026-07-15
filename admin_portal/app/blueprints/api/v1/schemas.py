from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RegisterDeviceRequest(BaseModel):
    device_id: str = Field(..., min_length=8, max_length=64)
    device_name: str | None = Field(None, max_length=120)
    manufacturer: str | None = Field(None, max_length=80)
    model: str | None = Field(None, max_length=80)
    android_version: str | None = Field(None, max_length=20)
    app_version_name: str | None = Field(None, max_length=20)
    app_version_code: int | None = None


class HeartbeatRequest(BaseModel):
    app_version_name: str | None = Field(None, max_length=20)
    app_version_code: int | None = None


class MessageItem(BaseModel):
    client_message_id: str = Field(..., min_length=1, max_length=64)
    sender_raw: str = Field(..., min_length=1, max_length=32)
    sender_matched: str = Field(..., min_length=1, max_length=32)
    body: str = Field(..., min_length=1, max_length=2000)
    received_at: datetime

    @field_validator("received_at")
    @classmethod
    def _ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            from datetime import timezone

            return value.replace(tzinfo=timezone.utc)
        return value


class MessagesRequest(BaseModel):
    messages: list[MessageItem] = Field(..., min_length=1, max_length=100)

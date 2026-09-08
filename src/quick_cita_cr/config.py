from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from platformdirs import user_config_dir, user_data_dir, user_log_dir
from pydantic import BaseModel, Field, SecretStr, field_validator

APP_NAME = "quick-cita-cr"
DEFAULT_CONFIG_PATH = Path(user_config_dir(APP_NAME)) / "config.yaml"
DEFAULT_SECRETS_PATH = Path(user_config_dir(APP_NAME)) / "secrets.env"
DEFAULT_DATA_DIR = Path(user_data_dir(APP_NAME))
DEFAULT_LOG_DIR = Path(user_log_dir(APP_NAME))


class AppointmentConfig(BaseModel):
    license_class: str = "B1"
    branches: list[str] = Field(default_factory=lambda: ["ALAJUELA"])
    quick_window_days: int = Field(default=21, ge=1, le=365)
    notify_on_first_run: bool = True
    notify_on_new_dates: bool = True
    notify_on_earlier_best: bool = True
    notify_on_within_window: bool = True

    @field_validator("branches")
    @classmethod
    def branches_must_not_be_empty(cls, value: list[str]) -> list[str]:
        cleaned = [branch.strip().upper() for branch in value if branch.strip()]
        if not cleaned:
            raise ValueError("at least one branch is required")
        return cleaned


class ScheduleConfig(BaseModel):
    interval_minutes: int = Field(default=12, ge=5, le=240)
    jitter_percent: int = Field(default=20, ge=0, le=50)
    max_failures_before_pause: int = Field(default=3, ge=1, le=20)
    pause_minutes_after_failures: int = Field(default=60, ge=5, le=1440)


class BrowserConfig(BaseModel):
    headless: bool = True
    channel: str | None = None
    executable_path: Path | None = None
    profile_dir: Path = DEFAULT_DATA_DIR / "browser-profile"
    timeout_seconds: int = Field(default=45, ge=10, le=180)


class EmailConfig(BaseModel):
    enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = Field(default=587, ge=1, le=65535)
    from_address: str = ""
    to_addresses: list[str] = Field(default_factory=list)


class NotificationConfig(BaseModel):
    email: EmailConfig = Field(default_factory=EmailConfig)


class Secrets(BaseModel):
    id_type: str
    identification: SecretStr
    password: SecretStr
    receipt_number: SecretStr
    email_username: str | None = None
    email_password: SecretStr | None = None


class AppConfig(BaseModel):
    appointment: AppointmentConfig = Field(default_factory=AppointmentConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    database_path: Path = DEFAULT_DATA_DIR / "state.sqlite3"
    log_dir: Path = DEFAULT_LOG_DIR


def write_default_config(path: Path = DEFAULT_CONFIG_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
    return path


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    if not path.exists():
        write_default_config(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return AppConfig.model_validate(data)


def load_secrets(secrets_path: Path = DEFAULT_SECRETS_PATH) -> Secrets:
    load_dotenv()
    if secrets_path.exists():
        load_dotenv(secrets_path)
    data: dict[str, Any] = {
        "id_type": os.getenv("QUICK_CITA_ID_TYPE", "CI"),
        "identification": os.getenv("QUICK_CITA_IDENTIFICATION", ""),
        "password": os.getenv("QUICK_CITA_PASSWORD", ""),
        "receipt_number": os.getenv("QUICK_CITA_RECEIPT_NUMBER", ""),
        "email_username": os.getenv("QUICK_CITA_EMAIL_USERNAME"),
        "email_password": os.getenv("QUICK_CITA_EMAIL_PASSWORD"),
    }
    missing = [key for key in ["identification", "password", "receipt_number"] if not data[key]]
    if missing:
        raise ValueError(
            "Missing required secret(s): "
            + ", ".join(missing)
            + f". Set them in environment variables or {secrets_path}."
        )
    return Secrets.model_validate(data)


DEFAULT_CONFIG_YAML = """appointment:
  license_class: B1
  branches:
    - ALAJUELA
    - HEREDIA
  quick_window_days: 21
  notify_on_first_run: true
  notify_on_new_dates: true
  notify_on_earlier_best: true
  notify_on_within_window: true
schedule:
  interval_minutes: 12
  jitter_percent: 20
  max_failures_before_pause: 3
  pause_minutes_after_failures: 60
browser:
  headless: true
  channel: null
  executable_path: null
  profile_dir: ~/.local/share/quick-cita-cr/browser-profile
  timeout_seconds: 45
notifications:
  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
    from_address: your.gmail@gmail.com
    to_addresses:
      - your.gmail@gmail.com
"""

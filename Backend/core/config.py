"""
Application Settings Module

Loads eKlAVYA configuration from environment variables with safe local
development defaults. All settings have explicit defaults so the application
starts without any external credentials.

Environment Variables:
    ENVIRONMENT: deployment environment (development|staging|production)
    API_V1_PREFIX: URL prefix for versioned eKlAVYA endpoints
    TESTING_MODE: enable development header authentication (never in production)
    REPOSITORY_BACKEND: persistence backend (memory only in this implementation)
    LOCAL_UPLOAD_DIR: private local directory for uploaded scan pages
    LOCAL_MEDIA_DIR: private local directory for generated media (mock audio)
    MOCK_PROVIDERS: use deterministic local providers (OCR, answering, speech, decisions)
    MAX_UPLOAD_MB: maximum accepted upload size in megabytes
    MAX_SCAN_PAGES: maximum pages per scan
    SIMULATED_CALL_RING_SECONDS: ring duration before a delivery becomes missed
    SEED_ON_STARTUP: load deterministic development seed data at startup
    IDEMPOTENCY_RETENTION_HOURS: retention for stored idempotency responses
    QUIET_HOURS_START / QUIET_HOURS_END: default quiet-hours window (24h local)
    MAX_SIMULATED_CALLS_PER_DAY: per-sender frequency limit for simulated calls

Author: eKlAVYA Backend
Version: 1.0.0
"""

import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


TRUE_VALUES = {"1", "true", "yes", "on"}


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_VALUES


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_str(name: str, default: str) -> str:
    return os.getenv(name, default)


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    testing_mode: bool = True
    repository_backend: str = "memory"
    local_upload_dir: str = "./local_data/uploads"
    local_media_dir: str = "./local_data/media"
    mock_providers: bool = True
    max_upload_mb: int = 10
    max_scan_pages: int = 10
    simulated_call_ring_seconds: int = 45
    seed_on_startup: bool = True
    idempotency_retention_hours: int = 24
    quiet_hours_start: int = 21
    quiet_hours_end: int = 7
    max_simulated_calls_per_day: int = 20

    def ensure_local_dirs(self) -> None:
        """Create private local storage directories if they do not exist."""
        Path(self.local_upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.local_media_dir).mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    """
    Build Settings from the process environment with development defaults.

    Safety rule: TESTING_MODE authentication must never be silently enabled
    in production, so this function refuses to start in that combination.

    Returns:
        Settings: validated application settings

    Raises:
        RuntimeError: if TESTING_MODE is enabled with ENVIRONMENT=production
    """
    settings = Settings(
        environment=_get_str("ENVIRONMENT", "development").strip().lower(),
        api_v1_prefix=_get_str("API_V1_PREFIX", "/api/v1"),
        testing_mode=_get_bool("TESTING_MODE", True),
        repository_backend=_get_str("REPOSITORY_BACKEND", "memory"),
        local_upload_dir=_get_str("LOCAL_UPLOAD_DIR", "./local_data/uploads"),
        local_media_dir=_get_str("LOCAL_MEDIA_DIR", "./local_data/media"),
        mock_providers=_get_bool("MOCK_PROVIDERS", True),
        max_upload_mb=_get_int("MAX_UPLOAD_MB", 10),
        max_scan_pages=_get_int("MAX_SCAN_PAGES", 10),
        simulated_call_ring_seconds=_get_int("SIMULATED_CALL_RING_SECONDS", 45),
        seed_on_startup=_get_bool("SEED_ON_STARTUP", True),
        idempotency_retention_hours=_get_int("IDEMPOTENCY_RETENTION_HOURS", 24),
        quiet_hours_start=_get_int("QUIET_HOURS_START", 21),
        quiet_hours_end=_get_int("QUIET_HOURS_END", 7),
        max_simulated_calls_per_day=_get_int("MAX_SIMULATED_CALLS_PER_DAY", 20),
    )

    if settings.testing_mode and settings.environment == "production":
        raise RuntimeError(
            "TESTING_MODE authentication cannot be enabled in production. "
            "Set TESTING_MODE=false or ENVIRONMENT=development."
        )

    return settings


_settings_lock = threading.Lock()
_settings_cache: Optional[Settings] = None


def get_settings() -> Settings:
    """Return the process-wide Settings singleton."""
    global _settings_cache
    with _settings_lock:
        if _settings_cache is None:
            _settings_cache = load_settings()
        return _settings_cache


def reset_settings_cache() -> None:
    """Clear the Settings singleton (used by tests)."""
    global _settings_cache
    with _settings_lock:
        _settings_cache = None

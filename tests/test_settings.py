from __future__ import annotations

from packages.infrastructure.settings import Settings


def test_settings_read_environment_values(monkeypatch: object) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/4")  # type: ignore[attr-defined]
    monkeypatch.setenv("APP_ENV", "test")  # type: ignore[attr-defined]

    settings = Settings()

    assert str(settings.redis_url) == "redis://redis:6379/4"
    assert settings.app_env == "test"

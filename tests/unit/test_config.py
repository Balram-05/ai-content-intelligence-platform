from app.core.config import get_settings


def test_settings_default_values():
    """Verify default configuration settings."""
    settings = get_settings()
    assert settings.APP_NAME == "AI Personal Branding & Content Intelligence Platform"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.FASTAPI_PORT == 8000
    assert settings.MONGODB_DB_NAME == "content_intelligence_db"

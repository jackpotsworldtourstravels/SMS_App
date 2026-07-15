import os


def _normalize_database_url(raw_url: str | None) -> str | None:
    """Render (and most hosts) hand back postgres:// or plain postgresql://,
    which SQLAlchemy defaults to the psycopg2 driver. This project uses
    psycopg (v3) instead, so force that dialect regardless of what the
    host's connection string scheme says."""

    if not raw_url:
        return raw_url

    if raw_url.startswith("postgres://"):
        raw_url = "postgresql://" + raw_url[len("postgres://"):]

    if raw_url.startswith("postgresql://"):
        raw_url = "postgresql+psycopg://" + raw_url[len("postgresql://"):]

    return raw_url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-dev-secret")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.environ.get("DATABASE_URL"))
    # pool_size/max_overflow are QueuePool (Postgres) options that SQLite's
    # StaticPool rejects outright, so TestConfig overrides this to just
    # {"pool_pre_ping": True}.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEVICE_OFFLINE_THRESHOLD_MINUTES = int(
        os.environ.get("DEVICE_OFFLINE_THRESHOLD_MINUTES", "20")
    )
    HEARTBEAT_INTERVAL_SECONDS = int(
        os.environ.get("HEARTBEAT_INTERVAL_SECONDS", "1200")
    )

    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    ENABLE_STATUS_SWEEP = True


class DevConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProdConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "sqlite:///:memory:",
    )
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    ENABLE_STATUS_SWEEP = False

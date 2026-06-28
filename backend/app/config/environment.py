from app.config.settings import settings


def is_production() -> bool:
    return settings.PROJECT_NAME.lower().find("production") >= 0

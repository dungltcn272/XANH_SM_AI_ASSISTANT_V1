from app.config.settings import settings


def groq_configured() -> bool:
    return bool(settings.GROQ_API_KEY)

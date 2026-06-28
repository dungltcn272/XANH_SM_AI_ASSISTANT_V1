from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config.settings import settings


connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 30}
elif settings.DATABASE_URL.startswith("postgresql"):
    connect_args = {"options": "-c timezone=Asia/Ho_Chi_Minh"}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)


@event.listens_for(engine, "connect")
def set_connection_timezone(dbapi_connection, connection_record) -> None:
    if not settings.DATABASE_URL.startswith("postgresql"):
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SET TIME ZONE 'Asia/Ho_Chi_Minh'")
    finally:
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

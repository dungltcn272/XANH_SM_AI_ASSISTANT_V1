from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Configure SQLite specific options for thread safety and timeout to prevent locking crashes
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 30}
elif settings.DATABASE_URL.startswith("postgresql"):
    connect_args = {"options": "-c timezone=Asia/Ho_Chi_Minh"}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)


@event.listens_for(engine, "connect")
def set_connection_timezone(dbapi_connection, connection_record):
    if not settings.DATABASE_URL.startswith("postgresql"):
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SET TIME ZONE 'Asia/Ho_Chi_Minh'")
    finally:
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os
import datetime
import threading
import sys
import json
from typing import Optional, Any

LOCK = threading.Lock()

def log_event(
    level: str, 
    phase: str, 
    message: str, 
    error_type: Optional[str] = None, 
    details: Any = None,
    query: Optional[str] = None,
    intent: Optional[str] = None
):
    # Tắt hoàn toàn việc log INFO theo yêu cầu của user
    if level.upper() == "INFO":
        return

    # Auto-resolve error type if exception context exists
    if level.upper() in ("ERROR", "WARN") and not error_type:
        exc_type, _, _ = sys.exc_info()
        if exc_type is not None:
            error_type = exc_type.__name__
            
    details_str = ""
    if details is not None:
        try:
            if isinstance(details, (dict, list)):
                details_str = json.dumps(details, ensure_ascii=False)
            else:
                details_str = str(details)
        except Exception:
            details_str = str(details)

    # Save to database (ErrorLog table)
    try:
        from app.db.database import SessionLocal
        from app.db.models import ErrorLog
        
        db = SessionLocal()
        try:
            db_log = ErrorLog(
                query=query,
                intent=intent,
                error_stage=phase.upper(),
                error_cause=error_type or "",
                message=message,
                details=details_str
            )
            db.add(db_log)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
    except Exception:
        pass


def log_info(phase: str, message: str, details: Any = None, query: Optional[str] = None, intent: Optional[str] = None):
    # Sẽ bị ignore bên trong log_event, giữ lại hàm để tương thích mã cũ
    log_event("INFO", phase, message, details=details, query=query, intent=intent)

def log_warn(phase: str, message: str, details: Any = None, query: Optional[str] = None, intent: Optional[str] = None):
    log_event("WARN", phase, message, details=details, query=query, intent=intent)

def log_error(phase: str, message: str, error_type: Optional[str] = None, details: Any = None, query: Optional[str] = None, intent: Optional[str] = None):
    log_event("ERROR", phase, message, error_type=error_type, details=details, query=query, intent=intent)


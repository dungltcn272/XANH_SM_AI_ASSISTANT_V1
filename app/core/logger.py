import os
import datetime
import threading
import sys
import json
from typing import Optional, Any

LOCK = threading.Lock()

# Tùy chỉnh mức độ log từ biến môi trường, mặc định là INFO cho mọi thứ.
# Nếu set RAG_LOG_LEVEL=WARN, các log_info của RAG sẽ bị bỏ qua.
RAG_LOG_LEVEL = os.environ.get("RAG_LOG_LEVEL", "INFO").upper()
# Danh sách các phase liên quan đến RAG
RAG_PHASES = {"RAG", "RETRIEVAL", "NLU", "GATEWAY", "CLASSIFIER", "CACHE"}

def log_event(level: str, phase: str, message: str, error_type: Optional[str] = None, details: Any = None):
    # Lọc log INFO của RAG nếu cấu hình yêu cầu
    if level.upper() == "INFO" and phase.upper() in RAG_PHASES and RAG_LOG_LEVEL in ("WARN", "ERROR"):
        return

    timestamp = datetime.datetime.now().isoformat()
    
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
            
    # Print to standard output for cloud logs (Railway) (Disabled per user request)
    # with LOCK:
    #     log_line = f"[{timestamp}] [{level.upper()}] [{phase.upper()}] {message}"
    #     if error_type:
    #         log_line += f" (Error: {error_type})"
    #     if details_str:
    #         log_line += f" | Details: {details_str}"
    #     
    #     if level.upper() in ("ERROR", "WARN"):
    #         sys.stderr.write(log_line + "\n")
    #         sys.stderr.flush()
    #     else:
    #         sys.stdout.write(log_line + "\n")
    #         sys.stdout.flush()

    # Save to database (SystemLog table)
    try:
        from app.db.database import SessionLocal
        from app.db.models import SystemLog
        
        db = SessionLocal()
        try:
            db_log = SystemLog(
                level=level.upper(),
                phase=phase.upper(),
                error_type=error_type or "",
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


def log_info(phase: str, message: str, details: Any = None):
    log_event("INFO", phase, message, details=details)

def log_warn(phase: str, message: str, details: Any = None):
    log_event("WARN", phase, message, details=details)

def log_error(phase: str, message: str, error_type: Optional[str] = None, details: Any = None):
    log_event("ERROR", phase, message, error_type=error_type, details=details)

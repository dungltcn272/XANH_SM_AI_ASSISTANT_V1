import os
import csv
import datetime
import threading
import sys
import json
from typing import Optional, Any

LOCK = threading.Lock()
# Put logs in the root project directory's 'logs' folder
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

def init_logs():
    os.makedirs(LOGS_DIR, exist_ok=True)
    headers = ["timestamp", "level", "phase", "error_type", "message", "details"]
    for filename in ["system_logs.csv", "error_log.csv"]:
        filepath = os.path.join(LOGS_DIR, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

def log_event(level: str, phase: str, message: str, error_type: Optional[str] = None, details: Any = None):
    try:
        init_logs()
    except Exception:
        pass # Safeguard to avoid crashing application if log directory is unwritable
        
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
            
    row = [timestamp, level.upper(), phase.upper(), error_type or "", message, details_str]
    
    # Write to system_logs.csv (all events) and error_log.csv (warn, error)
    targets = ["system_logs.csv"]
    if level.upper() in ("WARN", "ERROR") or error_type:
        targets.append("error_log.csv")
        
    with LOCK:
        for filename in targets:
            filepath = os.path.join(LOGS_DIR, filename)
            try:
                with open(filepath, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
            except Exception:
                pass

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

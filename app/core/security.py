from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, GuestSession
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_entity(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        return {"type": "anonymous", "entity": None}
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        entity_type = payload.get("type")
        entity_id = payload.get("sub")
        
        if entity_type == "user":
            user = db.query(User).filter(User.id == entity_id).first()
            if user:
                return {"type": "user", "entity": user}
                
        elif entity_type == "guest":
            session = db.query(GuestSession).filter(GuestSession.session_token == entity_id).first()
            if session:
                return {"type": "guest", "entity": session}
                
    except JWTError:
        pass
        
    return {"type": "anonymous", "entity": None}

def get_current_admin(entity: dict = Depends(get_current_entity)):
    if entity["type"] != "user" or entity["entity"].role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return entity["entity"]

from sqlalchemy.orm import Session

from app.db.models import DocumentChunk


def list_document_chunks(db: Session, limit: int = 50) -> list[DocumentChunk]:
    return db.query(DocumentChunk).limit(limit).all()

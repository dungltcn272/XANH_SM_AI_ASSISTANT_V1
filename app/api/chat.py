from pydantic import BaseModel
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Conversation
from app.core.security import get_current_entity
from app.rag.pipeline import stream_chat_pipeline
from app.core.logger import log_error
from typing import Optional, AsyncGenerator
import asyncio

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    image_base64: Optional[str] = None
    deep_search: bool = False


async def _run_stream_in_thread(gen_func, **kwargs) -> AsyncGenerator[str, None]:
    """
    Wraps a synchronous generator inside an async generator by running it
    in a dedicated OS thread and passing chunks to a native asyncio.Queue.
    This prevents thread pool thrashing (calling run_in_executor for hundreds of
    stream tokens), which causes thread pool exhaustion and net::ERR_CONNECTION_RESET.
    """
    import asyncio
    import threading
    from app.db.database import SessionLocal

    loop = asyncio.get_event_loop()
    async_queue = asyncio.Queue()
    SENTINEL = object()

    def run_sync():
        # Create a fresh database session inside the background thread to avoid SQLite cross-thread access
        # and dependency lifecycle issues (session closed by FastAPI before streaming completes)
        db_session = SessionLocal()
        kwargs['db'] = db_session
        try:
            for chunk in gen_func(**kwargs):
                loop.call_soon_threadsafe(async_queue.put_nowait, chunk)
        except Exception as e:
            log_error("CHAT", f"Exception in chat stream background thread: {e}")
            loop.call_soon_threadsafe(async_queue.put_nowait, e)
        finally:
            db_session.close()
            loop.call_soon_threadsafe(async_queue.put_nowait, SENTINEL)

    thread = threading.Thread(target=run_sync, daemon=True)
    thread.start()

    while True:
        # Get next item from async queue natively and non-blockingly without threadpool overhead
        item = await async_queue.get()
        if item is SENTINEL:
            break
        if isinstance(item, Exception):
            # Yield fallback error message instead of crashing
            yield f"data: Xin loi, he thong gap su co. Vui long thu lai.\n\n"
            yield "data: [DONE]\n\n"
            break
        yield item


@router.post("")
async def chat_endpoint(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_entity: dict = Depends(get_current_entity)
):
    entity_type = current_entity.get("type")
    entity_obj = current_entity.get("entity")

    # Tạo hoặc lấy conversation
    conv_id = req.conversation_id
    if conv_id:
        # Ensure conversation exists to satisfy PostgreSQL strict foreign key constraints
        existing_conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not existing_conv:
            new_conv = Conversation(id=conv_id)
            if entity_type == "user" and entity_obj:
                new_conv.user_id = entity_obj.id
            elif entity_type == "guest" and entity_obj:
                new_conv.guest_id = entity_obj.id
            db.add(new_conv)
            db.commit()
    else:
        new_conv = Conversation()
        if entity_type == "user" and entity_obj:
            new_conv.user_id = entity_obj.id
        elif entity_type == "guest" and entity_obj:
            new_conv.guest_id = entity_obj.id
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        conv_id = new_conv.id

    user_identifier = entity_obj.id if entity_obj else "anonymous"

    return StreamingResponse(
        _run_stream_in_thread(
            stream_chat_pipeline,
            db=db,
            user_id=user_identifier,
            conversation_id=conv_id,
            question=req.query,
            image_base64=req.image_base64,
            is_deep_search=req.deep_search
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


from typing import AsyncGenerator, Optional

import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.assistant.personas import get_persona_config
from app.assistant.pipeline import stream_chat_pipeline
from app.core.logger import log_error
from app.core.security import get_current_entity
from app.db.database import get_db
from app.db.models import Conversation

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    display_query: Optional[str] = None
    conversation_id: Optional[str] = None
    image_base64: Optional[str] = None
    deep_search: bool = False
    persona: str = "customer"


async def _run_stream_in_thread(gen_func, **kwargs) -> AsyncGenerator[str, None]:
    """
    Run a synchronous streaming generator on a dedicated thread and bridge
    chunks back into the async response without exhausting the thread pool.
    """
    import threading

    from app.db.database import SessionLocal

    loop = asyncio.get_event_loop()
    async_queue = asyncio.Queue()
    sentinel = object()

    def run_sync() -> None:
        db_session = SessionLocal()
        kwargs["db"] = db_session
        try:
            for chunk in gen_func(**kwargs):
                loop.call_soon_threadsafe(async_queue.put_nowait, chunk)
        except Exception as exc:
            log_error("CHAT", f"Exception in chat stream background thread: {exc}")
            loop.call_soon_threadsafe(async_queue.put_nowait, exc)
        finally:
            db_session.close()
            loop.call_soon_threadsafe(async_queue.put_nowait, sentinel)

    thread = threading.Thread(target=run_sync, daemon=True)
    thread.start()

    while True:
        item = await async_queue.get()
        if item is sentinel:
            break
        if isinstance(item, Exception):
            yield "data: Xin loi, he thong gap su co. Vui long thu lai.\n\n"
            yield "data: [DONE]\n\n"
            break
        yield item


@router.post("")
async def chat_endpoint(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_entity: dict = Depends(get_current_entity),
):
    entity_type = current_entity.get("type")
    entity_obj = current_entity.get("entity")
    actor_id = getattr(entity_obj, "id", None)
    persona_config = get_persona_config(req.persona)
    persona_id = persona_config.persona_id.value

    conv_id = req.conversation_id
    if conv_id:
        conversation = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conversation:
            conversation = Conversation(id=conv_id, actor_id=actor_id, persona_id=persona_id)
            db.add(conversation)
            db.commit()
        elif conversation.persona_id != persona_id:
            conversation.persona_id = persona_id
            db.commit()
    else:
        conversation = Conversation(actor_id=actor_id, persona_id=persona_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conv_id = conversation.id

    return StreamingResponse(
        _run_stream_in_thread(
            stream_chat_pipeline,
            db=db,
            user_id=actor_id or "anonymous",
            entity_type=entity_type,
            conversation_id=conv_id,
            question=req.query,
            display_query=req.display_query,
            image_base64=req.image_base64,
            is_deep_search=req.deep_search,
            persona=persona_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )

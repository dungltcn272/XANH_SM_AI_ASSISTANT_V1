from __future__ import annotations

import os
import sys
from pathlib import Path


DB_PATH = Path("tmp_smoke_backend.db")
os.environ["DATABASE_URL"] = f"sqlite:///./{DB_PATH.as_posix()}"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

import app.db.base  # noqa: E402,F401
from app.assistant.memory.user_profile_memory import get_profile_snapshot, refresh_profile_snapshot  # noqa: E402
from app.config.settings import settings  # noqa: E402
from app.db.models import Actor, FaqCandidate, FaqEntry, FaqQuestionVariant, Memory, Persona  # noqa: E402
from app.db.session import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


def _seed_persona(db) -> None:
    if not db.query(Persona).filter(Persona.id == "customer").first():
        db.add(Persona(id="customer", name="Customer", default_prompt_key="customer_persona"))
        db.commit()


def run() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    _seed_persona(db)
    db.close()

    client = TestClient(app)

    guest = client.post("/api/v1/auth/guest")
    assert guest.status_code == 200, guest.text
    token = guest.json()["access_token"]

    chat = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "Dat xe tu Vinhomes Central Park den san bay tan son nhat", "persona": "customer"},
    )
    assert chat.status_code == 200, chat.text
    assert "ride_support" in chat.text, chat.text[:500]

    db = SessionLocal()
    _seed_persona(db)
    db.add(
        FaqEntry(
            id="faq_smoke",
            persona_id="customer",
            canonical_question="Tong dai Xanh SM la gi?",
            canonical_answer="Dạ anh/chị, tổng đài Xanh SM là 1900 2088.",
            intent="rag",
            scope="public",
            status="published",
        )
    )
    db.add(FaqQuestionVariant(faq_entry_id="faq_smoke", question_text="Tong dai Xanh SM la gi?", normalized_question="tong dai xanh sm la gi"))
    db.commit()
    db.close()

    cache = client.get("/api/v1/rag/answer", params={"q": "Tong dai Xanh SM la gi?"})
    assert cache.status_code == 200, cache.text
    assert cache.json().get("cache", {}).get("hit") is True, cache.json()

    db = SessionLocal()
    actor = Actor(actor_type="customer", display_name="Smoke User")
    db.add(actor)
    db.commit()
    db.refresh(actor)
    db.add(Memory(actor_id=actor.id, persona_id="customer", memory_type="preference", scope="food", content="Anh/chị thích món ít cay.", confidence=0.9, status="active"))
    db.commit()
    profile = refresh_profile_snapshot(db, actor_id=actor.id, persona_id="customer")
    loaded = get_profile_snapshot(db, actor_id=actor.id, persona_id="customer")
    assert profile["source_count"] == 1
    assert len(loaded["food"]["preferences"]) == 1
    memory_id = db.query(Memory).filter(Memory.actor_id == actor.id).first().id
    db.close()

    actor_token = client.post("/api/v1/auth/guest").json()["access_token"]
    db = SessionLocal()
    from app.db.models import ActorIdentity

    guest_identity = db.query(ActorIdentity).order_by(ActorIdentity.created_at.desc()).first()
    db.query(Memory).filter(Memory.id == memory_id).update({"actor_id": guest_identity.actor_id})
    db.commit()
    db.close()
    memories = client.get("/api/v1/memories", headers={"Authorization": f"Bearer {actor_token}"})
    assert memories.status_code == 200, memories.text
    assert len(memories.json()) >= 1
    forget = client.post(f"/api/v1/memories/{memory_id}/forget", headers={"Authorization": f"Bearer {actor_token}"})
    assert forget.status_code == 200, forget.text

    admin = client.post("/api/v1/auth/admin-login", json={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD})
    assert admin.status_code == 200, admin.text
    admin_token = admin.json()["access_token"]
    db = SessionLocal()
    db.add(
        FaqCandidate(
            id="faqcand_smoke",
            persona_id="customer",
            user_query="Gia cuoc Xanh SM?",
            canonical_question="Gia cuoc Xanh SM?",
            proposed_answer="Dạ anh/chị, giá cước phụ thuộc dịch vụ và khu vực.",
            eligibility_score=0.9,
            status="candidate",
        )
    )
    db.commit()
    db.close()
    candidates = client.get("/api/v1/admin/faq-candidates", headers={"Authorization": f"Bearer {admin_token}"})
    assert candidates.status_code == 200, candidates.text
    publish = client.post("/api/v1/admin/faq-candidates/faqcand_smoke/publish", headers={"Authorization": f"Bearer {admin_token}"}, json={})
    assert publish.status_code == 200, publish.text

    print("backend smoke: ok")


if __name__ == "__main__":
    try:
        run()
    finally:
        engine.dispose()
        if DB_PATH.exists():
            try:
                DB_PATH.unlink()
            except PermissionError:
                pass

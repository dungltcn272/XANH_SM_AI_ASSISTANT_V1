# Xanh SM Modular Backend

Source chinh nam trong `backend/app`.

## Runtime Layers

- `api/v1`: FastAPI routes.
- `assistant`: orchestrator, NLU, memory, persona, prompt, policy.
- `domains`: RAG, food, ride, driver, merchant, operator, executive.
- `tools`: LangChain/tool adapters over domain services.
- `integrations`: OpenAI, Groq, Cohere, Google, external clients.
- `db`: SQLAlchemy session, models, repositories.
- `schemas`: Pydantic request/response contracts.
- `cache`, `vectorstore`, `voice`, `realtime`, `workers`: supporting runtime modules.

## API Contract

FE doc: [docs/API_CONTRACT.md](docs/API_CONTRACT.md).

## Run Local

Run from repo root:

```powershell
cd backend
..\venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

For LAN access:

```powershell
cd backend
..\venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

## Migrations

Run Alembic from repo root:

```powershell
.\venv\Scripts\alembic.exe upgrade head
```

`alembic/env.py` adds `backend/` to `sys.path`, so imports resolve to `backend/app`.

## Docker

Dockerfile stays at repo root for Railway/Docker build context, but runtime imports come from `backend/app` via `PYTHONPATH=/app/backend`. There is no root `app/` shim anymore.

## Verify

```powershell
cd backend
..\venv\Scripts\python.exe -m compileall app
```

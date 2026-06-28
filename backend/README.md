# Xanh SM Modular Backend

Source chính nằm trong `backend/app`.

## Runtime Layers

- `api/v1`: route mỏng, chỉ validate request và gọi service/runtime.
- `assistant`: AI Brain gồm orchestrator, persona, memory, NLU, policy, prompt.
- `domains`: business logic theo RAG, food, ride, driver, merchant, operator, executive, travel, commerce, user.
- `tools`: adapter cho agent gọi domain service.
- `integrations`: client ra dịch vụ ngoài.
- `db`: session, model, repository, seed/migration boundary.
- `schemas`: Pydantic request/response contract.
- `voice`, `realtime`, `ml`, `vectorstore`, `cache`, `workers`: module mở rộng đúng kiến trúc mục tiêu.

## API Contract

FE đọc [docs/API_CONTRACT.md](docs/API_CONTRACT.md).

## Run

```powershell
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

## Docker

Dockerfile hiện đặt ở repo root để Railway/Docker build lấy được `requirements.txt`, `alembic`, shim `app/` và source `backend/app` trong cùng build context. Nếu tách backend thành repo riêng sau này thì mới nên chuyển Dockerfile vào `backend/`.

## Verify

```powershell
.\venv\Scripts\python.exe -m compileall app backend/app
```

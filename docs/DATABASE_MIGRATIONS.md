# Database migrations

Project này dùng Alembic để quản lý thay đổi schema database. App không tự chạy
`Base.metadata.create_all()` hay `app/db/migrations.py` khi startup nữa.

## Ý chính cần nhớ

Khi muốn thay đổi database, không phải chỉ sửa model rồi chạy `alembic upgrade head`.

Flow đúng là:

1. Sửa SQLAlchemy model trong `app/db/models.py`.
2. Tạo migration file mới bằng `alembic revision --autogenerate`.
3. Review file migration vừa sinh trong `alembic/versions/`.
4. Chạy `alembic upgrade head` để áp dụng migration vào database.
5. Commit cả model và migration file.

Nói ngắn gọn: `revision --autogenerate` tạo bản kế hoạch thay đổi DB, còn
`upgrade head` thực thi bản kế hoạch đó.

## Deploy bằng Docker

Docker image sẽ tự chạy migration trước khi start API:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

Lệnh này nằm trong `Dockerfile`, nên mỗi lần deploy container mới, database sẽ được
cập nhật đến revision mới nhất trước khi FastAPI nhận request.

## Khi muốn thay đổi database

1. Sửa SQLAlchemy model trong `app/db/models.py`.

Ví dụ thêm một cột mới:

```python
class FoodCatalog(Base):
    __tablename__ = "food_catalog"

    item_id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
```

2. Tạo migration mới:

```bash
alembic revision --autogenerate -m "describe your change"
```

Ví dụ:

```bash
alembic revision --autogenerate -m "add is_active to food catalog"
```

3. Mở file mới trong `alembic/versions/` và review kỹ `upgrade()` / `downgrade()`.
   Alembic autogenerate rất hữu ích, nhưng không nên commit migration mà chưa đọc.

Ví dụ migration có thể trông như sau:

```python
def upgrade() -> None:
    op.add_column("food_catalog", sa.Column("is_active", sa.Boolean(), nullable=True))
    op.create_index(op.f("ix_food_catalog_is_active"), "food_catalog", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_food_catalog_is_active"), table_name="food_catalog")
    op.drop_column("food_catalog", "is_active")
```

4. Chạy migration ở local:

```bash
alembic upgrade head
```

5. Test backend:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

6. Commit cả model và migration:

```bash
git add app/db/models.py alembic/ docs/DATABASE_MIGRATIONS.md
git commit -m "add database migration for ..."
```

7. Deploy. Docker sẽ tự chạy `alembic upgrade head`.

## Database đã tồn tại trước khi dùng Alembic

Baseline đầu tiên là `20260620_0001_initial_schema`. Migration này dùng
`Base.metadata.create_all()`, nên:

- Database mới: Alembic tạo các bảng hiện có trong model.
- Database đã có bảng: Alembic không tạo lại bảng đã tồn tại, sau đó ghi version vào
  bảng `alembic_version`.

Nếu database production đang lệch xa model hiện tại, hãy backup database trước, chạy
migration trên staging, rồi mới deploy production.

## Một số lệnh hay dùng

Xem revision hiện tại của database:

```bash
alembic current
```

Xem migration mới nhất trong code:

```bash
alembic heads
```

Nâng database lên bản mới nhất:

```bash
alembic upgrade head
```

Rollback một migration:

```bash
alembic downgrade -1
```

## Nguyên tắc

- Không sửa database production bằng tay nếu thay đổi đó cần tồn tại lâu dài.
- Không dùng `app/db/migrations.py` cho thay đổi schema mới.
- Không để deploy tự sinh migration bằng `--autogenerate`; deploy chỉ chạy migration file đã được commit.
- Luôn review migration trước khi commit, nhất là các lệnh drop column/table.

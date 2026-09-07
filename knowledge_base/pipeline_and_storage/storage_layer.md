# Storage Layer & Async Database Engine

> Implementation: [database/connection.py](file:///e:/study/ASTRA/ast-triage-core/database/connection.py) and [database/models.py](file:///e:/study/ASTRA/ast-triage-core/database/models.py)

ASTRA uses an asynchronous relational database architecture powered by SQLAlchemy 2.0 and `aiosqlite` (with seamless configuration for `asyncpg` in PostgreSQL production deployments).

---

## 1. Engine Initialization and Connection Pooling

Located in [database/connection.py](file:///e:/study/ASTRA/ast-triage-core/database/connection.py):

- **Cached Engine Singleton**:
  ```python
  @lru_cache()
  def get_async_engine() -> AsyncEngine:
      settings = get_settings()
      connect_args = {}
      if settings.DATABASE_URL.startswith("sqlite"):
          connect_args["check_same_thread"] = False

      return create_async_engine(
          settings.DATABASE_URL,
          echo=settings.DEBUG,
          connect_args=connect_args,
      )
  ```
- **SQLite Concurrency Support**: SQLite connections in multi-threaded environments require `check_same_thread=False` to prevent thread affinity exceptions during asynchronous task handoffs.
- **Production Dialect Switch**: Swapping from development SQLite (`sqlite+aiosqlite:///./data/astra.db`) to PostgreSQL (`postgresql+asyncpg://user:pass@host/db`) requires only modifying the `DATABASE_URL` environment variable in `.env`.

---

## 2. Session Lifecycle and Generator Pattern

Database operations must use the async context manager factory to guarantee proper session cleanup and connection release:

```python
@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

- **Automatic Rollback**: Any unhandled exception during feature persistence triggers an immediate rollback before bubbling up.
- **Strict Async Discipline**: Direct blocking database queries (`session.query()`) are forbidden. All queries must use SQLAlchemy 2.0 executable select statements (`await session.execute(select(...))`).

---

## 3. Database Initialization Gate

The schema can be initialized or verified from the command line:

```powershell
python -c "import asyncio; from database.connection import init_db; asyncio.run(init_db())"
```

This runs `Base.metadata.create_all()` across all registered models ([Repository](file:///e:/study/ASTRA/ast-triage-core/database/models.py#L42-L68), [PullRequest](file:///e:/study/ASTRA/ast-triage-core/database/models.py#L71-L136), [FeatureRecord](file:///e:/study/ASTRA/ast-triage-core/database/models.py#L138-L245), [TriagePrediction](file:///e:/study/ASTRA/ast-triage-core/database/models.py#L248-L306)).

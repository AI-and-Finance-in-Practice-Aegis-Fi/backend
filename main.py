import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

_SEQUENCES = [
    ('department',        'department_id'),
    ('employee',          'employee_id'),
    ('saas_subscription', 'subscription_id'),
    ('saas_usage',        'usage_id'),
    ('transaction',       'transaction_id'),
    ('ai_payment_policy', 'policy_id'),
    ('approval_log',      'approval_id'),
    ('audit_log',         'audit_id'),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 시퀀스 동기화 (seed 데이터 삽입 후 시퀀스가 뒤처진 경우 복구)
    async with AsyncSessionLocal() as db:
        for table, col in _SEQUENCES:
            try:
                await db.execute(text(
                    f"SELECT setval("
                    f"pg_get_serial_sequence('{table}', '{col}'), "
                    f"COALESCE((SELECT MAX({col}) FROM {table}), 1)"
                    f")"
                ))
            except Exception as e:
                logger.warning("Sequence sync failed for %s.%s: %s", table, col, e)
        await db.commit()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

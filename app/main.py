from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .lifecycle import lifecycle
from .auth import verify_api_key
from .config import get_settings
from .cost_guard import CostGuard
from .logging_utils import log_event
from .rate_limiter import RateLimiter
from .store import ConversationStore, get_redis_client


SERVICE_NAME = "production-agent"
SERVICE_VERSION = "1.0.0"


# ============================================================
# Request model
# ============================================================

class AskRequest(BaseModel):
    question: str = Field(min_length=1)


# ============================================================
# Redis / Store dependencies
# ============================================================

def get_store() -> ConversationStore:
    """Tạo ConversationStore dùng Redis."""
    settings = get_settings()
    client = get_redis_client(settings.redis_url)
    return ConversationStore(client)


def get_rate_limiter() -> RateLimiter:
    """Tạo RateLimiter từ cấu hình."""
    settings = get_settings()
    client = get_redis_client(settings.redis_url)

    return RateLimiter(
        client=client,
        limit_per_minute=settings.rate_limit_per_minute,
    )


def get_cost_guard() -> CostGuard:
    """Tạo CostGuard từ cấu hình."""
    settings = get_settings()
    client = get_redis_client(settings.redis_url)

    return CostGuard(
        client=client,
        monthly_budget_usd=settings.monthly_budget_usd,
    )


# ============================================================
# LLM
# ============================================================

def ask_llm(question: str, history: list[dict]) -> dict:
    """Mock LLM dùng cho CP3."""

    answer = f"Mock answer: {question}"

    tokens_in = max(1, len(question.split()))
    tokens_out = 10

    # Chi phí nhỏ nhưng > 0 để test CostGuard.record()
    cost_usd = 0.0000222

    return {
        "answer": answer,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": cost_usd,
    }


# ============================================================
# Lifespan
# ============================================================

@asynccontextmanager
async def lifespan(_app: FastAPI):
    lifecycle.install()

    log_event(
        "service_started",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
    )

    yield

    log_event(
        "service_stopped",
        service=SERVICE_NAME,
    )


# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(
    title=SERVICE_NAME,
    version=SERVICE_VERSION,
    lifespan=lifespan,
)


# ============================================================
# Health check
# ============================================================

@app.get("/health")
def health():
    """Liveness check.

    /health chỉ kiểm tra process có đang shutdown hay không.
    Không kiểm tra Redis.
    """

    if lifecycle.shutting_down:
        return JSONResponse(
            status_code=503,
            content={"status": "shutting_down"},
        )

    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }


# ============================================================
# Readiness check
# ============================================================

@app.get("/ready")
def ready(
    store: ConversationStore = Depends(get_store),
):
    """Readiness check.

    Instance chỉ được xem là ready khi:
      1. Process chưa shutdown.
      2. Redis đang hoạt động.
    """

    # Process đang shutdown -> không nhận traffic mới
    if lifecycle.shutting_down:
        return JSONResponse(
            status_code=503,
            content={"status": "shutting_down"},
        )

    # Redis không hoạt động -> không sẵn sàng phục vụ
    if not store.ping():
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready"},
        )

    return {
        "status": "ready",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }


# ============================================================
# Main endpoint
# ============================================================

@app.post("/ask")
def ask(
    payload: AskRequest,
    user_id: str = Depends(verify_api_key),
    store: ConversationStore = Depends(get_store),
    limiter: RateLimiter = Depends(get_rate_limiter),
    guard: CostGuard = Depends(get_cost_guard),
):
    """
    Hỏi agent một câu.

    CP3 yêu cầu thứ tự:

        1. verify_api_key
        2. limiter.check
        3. guard.check
        4. store.get_history
        5. ask_llm
        6. store.append user
        7. store.append assistant
        8. guard.record
        9. log_event
        10. response
    """

    # 1. API key đã được kiểm tra bởi Depends(verify_api_key)

    # 2. Rate limit
    limiter.check(user_id)

    # 3. Cost guard
    # Phải kiểm tra trước khi gọi LLM.
    guard.check(user_id)

    # 4. Lấy lịch sử hội thoại
    history = store.get_history(user_id)
    history_length = len(history)

    # 5. Gọi LLM
    result = ask_llm(
        payload.question,
        history,
    )

    answer = result["answer"]
    tokens_in = result["tokens_in"]
    tokens_out = result["tokens_out"]
    cost_usd = result["cost_usd"]

    # 6. Lưu câu hỏi user
    store.append(
        user_id,
        "user",
        payload.question,
    )

    # 7. Lưu câu trả lời assistant
    store.append(
        user_id,
        "assistant",
        answer,
    )

    # 8. Ghi nhận chi phí thực tế
    total_spent = guard.record(
        user_id,
        cost_usd,
    )

    # 9. Structured log
    log_event(
        "ask_completed",
        user_id=user_id,
        cost=cost_usd,
        total_spent=total_spent,
    )

    # 10. Response
    return {
        "answer": answer,
        "user_id": user_id,
        "history_length": history_length,
        "cost_usd": cost_usd,
        "tokens": tokens_in + tokens_out,
    }
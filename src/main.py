from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from src.exception import rate_limit_exceeded_handler, unhandled_exception_handler
from src.health import router as health_router
from src.recording import router as recording_router
from src.shared.audit.middleware import audit_request_middleware
from src.shared.config import settings
from src.shared.database.engine import close_database, init_database
from src.shared.rate_limit import global_rate_limit_middleware, limiter


@asynccontextmanager
async def lifespan(app: FastAPI):  # pyright: ignore[reportUnusedParameter]
    settings.recordings_dir.mkdir(parents=True, exist_ok=True)
    await init_database()
    yield
    await close_database()


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter

# Middlewares (the last one added is the outermost)
app.add_middleware(BaseHTTPMiddleware, dispatch=audit_request_middleware)
# Outside the audit, so a flood rejected by the global limit doesn't fill audit_request
app.add_middleware(BaseHTTPMiddleware, dispatch=global_rate_limit_middleware)

# Exception handlers
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Routes
app.include_router(health_router)
app.include_router(recording_router)

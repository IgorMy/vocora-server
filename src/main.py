from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse
from scalar_fastapi import (
    Layout,
    get_scalar_api_reference,  # pyright: ignore[reportUnknownVariableType]
)
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from src.exception import rate_limit_exceeded_handler, unhandled_exception_handler
from src.health import router as health_router
from src.recording import router as recording_router
from src.shared.audit.middleware import audit_request_middleware
from src.shared.config import settings
from src.shared.database.engine import close_database, init_database
from src.shared.rate_limit import global_rate_limit_middleware, limiter
from src.shared.version import (
    API_PREFIX,
    DOCS_URL,
    OPENAPI_URL,
    VERSION,
)


@asynccontextmanager
async def lifespan(app: FastAPI):  # pyright: ignore[reportUnusedParameter]
    settings.recordings_dir.mkdir(parents=True, exist_ok=True)
    await init_database()
    yield
    await close_database()


app = FastAPI(
    title="Vocora API",
    version=VERSION,
    # Swagger UI and ReDoc are replaced by Scalar, served at DOCS_URL below
    docs_url=None,
    redoc_url=None,
    openapi_url=OPENAPI_URL,
    lifespan=lifespan,
)
app.state.limiter = limiter

# Middlewares (the last one added is the outermost)
app.add_middleware(BaseHTTPMiddleware, dispatch=audit_request_middleware)
# Outside the audit, so a flood rejected by the global limit doesn't fill audit_request
app.add_middleware(BaseHTTPMiddleware, dispatch=global_rate_limit_middleware)

# Exception handlers
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Routes
@app.get(DOCS_URL, include_in_schema=False)
async def docs() -> HTMLResponse:
    return get_scalar_api_reference(
        openapi_url=OPENAPI_URL,
        title=app.title,
        layout=Layout.CLASSIC,
        # Name of the scheme FastAPI generates for HTTPBearer (see require_token)
        authentication={"preferredSecurityScheme": "HTTPBearer"},
        # Keep the token in the browser's localStorage across reloads and restarts
        persist_auth=True,
    )


# Infrastructure, outside the API version: its path must not change between versions
app.include_router(health_router)

# Versioned API (/v{major}), consumed by the app
api_router = APIRouter(prefix=API_PREFIX)
api_router.include_router(recording_router)
app.include_router(api_router)

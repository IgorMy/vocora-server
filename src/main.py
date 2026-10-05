from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.exception import unhandled_exception_handler
from src.health import router as health_router
from src.shared.config import settings
from src.shared.database.engine import close_database, init_database


@asynccontextmanager
async def lifespan(app: FastAPI):  # pyright: ignore[reportUnusedParameter]
    settings.recordings_dir.mkdir(parents=True, exist_ok=True)
    await init_database()
    yield
    await close_database()


app = FastAPI(lifespan=lifespan)

# Exception handlers
app.add_exception_handler(Exception, unhandled_exception_handler)

# Routes
app.include_router(health_router)
